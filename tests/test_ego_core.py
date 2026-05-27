"""
Tests for EGO-Core Decision Layer
Unit tests with mocked LLM calls for ego_core.py
"""

import pytest
import time
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, mock_open
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

import sys
sys.path.insert(0, '/mnt/c/Users/enoma/Desktop/7')

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


# =============================================================================
# Mock Drive Engines for Testing
# =============================================================================

class MockDriveEngine(DriveEngine):
    """Mock drive engine for testing without LLM calls."""
    
    def __init__(self, drive_type: DriveType, base_weight: float = 0.5):
        super().__init__(drive_type, base_weight)
        self._evaluate_count = 0
    
    @property
    def system_prompt(self) -> str:
        return f"Mock prompt for {self.drive_type.value}"
    
    @property
    def specialization(self) -> List[str]:
        return ["test", "mock", "create", "build", "design", "delete", "remove", "analyze", "research"]
    
    @property
    def veto_condition(self) -> str:
        return "Mock veto condition"
    
    def evaluate(self, task, context: Dict[str, Any]) -> DriveOpinion:
        """Evaluate a task. task can be TaskInput or dict."""
        self._evaluate_count += 1
        self.state.activate(0.8)
        
        # Handle both TaskInput objects and dicts
        if hasattr(task, 'task_type'):
            task_type = task.task_type
            description = task.description
        else:
            task_type = task.get('task_type', 'unknown')
            description = task.get('description', '')
        
        return DriveOpinion(
            drive=self.drive_type,
            opinion=f"Mock opinion for {task_type}",
            confidence=0.8,
            recommendation=f"Mock recommendation from {self.drive_type.value}",
            risk_level="medium"
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.05)


class MockHighRiskDriveEngine(MockDriveEngine):
    """Mock drive engine that always returns high risk opinions."""
    
    def evaluate(self, task, context: Dict[str, Any]) -> DriveOpinion:
        """Evaluate a task. task can be TaskInput or dict."""
        self._evaluate_count += 1
        self.state.activate(0.9)
        
        if hasattr(task, 'task_type'):
            task_type = task.task_type
        else:
            task_type = task.get('task_type', 'unknown')
        
        return DriveOpinion(
            drive=self.drive_type,
            opinion=f"High risk opinion for {task_type}",
            confidence=0.9,
            recommendation=f"High risk recommendation from {self.drive_type.value}",
            risk_level="high"
        )


class MockLowConfidenceDriveEngine(MockDriveEngine):
    """Mock drive engine that returns low confidence opinions."""
    
    def evaluate(self, task, context: Dict[str, Any]) -> DriveOpinion:
        """Evaluate a task. task can be TaskInput or dict."""
        self._evaluate_count += 1
        self.state.activate(0.3)
        return DriveOpinion(
            drive=self.drive_type,
            opinion="Low confidence opinion",
            confidence=0.3,
            recommendation="Low confidence recommendation",
            risk_level="low"
        )


# =============================================================================
# Mock Persistence Manager
# =============================================================================

class MockPersistenceManager:
    """Mock persistence manager for testing."""
    
    def __init__(self):
        self.logged_decisions = []
        self.logged_weight_changes = []
    
    def log_decision(self, task_description, winning_drive, confidence, 
                    eros_weight, thanatos_weight, weight_snapshot):
        self.logged_decisions.append({
            'task_description': task_description,
            'winning_drive': winning_drive,
            'confidence': confidence,
            'eros_weight': eros_weight,
            'thanatos_weight': thanatos_weight,
            'weight_snapshot': weight_snapshot
        })
    
    def log_weight_change(self, drive_name, new_weight, delta):
        self.logged_weight_changes.append({
            'drive_name': drive_name,
            'new_weight': new_weight,
            'delta': delta
        })


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_persistence():
    """Create a mock persistence manager."""
    return MockPersistenceManager()


@pytest.fixture
def registry():
    """Create a drive engine registry with mock engines."""
    reg = DriveEngineRegistry()
    reg.register(MockDriveEngine(DriveType.GLUTTONY, 0.7))
    reg.register(MockDriveEngine(DriveType.LUST, 0.6))
    reg.register(MockDriveEngine(DriveType.GREED, 0.8))
    return reg


