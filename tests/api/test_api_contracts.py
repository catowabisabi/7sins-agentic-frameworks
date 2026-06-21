"""
7Sins API Contract Tests
Level: C - API Contract Tests
Tests Python module-level API contracts (dataclasses, enums, function signatures)
"""

import pytest
import sys
import os
import inspect

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class TestDriveTypeEnum:
    """C.1: DriveType enum contract."""

    def test_all_expected_values_exist(self):
        """All expected DriveType values must exist."""
        from src.core.drive_engine import DriveType

        expected = {
            "GLUTTONY", "LUST", "GREED", "SLOTH",
            "PRIDE", "WRATH", "ENVY", "EROS", "THANATOS"
        }
        actual = {e.name for e in DriveType}
        assert expected == actual, f"Missing: {expected - actual}"

    def test_seven_sins_count(self):
        """Exactly 7 main Sins."""
        from src.core.drive_engine import DriveType

        seven = {
            DriveType.GLUTTONY, DriveType.LUST, DriveType.GREED,
            DriveType.SLOTH, DriveType.PRIDE, DriveType.WRATH, DriveType.ENVY
        }
        assert len(seven) == 7

    def test_drive_type_has_value(self):
        """Each DriveType has a string value."""
        from src.core.drive_engine import DriveType

        for dt in DriveType:
            assert hasattr(dt, "value")
            assert isinstance(dt.value, str)
            assert len(dt.value) > 0


class TestDecisionPhaseEnum:
    """C.2: DecisionPhase enum contract."""

    def test_all_phases_defined(self):
        """All decision phases must be defined."""
        from src.core.ego_core import DecisionPhase

        expected_phases = {
            "PARSING", "CONSULTATION", "DEBATE",
            "VOTING", "EXECUTION", "REFLECTION"
        }
        actual = {p.name for p in DecisionPhase}
        assert expected_phases == actual

    def test_phase_count(self):
        """Must have exactly 6 phases."""
        from src.core.ego_core import DecisionPhase
        assert len(DecisionPhase) == 6

    def test_phase_values_are_strings(self):
        """Each phase has a string value."""
        from src.core.ego_core import DecisionPhase

        for phase in DecisionPhase:
            assert hasattr(phase, "value")
            assert isinstance(phase.value, str)


class TestTaskInputContract:
    """C.3: TaskInput dataclass contract."""

    def test_required_fields_present(self):
        """TaskInput has description and task_type fields."""
        from src.core.ego_core import TaskInput

        sig = inspect.signature(TaskInput)
        params = list(sig.parameters.keys())

        assert "description" in params
        assert "task_type" in params

    def test_default_values(self):
        """TaskInput default values are correct."""
        from src.core.ego_core import TaskInput

        task = TaskInput(description="test", task_type="debug")
        assert task.constraints == []
        assert task.context == {}
        assert task.priority == 0.5

    def test_all_fields_writable(self):
        """TaskInput fields are writable."""
        from src.core.ego_core import TaskInput

        task = TaskInput(
            description="test",
            task_type="debug",
            constraints=["no-force-push"],
            context={"key": "value"},
            priority=0.9
        )
        assert task.constraints == ["no-force-push"]
        assert task.context == {"key": "value"}
        assert task.priority == 0.9


class TestDecisionResultContract:
    """C.4: DecisionResult dataclass contract."""

    def test_all_required_fields_present(self):
        """DecisionResult has all required fields."""
        from src.core.ego_core import DecisionResult

        sig = inspect.signature(DecisionResult)
        params = list(sig.parameters.keys())

        required = ["recommendation", "selected_drives", "confidence", "phase", "reasoning"]
        for field in required:
            assert field in params, f"Missing field: {field}"

    def test_field_types(self):
        """DecisionResult field types are correct."""
        from src.core.ego_core import DecisionResult, DecisionPhase
        from src.core.drive_engine import DriveType

        result = DecisionResult(
            recommendation="Run tests",
            selected_drives=[(DriveType.WRATH, 0.5)],
            confidence=0.85,
            phase=DecisionPhase.EXECUTION,
            reasoning="Wrath wins"
        )

        assert isinstance(result.recommendation, str)
        assert isinstance(result.selected_drives, list)
        assert isinstance(result.confidence, float)
        assert isinstance(result.phase, DecisionPhase)
        assert isinstance(result.reasoning, str)


