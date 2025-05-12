# services/llm_service.py - Služba pro LLM integraci

import os
import requests
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from services.semantic_api_client import SemanticApiClient

class LLMService:
    """
    Služba pro integraci s jazykovými modely a kontextovým vyhledáváním.
    
    Tato služba poskytuje rozhraní pro generování textu pomocí LLM s využitím
    kontextu z projektů a dokumentů.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializace služby.
        
        Args:
            config: Konfigurace aplikace
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Inicializace klienta pro sémantickou službu
        semantic_api_url = os.environ.get('SEMANTIC_API_URL', 'http://localhost:5050')
        self.semantic_client = SemanticApiClient(base_url=semantic_api_url)
        
        # Konfigurace pro LLM
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.default_model = os.environ.get('DEFAULT_LLM_MODEL', 'gpt-3.5-turbo')
        self.default_provider = self._get_default_provider()
        
        # Nastavení výchozích parametrů pro generování
        self.default_params = {
            'temperature': 0.2,
            'max_tokens': 1000
        }
    
    def _get_default_provider(self) -> str:
        """
        Určí výchozího poskytovatele LLM na základě dostupných API klíčů.
        
        Returns:
            str: Výchozí poskytovatel ('openai', 'anthropic', 'none')
        """
        if self.openai_api_key:
            return 'openai'
        elif self.anthropic_api_key:
            return 'anthropic'
        else:
            return 'none'
    
    def general_chat(self, message: str) -> str:
        """
        Generuje odpověď na zprávu bez specifického kontextu.
        
        Args:
            message: Zpráva od uživatele
            
        Returns:
            str: Vygenerovaná odpověď
        """
        # Základní prompt pro obecný chat
        prompt = f"""Jsi asistent v aplikaci pro kancelářskou automatizaci, který pomáhá uživatelům s jejich dotazy.
Odpověz na dotaz uživatele co nejlépe.

OTÁZKA: {message}

ODPOVĚĎ:"""
        
        # Volání LLM na základě nakonfigurovaného poskytovatele
        if self.default_provider == 'openai':
            return self._call_openai(prompt)
        elif self.default_provider == 'anthropic':
            return self._call_anthropic(prompt)
        else:
            raise ValueError("LLM není nakonfigurováno. Nastavte API klíč v proměnných prostředí.")
    
    def chat_with_project(self, project_id: Union[int, str], message: str, 
                        max_context_chunks: int = 10) -> Dict[str, Any]:
        """
        Vygeneruje odpověď na zprávu v kontextu konkrétního projektu.
        
        Args:
            project_id: ID projektu pro kontext
            message: Zpráva od uživatele
            max_context_chunks: Maximální počet kontextových chunků
            
        Returns:
            Dict: Výsledek s odpovědí nebo chybou
        """
        # Kontrola, zda je LLM nakonfigurováno
        if self.default_provider == 'none':
            return {
                "status": "error",
                "message": "LLM není nakonfigurováno. Nastavte API klíč v proměnných prostředí.",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Získání kontextu projektu na základě dotazu
            context_result = self.semantic_client.get_project_context(
                project_id=str(project_id),
                query=message,
                max_chunks=max_context_chunks
            )
            
            # Kontrola, zda byl kontext úspěšně získán
            if isinstance(context_result, dict) and context_result.get('status') == 'error':
                self.logger.error(f"Chyba při získávání kontextu: {context_result.get('message')}")
                
                # Pokud sémantická služba není dostupná, pokračujeme bez kontextu
                context_text = "Pro tento projekt nebyl nalezen žádný relevantní kontext."
            else:
                # Sestavení kontextu z chunků
                chunks = context_result.get('chunks', [])
                context_text = self._prepare_context_from_chunks(chunks)
            
            # Vytvoření LLM promptu s kontextem
            prompt = self._create_chat_prompt(message, context_text)
            
            # Volání LLM na základě nakonfigurovaného poskytovatele
            if self.default_provider == 'openai':
                response_text = self._call_openai(prompt)
            elif self.default_provider == 'anthropic':
                response_text = self._call_anthropic(prompt)
            else:
                return {
                    "status": "error",
                    "message": f"Nepodporovaný poskytovatel LLM: {self.default_provider}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Vytvoření odpovědi
            return {
                "status": "success",
                "message": "Odpověď byla úspěšně vygenerována",
                "response": response_text,
                "context_chunks": len(chunks) if isinstance(context_result, dict) else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Chyba při generování odpovědi: {str(e)}")
            return {
                "status": "error",
                "message": f"Chyba při generování odpovědi: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _prepare_context_from_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Připraví kontext z chunků pro LLM.
        
        Args:
            chunks: Seznam chunků s textem a metadaty
            
        Returns:
            str: Formátovaný kontext pro LLM
        """
        if not chunks:
            return "Pro tento dotaz nebyl nalezen žádný relevantní kontext."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get('text', '')
            importance = chunk.get('importance_score', 0)
            
            # Přidání relevantních metadat, pokud existují
            metadata = []
            if chunk.get('annotation'):
                annotation = chunk.get('annotation')
                if annotation.get('main_topic'):
                    metadata.append(f"Téma: {annotation.get('main_topic')}")
                if annotation.get('categories'):
                    categories = annotation.get('categories')
                    if isinstance(categories, list) and categories:
                        metadata.append(f"Kategorie: {', '.join(categories)}")
            
            # Sestavení chunku s metadaty
            context_parts.append(
                f"FRAGMENT {i+1}:\n"
                + (f"[{', '.join(metadata)}]\n" if metadata else "")
                + f"{chunk_text}\n"
            )
        
        return "\n\n".join(context_parts)
    
    def _create_chat_prompt(self, question: str, context: str) -> str:
        """
        Vytvoří prompt pro LLM s kontextem a otázkou.
        
        Args:
            question: Otázka od uživatele
            context: Kontext z dokumentů
            
        Returns:
            str: Kompletní prompt pro LLM
        """
        return f"""Jsi asistent, který odpovídá na otázky na základě poskytnutého kontextu projektu.
Tvým úkolem je poskytnout co nejlepší odpověď s využitím následujícího kontextu:

===== KONTEXT PROJEKTU =====
{context}
===================

OTÁZKA: {question}

ODPOVĚĎ:"""
    
    def _call_openai(self, prompt: str) -> str:
        """
        Volá OpenAI API pro generování odpovědi.
        
        Args:
            prompt: Prompt pro LLM
            
        Returns:
            str: Vygenerovaná odpověď
        """
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            data = {
                "model": self.default_model,
                "messages": [
                    {"role": "system", "content": "Jsi asistent, který pomáhá s informacemi z projektu."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.default_params['temperature'],
                "max_tokens": self.default_params['max_tokens']
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            
            return response_data["choices"][0]["message"]["content"]
            
        except Exception as e:
            self.logger.error(f"Chyba při volání OpenAI API: {str(e)}")
            raise
    
    def _call_anthropic(self, prompt: str) -> str:
        """
        Volá Anthropic API pro generování odpovědi.
        
        Args:
            prompt: Prompt pro LLM
            
        Returns:
            str: Vygenerovaná odpověď
        """
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01"
            }
            
            # Claude expects a different format than system/user messages
            system_prompt = "Jsi asistent, který pomáhá s informacemi z projektu."
            
            data = {
                "model": "claude-3-sonnet-20240229",  # Use the appropriate Claude model
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.default_params['temperature'],
                "max_tokens": self.default_params['max_tokens']
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            
            return response_data["content"][0]["text"]
            
        except Exception as e:
            self.logger.error(f"Chyba při volání Anthropic API: {str(e)}")
            raise