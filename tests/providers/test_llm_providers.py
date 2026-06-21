"""
7Sins External Provider Tests
Level: G - External Provider Tests
Tests LLM provider integration (MiniMax API)
"""

import pytest
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def has_api_key():
    """Check if MINIMAX_API_KEY is set."""
    return bool(os.environ.get("MINIMAX_API_KEY"))


def has_search_available():
    """Check if search tool is available."""
    try:
        from src.tools.search import get_search_tool
        tool = get_search_tool()
        return tool is not None
    except Exception:
        return False


class MockLLMResponse:
    """Mock LLM response for testing."""
    def __init__(self, content: str):
        self.content = content


class MockMiniMaxProvider:
    """Mock MiniMax provider for testing."""
    
    def complete(self, prompt: str, system_prompt: str) -> MockLLMResponse:
        return MockLLMResponse(
            "OPINION: This is a test opinion\n"
            "CONFIDENCE: 0.8\n"
            "RECOMMENDATION: Proceed with caution\n"
            "RISK: medium"
        )


class TestProviderResponseStructure:
    """G.2: Mock provider returns correct structure."""

    def test_mock_response_has_content(self):
        """Mock provider response has content attribute."""
        mock = MockMiniMaxProvider()
        response = mock.complete("test", "system")

        assert hasattr(response, "content")
        assert isinstance(response.content, str)
        assert len(response.content) > 0

    def test_mock_response_parsable(self):
        """Mock response is parsable by opinion parser."""
        from src.engines.seven_sins import _parse_llm_opinion
        from src.core.drive_engine import DriveType

        mock = MockMiniMaxProvider()
        response = mock.complete("test", "system")

        opinion = _parse_llm_opinion(response.content, DriveType.WRATH)

        assert opinion is not None
        assert opinion.drive == DriveType.WRATH


class TestAllEnginesInstantiation:
    """G.3: All engines can be instantiated together."""

    def test_all_7_engines_together(self):
        """All 7 engines can coexist without conflict."""
        from src.engines.seven_sins import (
            GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
            PrideEngine, WrathEngine, EnvyEngine
        )

        engines = [
            GluttonyEngine(),
            LustEngine(),
            GreedEngine(),
            SlothEngine(),
            PrideEngine(),
            WrathEngine(),
            EnvyEngine(),
        ]

        assert len(engines) == 7
        drive_types = {e.drive_type for e in engines}
        assert len(drive_types) == 7  # All unique


class TestLLMResponseParsing:
    """G.4: LLM response parsing stability."""

    def test_various_format_parsing(self):
        """Various LLM response formats are parsed correctly."""
        from src.engines.seven_sins import _parse_llm_opinion
        from src.core.drive_engine import DriveType

        # Standard format
        response1 = (
            "OPINION: Good approach\n"
            "CONFIDENCE: 0.8\n"
            "RECOMMENDATION: Proceed\n"
            "RISK: low"
        )
        opinion1 = _parse_llm_opinion(response1, DriveType.GLUTTONY)
        assert 0.7 <= opinion1.confidence <= 0.9
        assert opinion1.risk_level == "low"

        # Extra whitespace
        response2 = (
            "  OPINION:   Test  \n"
            "  CONFIDENCE:  0.75  \n"
            "  RECOMMENDATION:   Go\n"
            "  RISK: medium  "
        )
        opinion2 = _parse_llm_opinion(response2, DriveType.GLUTTONY)
        assert opinion2.confidence == 0.75
        assert opinion2.risk_level == "medium"

    def test_fallback_on_malformed_response(self):
        """Malformed response falls back correctly."""
        from src.engines.seven_sins import _parse_llm_opinion
        from src.core.drive_engine import DriveType, FALLBACK_CONFIDENCE

        # Completely malformed
        response = "totally invalid response format"
        opinion = _parse_llm_opinion(response, DriveType.WRATH)

        assert opinion is not None
        assert opinion.drive == DriveType.WRATH
        assert opinion.confidence == FALLBACK_CONFIDENCE[DriveType.WRATH]


class TestProviderErrorHandling:
    """G.5: Provider error handling."""

    def test_timeout_raises(self):
        """Provider timeout raises exception."""
        from unittest.mock import Mock, patch
        from src.engines.seven_sins import WrathEngine
        from src.core.ego_core import TaskInput

        engine = WrathEngine()
        mock_provider = Mock()
        mock_provider.complete.side_effect = TimeoutError("Request timeout")

        with patch.object(engine, "_llm_provider", mock_provider):
            with pytest.raises(TimeoutError):
                engine.evaluate(
                    TaskInput(description="test", task_type="debug"),
                    {}
                )

    def test_connection_error_raises(self):
        """Connection error raises exception."""
        from unittest.mock import Mock, patch
        from src.engines.seven_sins import WrathEngine
        from src.core.ego_core import TaskInput

        engine = WrathEngine()
        mock_provider = Mock()
        mock_provider.complete.side_effect = ConnectionError("Connection refused")

        with patch.object(engine, "_llm_provider", mock_provider):
            with pytest.raises(ConnectionError):
                engine.evaluate(
                    TaskInput(description="test", task_type="debug"),
                    {}
                )


@pytest.mark.skipif(not has_api_key(), reason="Requires MINIMAX_API_KEY")
class TestMiniMaxDirectCall:
    """G.1: Direct MiniMax API call (requires real API key)."""

    def test_minimax_basic_connectivity(self):
        """Basic connectivity to MiniMax API."""
        from src.engines.minimax_provider import create_minimax_provider

        provider = create_minimax_provider(
            api_key=os.environ["MINIMAX_API_KEY"],
            group_id=os.environ.get("MINIMAX_GROUP_ID", "")
        )

        response = provider.complete(
            prompt="What is 2+2? Reply with just the number.",
            system_prompt="You are a calculator. Reply only with the answer."
        )

        assert response.content is not None
        assert len(response.content) > 0
        assert "4" in response.content


@pytest.mark.skipif(not has_search_available(), reason="Search tool not available")
class TestSearchToolReal:
    """G.6: Real search tool call."""

    def test_search_returns_list(self):
        """Search tool returns a list of results."""
        from src.tools.search import get_search_tool

        tool = get_search_tool()
        results = tool.search("7 sins AI agent", count=3)

        assert isinstance(results, list)
        assert len(results) <= 3
