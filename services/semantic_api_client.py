# services/semantic_api_client.py - Improved version with fallback mechanisms

import requests
import json
import os
from typing import Dict, List, Any, Optional, Union, BinaryIO
import time
import logging

class SemanticApiClient:
    """
    Klient pro komunikaci se sémantickou mikroslužbou.
    
    Poskytuje rozhraní pro interakci s API sémantické služby pro analýzu dokumentů,
    získávání kontextu a další operace související s sémantickým zpracováním.
    
    Zahrnuje mechanismy pro graceful degradation, když služba není dostupná.
    """
    
    def __init__(self, base_url: str = "http://localhost:5050", timeout: int = 10):
        """
        Inicializace klienta pro sémantickou službu.
        
        Args:
            base_url: Základní URL adresa sémantické služby
            timeout: Časový limit pro API požadavky v sekundách
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Flag to track if service is available
        self._service_available = None
    
    def is_service_available(self) -> bool:
        """
        Zkontroluje, zda je sémantická služba dostupná.
        
        Returns:
            bool: True pokud je služba dostupná, jinak False
        """
        if self._service_available is None:
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=2)
                self._service_available = response.status_code == 200
            except requests.RequestException:
                self._service_available = False
        
        return self._service_available
    
    def check_health(self) -> Dict[str, Any]:
        """
        Zkontroluje stav služby.
        
        Returns:
            Dict: Informace o stavu služby a dostupných modelech
        """
        if not self.is_service_available():
            return {
                "status": "error",
                "message": "Sémantická služba není dostupná",
                "service_url": self.base_url
            }
            
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Chyba při kontrole stavu služby: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Získá seznam dostupných modelů pro analýzu.
        
        Returns:
            Dict: Seznam dostupných modelů pro různé kroky analýzy
        """
        if not self.is_service_available():
            return {
                "status": "error",
                "message": "Sémantická služba není dostupná"
            }
            
        try:
            response = requests.get(f"{self.base_url}/api/models", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Chyba při získávání dostupných modelů: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def analyze_document(self, file_path: str, project_id: Optional[str] = None, 
                        mode: str = "intelligent", 
                        sentence_model: Optional[str] = None,
                        chunking_model: Optional[str] = None,
                        annotation_model: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzuje dokument pomocí sémantické služby.
        
        Args:
            file_path: Cesta k dokumentu, který má být analyzován
            project_id: ID projektu, ke kterému dokument patří (volitelné)
            mode: Režim analýzy ('sentence', 'chunk', 'intelligent')
            sentence_model: Model pro analýzu vět (volitelné)
            chunking_model: Model pro seskupování vět (volitelné)
            annotation_model: Model pro anotaci chunků (volitelné)
            
        Returns:
            Dict: Výsledek operace s ID analýzy
        """
        if not self.is_service_available():
            return {
                "status": "error",
                "message": "Sémantická služba není dostupná pro analýzu dokumentu"
            }
            
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                
                data = {
                    'mode': mode
                }
                
                if project_id:
                    data['project_id'] = project_id
                if sentence_model:
                    data['sentence_model'] = sentence_model
                if chunking_model:
                    data['chunking_model'] = chunking_model
                if annotation_model:
                    data['annotation_model'] = annotation_model
                
                response = requests.post(
                    f"{self.base_url}/api/analyze",
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        
        except FileNotFoundError:
            self.logger.error(f"Soubor nebyl nalezen: {file_path}")
            return {
                "status": "error",
                "message": f"Soubor nebyl nalezen: {file_path}"
            }
        except requests.RequestException as e:
            self.logger.error(f"Chyba při analýze dokumentu: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_project_context(self, project_id: str, query: str = "", max_chunks: int = 10) -> Dict[str, Any]:
        """
        Získá kontext projektu pro vyhledávání nebo generování odpovědí.
        
        Args:
            project_id: ID projektu
            query: Dotaz pro vyhledání relevantních chunků (volitelné)
            max_chunks: Maximální počet chunků k vrácení
            
        Returns:
            Dict: Kontext projektu jako seznam chunků
        """
        if not self.is_service_available():
            self.logger.warning(f"Sémantická služba není dostupná pro získání kontextu projektu {project_id}")
            return {
                "project_id": project_id,
                "chunk_count": 0,
                "chunks": []
            }
            
        try:
            params = {
                'max_chunks': max_chunks
            }
            
            if query:
                params['query'] = query
            
            response = requests.get(
                f"{self.base_url}/api/context/{project_id}",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Chyba při získávání kontextu projektu: {str(e)}")
            return {
                "project_id": project_id,
                "chunk_count": 0,
                "chunks": []
            }