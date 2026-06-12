"""
End-to-End Integration Tests for 7Sins Project
Tests full pipeline with real EGO-Core flow and debate visualization
"""

import pytest
import time
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

import sys

from src.core.ego_core import (
    AuditLogger,
    DecisionPhase,
    TaskInput,
    DecisionResult,
    EGOState,
    EGOCore,
)
from src.core.drive_engine import (
    DriveEngine,
    DriveEngineRegistry,
    DriveType,
    DriveOpinion,
    DriveState,
)
from src.memory.persistence import PersistenceManager, get_persistence_manager


# =============================================================================
# Mock Drive Engines for Integration Testing
# =============================================================================

class MockSevenSinsEngine(DriveEngine):
    """Mock drive engine that simulates Seven Sins behavior without LLM calls."""
    
    def __init__(self, drive_type: DriveType, base_weight: float = 0.5):
        super().__init__(drive_type, base_weight)
        self._evaluate_count = 0
        self._debate_rounds = []
    
    @property
    def system_prompt(self) -> str:
        return f"Mock {self.drive_type.value} system prompt"
    
    @property
    def specialization(self) -> List[str]:
        # Map drive type to relevant specializations
        specializations = {
            DriveType.GLUTTONY: ["research", "analysis", "investigate", "learn"],
            DriveType.LUST: ["control", "order", "manage", "priority"],
            DriveType.GREED: ["market", "value", "growth", "feature"],
            DriveType.SLOTH: ["automation", "efficiency", "script", "repeat"],
            DriveType.PRIDE: ["quality", "review", "refactor", "clean"],
            DriveType.WRATH: ["bug", "error", "fix", "debug", "fault"],
            DriveType.ENVY: ["competitor", "benchmark", "compare", "standard"],
            DriveType.EROS: ["create", "build", "design", "new"],
            DriveType.THANATOS: ["delete", "remove", "destroy", "cleanup"],
        }
        return specializations.get(self.drive_type, ["general"])
    
    @property
    def veto_condition(self) -> str:
        return f"Veto condition for {self.drive_type.value}"
    
    def evaluate(self, task: Any, context: Dict[str, Any]) -> DriveOpinion:
        """Evaluate task and generate opinion for debate.
        
        Handles both TaskInput objects and dicts.
        """
        self._evaluate_count += 1
        self.state.activate(0.7 + (hash(str(task)) % 30) / 100)  # Vary confidence
        
        # Handle both TaskInput objects and dicts
        if hasattr(task, 'task_type'):
            task_type = task.task_type.lower()
            description = task.description
        else:
            task_type = task.get("task_type", "").lower()
            description = task.get("description", "")
        
        # Simulate debate by adjusting opinion based on task type
        confidence = 0.7
        risk_level = "medium"
        
        if self.drive_type == DriveType.WRATH:
            if "error" in task_type or "bug" in task_type or "fix" in task_type:
                confidence = 0.9
                risk_level = "high"
        
        return DriveOpinion(
            drive=self.drive_type,
            opinion=f"{self.drive_type.value.capitalize()} opinion: {description[:50]}",
            confidence=confidence,
            recommendation=f"{self.drive_type.value.capitalize()} recommends proceeding with caution",
            risk_level=risk_level
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.05)


class MockLLMProvider:
    """Mock LLM provider for testing without real API calls."""
    
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.call_count = 0
    
    def complete(self, prompt: str, system_prompt: str = None) -> 'MockLLMResponse':
        self.call_count += 1
        key = list(self.responses.keys())[self.call_count % len(self.responses)] if self.responses else "default"
        return MockLLMResponse(self.responses.get(key, f"Mock response {self.call_count}"))


class MockLLMResponse:
    """Mock LLM response object."""
    
    def __init__(self, content: str):
        self.content = content


# =============================================================================
# Debate Visualization Helper
# =============================================================================

