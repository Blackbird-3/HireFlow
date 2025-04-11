# utils/ollama_client.py

import requests
import json
import time
import os
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ollama_client")

class OllamaClient:
    """Client for interacting with local Ollama instance for LLM inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:1b"):
        """
        Initialize Ollama client
        
        Args:
            base_url: URL of the Ollama API
            model: Default model to use for inference
        """
        self.base_url = base_url
        self.default_model = model
        self.available = self._check_availability()
        
        # If Ollama is available, check if model is available
        if self.available:
            self._ensure_model_available()
    
    def _check_availability(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama service not available: {e}")
            return False
    
    def _ensure_model_available(self) -> None:
        """Check if the model is available and pull it if not"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            models = response.json().get("models", [])
            
            model_names = [model.get("name") for model in models]
            if self.default_model not in model_names:
                logger.info(f"Model {self.default_model} not found. Pulling from Ollama...")
                self._pull_model()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking model availability: {e}")
    
    def _pull_model(self) -> None:
        """Pull the model from Ollama"""
        try:
            # This is a long-running operation, so we'll just start it
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.default_model},
                stream=True
            )
            
            logger.info(f"Started pulling model {self.default_model}")
            
            # Log progress
            for line in response.iter_lines():
                if line:
                    progress_data = json.loads(line)
                    if "completed" in progress_data and progress_data["completed"]:
                        logger.info(f"Model {self.default_model} pulled successfully")
                        break
                    elif "status" in progress_data:
                        logger.info(f"Pull status: {progress_data['status']}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error pulling model: {e}")
    
    def generate(self, 
                prompt: str, 
                model: Optional[str] = None, 
                system_prompt: Optional[str] = None,
                max_tokens: int = 1000,
                temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate text using Ollama
        
        Args:
            prompt: The prompt to generate from
            model: Model to use (defaults to self.default_model)
            system_prompt: Optional system prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict containing generated text and metadata
        """
        if not self.available:
            logger.warning("Ollama not available. Returning fallback response.")
            return {
                "error": "Ollama not available",
                "text": "Sorry, the local LLM service is not available. Please check your Ollama installation."
            }
        
        model_name = model or self.default_model
        
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "text": result.get("response", ""),
                    "model": model_name,
                    "total_duration": result.get("total_duration", 0),
                    "load_duration": result.get("load_duration", 0),
                    "prompt_eval_count": result.get("prompt_eval_count", 0),
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0)
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {
                    "error": f"API error: {response.status_code}",
                    "text": "An error occurred while generating text."
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {
                "error": f"Request error: {str(e)}",
                "text": "An error occurred while connecting to Ollama."
            }
    
    def chat(self, 
             messages: list, 
             model: Optional[str] = None,
             system_prompt: Optional[str] = None,
             max_tokens: int = 1000,
             temperature: float = 0.7) -> Dict[str, Any]:
        """
        Chat completion using Ollama
        
        Args:
            messages: List of messages in the format [{"role": "user", "content": "..."}]
            model: Model to use (defaults to self.default_model)
            system_prompt: Optional system prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict containing generated response and metadata
        """
        if not self.available:
            logger.warning("Ollama not available. Returning fallback response.")
            return {
                "error": "Ollama not available",
                "message": {
                    "role": "assistant",
                    "content": "Sorry, the local LLM service is not available. Please check your Ollama installation."
                }
            }
        
        model_name = model or self.default_model
        
        request_data = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "message": result.get("message", {"role": "assistant", "content": ""}),
                    "model": model_name,
                    "total_duration": result.get("total_duration", 0),
                    "load_duration": result.get("load_duration", 0),
                    "prompt_eval_count": result.get("prompt_eval_count", 0),
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0)
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {
                    "error": f"API error: {response.status_code}",
                    "message": {
                        "role": "assistant", 
                        "content": "An error occurred while generating a response."
                    }
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {
                "error": f"Request error: {str(e)}",
                "message": {
                    "role": "assistant",
                    "content": "An error occurred while connecting to Ollama."
                }
            }

# Singleton instance for reuse
ollama = OllamaClient()

# Example usage
def get_llm_response(prompt, system_prompt=None, fallback_text=""):
    """
    Get a response from the LLM with fallback handling
    
    Args:
        prompt: The prompt to send to the LLM
        system_prompt: Optional system prompt
        fallback_text: Text to return if LLM is unavailable
        
    Returns:
        String response from the LLM or fallback text
    """
    response = ollama.generate(prompt, system_prompt=system_prompt)
    
    if "error" in response:
        logger.warning(f"Using fallback for prompt: {prompt[:50]}...")
        return fallback_text
    
    return response["text"]