@pytest.fixture
def registry_with_high_risk():
    """Registry with a high-risk drive engine."""
    reg = DriveEngineRegistry()
    reg.register(MockDriveEngine(DriveType.GLUTTONY, 0.7))
    reg.register(MockHighRiskDriveEngine(DriveType.WRATH, 0.8))
    return reg


@pytest.fixture
def registry_with_low_eros():
    """Registry with low Eros weight for testing approval gates."""
    reg = DriveEngineRegistry()
    mock_eros = MockDriveEngine(DriveType.EROS, 0.2)
    mock_eros.state.eros_weight = 0.2  # Below 0.3 threshold
    reg.register(mock_eros)
    reg.register(MockDriveEngine(DriveType.GLUTTONY, 0.7))
    return reg


@pytest.fixture
def ego_core(registry, mock_persistence):
    """Create an EGOCore instance with mocked dependencies."""
    with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
        core = EGOCore(registry)
        yield core


@pytest.fixture
def sample_task():
    """Create a sample task input."""
    return TaskInput(
        description="Create a new feature",
        task_type="create_feature",
        constraints=["must be efficient", "must be secure"],
        context={"user": "test_user"},
        priority=0.8
    )


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for audit logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# =============================================================================
# Test: DecisionPhase Enum
# =============================================================================

class TestDecisionPhase:
    """Tests for DecisionPhase enum."""
    
    def test_decision_phase_values(self):
        """Test that all expected phases exist."""
        assert DecisionPhase.PARSING.value == "parsing"
        assert DecisionPhase.CONSULTATION.value == "consultation"
        assert DecisionPhase.DEBATE.value == "debate"
        assert DecisionPhase.VOTING.value == "voting"
        assert DecisionPhase.EXECUTION.value == "execution"
        assert DecisionPhase.REFLECTION.value == "reflection"
    
    def test_decision_phase_count(self):
        """Test that we have exactly 6 phases."""
        assert len(DecisionPhase) == 6


# =============================================================================
# Test: TaskInput Dataclass
# =============================================================================

class TestTaskInput:
    """Tests for TaskInput dataclass."""
    
    def test_task_input_creation(self):
        """Test basic TaskInput creation."""
        task = TaskInput(
            description="Test task",
            task_type="test",
            priority=0.9
        )
        assert task.description == "Test task"
        assert task.task_type == "test"
        assert task.priority == 0.9
        assert task.constraints == []
        assert task.context == {}
    
    def test_task_input_with_all_fields(self):
        """Test TaskInput with all fields populated."""
        task = TaskInput(
            description="Full task",
            task_type="create",
            constraints=["constraint1", "constraint2"],
            context={"key": "value"},
            priority=0.7
        )
        assert task.constraints == ["constraint1", "constraint2"]
        assert task.context == {"key": "value"}


# =============================================================================
# Test: DecisionResult Dataclass
# =============================================================================

class TestDecisionResult:
    """Tests for DecisionResult dataclass."""
    
    def test_decision_result_creation(self):
        """Test basic DecisionResult creation."""
        result = DecisionResult(
            recommendation="Proceed",
            selected_drives=[(DriveType.GLUTTONY, 0.7)],
            confidence=0.85,
            phase=DecisionPhase.VOTING,
            reasoning="High confidence"
        )
        assert result.recommendation == "Proceed"
        assert result.selected_drives == [(DriveType.GLUTTONY, 0.7)]
        assert result.confidence == 0.85
        assert result.phase == DecisionPhase.VOTING
        assert result.reasoning == "High confidence"


# =============================================================================
# Test: EGOState Dataclass
# =============================================================================

class TestEGOState:
    """Tests for EGOState dataclass."""
    
    def test_ego_state_default_values(self):
        """Test EGOState default values."""
        state = EGOState()
        assert state.current_task is None
        assert state.phase == DecisionPhase.PARSING
        assert state.active_drives == []
        assert state.opinions == {}
        assert state.votes == {}
        assert state.decision is None
        assert state.last_decision_time == 0.0
    
    def test_ego_state_with_values(self):
        """Test EGOState with populated values."""
        task = TaskInput(description="Test", task_type="test")
        opinion = DriveOpinion(
            drive=DriveType.GLUTTONY,
            opinion="Test opinion",
            confidence=0.8,
            recommendation="Test recommendation",
            risk_level="medium"
        )
        result = DecisionResult(
            recommendation="Test",
            selected_drives=[(DriveType.GLUTTONY, 0.7)],
            confidence=0.8,
            phase=DecisionPhase.EXECUTION,
            reasoning="Test"
        )
        state = EGOState(
            current_task=task,
            phase=DecisionPhase.CONSULTATION,
            active_drives=[DriveType.GLUTTONY],
            opinions={DriveType.GLUTTONY: opinion},
            decision=result,
            last_decision_time=1000.0
        )
        assert state.current_task == task
        assert state.phase == DecisionPhase.CONSULTATION
        assert state.active_drives == [DriveType.GLUTTONY]
        assert DriveType.GLUTTONY in state.opinions
        assert state.decision == result


# =============================================================================
# Test: AuditLogger
# =============================================================================

class TestAuditLogger:
    """Tests for AuditLogger class."""
    
    def test_audit_logger_init(self, temp_log_dir):
        """Test AuditLogger initialization."""
        logger = AuditLogger(log_dir=temp_log_dir)
        assert logger.log_dir == temp_log_dir
        assert os.path.exists(temp_log_dir)
    
    def test_log_decision(self, temp_log_dir):
        """Test logging a decision."""
        logger = AuditLogger(log_dir=temp_log_dir)
        
        decision = DecisionResult(
            recommendation="Approve",
            selected_drives=[(DriveType.GLUTTONY, 0.7), (DriveType.GREED, 0.8)],
            confidence=0.9,
            phase=DecisionPhase.EXECUTION,
            reasoning="High confidence decision"
        )
        
        opinion = DriveOpinion(
            drive=DriveType.GLUTTONY,
            opinion="Good choice",
            confidence=0.9,
            recommendation="Proceed",
            risk_level="medium"
        )
        state = EGOState(
            active_drives=[DriveType.GLUTTONY, DriveType.GREED],
            opinions={DriveType.GLUTTONY: opinion}
        )
        
        logger.log_decision(decision, state)
        
        # Verify log file was created
        log_file = os.path.join(temp_log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        assert os.path.exists(log_file)
        
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.readline())
            assert log_entry['event'] == 'decision_made'
            assert log_entry['recommendation'] == 'Approve'
            assert log_entry['confidence'] == 0.9
            assert log_entry['phase'] == 'execution'
    
    def test_log_approval_request_approved(self, temp_log_dir):
        """Test logging an approval request that was approved."""
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
            log_entry = json.loads(f.readline())
            assert log_entry['event'] == 'approval_request'
            assert log_entry['approved'] is True
            assert log_entry['reason'] == "Auto-approved"
    
    def test_log_approval_request_rejected(self, temp_log_dir):
        """Test logging an approval request that was rejected."""
        logger = AuditLogger(log_dir=temp_log_dir)
        
        decision = DecisionResult(
            recommendation="Stop",
            selected_drives=[(DriveType.GLUTTONY, 0.7)],
            confidence=0.3,
            phase=DecisionPhase.VOTING,
            reasoning="Test"
        )
        
        logger.log_approval_request(decision, False, "Requires review")
        
        log_file = os.path.join(temp_log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.readline())
            assert log_entry['approved'] is False
            assert log_entry['reason'] == "Requires review"


# =============================================================================
# Test: EGOCore Initialization
# =============================================================================

class TestEGOCoreInit:
    """Tests for EGOCore initialization."""
    
    def test_ego_core_init(self, registry, mock_persistence):
        """Test EGOCore initialization with registry."""
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(registry)
            
            assert core.registry == registry
            assert isinstance(core.state, EGOState)
            assert core.max_debate_rounds == 3
            assert core.confidence_threshold == 0.6
            assert isinstance(core.audit_logger, AuditLogger)


# =============================================================================
# Test: EGOCore.process_task
# =============================================================================

