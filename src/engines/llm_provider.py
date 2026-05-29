"""
LLM Provider Abstraction for 7Sins Project
Abstract base class for LLM integrations (MiniMax, OpenAI, Anthropic)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import threading


@dataclass
class LLMResponse:
    """Structured response from LLM provider"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    raw_response: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str = "default", **kwargs):
        self.api_key = api_key
        self.model = model
        self.extra_config = kwargs
    
    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        Send a completion request to the LLM.
        
        Args:
            prompt: User prompt with task context
            system_prompt: System prompt defining the drive's persona
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with structured response data
        """
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Send a chat completion request to the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Provider-specific parameters
            
        Returns:
            LLMResponse with structured response data
        """
        pass
    
    def parse_drive_opinion(self, response: LLMResponse) -> Dict[str, Any]:
        """
        Parse LLM response into drive opinion fields.
        Override in subclass if provider needs special parsing.
        
        Returns:
            Dict with: opinion (str), confidence (float), recommendation (str), risk_level (str)
        """
        content = response.content.strip()
        
        # Simple parsing - attempt to extract structured info
        opinion = content
        confidence = 0.7  # default
        recommendation = content
        risk_level = "medium"  # default
        
        # Basic attempt to parse confidence if mentioned
        import re
        conf_match = re.search(r'confidence[:\s]+([0-9.]+)', content, re.IGNORECASE)
        if conf_match:
            confidence = float(conf_match.group(1))
        
        # Parse risk level
        risk_match = re.search(r'risk[:\s]+(low|medium|high)', content, re.IGNORECASE)
        if risk_match:
            risk_level = risk_match.group(1).lower()
        
        return {
            "opinion": opinion,
            "confidence": confidence,
            "recommendation": recommendation,
            "risk_level": risk_level
        }


class LLMProviderRegistry:
    """Registry for managing LLM provider instances - thread-safe implementation"""
    
    _instances: Dict[str, 'LLMProviderRegistry'] = {}
    _lock = threading.Lock()
    
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._instance_lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, name: str = "default") -> 'LLMProviderRegistry':
        """Get or create a named registry instance (thread-safe singleton per name)"""
        with cls._lock:
            if name not in cls._instances:
                cls._instances[name] = cls()
            return cls._instances[name]
    
    def register(self, name: str, provider: LLMProvider):
        """Register a provider (thread-safe)"""
        with self._instance_lock:
            self._providers[name] = provider
    
    def get(self, name: str) -> Optional[LLMProvider]:
        """Get a provider by name (thread-safe)"""
        with self._instance_lock:
            return self._providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names (thread-safe)"""
        with self._instance_lock:
            return list(self._providers.keys())
    
    # Backward compatibility: class methods that delegate to default instance
    @classmethod
    def register(cls, name: str, provider: LLMProvider):
        """Register a provider (class method, thread-safe)"""
        cls.get_instance().register(name, provider)
    
    @classmethod
    def get(cls, name: str) -> Optional[LLMProvider]:
        """Get a provider by name (class method, thread-safe)"""
        return cls.get_instance().get(name)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered provider names (class method, thread-safe)"""
        return cls.get_instance().list_providers()
