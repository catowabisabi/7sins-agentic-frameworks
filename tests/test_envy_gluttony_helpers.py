"""
Unit tests for envy_gluttony_helpers search injection functions.

Tests the inject_competitor_search and inject_research_context functions
which are used by EnvyEngine and GluttonyEngine respectively.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.ego_core import TaskInput
from src.engines.envy_gluttony_helpers import (
    inject_competitor_search,
    inject_research_context,
)
from src.tools.search import SearchUnavailableError


class TestInjectCompetitorSearch:
    """Tests for inject_competitor_search function."""

    def test_injects_competitor_info_on_competitive_task_type(self):
        """AC1: Verify competitor_info injected when task_type matches competitive keywords."""
        task = TaskInput(task_type="competitor_analysis", description="analyze competitors")
        context = {}
        mock_search_tool = MagicMock()
        mock_search_tool.search.return_value = [{"name": "CompetitorA"}, {"name": "CompetitorB"}]

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_competitor_search(task, context)

        assert "competitor_info" in context
        assert context["competitor_info"] == [{"name": "CompetitorA"}, {"name": "CompetitorB"}]
        mock_search_tool.search.assert_called_once_with("analyze competitors", count=10)

    def test_injects_competitor_info_on_benchmark_task_type(self):
        """Verify competitor_info injected when task_type contains 'benchmark'."""
        task = TaskInput(task_type="benchmark_study", description="benchmark study")
        context = {}
        mock_search_tool = MagicMock()
        mock_search_tool.search.return_value = [{"name": "BenchmarkData"}]

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_competitor_search(task, context)

        assert "competitor_info" in context
        assert context["competitor_info"] == [{"name": "BenchmarkData"}]

    def test_injects_competitor_info_on_compare_task_type(self):
        """Verify competitor_info injected when task_type contains 'compare'."""
        task = TaskInput(task_type="compare_products", description="compare products")
        context = {}
        mock_search_tool = MagicMock()
        mock_search_tool.search.return_value = [{"name": "ProductA"}, {"name": "ProductB"}]

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_competitor_search(task, context)

        assert "competitor_info" in context

    def test_handles_search_unavailable_error_gracefully(self):
        """AC3: Verify graceful handling when SearchUnavailableError is raised."""
        task = TaskInput(task_type="competitor_analysis", description="analyze competitors")
        context = {}

        with patch("src.engines.envy_gluttony_helpers.get_search_tool") as mock_get_tool:
            mock_get_tool.side_effect = SearchUnavailableError("Search unavailable")
            inject_competitor_search(task, context)

        # Context should remain unchanged
        assert "competitor_info" not in context

    def test_no_op_when_task_type_does_not_match_keywords(self):
        """AC4: Verify no-op when task_type does not contain competitive keywords."""
        task = TaskInput(task_type="regular_task", description="some regular task")
        context = {}
        mock_search_tool = MagicMock()

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_competitor_search(task, context)

        # get_search_tool should not be called
        mock_search_tool.search.assert_not_called()
        assert "competitor_info" not in context

    def test_no_op_when_task_type_is_empty(self):
        """Verify no-op when task_type is empty string."""
        task = TaskInput(task_type="", description="some task")
        context = {}
        mock_search_tool = MagicMock()

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_competitor_search(task, context)

        mock_search_tool.search.assert_not_called()
        assert "competitor_info" not in context

    def test_no_op_when_task_type_missing(self):
        """Verify no-op when task_type key is missing from task."""
        task = TaskInput(task_type="", description="some task")
        context = {}
        mock_search_tool = MagicMock()

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_competitor_search(task, context)

        mock_search_tool.search.assert_not_called()
        assert "competitor_info" not in context

    def test_no_injection_when_search_returns_empty_results(self):
        """Verify no competitor_info injected when search returns empty list."""
        task = TaskInput(task_type="competitor_analysis", description="analyze competitors")
        context = {}
        mock_search_tool = MagicMock()
        mock_search_tool.search.return_value = []

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_competitor_search(task, context)

        assert "competitor_info" not in context


class TestInjectResearchContext:
    """Tests for inject_research_context function."""

    def test_injects_search_results_on_research_task_type(self):
        """AC2: Verify search_results injected when task_type matches research keywords."""
        task = TaskInput(task_type="research_analysis", description="research topics")
        context = {}
        mock_search_tool = MagicMock()
        mock_search_tool.search.return_value = [{"title": "Article1"}, {"title": "Article2"}]

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_research_context(task, context)

        assert "search_results" in context
        assert context["search_results"] == [{"title": "Article1"}, {"title": "Article2"}]
        mock_search_tool.search.assert_called_once_with("research topics", count=10)

    def test_injects_search_results_on_search_task_type(self):
        """Verify search_results injected when task_type contains 'search'."""
        task = TaskInput(task_type="search_inventory", description="search inventory")
        context = {}
        mock_search_tool = MagicMock()
        mock_search_tool.search.return_value = [{"title": "InventoryItem"}]

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_research_context(task, context)

        assert "search_results" in context
        assert context["search_results"] == [{"title": "InventoryItem"}]

    def test_injects_search_results_on_investigate_task_type(self):
        """Verify search_results injected when task_type contains 'investigate'."""
        task = TaskInput(task_type="investigate_issue", description="investigate the issue")
        context = {}
        mock_search_tool = MagicMock()
        mock_search_tool.search.return_value = [{"title": "IssueData"}]

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_research_context(task, context)

        assert "search_results" in context

    def test_handles_search_unavailable_error_gracefully(self):
        """AC3: Verify graceful handling when SearchUnavailableError is raised."""
        task = TaskInput(task_type="research_analysis", description="research topics")
        context = {}

        with patch("src.engines.envy_gluttony_helpers.get_search_tool") as mock_get_tool:
            mock_get_tool.side_effect = SearchUnavailableError("Search unavailable")
            inject_research_context(task, context)

        # Context should remain unchanged
        assert "search_results" not in context

    def test_no_op_when_task_type_does_not_match_keywords(self):
        """AC4: Verify no-op when task_type does not contain research keywords."""
        task = TaskInput(task_type="regular_task", description="some regular task")
        context = {}
        mock_search_tool = MagicMock()

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_research_context(task, context)

        # get_search_tool should not be called
        mock_search_tool.search.assert_not_called()
        assert "search_results" not in context

    def test_no_op_when_task_type_is_empty(self):
        """Verify no-op when task_type is empty string."""
        task = TaskInput(task_type="", description="some task")
        context = {}
        mock_search_tool = MagicMock()

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_research_context(task, context)

        mock_search_tool.search.assert_not_called()
        assert "search_results" not in context

    def test_no_op_when_task_type_missing(self):
        """Verify no-op when task_type key is missing from task."""
        task = TaskInput(task_type="", description="some task")
        context = {}
        mock_search_tool = MagicMock()

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_research_context(task, context)

        mock_search_tool.search.assert_not_called()
        assert "search_results" not in context

    def test_no_injection_when_search_returns_empty_results(self):
        """Verify no search_results injected when search returns empty list."""
        task = TaskInput(task_type="research_analysis", description="research topics")
        context = {}
        mock_search_tool = MagicMock()
        mock_search_tool.search.return_value = []

        with patch("src.engines.envy_gluttony_helpers.get_search_tool", return_value=mock_search_tool):
            inject_research_context(task, context)

        assert "search_results" not in context