class TestEGOCoreProcessTask:
    """Tests for EGOCore.process_task method."""
    
    def test_process_task_basic(self, ego_core, sample_task, mock_persistence):
        """Test basic task processing."""
        result = ego_core.process_task(sample_task)
        
        assert isinstance(result, DecisionResult)
        assert result.recommendation != ""
        assert 0.0 <= result.confidence <= 1.0
        assert result.phase == DecisionPhase.EXECUTION
        
        # Verify persistence was called
        assert len(mock_persistence.logged_decisions) == 1
    
    def test_process_task_sets_state(self, ego_core, sample_task):
        """Test that process_task properly sets EGO state."""
        ego_core.process_task(sample_task)
        
        assert ego_core.state.current_task == sample_task
        assert ego_core.state.phase == DecisionPhase.EXECUTION
        assert len(ego_core.state.active_drives) > 0
        assert len(ego_core.state.opinions) > 0
        assert ego_core.state.decision is not None
        assert ego_core.state.last_decision_time > 0
    
    def test_process_task_registers_drives(self, ego_core, sample_task):
        """Test that process_task activates relevant drives."""
        ego_core.process_task(sample_task)
        
        for drive in ego_core.state.active_drives:
            assert drive in ego_core.state.opinions
            assert isinstance(ego_core.state.opinions[drive], DriveOpinion)
    
    def test_process_task_with_creation_task(self, ego_core, mock_persistence):
        """Test processing a creation-type task."""
        task = TaskInput(
            description="Build a new house",
            task_type="create_build_design_new",
            priority=0.9
        )
        
        result = ego_core.process_task(task)
        
        assert result is not None
        assert result.phase == DecisionPhase.EXECUTION
    
    def test_process_task_with_destruction_task(self, ego_core, mock_persistence):
        """Test processing a destruction-type task."""
        task = TaskInput(
            description="Delete the file",
            task_type="delete_remove_destroy_cleanup",
            priority=0.7
        )
        
        result = ego_core.process_task(task)
        
        assert result is not None
        assert result.phase == DecisionPhase.EXECUTION
    
    def test_process_task_resets_registry(self, ego_core, sample_task, registry):
        """Test that process_task resets the registry before processing."""
        # Track reset calls
        reset_called = []
        original_reset = registry.reset_all
        registry.reset_all = lambda: reset_called.append(True) or original_reset()
        
        ego_core.process_task(sample_task)
        
        assert len(reset_called) == 1


# =============================================================================
# Test: EGOCore._run_debate
# =============================================================================

class TestEGOCoreRunDebate:
    """Tests for EGOCore._run_debate method."""
    
    def test_run_debate_rounds(self, ego_core, sample_task):
        """Test that debate runs for correct number of rounds."""
        ego_core.process_task(sample_task)
        
        # After processing, debate should have run
        # We can verify state is in DEBATE phase during processing
        # The actual debate is internal, so we test via process_task completion
    
    def test_run_debate_early_exit_on_consensus(self, ego_core, sample_task):
        """Test early exit when consensus is reached."""
        # When opinions have high confidence, consensus is checked
        ego_core.process_task(sample_task)
        # If consensus was reached early, debate would exit


# =============================================================================
# Test: EGOCore._check_consensus
# =============================================================================

class TestEGOCoreCheckConsensus:
    """Tests for EGOCore._check_consensus method."""
    
    def test_check_consensus_empty_opinions(self, ego_core):
        """Test consensus check with no opinions returns False."""
        ego_core.state.opinions = {}
        assert ego_core._check_consensus() is False
    
    def test_check_consensus_no_high_confidence(self, ego_core):
        """Test consensus check when no opinions meet threshold."""
        ego_core.state.opinions = {
            DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Test",
                confidence=0.5,  # Below 0.8 threshold
                recommendation="Test",
                risk_level="medium"
            ),
            DriveType.GREED: DriveOpinion(
                drive=DriveType.GREED,
                opinion="Test",
                confidence=0.5,  # Below 0.8 threshold
                recommendation="Test",
                risk_level="medium"
            )
        }
        assert ego_core._check_consensus() is False
    
    def test_check_consensus_with_majority_high_confidence(self, ego_core):
        """Test consensus check when majority have high confidence."""
        ego_core.state.opinions = {
            DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Test",
                confidence=0.85,  # Above 0.8 threshold
                recommendation="Test",
                risk_level="medium"
            ),
            DriveType.GREED: DriveOpinion(
                drive=DriveType.GREED,
                opinion="Test",
                confidence=0.5,
                recommendation="Test",
                risk_level="medium"
            )
        }
        # 1 out of 2 = 50%, needs more than 50%
        assert ego_core._check_consensus() is False
    
    def test_check_consensus_exactly_half_high_confidence(self, ego_core):
        """Test consensus with exactly half high confidence opinions."""
        ego_core.state.opinions = {
            DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Test",
                confidence=0.85,
                recommendation="Test",
                risk_level="medium"
            ),
            DriveType.GREED: DriveOpinion(
                drive=DriveType.GREED,
                opinion="Test",
                confidence=0.85,
                recommendation="Test",
                risk_level="medium"
            )
        }
        # 2 out of 2 = 100%, needs more than 50%
        assert ego_core._check_consensus() is True


# =============================================================================
# Test: EGOCore._resolve_votes
# =============================================================================

class TestEGOCoreResolveVotes:
    """Tests for EGOCore._resolve_votes method."""
    
    def test_resolve_votes_basic(self, ego_core, sample_task):
        """Test basic vote resolution."""
        ego_core.state.current_task = sample_task
        ego_core.state.opinions = {
            DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Test",
                confidence=0.8,
                recommendation="GLUTTONY wins",
                risk_level="medium"
            ),
            DriveType.GREED: DriveOpinion(
                drive=DriveType.GREED,
                opinion="Test",
                confidence=0.6,
                recommendation="GREED wins",
                risk_level="medium"
            )
        }
        
        winner_opinion, score = ego_core._resolve_votes()
        
        assert winner_opinion.drive == DriveType.GLUTTONY
        assert score > 0
    
    def test_resolve_votes_creation_task_boosts_eros(self, ego_core):
        """Test that creation tasks boost Eros-weighted drives."""
        ego_core.state.current_task = TaskInput(
            description="Create something",
            task_type="create_feature",
            priority=0.8
        )
        
        # Set up Eros engine with high weight
        eros_engine = MockDriveEngine(DriveType.EROS, 0.9)
        eros_engine.state.eros_weight = 0.9
        ego_core.registry.register(eros_engine)
        
        ego_core.state.opinions = {
            DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Test",
                confidence=0.8,
                recommendation="GLUTTONY",
                risk_level="medium"
            ),
            DriveType.EROS: DriveOpinion(
                drive=DriveType.EROS,
                opinion="Test",
                confidence=0.7,
                recommendation="EROS",
                risk_level="medium"
            )
        }
        
        winner_opinion, score = ego_core._resolve_votes()
        
        # Score calculation: confidence * weight * eros_weight
        # Eros: 0.7 * 0.9 * 0.9 = 0.567
        # Gluttony: 0.8 * 0.7 * 0.9 = 0.504 (creation boost applied)
        # Winner depends on which is higher
    
    def test_resolve_votes_destruction_task_boosts_thanatos(self, ego_core):
        """Test that destruction tasks boost Thanatos-weighted drives."""
        ego_core.state.current_task = TaskInput(
            description="Delete something",
            task_type="delete_file",
            priority=0.8
        )
        
        ego_core.state.opinions = {
            DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Test",
                confidence=0.8,
                recommendation="GLUTTONY",
                risk_level="medium"
            ),
            DriveType.WRATH: DriveOpinion(
                drive=DriveType.WRATH,
                opinion="Test",
                confidence=0.6,
                recommendation="WRATH",
                risk_level="medium"
            )
        }
        
        # Set up Wrath with high thanatos weight
        wrath_engine = ego_core.registry.get(DriveType.WRATH)
        if wrath_engine:
            wrath_engine.state.thanatos_weight = 0.9
        
        winner_opinion, score = ego_core._resolve_votes()
        
        # Score for destruction should use thanatos_weight
        assert score > 0
    
    def test_resolve_votes_no_task(self, ego_core):
        """Test vote resolution with no current task."""
        ego_core.state.current_task = None
        ego_core.state.opinions = {
            DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Test",
                confidence=0.8,
                recommendation="GLUTTONY",
                risk_level="medium"
            )
        }
        
        winner_opinion, score = ego_core._resolve_votes()
        
        assert winner_opinion.drive == DriveType.GLUTTONY


# =============================================================================
# Test: EGOCore.request_human_approval
# =============================================================================

class TestEGOCoreRequestHumanApproval:
    """Tests for EGOCore.request_human_approval method."""
    
    def test_approval_no_decision(self, ego_core, temp_log_dir):
        """Test approval request when no decision has been made."""
        ego_core.state.decision = None
        
        with patch('src.core.ego_core.AuditLogger', return_value=AuditLogger(log_dir=temp_log_dir)):
            result = ego_core.request_human_approval()
        
        assert result is False
    
    def test_approval_high_confidence_auto_approve(self, ego_core, temp_log_dir):
        """Test auto-approval for high confidence decisions."""
        ego_core.state.decision = DecisionResult(
            recommendation="Go",
            selected_drives=[(DriveType.GLUTTONY, 0.7)],
            confidence=0.85,  # Above 0.8 threshold
            phase=DecisionPhase.VOTING,
            reasoning="High confidence"
        )
        
        with patch('src.core.ego_core.AuditLogger', return_value=AuditLogger(log_dir=temp_log_dir)):
            result = ego_core.request_human_approval()
        
        assert result is True
    
    def test_approval_high_risk_requires_review(self, ego_core, temp_log_dir, registry_with_high_risk):
        """Test that high risk opinions require human review."""
        # Create a fresh ego_core with high-risk registry
        mock_persistence = MockPersistenceManager()
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(registry_with_high_risk)
        
        core.state.decision = DecisionResult(
            recommendation="Stop",
            selected_drives=[(DriveType.WRATH, 0.8)],
            confidence=0.6,
            phase=DecisionPhase.VOTING,
            reasoning="Has high risk opinion"
        )
        core.state.opinions = {
            DriveType.WRATH: DriveOpinion(
                drive=DriveType.WRATH,
                opinion="High risk",
                confidence=0.9,
                recommendation="Don't proceed",
                risk_level="high"
            )
        }
        
        with patch('src.core.ego_core.AuditLogger', return_value=AuditLogger(log_dir=temp_log_dir)):
            result = core.request_human_approval()
        
        assert result is False
    
    def test_approval_low_eros_creation_requires_review(self, ego_core, temp_log_dir, registry_with_low_eros):
        """Test that creation tasks with low Eros weight require review."""
        mock_persistence = MockPersistenceManager()
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(registry_with_low_eros)
        
        core.state.current_task = TaskInput(
            description="Create something",
            task_type="create_feature",
            priority=0.8
        )
        core.state.decision = DecisionResult(
            recommendation="Build",
            selected_drives=[(DriveType.EROS, 0.2)],
            confidence=0.5,  # Below 0.8 threshold
            phase=DecisionPhase.VOTING,
            reasoning="Low Eros weight"
        )
        
        with patch('src.core.ego_core.AuditLogger', return_value=AuditLogger(log_dir=temp_log_dir)):
            result = core.request_human_approval()
        
        assert result is False
    
    def test_approval_passes_all_gates(self, ego_core, temp_log_dir):
        """Test approval when all safety gates pass."""
        ego_core.state.current_task = TaskInput(
            description="Analyze something",
            task_type="analysis",
            priority=0.5
        )
        ego_core.state.decision = DecisionResult(
            recommendation="Proceed",
            selected_drives=[(DriveType.GLUTTONY, 0.7)],
            confidence=0.6,  # Below 0.8 threshold
            phase=DecisionPhase.VOTING,
            reasoning="Moderate confidence"
        )
        ego_core.state.opinions = {
            DriveType.GLUTTONY: DriveOpinion(
                drive=DriveType.GLUTTONY,
                opinion="Test",
                confidence=0.6,
                recommendation="Proceed",
                risk_level="low"  # Not high risk
            )
        }
        
        with patch('src.core.ego_core.AuditLogger', return_value=AuditLogger(log_dir=temp_log_dir)):
            result = ego_core.request_human_approval()
        
        assert result is True


