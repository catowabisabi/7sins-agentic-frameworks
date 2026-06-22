"""
MiniMax LLM Provider Implementation
Integrates MiniMax's Abab6.5s model with the 7Sins LLM abstraction
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

from .llm_provider import LLMProvider, LLMResponse, LLMProviderRegistry


class MiniMaxProvider(LLMProvider):
    """
    MiniMax provider using the MiniMax API.
    API endpoint: https://api.minimax.chat/v1/text/chatcompletion_pro
    """
    
    def __init__(self, api_key: str, model: str = "MiniMax-ABab6.5s", group_id: str = None, **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.group_id = group_id or os.environ.get("MINIMAX_GROUP_ID", "")
        self.base_url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
        self.default_temperature = kwargs.get("temperature", 0.7)
        self.default_max_tokens = kwargs.get("max_tokens", 512)
    
    def _build_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _build_messages(self, prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        Send completion request to MiniMax API.
        
        Args:
            prompt: User prompt with task context
            system_prompt: System prompt defining the drive's persona
            **kwargs: temperature, max_tokens, top_p, etc.
        """
        messages = self._build_messages(prompt, system_prompt)
        return self.chat(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Send chat completion request to MiniMax API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: temperature, max_tokens, top_p, etc.
        """
        temperature = kwargs.get("temperature", self.default_temperature)
        max_tokens = kwargs.get("max_tokens", self.default_max_tokens)
        top_p = kwargs.get("top_p", 0.95)
        
        payload = {
            "model": self.model,
            "messages": messages,
            "group_id": self.group_id,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "n": 1,
            "stream": False
        }
        
        try:
            request = urllib.request.Request(
                self.base_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._build_headers(),
                method="POST"
            )
            
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return self._parse_response(result)
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp is not None else ""
            raise Exception(f"MiniMax API error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"MiniMax connection error: {e.reason}")
    
    def _parse_response(self, raw: Dict[str, Any]) -> LLMResponse:
        """Parse MiniMax API response into LLMResponse"""
        try:
            choices = raw.get("choices", [])
            if not choices:
                raise Exception("No choices in MiniMax response")
            
            choice = choices[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            
            # Calculate tokens
            usage = raw.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            finish_reason = choice.get("finish_reason", "stop")
            
            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                raw_response=raw
            )
        except Exception as e:
            raise Exception(f"Failed to parse MiniMax response: {e}, raw: {raw}")


def create_minimax_provider(api_key: str = None, model: str = "MiniMax-ABab6.5s", **kwargs) -> MiniMaxProvider:
    """
    Factory function to create and register a MiniMax provider.
    Reads API key and group ID from environment if not provided.
    """
    api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
    group_id = kwargs.get("group_id") or os.environ.get("MINIMAX_GROUP_ID", "")
    
    if not api_key:
        raise ValueError("MiniMax API key is required. Set MINIMAX_API_KEY environment variable or pass api_key parameter.")
    
    provider = MiniMaxProvider(api_key=api_key, model=model, group_id=group_id, **kwargs)
    LLMProviderRegistry.register_provider("minimax", provider)
    return provider
