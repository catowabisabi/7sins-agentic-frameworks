"""
Tests for EGO-Core Veto Logic
Unit tests for veto mechanism in ego_core.py
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
# Mock Drive Engines for Veto Testing
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


class MockVetoEngine(MockDriveEngine):
    """Mock drive engine with configurable veto power."""
    
    def __init__(self, drive_type: DriveType, base_weight: float = 0.5, veto_power: float = 0.0):
        super().__init__(drive_type, base_weight)
        self._veto_power = veto_power
    
    def get_veto_power(self) -> float:
        """Return configurable veto power."""
        return self._veto_power


class MockVetoEngineWithOpinion(MockVetoEngine):
    """Mock veto engine that returns a specific recommendation when veto fires."""
    
    def __init__(self, drive_type: DriveType, base_weight: float = 0.5, veto_power: float = 0.0,
                 veto_recommendation: str = "VETO RECOMMENDATION"):
        super().__init__(drive_type, base_weight, veto_power)
        self._veto_recommendation = veto_recommendation
    
    def evaluate(self, task, context: Dict[str, Any]) -> DriveOpinion:
        """Evaluate a task and store the opinion for veto retrieval."""
        self._evaluate_count += 1
        self.state.activate(0.8)
        
        if hasattr(task, 'task_type'):
            task_type = task.task_type
        else:
            task_type = task.get('task_type', 'unknown')
        
        opinion = DriveOpinion(
            drive=self.drive_type,
            opinion=f"Veto opinion for {task_type}",
            confidence=0.8,
            recommendation=self._veto_recommendation,
            risk_level="medium"
        )
        self.add_opinion(opinion)
        return opinion


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
# Test: Single Veto Trigger
# =============================================================================

class TestSingleVetoTrigger:
    """Tests for single veto trigger scenario."""
    
    def test_single_veto_trigger(self, mock_persistence, sample_task, temp_log_dir):
        """Test that when one engine has veto_power >= 1.0, veto_used=True and that engine's recommendation is used."""
        # Create registry with one veto engine and one normal engine
        reg = DriveEngineRegistry()
        normal_engine = MockDriveEngine(DriveType.GLUTTONY, 0.7)
        veto_engine = MockVetoEngineWithOpinion(DriveType.WRATH, 0.6, veto_power=1.0,
                                                veto_recommendation="VETO OVERRIDE RECOMMENDATION")
        
        reg.register(normal_engine)
        reg.register(veto_engine)
        
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(reg)
        
        result = core.process_task(sample_task)
        
        # Verify veto was used
        assert result.recommendation == "VETO OVERRIDE RECOMMENDATION"
        assert "(veto override)" in result.reasoning
        assert veto_engine.state.veto_used is True
        assert normal_engine.state.veto_used is False


# =============================================================================
# Test: Multiple Veto Triggers (Last-Engine-Wins)
# =============================================================================

class TestMultipleVetoTriggers:
    """Tests for multiple veto triggers scenario (last-engine-wins behavior)."""
    
    def test_multiple_veto_triggers(self, mock_persistence, sample_task, temp_log_dir):
        """Test that when multiple engines have veto_power >= 1.0, last engine's recommendation wins."""
        # Create registry with two veto engines
        reg = DriveEngineRegistry()
        veto_engine_1 = MockVetoEngineWithOpinion(DriveType.GLUTTONY, 0.7, veto_power=1.0,
                                                  veto_recommendation="FIRST VETO")
        veto_engine_2 = MockVetoEngineWithOpinion(DriveType.WRATH, 0.6, veto_power=1.0,
                                                  veto_recommendation="SECOND VETO")
        
        reg.register(veto_engine_1)
        reg.register(veto_engine_2)
        
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(reg)
        
        result = core.process_task(sample_task)
        
        # Last engine (WRATH) should win due to last-engine-wins behavior
        assert result.recommendation == "SECOND VETO"
        assert "(veto override)" in result.reasoning
        # Both engines should have veto_used = True
        assert veto_engine_1.state.veto_used is True
        assert veto_engine_2.state.veto_used is True


# =============================================================================
# Test: No Veto Trigger
# =============================================================================

class TestNoVetoTrigger:
    """Tests for scenario with no veto triggers."""
    
    def test_no_veto_trigger(self, mock_persistence, sample_task, temp_log_dir):
        """Test that when no engine has veto, normal voting winner is used."""
        # Create registry with engines that have no veto power
        reg = DriveEngineRegistry()
        engine1 = MockVetoEngineWithOpinion(DriveType.GLUTTONY, 0.7, veto_power=0.5,
                                            veto_recommendation="GLUTTONY REC")
        engine2 = MockVetoEngineWithOpinion(DriveType.LUST, 0.6, veto_power=0.3,
                                            veto_recommendation="LUST REC")
        
        reg.register(engine1)
        reg.register(engine2)
        
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(reg)
        
        result = core.process_task(sample_task)
        
        # Should use normal voting winner (not veto)
        assert "(veto override)" not in result.reasoning
        # Neither engine should have veto_used = True
        assert engine1.state.veto_used is False
        assert engine2.state.veto_used is False


# =============================================================================
# Test: Veto Used Flag Set Correctly
# =============================================================================

class TestVetoUsedFlagSetCorrectly:
    """Tests for verifying veto_used flag is set correctly."""
    
    def test_veto_used_flag_set_correctly(self, mock_persistence, sample_task, temp_log_dir):
        """Test that only engines with veto power >= 1.0 have veto_used=True."""
        # Create registry with mixed engines
        reg = DriveEngineRegistry()
        no_veto_engine = MockVetoEngineWithOpinion(DriveType.GLUTTONY, 0.7, veto_power=0.0,
                                                   veto_recommendation="NO VETO")
        low_veto_engine = MockVetoEngineWithOpinion(DriveType.LUST, 0.6, veto_power=0.8,
                                                    veto_recommendation="LOW VETO")
        full_veto_engine = MockVetoEngineWithOpinion(DriveType.WRATH, 0.5, veto_power=1.0,
                                                     veto_recommendation="FULL VETO")
        
        reg.register(no_veto_engine)
        reg.register(low_veto_engine)
        reg.register(full_veto_engine)
        
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(reg)
        
        result = core.process_task(sample_task)
        
        # Only full veto engine should have veto_used = True
        assert no_veto_engine.state.veto_used is False
        assert low_veto_engine.state.veto_used is False
        assert full_veto_engine.state.veto_used is True
        
        # Result should use the full veto engine's recommendation
        assert result.recommendation == "FULL VETO"


# =============================================================================
# Test: Veto Threshold Boundary
# =============================================================================

class TestVetoThresholdBoundary:
    """Tests for veto threshold boundary conditions."""
    
    def test_veto_at_exactly_1_0(self, mock_persistence, sample_task, temp_log_dir):
        """Test that veto triggers at exactly 1.0."""
        reg = DriveEngineRegistry()
        engine = MockVetoEngineWithOpinion(DriveType.GLUTTONY, 0.7, veto_power=1.0,
                                            veto_recommendation="EXACTLY ONE")
        
        reg.register(engine)
        
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(reg)
        
        result = core.process_task(sample_task)
        
        assert engine.state.veto_used is True
        assert result.recommendation == "EXACTLY ONE"
    
    def test_veto_just_below_1_0(self, mock_persistence, sample_task, temp_log_dir):
        """Test that veto does NOT trigger at 0.99."""
        reg = DriveEngineRegistry()
        engine = MockVetoEngineWithOpinion(DriveType.GLUTTONY, 0.7, veto_power=0.99,
                                            veto_recommendation="JUST BELOW")
        
        reg.register(engine)
        
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(reg)
        
        result = core.process_task(sample_task)
        
        assert engine.state.veto_used is False
        assert "(veto override)" not in result.reasoning


# =============================================================================
# Test: Veto With High Confidence Normal Winner
# =============================================================================

class TestVetoWithHighConfidence:
    """Tests for veto behavior when normal winner has high confidence."""
    
    def test_veto_overrides_high_confidence_winner(self, mock_persistence, sample_task, temp_log_dir):
        """Test that veto still overrides even when normal voting winner has high confidence."""
        reg = DriveEngineRegistry()
        high_conf_engine = MockVetoEngineWithOpinion(DriveType.GLUTTONY, 0.9, veto_power=0.0,
                                                     veto_recommendation="HIGH CONF WINNER")
        veto_engine = MockVetoEngineWithOpinion(DriveType.WRATH, 0.3, veto_power=1.0,
                                                veto_recommendation="VETO OVERRIDE")
        
        reg.register(high_conf_engine)
        reg.register(veto_engine)
        
        with patch('src.core.ego_core.get_persistence_manager', return_value=mock_persistence):
            core = EGOCore(reg)
        
        result = core.process_task(sample_task)
        
        # Veto should override even though GLUTTONY might win normal voting
        assert result.recommendation == "VETO OVERRIDE"
        assert veto_engine.state.veto_used is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