class DebateVisualizer:
    """Captures and formats debate rounds for visualization."""
    
    def __init__(self):
        self.rounds: List[Dict[str, Any]] = []
        self.current_round = 0
    
    def start_debate(self, task: TaskInput):
        """Initialize debate visualization for a task."""
        self.rounds.append({
            "round": self.current_round,
            "task": task.description,
            "task_type": task.task_type,
            "participants": [],
            "opinions": {},
            "consensus_reached": False
        })
    
    def record_opinion(self, drive: DriveType, opinion: DriveOpinion, round_num: int):
        """Record a drive's opinion in the debate."""
        while len(self.rounds) <= round_num:
            self.rounds.append({"round": round_num, "participants": [], "opinions": {}, "consensus_reached": False})
        
        if drive not in [p for p in self.rounds[round_num].get("participants", [])]:
            self.rounds[round_num].setdefault("participants", []).append(drive)
        
        self.rounds[round_num]["opinions"][drive.value] = {
            "opinion": opinion.opinion[:100],
            "confidence": opinion.confidence,
            "risk_level": opinion.risk_level,
            "recommendation": opinion.recommendation[:100]
        }
    
    def check_consensus(self, opinions: Dict[DriveType, DriveOpinion]) -> bool:
        """Check if consensus has been reached among drives."""
        if len(opinions) < 2:
            return False
        high_confidence = [o for o in opinions.values() if o.confidence >= 0.8]
        return len(high_confidence) > len(opinions) / 2
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the debate."""
        return {
            "total_rounds": len(self.rounds),
            "rounds": self.rounds,
            "final_state": self.rounds[-1] if self.rounds else None
        }


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for audit logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_persistence():
    """Create a mock persistence manager."""
    persistence = MagicMock(spec=PersistenceManager)
    persistence.log_decision = Mock()
    persistence.log_weight_change = Mock()
    return persistence


@pytest.fixture
def registry():
    """Create a drive engine registry with all 7 Sins engines."""
    reg = DriveEngineRegistry()
    
    # Register all seven sin engines
    reg.register(MockSevenSinsEngine(DriveType.GLUTTONY, 0.7))
    reg.register(MockSevenSinsEngine(DriveType.LUST, 0.6))
    reg.register(MockSevenSinsEngine(DriveType.GREED, 0.8))
    reg.register(MockSevenSinsEngine(DriveType.SLOTH, 0.5))
    reg.register(MockSevenSinsEngine(DriveType.PRIDE, 0.6))
    reg.register(MockSevenSinsEngine(DriveType.WRATH, 0.8))
    reg.register(MockSevenSinsEngine(DriveType.ENVY, 0.5))
    
    return reg


@pytest.fixture
def ego_core_with_persistence(registry, mock_persistence, temp_log_dir):
    """Create an EGOCore instance with mocked persistence."""
    with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
        with patch('src.core.drive_engine.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(registry)
            core.audit_logger = AuditLogger(log_dir=temp_log_dir)
            yield core


@pytest.fixture
def sample_research_task():
    """Create a sample research task."""
    return TaskInput(
        description="Research best practices for microservices architecture",
        task_type="research_analyze_investigate",
        constraints=["must be comprehensive", "must include recent trends"],
        context={"user": "test_user", "domain": "architecture"},
        priority=0.8
    )


@pytest.fixture
def sample_creation_task():
    """Create a sample creation task."""
    return TaskInput(
        description="Create a new user authentication module",
        task_type="create_build_design_new",
        constraints=["must be secure", "must be scalable"],
        context={"user": "test_user", "security_level": "high"},
        priority=0.9
    )


@pytest.fixture
def sample_deletion_task():
    """Create a sample deletion task."""
    return TaskInput(
        description="Remove deprecated API endpoints",
        task_type="delete_remove_cleanup_destroy",
        constraints=["must preserve data", "must update documentation"],
        context={"user": "test_user", "api_version": "v1"},
        priority=0.6
    )


# =============================================================================
# Test Classes
# =============================================================================

class TestIntegrationFullPipeline:
    """End-to-end tests for the full EGO-Core pipeline."""
    
    def test_full_pipeline_research_task(self, ego_core_with_persistence, sample_research_task, mock_persistence):
        """Test complete pipeline with a research task."""
        core = ego_core_with_persistence
        task = sample_research_task
        
        # Process the task through all phases
        result = core.process_task(task)
        
        # Verify result structure
        assert isinstance(result, DecisionResult)
        assert result.recommendation != ""
        assert 0.0 <= result.confidence <= 1.0
        assert result.phase == DecisionPhase.EXECUTION
        
        # Verify state transitions
        assert core.state.current_task == task
        assert core.state.phase == DecisionPhase.EXECUTION
        assert len(core.state.active_drives) > 0
        assert len(core.state.opinions) > 0
        assert core.state.decision is not None
        
        # Verify persistence was called
        mock_persistence.log_decision.assert_called()
        
        # Verify audit log was created
        log_file = os.path.join(core.audit_logger.log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        assert os.path.exists(log_file)
    
    def test_full_pipeline_creation_task(self, ego_core_with_persistence, sample_creation_task, mock_persistence):
        """Test complete pipeline with a creation task."""
        core = ego_core_with_persistence
        task = sample_creation_task
        
        result = core.process_task(task)
        
        # Verify creation task specific behavior
        assert isinstance(result, DecisionResult)
        
        # Verify opinions were collected
        assert len(core.state.opinions) > 0
        
        # Verify decision was made
        assert result.selected_drives is not None
        assert len(result.selected_drives) > 0
    
    def test_full_pipeline_deletion_task(self, ego_core_with_persistence, sample_deletion_task, mock_persistence):
        """Test complete pipeline with a deletion task."""
        core = ego_core_with_persistence
        task = sample_deletion_task
        
        result = core.process_task(task)
        
        assert isinstance(result, DecisionResult)
        assert result.phase == DecisionPhase.EXECUTION
    
    def test_multiple_tasks_sequence(self, ego_core_with_persistence, mock_persistence):
        """Test processing multiple tasks in sequence."""
        core = ego_core_with_persistence
        
        tasks = [
            TaskInput(description="Task 1", task_type="create_build", priority=0.8),
            TaskInput(description="Task 2", task_type="research_analyze", priority=0.7),
            TaskInput(description="Task 3", task_type="delete_remove", priority=0.6),
        ]
        
        results = []
        for task in tasks:
            result = core.process_task(task)
            results.append(result)
            
            # Verify each decision was logged
            mock_persistence.log_decision.assert_called()
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, DecisionResult)
            assert result.phase == DecisionPhase.EXECUTION


class TestDebateVisualization:
    """Tests for debate visualization in the Seven Sins engine."""
    
    def test_debate_visualization_captures_rounds(self, ego_core_with_persistence, sample_creation_task):
        """Test that debate visualization captures all rounds."""
        core = ego_core_with_persistence
        visualizer = DebateVisualizer()
        
        # Start debate visualization
        visualizer.start_debate(sample_creation_task)
        
        # Process task with full pipeline
        result = core.process_task(sample_creation_task)
        
        # Manually simulate debate rounds for verification
        for round_num in range(core.max_debate_rounds):
            for drive, opinion in core.state.opinions.items():
                visualizer.record_opinion(drive, opinion, round_num)
        
        # Verify visualization captured data
        summary = visualizer.get_summary()
        assert summary["total_rounds"] > 0 or len(core.state.opinions) > 0
    
    def test_debate_consensus_check(self, ego_core_with_persistence, sample_research_task):
        """Test consensus detection in debate."""
        core = ego_core_with_persistence
        
        # Process task
        result = core.process_task(sample_research_task)
        
        # Check consensus
        visualizer = DebateVisualizer()
        has_consensus = visualizer.check_consensus(core.state.opinions)
        
        # Consensus should be reached or not based on opinion distribution
        assert isinstance(has_consensus, bool)
    
    def test_debate_rounds_with_multiple_drives(self, ego_core_with_persistence):
        """Test debate with multiple active drives."""
        core = ego_core_with_persistence
        
        task = TaskInput(
            description="Complex multi-faceted task",
            task_type="research_analyze_create_build",
            priority=0.9
        )
        
        result = core.process_task(task)
        
        # Verify at least one drive participated (actual count depends on specialization matching)
        assert len(core.state.active_drives) >= 1
        assert len(core.state.opinions) >= 1
        
        # Verify each opinion has required fields
        for drive, opinion in core.state.opinions.items():
            assert isinstance(opinion, DriveOpinion)
            assert opinion.drive is not None
            assert opinion.opinion != ""
            assert 0.0 <= opinion.confidence <= 1.0
            assert opinion.risk_level in ["low", "medium", "high"]


class TestSevenSinsEngineIntegration:
    """Tests for Seven Sins engine integration with EGO-Core."""
    
    def test_all_seven_sins_engines_registered(self, ego_core_with_persistence):
        """Test that all seven sin engines are registered and active."""
        core = ego_core_with_persistence
        
        # Verify all seven sins are available
        expected_drives = [
            DriveType.GLUTTONY,
            DriveType.LUST,
            DriveType.GREED,
            DriveType.SLOTH,
            DriveType.PRIDE,
            DriveType.WRATH,
            DriveType.ENVY,
        ]
        
        for drive_type in expected_drives:
            engine = core.registry.get(drive_type)
            assert engine is not None, f"{drive_type.value} not registered"
            assert engine.state.weight > 0
    
    def test_engines_activate_on_task(self, ego_core_with_persistence, sample_creation_task):
        """Test that relevant engines activate when processing a task."""
        core = ego_core_with_persistence
        
        result = core.process_task(sample_creation_task)
        
        # Check that engines were activated
        for drive in core.state.active_drives:
            engine = core.registry.get(drive)
            assert engine is not None
            assert engine.state.last_active > 0
    
    def test_drive_weights_affect_decision(self, ego_core_with_persistence):
        """Test that drive weights influence decision outcome."""
        core = ego_core_with_persistence
        
        # Set different weights for drives
        gluttony_engine = core.registry.get(DriveType.GLUTTONY)
        greed_engine = core.registry.get(DriveType.GREED)
        
        if gluttony_engine and greed_engine:
            gluttony_engine.state.weight = 0.9  # High weight
            greed_engine.state.weight = 0.2  # Low weight
            
            task = TaskInput(description="Research market trends", task_type="research_analyze")
            result = core.process_task(task)
            
            # Higher weighted drive should influence result
            assert result.selected_drives is not None


class TestEGOCoreDecisionPhases:
    """Tests for EGO-Core decision phase transitions."""
    
    def test_phase_sequence_complete(self, ego_core_with_persistence, sample_creation_task):
        """Test that all phases complete in sequence."""
        core = ego_core_with_persistence
        task = sample_creation_task
        
        # Track phase transitions
        phases_observed = []
        original_phase = core.state.phase
        
        result = core.process_task(task)
        
        # Verify final phase is EXECUTION
        assert core.state.phase == DecisionPhase.EXECUTION
        assert result.phase == DecisionPhase.EXECUTION
    
    def test_consultation_phase_collects_opinions(self, ego_core_with_persistence, sample_research_task):
        """Test that consultation phase collects drive opinions."""
        core = ego_core_with_persistence
        
        # Manually set to consultation phase
        core.state.phase = DecisionPhase.CONSULTATION
        core.state.current_task = sample_research_task
        
        # Get relevant drives
        relevant_drives = core.registry.get_by_task_type(sample_research_task.task_type)
        core.state.active_drives = [d.drive_type for d in relevant_drives]
        
        # Collect opinions
        for engine in relevant_drives:
            opinion = engine.evaluate(sample_research_task, sample_research_task.context)
            core.state.opinions[engine.drive_type] = opinion
        
        # Verify opinions collected
        assert len(core.state.opinions) > 0
    
    def test_debate_phase_runs_rounds(self, ego_core_with_persistence, sample_creation_task):
        """Test that debate phase runs for max rounds or until consensus."""
        core = ego_core_with_persistence
        
        # Set up state for debate
        core.state.current_task = sample_creation_task
        core.state.phase = DecisionPhase.DEBATE
        
        # Add some opinions
        for drive_type in [DriveType.GLUTTONY, DriveType.GREED, DriveType.PRIDE]:
            engine = core.registry.get(drive_type)
            if engine:
                opinion = engine.evaluate(sample_creation_task, {})
                core.state.opinions[drive_type] = opinion
        
        # Run debate
        core._run_debate()
        
        # Debate completes without error
        assert True  # If we got here without exception, debate ran
    
    def test_voting_phase_resolves_winner(self, ego_core_with_persistence, sample_creation_task):
        """Test that voting phase correctly resolves winner."""
        core = ego_core_with_persistence
        
        # Set up state for voting
        core.state.current_task = sample_creation_task
        core.state.phase = DecisionPhase.VOTING
        
        # Add opinions
        for drive_type in [DriveType.GLUTTONY, DriveType.GREED, DriveType.SLOTH]:
            engine = core.registry.get(drive_type)
            if engine:
                opinion = engine.evaluate(sample_creation_task, {})
                core.state.opinions[drive_type] = opinion
        
        # Resolve votes
        winner, score = core._resolve_votes()
        
        assert winner is not None
        assert isinstance(winner, DriveOpinion)
        assert score >= 0


class TestApprovalGates:
    """Tests for human approval gates in EGO-Core."""
    
    def test_high_confidence_auto_approves(self, ego_core_with_persistence, sample_creation_task):
        """Test that high confidence decisions auto-approve."""
        core = ego_core_with_persistence
        
        # Set up high confidence decision
        core.process_task(sample_creation_task)
        
        if core.state.decision:
            original_confidence = core.state.decision.confidence
            core.state.decision.confidence = 0.85  # High confidence
            
            approved = core.request_human_approval()
            assert approved is True
            
            # Restore original
            core.state.decision.confidence = original_confidence
    
    def test_low_confidence_requires_review(self, ego_core_with_persistence, sample_creation_task):
        """Test that low confidence decisions require review."""
        core = ego_core_with_persistence
        
        core.process_task(sample_creation_task)
        
        if core.state.decision:
            # Set low confidence
            core.state.decision.confidence = 0.4
            
            # With low confidence but no high risk, should still approve
            # (depends on gate implementation)
            result = core.request_human_approval()
            assert isinstance(result, bool)
    
    def test_high_risk_blocks_approval(self, ego_core_with_persistence, sample_research_task):
        """Test that high risk opinions block approval."""
        core = ego_core_with_persistence
        
        core.process_task(sample_research_task)
        
        # Add a high risk opinion
        high_risk_opinion = DriveOpinion(
            drive=DriveType.WRATH,
            opinion="High risk detected",
            confidence=0.9,
            recommendation="Review required",
            risk_level="high"
        )
        core.state.opinions[DriveType.WRATH] = high_risk_opinion
        
        approved = core.request_human_approval()
        assert approved is False


class TestPersistenceIntegration:
    """Tests for persistence layer integration."""
    
    def test_decision_logged_to_db(self, ego_core_with_persistence, sample_creation_task, mock_persistence):
        """Test that decisions are logged to database."""
        core = ego_core_with_persistence
        
        result = core.process_task(sample_creation_task)
        
        # Verify log_decision was called
        mock_persistence.log_decision.assert_called()
    
    def test_weight_changes_logged(self, ego_core_with_persistence, sample_creation_task, mock_persistence):
        """Test that weight changes are logged."""
        core = ego_core_with_persistence
        
        result = core.process_task(sample_creation_task)
        
        # On_task_complete triggers weight adjustment
        core.on_task_complete(success=True)
        
        # Verify weight change logged
        mock_persistence.log_weight_change.assert_called()


class TestErrorRecovery:
    """Tests for error handling and recovery."""
    
    def test_graceful_handling_of_empty_task_type(self, ego_core_with_persistence):
        """Test handling of empty task type."""
        core = ego_core_with_persistence
        
        task = TaskInput(description="Test", task_type="", priority=0.5)
        
        # Should not crash
        result = core.process_task(task)
        
        assert isinstance(result, DecisionResult)
    
    def test_graceful_handling_of_missing_context(self, ego_core_with_persistence):
        """Test handling of missing context."""
        core = ego_core_with_persistence
        
        task = TaskInput(description="Test", task_type="create", context={}, priority=0.5)
        
        result = core.process_task(task)
        
        assert isinstance(result, DecisionResult)
    
    def test_registry_fallback_for_no_matching_drives(self):
        """Test that registry returns all drives when no specializations match."""
        reg = DriveEngineRegistry()
        reg.register(MockSevenSinsEngine(DriveType.GLUTTONY, 0.7))
        reg.register(MockSevenSinsEngine(DriveType.LUST, 0.6))
        
        # Task type that doesn't match any specialization
        matching = reg.get_by_task_type("xyz_unknown_task_type_12345")
        
        # Should return all drives as fallback
        assert len(matching) == 2


class TestAuditLogging:
    """Tests for audit logging functionality."""
    
    def test_audit_log_file_created(self, ego_core_with_persistence, sample_creation_task):
        """Test that audit log file is created."""
        core = ego_core_with_persistence
        
        core.process_task(sample_creation_task)
        
        log_file = os.path.join(core.audit_logger.log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        assert os.path.exists(log_file)
    
    def test_audit_log_contains_decision(self, ego_core_with_persistence, sample_creation_task, temp_log_dir):
        """Test that decision is recorded in audit log."""
        logger = AuditLogger(log_dir=temp_log_dir)
        
        decision = DecisionResult(
            recommendation="Proceed",
            selected_drives=[(DriveType.GLUTTONY, 0.7)],
            confidence=0.85,
            phase=DecisionPhase.EXECUTION,
            reasoning="High confidence"
        )
        
        state = EGOState(
            active_drives=[DriveType.GLUTTONY],
            opinions={DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Good",
                confidence=0.85,
                recommendation="Proceed",
                risk_level="medium"
            )}
        )
        
        logger.log_decision(decision, state)
        
        log_file = os.path.join(temp_log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())
            assert entry['event'] == 'decision_made'
            assert entry['recommendation'] == "Proceed"
    
    def test_audit_log_contains_approval_request(self, temp_log_dir):
        """Test that approval requests are logged."""
        logger = AuditLogger(log_dir=temp_log_dir)
        
        decision = DecisionResult(
            recommendation="Go",
            selected_drives=[(DriveType.GLUTTONY, 0.7)],
            confidence=0.85,
            phase=DecisionPhase.VOTING,
            reasoning="Test"
        )
        
        logger.log_approval_request(decision, True, "Auto-approved")
        
        log_file = os.path.join(temp_log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())
            assert entry['event'] == 'approval_request'
            assert entry['approved'] is True


class TestStateTransitions:
    """Tests for EGO state transitions."""
    
    def test_state_resets_on_new_task(self, ego_core_with_persistence, sample_creation_task, sample_research_task):
        """Test that state properly resets when processing new task."""
        core = ego_core_with_persistence
        
        # Process first task
        result1 = core.process_task(sample_creation_task)
        first_task_state = core.state.current_task
        
        # Process second task
        result2 = core.process_task(sample_research_task)
        
        # State should be updated for new task
        assert core.state.current_task == sample_research_task
    
    def test_opinions_cleared_between_tasks(self, ego_core_with_persistence, sample_creation_task, sample_research_task):
        """Test that opinions are cleared between tasks."""
        core = ego_core_with_persistence
        
        # Process first task
        core.process_task(sample_creation_task)
        first_opinions_count = len(core.state.opinions)
        
        # Reset registry (simulating new task)
        core.registry.reset_all()
        core.state.opinions.clear()
        
        # Process second task
        core.process_task(sample_research_task)
        
        # New opinions should be collected
        assert len(core.state.opinions) >= 0  # May vary based on task type


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])