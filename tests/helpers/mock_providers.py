"""Mock LLM providers for testing."""

from typing import List, Dict, Any


class MockLLMResponse:
    """Mock LLM response matching real provider interface."""
    
    def __init__(self, content: str):
        self.content = content


class MockMiniMaxProvider:
    """Mock MiniMax provider for testing without real API calls."""
    
    def __init__(self, response_content: str = None):
        self._default_content = (
            response_content or
            "OPINION: This is a balanced approach\n"
            "CONFIDENCE: 0.8\n"
            "RECOMMENDATION: Proceed with standard implementation\n"
            "RISK: medium"
        )
    
    def complete(self, prompt: str, system_prompt: str) -> MockLLMResponse:
        return MockLLMResponse(self._default_content)


class MockSearchResult:
    """Mock search result item."""
    
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet
    
    def to_dict(self) -> Dict[str, str]:
        return {"title": self.title, "url": self.url, "snippet": self.snippet}


class MockSearchTool:
    """Mock search tool for testing."""
    
    def __init__(self, results: List[Dict[str, Any]] = None):
        self._results = results or [
            {"title": "Result 1", "url": "http://example.com/1", "snippet": "Snippet 1"},
            {"title": "Result 2", "url": "http://example.com/2", "snippet": "Snippet 2"},
        ]
    
    def search(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        return self._results[:count]
