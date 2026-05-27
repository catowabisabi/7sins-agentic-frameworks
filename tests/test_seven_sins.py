"""
Tests for Seven Sins Engine Isolation
Unit tests with mocked LLM calls for seven_sins.py

Tests each Sin independently with various task types to verify
that each Sin returns expected behavior for its specialization.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

import sys
sys.path.insert(0, '/mnt/c/Users/enoma/Desktop/7')

from src.core.drive_engine import DriveType, DriveOpinion, DriveState, DriveEngine
from src.engines.seven_sins import (
    GluttonyEngine,
    LustEngine,
    GreedEngine,
    SlothEngine,
    PrideEngine,
    WrathEngine,
    EnvyEngine,
)


# =============================================================================
# Mock LLM Provider and Response
# =============================================================================

class MockLLMResponse:
    """Mock LLM response for testing."""
    def __init__(self, content: str):
        self.content = content


class MockLLMProvider:
    """Mock LLM provider that returns predefined responses."""
    
    def __init__(self, response_content: str = "Mock response with confidence: 0.8 and risk: medium"):
        self._response_content = response_content
    
    def complete(self, prompt: str, system_prompt: str) -> MockLLMResponse:
        return MockLLMResponse(self._response_content)


class MockSearchTool:
    """Mock search tool for testing."""
    
    def search(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        return [
            {"title": f"Result {i} for {query}", "url": f"http://example.com/{i}", "snippet": f"Snippet {i}"}
            for i in range(min(count, 3))
        ]


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def mock_search():
    """Create a mock search tool."""
    return MockSearchTool()


@pytest.fixture
def gluttony_engine(mock_provider, mock_search):
    """Create a GluttonyEngine with mocked dependencies."""
    with patch('src.engines.seven_sins._get_llm_provider', return_value=mock_provider):
        with patch('src.engines.seven_sins.get_search_tool', return_value=mock_search):
            engine = GluttonyEngine()
            yield engine


@pytest.fixture
def lust_engine(mock_provider):
    """Create a LustEngine with mocked dependencies."""
    with patch('src.engines.seven_sins._get_llm_provider', return_value=mock_provider):
        engine = LustEngine()
        yield engine


@pytest.fixture
def greed_engine(mock_provider):
    """Create a GreedEngine with mocked dependencies."""
    with patch('src.engines.seven_sins._get_llm_provider', return_value=mock_provider):
        engine = GreedEngine()
        yield engine


@pytest.fixture
def sloth_engine(mock_provider):
    """Create a SlothEngine with mocked dependencies."""
    with patch('src.engines.seven_sins._get_llm_provider', return_value=mock_provider):
        engine = SlothEngine()
        yield engine


@pytest.fixture
def pride_engine(mock_provider):
    """Create a PrideEngine with mocked dependencies."""
    with patch('src.engines.seven_sins._get_llm_provider', return_value=mock_provider):
        engine = PrideEngine()
        yield engine


@pytest.fixture
def wrath_engine(mock_provider):
    """Create a WrathEngine with mocked dependencies."""
    with patch('src.engines.seven_sins._get_llm_provider', return_value=mock_provider):
        engine = WrathEngine()
        yield engine


@pytest.fixture
def envy_engine(mock_provider, mock_search):
    """Create an EnvyEngine with mocked dependencies."""
    with patch('src.engines.seven_sins._get_llm_provider', return_value=mock_provider):
        with patch('src.engines.seven_sins.get_search_tool', return_value=mock_search):
            engine = EnvyEngine()
            yield engine


# =============================================================================
# Test: GluttonyEngine - Knowledge Harvester
# =============================================================================

class TestGluttonyEngine:
    """Tests for GluttonyEngine (Knowledge Harvester)."""
    
    def test_gluttony_properties(self, gluttony_engine):
        """Test GluttonyEngine has correct properties."""
        assert gluttony_engine.drive_type == DriveType.GLUTTONY
        assert "research" in gluttony_engine.specialization
        assert "analysis" in gluttony_engine.specialization
        assert "explore" in gluttony_engine.specialization
        assert "investigate" in gluttony_engine.specialization
    
    def test_gluttony_system_prompt_contains_harvester(self, gluttony_engine):
        """Test system prompt reflects knowledge harvester nature."""
        assert "Gluttony" in gluttony_engine.system_prompt
        assert "Knowledge Harvester" in gluttony_engine.system_prompt
    
    def test_gluttony_veto_condition(self, gluttony_engine):
        """Test veto condition for insufficient information."""
        assert "information" in gluttony_engine.veto_condition.lower() or "knowledge" in gluttony_engine.veto_condition.lower()
    
    def test_gluttony_research_task(self, gluttony_engine):
        """Test Gluttony with research task type."""
        task = {
            "description": "Research AI safety techniques",
            "task_type": "research_investigate",
            "constraints": [],
        }
        context = {}
        
        opinion = gluttony_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.GLUTTONY
        assert 0.0 <= opinion.confidence <= 1.0
        assert opinion.risk_level in ["low", "medium", "high"]
        assert "search_results" in context or "Mock response" in opinion.opinion
    
    def test_gluttony_creation_task(self, gluttony_engine):
        """Test Gluttony with creation task adjusts eros weight."""
        task = {
            "description": "Create a new research framework",
            "task_type": "create_build_design_new",
            "constraints": [],
        }
        context = {}
        
        initial_eros = gluttony_engine.state.eros_weight
        opinion = gluttony_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.GLUTTONY
    
    def test_gluttony_deletion_task(self, gluttony_engine):
        """Test Gluttony with deletion task adjusts thanatos weight."""
        task = {
            "description": "Delete outdated research files",
            "task_type": "delete_remove_destroy_cleanup",
            "constraints": [],
        }
        context = {}
        
        opinion = gluttony_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.GLUTTONY


# =============================================================================
# Test: LustEngine - Sovereign Architect
# =============================================================================

class TestLustEngine:
    """Tests for LustEngine (Sovereign Architect)."""
    
    def test_lust_properties(self, lust_engine):
        """Test LustEngine has correct properties."""
        assert lust_engine.drive_type == DriveType.LUST
        assert "control" in lust_engine.specialization
        assert "order" in lust_engine.specialization
        assert "architecture" in lust_engine.specialization
        assert "manage" in lust_engine.specialization
    
    def test_lust_system_prompt_contains_architect(self, lust_engine):
        """Test system prompt reflects sovereign architect nature."""
        assert "Lust" in lust_engine.system_prompt
        assert "Sovereign Architect" in lust_engine.system_prompt
    
    def test_lust_veto_condition(self, lust_engine):
        """Test veto condition for loss of control."""
        assert "control" in lust_engine.veto_condition.lower() or "integrity" in lust_engine.veto_condition.lower()
    
    def test_lust_control_task(self, lust_engine):
        """Test Lust with control/architecture task."""
        task = {
            "description": "Design access control system",
            "task_type": "create_architecture_control",
            "constraints": [],
        }
        context = {}
        
        opinion = lust_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.LUST
        assert 0.0 <= opinion.confidence <= 1.0
    
    def test_lust_resource_management_task(self, lust_engine):
        """Test Lust with resource management task."""
        task = {
            "description": "Manage system resources",
            "task_type": "manage_resource_priority",
            "constraints": [],
        }
        context = {}
        
        opinion = lust_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.LUST


# =============================================================================
# Test: GreedEngine - Value Maximizer
# =============================================================================

class TestGreedEngine:
    """Tests for GreedEngine (Value Maximizer)."""
    
    def test_greed_properties(self, greed_engine):
        """Test GreedEngine has correct properties."""
        assert greed_engine.drive_type == DriveType.GREED
        assert "market" in greed_engine.specialization
        assert "value" in greed_engine.specialization
        assert "revenue" in greed_engine.specialization
        assert "growth" in greed_engine.specialization
    
    def test_greed_system_prompt_contains_maximizer(self, greed_engine):
        """Test system prompt reflects value maximizer nature."""
        assert "Greed" in greed_engine.system_prompt
        assert "Value Maximizer" in greed_engine.system_prompt
    
    def test_greed_veto_condition(self, greed_engine):
        """Test veto condition for unclear value."""
        assert "value" in greed_engine.veto_condition.lower() or "roi" in greed_engine.veto_condition.lower()
    
    def test_greed_market_task(self, greed_engine):
        """Test Greed with market/value task."""
        task = {
            "description": "Analyze market opportunity",
            "task_type": "market_value_strategy",
            "constraints": [],
        }
        context = {}
        
        opinion = greed_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.GREED
        assert 0.0 <= opinion.confidence <= 1.0
    
    def test_greed_feature_task(self, greed_engine):
        """Test Greed with feature/growth task."""
        task = {
            "description": "Implement user growth feature",
            "task_type": "create_feature_growth",
            "constraints": [],
        }
        context = {}
        
        opinion = greed_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.GREED


# =============================================================================
# Test: SlothEngine - Lazy Genius
# =============================================================================

class TestSlothEngine:
    """Tests for SlothEngine (Lazy Genius)."""
    
    def test_sloth_properties(self, sloth_engine):
        """Test SlothEngine has correct properties."""
        assert sloth_engine.drive_type == DriveType.SLOTH
        assert "automation" in sloth_engine.specialization
        assert "efficiency" in sloth_engine.specialization
        assert "script" in sloth_engine.specialization
        assert "tool" in sloth_engine.specialization
    
    def test_sloth_system_prompt_contains_lazy_genius(self, sloth_engine):
        """Test system prompt reflects lazy genius nature."""
        assert "Sloth" in sloth_engine.system_prompt
        assert "Lazy Genius" in sloth_engine.system_prompt
    
    def test_sloth_veto_condition(self, sloth_engine):
        """Test veto condition for unnecessary complexity."""
        assert "complexity" in sloth_engine.veto_condition.lower() or "effort" in sloth_engine.veto_condition.lower()
    
    def test_sloth_automation_task(self, sloth_engine):
        """Test Sloth with automation task."""
        task = {
            "description": "Automate repetitive task",
            "task_type": "automation_script_tool",
            "constraints": [],
        }
        context = {}
        
        opinion = sloth_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.SLOTH
        assert 0.0 <= opinion.confidence <= 1.0
    
    def test_sloth_refactor_task(self, sloth_engine):
        """Test Sloth with refactor/efficiency task."""
        task = {
            "description": "Refactor code for efficiency",
            "task_type": "refactor_efficiency",
            "constraints": [],
        }
        context = {}
        
        opinion = sloth_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.SLOTH


# =============================================================================
# Test: PrideEngine - Quality Arbiter
# =============================================================================

class TestPrideEngine:
    """Tests for PrideEngine (Quality Arbiter)."""
    
    def test_pride_properties(self, pride_engine):
        """Test PrideEngine has correct properties."""
        assert pride_engine.drive_type == DriveType.PRIDE
        assert "review" in pride_engine.specialization
        assert "quality" in pride_engine.specialization
        assert "code" in pride_engine.specialization
        assert "clean" in pride_engine.specialization
    
    def test_pride_system_prompt_contains_arbiter(self, pride_engine):
        """Test system prompt reflects quality arbiter nature."""
        assert "Pride" in pride_engine.system_prompt
        assert "Quality Arbiter" in pride_engine.system_prompt
    
    def test_pride_veto_condition(self, pride_engine):
        """Test veto condition for quality standards."""
        assert "quality" in pride_engine.veto_condition.lower() or "standard" in pride_engine.veto_condition.lower()
    
    def test_pride_code_review_task(self, pride_engine):
        """Test Pride with code review task."""
        task = {
            "description": "Review code quality",
            "task_type": "review_code_quality",
            "constraints": [],
        }
        context = {}
        
        opinion = pride_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.PRIDE
        assert 0.0 <= opinion.confidence <= 1.0
    
    def test_pride_refactor_task(self, pride_engine):
        """Test Pride with refactor/clean task."""
        task = {
            "description": "Clean up code",
            "task_type": "refactor_clean_standard",
            "constraints": [],
        }
        context = {}
        
        opinion = pride_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.PRIDE


# =============================================================================
# Test: WrathEngine - Zero-Tolerance Guardian
# =============================================================================

class TestWrathEngine:
    """Tests for WrathEngine (Zero-Tolerance Guardian)."""
    
    def test_wrath_properties(self, wrath_engine):
        """Test WrathEngine has correct properties."""
        assert wrath_engine.drive_type == DriveType.WRATH
        assert "bug" in wrath_engine.specialization
        assert "error" in wrath_engine.specialization
        assert "debug" in wrath_engine.specialization
        assert "fix" in wrath_engine.specialization
    
    def test_wrath_system_prompt_contains_guardian(self, wrath_engine):
        """Test system prompt reflects zero-tolerance guardian nature."""
        assert "Wrath" in wrath_engine.system_prompt
        assert "Zero-Tolerance Guardian" in wrath_engine.system_prompt
    
    def test_wrath_veto_condition(self, wrath_engine):
        """Test veto condition for errors."""
        assert "error" in wrath_engine.veto_condition.lower() or "compromised" in wrath_engine.veto_condition.lower()
    
    def test_wrath_bug_fix_task(self, wrath_engine):
        """Test Wrath with bug fix task."""
        task = {
            "description": "Fix critical bug",
            "task_type": "fix_bug_error_debug",
            "constraints": [],
        }
        context = {}
        
        opinion = wrath_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.WRATH
        assert 0.0 <= opinion.confidence <= 1.0
    
    def test_wrath_fault_task(self, wrath_engine):
        """Test Wrath with fault/crash task."""
        task = {
            "description": "Debug crash issue",
            "task_type": "debug_fault_crash_fail",
            "constraints": [],
        }
        context = {}
        
        opinion = wrath_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.WRATH


# =============================================================================
# Test: EnvyEngine - Competitive Analyst
# =============================================================================

class TestEnvyEngine:
    """Tests for EnvyEngine (Competitive Analyst)."""
    
    def test_envy_properties(self, envy_engine):
        """Test EnvyEngine has correct properties."""
        assert envy_engine.drive_type == DriveType.ENVY
        assert "benchmark" in envy_engine.specialization
        assert "competitor" in envy_engine.specialization
        assert "compare" in envy_engine.specialization
        assert "best" in envy_engine.specialization
    
    def test_envy_system_prompt_contains_analyst(self, envy_engine):
        """Test system prompt reflects competitive analyst nature."""
        assert "Envy" in envy_engine.system_prompt
        assert "Competitive Analyst" in envy_engine.system_prompt
    
    def test_envy_veto_condition(self, envy_engine):
        """Test veto condition for competitive inferiority."""
        assert "inferior" in envy_engine.veto_condition.lower() or "competition" in envy_engine.veto_condition.lower()
    
    def test_envy_benchmark_task(self, envy_engine):
        """Test Envy with benchmark task."""
        task = {
            "description": "Benchmark against competitors",
            "task_type": "benchmark_competitor_compare",
            "constraints": [],
        }
        context = {}
        
        opinion = envy_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.ENVY
        assert 0.0 <= opinion.confidence <= 1.0
    
    def test_envy_industry_task(self, envy_engine):
        """Test Envy with industry comparison task."""
        task = {
            "description": "Compare with industry best",
            "task_type": "industry_best_standard",
            "constraints": [],
        }
        context = {}
        
        opinion = envy_engine.evaluate(task, context)
        
        assert isinstance(opinion, DriveOpinion)
        assert opinion.drive == DriveType.ENVY


# =============================================================================
# Test: Sin Engine Isolation - Each Sin Operates Independently
# =============================================================================

class TestSinEngineIsolation:
    """Tests to verify each Sin engine operates independently."""
    
    def test_all_sins_have_unique_drive_types(self, gluttony_engine, lust_engine, greed_engine,
                                              sloth_engine, pride_engine, wrath_engine, envy_engine):
        """Test that all Sins have unique drive types."""
        drive_types = [
            gluttony_engine.drive_type,
            lust_engine.drive_type,
            greed_engine.drive_type,
            sloth_engine.drive_type,
            pride_engine.drive_type,
            wrath_engine.drive_type,
            envy_engine.drive_type,
        ]
        assert len(drive_types) == len(set(drive_types)), "All Sins should have unique drive types"
    
    def test_all_sins_implement_drive_engine_interface(self):
        """Test that all Sins properly implement DriveEngine interface."""
        sin_engines = [
            GluttonyEngine,
            LustEngine,
            GreedEngine,
            SlothEngine,
            PrideEngine,
            WrathEngine,
            EnvyEngine,
        ]
        
        for engine_class in sin_engines:
            # Verify it's a subclass of DriveEngine
            assert issubclass(engine_class, DriveEngine), f"{engine_class.__name__} should be a DriveEngine subclass"
            
            # Verify it has required abstract properties
            assert hasattr(engine_class, 'system_prompt'), f"{engine_class.__name__} should have system_prompt property"
            assert hasattr(engine_class, 'specialization'), f"{engine_class.__name__} should have specialization property"
            assert hasattr(engine_class, 'veto_condition'), f"{engine_class.__name__} should have veto_condition property"
            
            # Verify it has required methods
            assert hasattr(engine_class, 'evaluate'), f"{engine_class.__name__} should have evaluate method"
            assert hasattr(engine_class, 'on_task_complete'), f"{engine_class.__name__} should have on_task_complete method"
    
    def test_all_sins_return_drive_opinion(self):
        """Test that all Sins return DriveOpinion from evaluate."""
        with patch('src.engines.seven_sins._get_llm_provider', return_value=MockLLMProvider()):
            with patch('src.engines.seven_sins.get_search_tool', return_value=MockSearchTool()):
                
                engines = [
                    GluttonyEngine(),
                    LustEngine(),
                    GreedEngine(),
                    SlothEngine(),
                    PrideEngine(),
                    WrathEngine(),
                    EnvyEngine(),
                ]
                
                task = {
                    "description": "Test task",
                    "task_type": "create_build",
                    "constraints": [],
                }
                
                for engine in engines:
                    opinion = engine.evaluate(task, {})
                    assert isinstance(opinion, DriveOpinion), f"{engine.drive_type} should return DriveOpinion"
                    assert opinion.drive == engine.drive_type
    
    def test_all_sins_handle_task_types_differently(self):
        """Test that Sins respond to task types based on their specialization."""
        mock_provider = MockLLMProvider()
        
        with patch('src.engines.seven_sins._get_llm_provider', return_value=mock_provider):
            with patch('src.engines.seven_sins.get_search_tool', return_value=MockSearchTool()):
                
                # Gluttony should be activated by research tasks
                gluttony = GluttonyEngine()
                research_task = {"description": "Research AI", "task_type": "research_analyze", "constraints": []}
                gluttony_opinion = gluttony.evaluate(research_task, {})
                assert gluttony.state.confidence > 0, "Gluttony should activate for research tasks"
                
                # Wrath should be activated by bug/error tasks
                wrath = WrathEngine()
                bug_task = {"description": "Fix bug", "task_type": "fix_bug_debug", "constraints": []}
                wrath_opinion = wrath.evaluate(bug_task, {})
                assert wrath.state.confidence > 0, "Wrath should activate for bug tasks"
                
                # Sloth should be activated by automation tasks
                sloth = SlothEngine()
                auto_task = {"description": "Automate task", "task_type": "automation_script", "constraints": []}
                sloth_opinion = sloth.evaluate(auto_task, {})
                assert sloth.state.confidence > 0, "Sloth should activate for automation tasks"


# =============================================================================
# Test: Sin Weight Adjustment
# =============================================================================

class TestSinWeightAdjustment:
    """Tests for Sin weight adjustment mechanisms."""
    
    def test_gluttony_adjusts_on_success(self, gluttony_engine):
        """Test Gluttony weight increases on successful task."""
        initial_weight = gluttony_engine.state.weight
        gluttony_engine.on_task_complete(success=True)
        assert gluttony_engine.state.weight >= initial_weight
    
    def test_gluttony_adjusts_on_failure(self, gluttony_engine):
        """Test Gluttony weight decreases on failed task."""
        initial_weight = gluttony_engine.state.weight
        gluttony_engine.on_task_complete(success=False)
        assert gluttony_engine.state.weight <= initial_weight
    
    def test_wrath_adjusts_on_failure(self, wrath_engine):
        """Test Wrath weight decreases significantly on failed task."""
        initial_weight = wrath_engine.state.weight
        wrath_engine.on_task_complete(success=False)
        assert wrath_engine.state.weight <= initial_weight
    
    def test_weight_bounds_enforced(self, gluttony_engine):
        """Test that weight stays within bounds."""
        # Try to increase weight beyond max
        for _ in range(20):
            gluttony_engine.adjust_weight(0.1)
        
        assert gluttony_engine.state.weight <= gluttony_engine.state.MAX_WEIGHT
        assert gluttony_engine.state.weight >= gluttony_engine.state.MIN_WEIGHT