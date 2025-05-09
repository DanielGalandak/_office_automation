# services/pdf_service.py - Služba pro práci s PDF

import os
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import io

class PdfService:
    """Služba pro práci s PDF soubory."""
    
    def __init__(self, config: dict):
        """
        Inicializace služby s konfigurací.
        
        Args:
            config: Slovník s konfigurací pro cesty k souborům
        """
        self.temp_folder = config.get('TEMP_FOLDER', 'temp')
    
    def merge_pdfs(self, pdf_files: List[str], output_path: str) -> Dict[str, Any]:
        """
        Sloučí několik PDF souborů do jednoho.
        
        Args:
            pdf_files: Seznam cest k PDF souborům
            output_path: Cesta pro uložení výsledného PDF
            
        Returns:
            Výsledek operace jako slovník
        """
        try:
            # Kontrola vstupních souborů
            for pdf_file in pdf_files:
                if not os.path.exists(pdf_file):
                    return {
                        'status': 'error',
                        'message': f'Soubor {pdf_file} neexistuje',
                        'timestamp': datetime.now().isoformat()
                    }
                if not pdf_file.lower().endswith('.pdf'):
                    return {
                        'status': 'error',
                        'message': f'Soubor {pdf_file} není PDF',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Sloučení PDF souborů
            merger = PdfMerger()
            
            for pdf_file in pdf_files:
                merger.append(pdf_file)
            
            # Uložení výsledného PDF
            merger.write(output_path)
            merger.close()
            
            # Získání informací o výsledném souboru
            result_pdf = PdfReader(output_path)
            
            return {
                'status': 'success',
                'message': f'PDF soubory byly úspěšně sloučeny',
                'output_path': output_path,
                'page_count': len(result_pdf.pages),
                'file_size': os.path.getsize(output_path),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def extract_text(self, pdf_file: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrahuje text z PDF souboru.
        
        Args:
            pdf_file: Cesta k PDF souboru
            output_path: Cesta pro uložení extrahovaného textu (volitelné)
            
        Returns:
            Výsledek operace jako slovník včetně extrahovaného textu
        """
        try:
            # Kontrola vstupního souboru
            if not os.path.exists(pdf_file):
                return {
                    'status': 'error',
                    'message': f'Soubor {pdf_file} neexistuje',
                    'timestamp': datetime.now().isoformat()
                }
            if not pdf_file.lower().endswith('.pdf'):
                return {
                    'status': 'error',
                    'message': f'Soubor {pdf_file} není PDF',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Nastavení výstupní cesty, pokud není zadána
            if not output_path:
                output_path = os.path.splitext(pdf_file)[0] + '.txt'
            
            # Otevření PDF souboru
            reader = PdfReader(pdf_file)
            
            # Extrakce textu z každé stránky
            all_text = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    all_text.append(f"--- Stránka {page_num + 1} ---\n{text}\n")
                else:
                    all_text.append(f"--- Stránka {page_num + 1} ---\n[Žádný extrahovatelný text]\n")
            
            # Spojení textu ze všech stránek
            extracted_text = '\n'.join(all_text)
            
            # Uložení textu do souboru
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            return {
                'status': 'success',
                'message': f'Text byl úspěšně extrahován z PDF',
                'output_path': output_path,
                'page_count': len(reader.pages),
                'text_length': len(extracted_text),
                'text': extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def create_pdf(self, title: str, content: str, output_path: str) -> Dict[str, Any]:
        """
        Vytvoří PDF soubor z textu.
        
        Args:
            title: Název PDF dokumentu
            content: Obsah PDF dokumentu
            output_path: Cesta pro uložení výsledného PDF
            
        Returns:
            Výsledek operace jako slovník
        """
        try:
            # Vytvoření PDF souboru
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=letter)
            width, height = letter
            
            # Nastavení fontu a velikosti
            c.setFont("Helvetica", 12)
            
            # Přidání titulku
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, height - 72, title)
            
            # Přidání data vytvoření
            c.setFont("Helvetica", 10)
            c.drawString(72, height - 100, f"Vytvořeno: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            
            # Rozdělení obsahu na řádky
            lines = content.split('\n')
            
            # Přidání obsahu
            c.setFont("Helvetica", 12)
            y_position = height - 130
            line_height = 14
            
            for line in lines:
                # Kontrola, zda se text vejde na stránku
                if y_position < 72:
                    c.showPage()
                    y_position = height - 72
                    c.setFont("Helvetica", 12)
                
                # Rozdělení dlouhých řádků
                while len(line) > 0:
                    # Maximální počet znaků na řádek (odhadem)
                    max_chars = 90
                    
                    if len(line) <= max_chars:
                        c.drawString(72, y_position, line)
                        y_position -= line_height
                        line = ""
                    else:
                        # Hledání posledního mezery před max_chars
                        cut_index = line[:max_chars].rfind(' ')
                        if cut_index == -1:  # Pokud není mezera, rozdělit násilně
                            cut_index = max_chars
                        
                        c.drawString(72, y_position, line[:cut_index])
                        y_position -= line_height
                        line = line[cut_index:].lstrip()
                    
                    # Kontrola, zda se další řádek vejde na stránku
                    if y_position < 72:
                        c.showPage()
                        y_position = height - 72
                        c.setFont("Helvetica", 12)
            
            # Uložení PDF
            c.save()
            
            # Získání PDF z BytesIO
            packet.seek(0)
            new_pdf = PdfReader(packet)
            
            # Vytvoření výsledného PDF souboru
            writer = PdfWriter()
            
            # Přidání stránek z nového PDF
            for page in new_pdf.pages:
                writer.add_page(page)
            
            # Uložení výsledného PDF
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return {
                'status': 'success',
                'message': f'PDF soubor byl úspěšně vytvořen',
                'output_path': output_path,
                'page_count': len(new_pdf.pages),
                'file_size': os.path.getsize(output_path),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }