"""
Search injection helpers for engines that require external data.

This module provides shared utilities for engines that need to inject
search results into the context before evaluation.
"""

import logging
from typing import Dict, Any, List

from src.tools.search import get_search_tool, SearchUnavailableError

logger = logging.getLogger(__name__)

__all__ = ['inject_competitor_search', 'inject_research_context']


def inject_competitor_search(task: Dict[str, Any], context: Dict[str, Any]) -> None:
    """
    Inject competitor benchmark data into context for competitive analysis.
    
    Searches for competitor information when task_type indicates competitive
    analysis (e.g., 'competitor', 'benchmark', 'compare' keywords).
    Results are stored under context["competitor_info"].
    """
    task_type = task.task_type if hasattr(task, 'task_type') else task.get('task_type', '')
    is_competitive = any(kw in task_type for kw in ["competitor", "benchmark", "compare"])
    
    if is_competitive:
        try:
            search_tool = get_search_tool()
            competitor_results = search_tool.search(task.description, count=10)
            if competitor_results:
                context["competitor_info"] = competitor_results
        except SearchUnavailableError:
            logger.warning("Search tool unavailable - proceeding without competitor data")


def inject_research_context(task: Dict[str, Any], context: Dict[str, Any]) -> None:
    """
    Inject research search results into context for deep investigation.
    
    Searches for research information when task_type indicates research
    (e.g., 'research', 'search', 'investigate' keywords).
    Results are stored under context["search_results"].
    """
    task_type = task.task_type if hasattr(task, 'task_type') else task.get('task_type', '')
    is_research = any(kw in task_type for kw in ["research", "search", "investigate"])
    
    if is_research:
        try:
            search_tool = get_search_tool()
            search_results = search_tool.search(task.description, count=10)
            if search_results:
                context["search_results"] = search_results
        except SearchUnavailableError:
            logger.warning("Search tool unavailable - proceeding without research data")