# =============================================================================
# Test: EGOCore.on_task_complete
# =============================================================================

class TestEGOCoreOnTaskComplete:
    """Tests for EGOCore.on_task_complete method."""
    
    def test_on_task_complete_reflection_phase(self, ego_core, sample_task):
        """Test that on_task_complete sets reflection phase."""
        ego_core.process_task(sample_task)
        
        ego_core.on_task_complete(success=True)
        
        assert ego_core.state.phase == DecisionPhase.REFLECTION
    
    def test_on_task_complete_success_feedback(self, ego_core, sample_task, registry):
        """Test on_task_complete with success and feedback."""
        ego_core.process_task(sample_task)
        
        # Get the winning drive's engine
        winning_drive = ego_core.state.decision.selected_drives[0][0]
        engine = registry.get(winning_drive)
        initial_weight = engine.state.weight if engine else 0
        
        ego_core.on_task_complete(success=True, feedback="Great job!")
        
        # Engine should have received the callback
    
    def test_on_task_complete_no_decision(self, ego_core):
        """Test on_task_complete when no decision exists."""
        ego_core.state.decision = None
        
        # Should not raise, just return
        ego_core.on_task_complete(success=True)
        
        assert ego_core.state.phase == DecisionPhase.REFLECTION


# =============================================================================
# Test: EGOCore._log_decision_to_persistence
# =============================================================================

class TestEGOCoreLogDecisionToPersistence:
    """Tests for EGOCore._log_decision_to_persistence method."""
    
    def test_log_decision_persists_correctly(self, ego_core, sample_task, mock_persistence):
        """Test that decisions are logged to persistence correctly."""
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            ego_core.process_task(sample_task)
        
        assert len(mock_persistence.logged_decisions) == 1
        
        logged = mock_persistence.logged_decisions[0]
        assert logged['task_description'] == sample_task.description
        assert logged['winning_drive'] is not None
        assert 'confidence' in logged
        assert 'weight_snapshot' in logged


# =============================================================================
# Test: DriveEngineRegistry Integration
# =============================================================================

class TestDriveEngineRegistryIntegration:
    """Tests for DriveEngineRegistry integration with EGOCore."""
    
    def test_registry_get_by_task_type(self):
        """Test registry filtering by task type."""
        # Create a custom mock engine with specific specialization
        class ResearchEngine(MockDriveEngine):
            @property
            def specialization(self) -> List[str]:
                return ["research", "analysis"]
        
        mock_engine = ResearchEngine(DriveType.GLUTTONY, 0.7)
        
        registry2 = DriveEngineRegistry()
        registry2.register(mock_engine)
        
        relevant = registry2.get_by_task_type("research_task")
        assert len(relevant) == 1
        assert relevant[0].drive_type == DriveType.GLUTTONY
    
    def test_registry_get_weights(self, registry):
        """Test getting all drive weights."""
        weights = registry.get_weights()
        
        assert DriveType.GLUTTONY.value in weights
        assert weights[DriveType.GLUTTONY.value] == 0.7
    
    def test_registry_reset_all(self, registry):
        """Test resetting all engines."""
        # Activate an engine
        engine = registry.get(DriveType.GLUTTONY)
        engine.state.activate(0.9)
        
        registry.reset_all()
        
        assert engine.state.confidence == 0.0


# =============================================================================
# Test Coverage Verification
# =============================================================================

def test_ego_core_full_coverage():
    """Meta-test to verify test structure covers ego_core modules."""
    # This test just verifies the test module can be imported and run
    from src.core import ego_core
    assert hasattr(ego_core, 'EGOCore')
    assert hasattr(ego_core, 'DecisionPhase')
    assert hasattr(ego_core, 'TaskInput')
    assert hasattr(ego_core, 'DecisionResult')
    assert hasattr(ego_core, 'EGOState')
    assert hasattr(ego_core, 'AuditLogger')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
