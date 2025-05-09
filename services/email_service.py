# services/email_service.py - Služba pro práci s emaily

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

class EmailService:
    """Služba pro odesílání a příjem emailů."""
    
    def __init__(self, config: dict):
        """
        Inicializace služby s konfigurací.
        
        Args:
            config: Slovník s konfigurací pro SMTP a IMAP servery
        """
        self.smtp_server = config.get('MAIL_SERVER', 'smtp.example.com')
        self.smtp_port = config.get('MAIL_PORT', 587)
        self.use_tls = config.get('MAIL_USE_TLS', True)
        self.username = config.get('MAIL_USERNAME', '')
        self.password = config.get('MAIL_PASSWORD', '')
        self.default_sender = config.get('MAIL_DEFAULT_SENDER', '')
        
        # IMAP konfigurace
        self.imap_server = config.get('IMAP_SERVER', self.smtp_server)
        self.imap_port = config.get('IMAP_PORT', 993)
    
    def send_email(self, recipient: str, subject: str, body: str, 
                   html_body: Optional[str] = None, 
                   attachments: List[str] = None) -> Dict[str, Any]:
        """
        Odešle email.
        
        Args:
            recipient: Email příjemce
            subject: Předmět emailu
            body: Tělo emailu v plain textu
            html_body: Tělo emailu v HTML (volitelné)
            attachments: Seznam cest k souborům pro přílohy
            
        Returns:
            Výsledek operace jako slovník
        """
        msg = MIMEMultipart('alternative')
        msg['From'] = self.default_sender
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Plain text verze
        msg.attach(MIMEText(body, 'plain'))
        
        # HTML verze (pokud je poskytnuta)
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        # Přílohy
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        attachment = MIMEApplication(file.read(), Name=os.path.basename(file_path))
                        attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(attachment)
        
        try:
            # Připojení k SMTP serveru
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            
            # Přihlášení
            if self.username and self.password:
                server.login(self.username, self.password)
            
            # Odeslání emailu
            server.send_message(msg)
            server.quit()
            
            return {
                'status': 'success',
                'message': f'Email odeslán na {recipient}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_inbox(self, limit: int = 10, folder: str = 'INBOX', 
                    unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Zkontroluje doručenou poštu.
        
        Args:
            limit: Maximální počet emailů k načtení
            folder: Složka ke kontrole
            unread_only: Zda načíst pouze nepřečtené emaily
            
        Returns:
            Seznam emailů jako slovníky
        """
        results = []
        
        try:
            # Připojení k IMAP serveru
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.username, self.password)
            mail.select(folder)
            
            # Vyhledání emailů
            search_criterion = 'UNSEEN' if unread_only else 'ALL'
            status, data = mail.search(None, search_criterion)
            email_ids = data[0].split()
            
            # Omezení počtu emailů
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            for email_id in email_ids:
                status, data = mail.fetch(email_id, '(RFC822)')
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Dekódování předmětu
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')
                
                # Dekódování odesílatele
                from_header, encoding = decode_header(msg['From'])[0]
                if isinstance(from_header, bytes):
                    from_header = from_header.decode(encoding if encoding else 'utf-8')
                
                # Získání data
                date_str = msg['Date']
                date_obj = None
                try:
                    # Pokus o parsování data
                    date_tuple = email.utils.parsedate_tz(date_str)
                    if date_tuple:
                        date_obj = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                except Exception:
                    date_obj = None
                
                # Získání těla emailu
                body = ""
                html_body = ""
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get('Content-Disposition'))
                        
                        # Přeskočení příloh
                        if 'attachment' in content_disposition:
                            continue
                        
                        # Extrakce textu
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset()
                            if not charset:
                                charset = 'utf-8'
                            
                            try:
                                decoded_payload = payload.decode(charset)
                                if content_type == 'text/plain':
                                    body = decoded_payload
                                elif content_type == 'text/html':
                                    html_body = decoded_payload
                            except Exception:
                                # Při chybě dekódování použijeme UTF-8 s nahrazením znaků
                                try:
                                    decoded_payload = payload.decode('utf-8', 'replace')
                                    if content_type == 'text/plain':
                                        body = decoded_payload
                                    elif content_type == 'text/html':
                                        html_body = decoded_payload
                                except Exception:
                                    pass
                else:
                    # Email není multipart
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset()
                        if not charset:
                            charset = 'utf-8'
                        
                        try:
                            body = payload.decode(charset)
                        except Exception:
                            # Při chybě dekódování použijeme UTF-8 s nahrazením znaků
                            body = payload.decode('utf-8', 'replace')
                
                # Přidání emailu do výsledků
                email_data = {
                    'id': email_id.decode(),
                    'subject': subject,
                    'from': from_header,
                    'date': date_obj.isoformat() if date_obj else date_str,
                    'body': body[:500] + "..." if len(body) > 500 else body,
                    'html_body': html_body[:500] + "..." if len(html_body) > 500 else html_body,
                    'has_attachments': any('attachment' in str(part.get('Content-Disposition', '')) for part in msg.walk())
                }
                
                results.append(email_data)
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            # Při chybě přidáme informaci o chybě do výsledků
            results.append({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return results
    
    def create_email_template(self, name: str, subject: str, body: str, 
                             html_body: Optional[str] = None) -> Dict[str, Any]:
        """
        Vytvoří šablonu emailu pro pozdější použití.
        
        Args:
            name: Název šablony
            subject: Předmět emailu
            body: Tělo emailu v plain textu
            html_body: Tělo emailu v HTML (volitelné)
            
        Returns:
            Výsledek operace jako slovník
        """
        # V reálné aplikaci bychom šablonu uložili do databáze
        # Pro demonstraci vrátíme jen informaci o vytvořené šabloně
        template = {
            'name': name,
            'subject': subject,
            'body': body,
            'html_body': html_body,
            'created_at': datetime.now().isoformat()
        }
        
        return {
            'status': 'success',
            'message': f'Šablona emailu "{name}" byla vytvořena',
            'template': template
        }
    
    def get_email_attachment(self, email_id: str, attachment_index: int, 
                           save_path: str, folder: str = 'INBOX') -> Dict[str, Any]:
        """
        Stáhne přílohu z konkrétního emailu.
        
        Args:
            email_id: ID emailu
            attachment_index: Index přílohy (0-based)
            save_path: Cesta pro uložení přílohy
            folder: Složka, ve které se email nachází
            
        Returns:
            Výsledek operace jako slovník
        """
        try:
            # Připojení k IMAP serveru
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.username, self.password)
            mail.select(folder)
            
            # Načtení emailu
            status, data = mail.fetch(email_id.encode() if isinstance(email_id, str) else email_id, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Hledání příloh
            attachments = []
            for part in msg.walk():
                content_disposition = str(part.get('Content-Disposition', ''))
                if 'attachment' in content_disposition:
                    attachments.append(part)
            
            # Kontrola, zda příloha existuje
            if not attachments or attachment_index >= len(attachments):
                return {
                    'status': 'error',
                    'message': f'Příloha s indexem {attachment_index} nebyla nalezena',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Získání vybrané přílohy
            attachment = attachments[attachment_index]
            
            # Získání názvu přílohy
            filename = "unknown"
            if attachment.get_filename():
                filename = attachment.get_filename()
                # Decode filename if needed
                if decode_header(filename)[0][1] is not None:
                    filename = decode_header(filename)[0][0]
                    if isinstance(filename, bytes):
                        filename = filename.decode(decode_header(filename)[0][1])
            
            # Uložení přílohy
            save_path = os.path.join(save_path, filename)
            with open(save_path, 'wb') as f:
                f.write(attachment.get_payload(decode=True))
            
            mail.close()
            mail.logout()
            
            return {
                'status': 'success',
                'message': f'Příloha byla stažena a uložena jako {filename}',
                'path': save_path,
                'filename': filename,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