class TestDriveOpinionContract:
    """C.5: DriveOpinion dataclass contract."""

    def test_required_fields_present(self):
        """DriveOpinion has all required fields."""
        from src.core.drive_engine import DriveOpinion, DriveType

        sig = inspect.signature(DriveOpinion)
        params = list(sig.parameters.keys())

        required = ["drive", "opinion", "confidence", "recommendation", "risk_level"]
        for field in required:
            assert field in params, f"Missing field: {field}"

    def test_risk_level_values(self):
        """risk_level must be low/medium/high."""
        from src.core.drive_engine import DriveOpinion, DriveType

        for risk in ["low", "medium", "high"]:
            opinion = DriveOpinion(
                drive=DriveType.WRATH,
                opinion="test",
                confidence=0.5,
                recommendation="test",
                risk_level=risk
            )
            assert opinion.risk_level == risk


class TestEGOStateContract:
    """C.6: EGOState dataclass contract."""

    def test_default_phase_is_parsing(self):
        """EGOState default phase is PARSING."""
        from src.core.ego_core import EGOState, DecisionPhase

        state = EGOState()
        assert state.phase == DecisionPhase.PARSING

    def test_default_collections_empty(self):
        """EGOState collections default to empty."""
        from src.core.ego_core import EGOState

        state = EGOState()
        assert state.active_drives == []
        assert state.opinions == {}
        assert state.votes == {}

    def test_mutable(self):
        """EGOState allows state changes."""
        from src.core.ego_core import EGOState, DecisionPhase
        from src.core.drive_engine import DriveType, DriveOpinion

        state = EGOState()
        state.phase = DecisionPhase.CONSULTATION
        state.opinions[DriveType.WRATH] = DriveOpinion(
            drive=DriveType.WRATH,
            opinion="risky",
            confidence=0.9,
            recommendation="abort",
            risk_level="high"
        )

        assert state.phase == DecisionPhase.CONSULTATION
        assert DriveType.WRATH in state.opinions


class TestDriveEngineRegistryContract:
    """C.7: DriveEngineRegistry API contract."""

    def test_required_methods_exist(self):
        """Registry has all required methods."""
        from src.core.drive_engine import DriveEngineRegistry

        registry = DriveEngineRegistry()

        required_methods = [
            "register", "get", "get_all",
            "get_by_task_type", "reset_all",
            "get_weights", "normalize_weights",
            "record_decision_outcome"
        ]
        for method in required_methods:
            assert hasattr(registry, method), f"Missing method: {method}"

    def test_register_get_roundtrip(self):
        """Registry register/get round-trip."""
        from src.core.drive_engine import DriveEngineRegistry, DriveType
        from src.engines.seven_sins import PrideEngine

        registry = DriveEngineRegistry()
        engine = PrideEngine()
        registry.register(engine)

        retrieved = registry.get(engine.drive_type)
        assert retrieved is engine
        assert retrieved.drive_type == DriveType.PRIDE

    def test_get_by_task_type_filters(self):
        """get_by_task_type filters engines correctly."""
        from src.core.drive_engine import DriveEngineRegistry, DriveType
        from src.engines.seven_sins import PrideEngine, WrathEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        registry.register(WrathEngine())

        relevant = registry.get_by_task_type("debug")
        assert any(e.drive_type == DriveType.WRATH for e in relevant)


class TestPersistenceManagerContract:
    """C.8: PersistenceManager API contract."""

    def test_required_methods_exist(self):
        """PersistenceManager has required methods."""
        from src.memory.persistence import PersistenceManager

        pm = PersistenceManager()

        required_methods = [
            "log_decision", "log_weight_change",
            "get_decision_logs", "get_weight_history"
        ]
        for method in required_methods:
            assert hasattr(pm, method), f"Missing method: {method}"
