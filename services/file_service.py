# services/file_service.py - Služba pro práci se soubory

import os
import shutil
import csv
import openpyxl
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import zipfile
import re
from docx import Document
from PyPDF2 import PdfReader, PdfWriter

class FileService:
    """Služba pro práci se soubory a konverze mezi formáty."""
    
    def __init__(self, config: dict):
        """
        Inicializace služby s konfigurací.
        
        Args:
            config: Slovník s konfigurací pro cesty k souborům
        """
        self.upload_folder = config.get('UPLOAD_FOLDER', 'uploads')
        self.temp_folder = config.get('TEMP_FOLDER', 'temp')
        self.allowed_extensions = config.get('ALLOWED_EXTENSIONS', 
                                           {'txt', 'pdf', 'docx', 'xlsx', 'csv'})
    
    def is_file_allowed(self, filename: str) -> bool:
        """
        Zkontroluje, zda je přípona souboru povolena.
        
        Args:
            filename: Jméno souboru
            
        Returns:
            True, pokud je přípona povolena, jinak False
        """
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def get_extension(self, filename: str) -> str:
        """
        Získá příponu souboru.
        
        Args:
            filename: Jméno souboru
            
        Returns:
            Přípona souboru
        """
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def convert_excel_to_csv(self, file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Převede Excel soubor na CSV.
        
        Args:
            file_path: Cesta k Excel souboru
            output_path: Cesta pro uložení CSV souboru (volitelné)
            
        Returns:
            Výsledek operace jako slovník
        """
        try:
            # Ověření přípony souboru
            if not file_path.endswith(('.xlsx', '.xls')):
                return {
                    'status': 'error',
                    'message': 'Vstupní soubor není Excel formát (.xlsx nebo .xls)',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Nastavení výstupní cesty
            if not output_path:
                output_path = os.path.splitext(file_path)[0] + '.csv'
            
            # Načtení Excel souboru s pandas
            df = pd.read_excel(file_path)
            
            # Uložení do CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            return {
                'status': 'success',
                'message': f'Excel soubor byl převeden na CSV',
                'output_path': output_path,
                'rows': len(df),
                'columns': len(df.columns),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def rename_files(self, directory: str, pattern: str, replacement: str, 
                   recursive: bool = False) -> Dict[str, Any]:
        """
        Přejmenuje soubory v adresáři podle vzoru.
        
        Args:
            directory: Cesta k adresáři
            pattern: Regulární výraz pro vyhledávání
            replacement: Náhrada za nalezené části
            recursive: Zda prohledávat i podadresáře
            
        Returns:
            Výsledek operace jako slovník
        """
        try:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                return {
                    'status': 'error',
                    'message': f'Adresář {directory} neexistuje nebo není adresář',
                    'timestamp': datetime.now().isoformat()
                }
            
            renamed_files = []
            pattern_re = re.compile(pattern)
            
            if recursive:
                # Rekurzivní procházení adresářů
                for root, dirs, files in os.walk(directory):
                    for filename in files:
                        if pattern_re.search(filename):
                            old_path = os.path.join(root, filename)
                            new_filename = pattern_re.sub(replacement, filename)
                            new_path = os.path.join(root, new_filename)
                            
                            if old_path != new_path:
                                os.rename(old_path, new_path)
                                renamed_files.append({
                                    'old_name': filename,
                                    'new_name': new_filename,
                                    'path': root
                                })
            else:
                # Pouze v hlavním adresáři
                for filename in os.listdir(directory):
                    if os.path.isfile(os.path.join(directory, filename)) and pattern_re.search(filename):
                        old_path = os.path.join(directory, filename)
                        new_filename = pattern_re.sub(replacement, filename)
                        new_path = os.path.join(directory, new_filename)
                        
                        if old_path != new_path:
                            os.rename(old_path, new_path)
                            renamed_files.append({
                                'old_name': filename,
                                'new_name': new_filename,
                                'path': directory
                            })
            
            return {
                'status': 'success',
                'message': f'Přejmenováno {len(renamed_files)} souborů',
                'renamed_files': renamed_files,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def organize_files(self, directory: str, target_directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Organizuje soubory podle jejich typu do podadresářů.
        
        Args:
            directory: Cesta k adresáři se soubory
            target_directory: Cílový adresář (volitelné)
            
        Returns:
            Výsledek operace jako slovník
        """
        try:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                return {
                    'status': 'error',
                    'message': f'Adresář {directory} neexistuje nebo není adresář',
                    'timestamp': datetime.now().isoformat()
                }
            
            if target_directory is None:
                target_directory = directory
            
            # Zajistit, že cílový adresář existuje
            os.makedirs(target_directory, exist_ok=True)
            
            # Kategorie souborů a jejich přípony
            categories = {
                'Dokumenty': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
                'Tabulky': ['xls', 'xlsx', 'csv', 'ods'],
                'Obrázky': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg'],
                'Audio': ['mp3', 'wav', 'ogg', 'flac', 'aac'],
                'Video': ['mp4', 'avi', 'mkv', 'mov', 'wmv'],
                'Archivy': ['zip', 'rar', '7z', 'tar', 'gz'],
                'Prezentace': ['ppt', 'pptx', 'odp'],
                'Kód': ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb']
            }
            
            # Vytvoření adresářů pro kategorie
            for category in categories:
                os.makedirs(os.path.join(target_directory, category), exist_ok=True)
            
            # Vytvoření adresáře pro ostatní soubory
            os.makedirs(os.path.join(target_directory, 'Ostatní'), exist_ok=True)
            
            moved_files = []
            
            # Procházení souborů a přesouvání podle typu
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # Přeskočení adresářů
                if not os.path.isfile(file_path):
                    continue
                
                # Získání přípony souboru
                extension = self.get_extension(filename)
                
                # Určení kategorie souboru
                category_found = False
                for category, extensions in categories.items():
                    if extension.lower() in extensions:
                        category_dir = os.path.join(target_directory, category)
                        dest_path = os.path.join(category_dir, filename)
                        
                        # Řešení kolizí názvů souborů
                        if os.path.exists(dest_path):
                            base, ext = os.path.splitext(filename)
                            counter = 1
                            while os.path.exists(os.path.join(category_dir, f"{base}_{counter}{ext}")):
                                counter += 1
                            dest_path = os.path.join(category_dir, f"{base}_{counter}{ext}")
                        
                        # Přesun souboru
                        shutil.move(file_path, dest_path)
                        moved_files.append({
                            'filename': filename,
                            'category': category,
                            'destination': dest_path
                        })
                        category_found = True
                        break
                
                # Pokud soubor nemá kategorii, přesuneme do "Ostatní"
                if not category_found:
                    other_dir = os.path.join(target_directory, 'Ostatní')
                    dest_path = os.path.join(other_dir, filename)
                    
                    # Řešení kolizí názvů souborů
                    if os.path.exists(dest_path):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(os.path.join(other_dir, f"{base}_{counter}{ext}")):
                            counter += 1
                        dest_path = os.path.join(other_dir, f"{base}_{counter}{ext}")
                    
                    # Přesun souboru
                    shutil.move(file_path, dest_path)
                    moved_files.append({
                        'filename': filename,
                        'category': 'Ostatní',
                        'destination': dest_path
                    })
            
            return {
                'status': 'success',
                'message': f'Přesunuto {len(moved_files)} souborů do kategorií',
                'moved_files': moved_files,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }