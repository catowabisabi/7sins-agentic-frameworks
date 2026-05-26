"""
Web Search Tool - Brave Search Integration
Provides search capability for research and competitive analysis
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single search result"""
    title: str
    url: str
    snippet: str
    source: str = "brave"


class BraveSearchTool:
    """Brave Search API integration for web search operations"""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("BRAVE_SEARCH_API_KEY", "")
        self._available = bool(self.api_key)

    @property
    def is_available(self) -> bool:
        """Check if search tool is available"""
        return self._available

    def search(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a web search using Brave Search API

        Args:
            query: Search query string
            count: Maximum number of results to return (default: 10)

        Returns:
            List of search result dictionaries with title, url, snippet
        """
        if not self._available:
            return self._empty_results()

        try:
            import urllib.request
            import urllib.parse

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key
            }

            params = urllib.parse.urlencode({
                "q": query,
                "count": min(count, 20)
            })

            url = f"{self.BASE_URL}?{params}"
            request = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                return self._parse_results(data)

        except Exception:
            return self._empty_results()

    def _parse_results(self, data: dict) -> List[Dict[str, Any]]:
        """Parse Brave Search API response into normalized format"""
        results = []
        web_results = data.get("web", {}).get("results", [])

        for item in web_results:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", item.get("snippet", "")),
                "source": "brave"
            })

        return results

    def _empty_results(self) -> List[Dict[str, Any]]:
        """Return empty search results when unavailable or on error"""
        return []


# Global search tool instance
_search_tool: Optional[BraveSearchTool] = None


def get_search_tool() -> BraveSearchTool:
    """Get or create the global search tool instance"""
    global _search_tool
    if _search_tool is None:
        _search_tool = BraveSearchTool()
    return _search_tool


def search_web(query: str, count: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function for web search

    Args:
        query: Search query
        count: Number of results

    Returns:
        List of search result dictionaries
    """
    tool = get_search_tool()
    return tool.search(query, count)