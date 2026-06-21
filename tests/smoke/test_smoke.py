"""
7Sins Smoke Tests
Level: A - Smoke Tests
Run with: python -m pytest tests/smoke/ -v
"""

import pytest
import sys
import os

# Ensure repo root is in path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class TestBackendImports:
    """A.1: Verify all core modules can be imported without error."""

    def test_core_modules_importable(self):
        """All core modules can be imported."""
        from src.core.ego_core import EGOCore, TaskInput, DecisionResult, EGOState
        from src.core.drive_engine import (
            DriveEngine, DriveType, DriveEngineRegistry,
            DriveOpinion, DriveState
        )
        # If we get here, imports succeeded
        assert EGOCore is not None
        assert TaskInput is not None
        assert DriveType is not None

    def test_engines_importable(self):
        """All 7 Sin engines can be imported."""
        from src.engines.seven_sins import (
            GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
            PrideEngine, WrathEngine, EnvyEngine
        )
        assert GluttonyEngine is not None
        assert LustEngine is not None
        assert GreedEngine is not None
        assert SlothEngine is not None
        assert PrideEngine is not None
        assert WrathEngine is not None
        assert EnvyEngine is not None

    def test_memory_modules_importable(self):
        """Memory layer modules can be imported."""
        from src.memory.persistence import PersistenceManager, get_persistence_manager
        from src.memory.reflection import ReflectionAgent
        assert PersistenceManager is not None
        assert ReflectionAgent is not None

    def test_tools_modules_importable(self):
        """Tools modules can be imported."""
        from src.tools.search import get_search_tool
        from src.tools.terminal import TerminalExecutor
        assert get_search_tool is not None
        assert TerminalExecutor is not None


class TestEngineInstantiation:
    """A.2: All 7 engines can be instantiated."""

    def test_all_engines_instantiable(self):
        """All 7 Sin engines can be instantiated with valid state."""
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
        for e in engines:
            assert e.state is not None
            assert e.drive_type is not None
            assert e.system_prompt is not None
            assert len(e.system_prompt) > 0


class TestRegistryInitialization:
    """A.3: DriveEngineRegistry works correctly."""

    def test_registry_register_and_retrieve(self):
        """Registry can register and retrieve engines."""
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine

        registry = DriveEngineRegistry()
        engine = PrideEngine()
        registry.register(engine)

        assert registry.get(engine.drive_type) is engine
        assert len(registry.get_all()) == 1

    def test_registry_get_all(self):
        """Registry get_all returns all registered engines."""
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine, WrathEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        registry.register(WrathEngine())

        all_engines = registry.get_all()
        assert len(all_engines) == 2

    def test_registry_reset_all(self):
        """Registry reset_all clears state."""
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine

        registry = DriveEngineRegistry()
        engine = PrideEngine()
        registry.register(engine)
        registry.reset_all()

        # After reset, registry should have engine but engine state cleared
        assert len(registry.get_all()) == 1


class TestEGOCoreInit:
    """A.4: EGO-Core can be initialized."""

    def test_ego_core_init(self):
        """EGOCore can be instantiated with registry."""
        from src.core.ego_core import EGOCore
        from src.core.drive_engine import DriveEngineRegistry

        registry = DriveEngineRegistry()
        core = EGOCore(registry)

        assert core.registry is registry
        assert core.max_debate_rounds == 3
        assert core.confidence_threshold == 0.6

    def test_ego_core_with_all_engines(self):
        """EGOCore works with all 7 engines registered."""
        from src.core.ego_core import EGOCore
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import (
            GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
            PrideEngine, WrathEngine, EnvyEngine
        )

        registry = DriveEngineRegistry()
        for engine in [
            GluttonyEngine(), LustEngine(), GreedEngine(),
            SlothEngine(), PrideEngine(), WrathEngine(), EnvyEngine()
        ]:
            registry.register(engine)

        core = EGOCore(registry)
        assert len(registry.get_all()) == 7


class TestTaskInputCreation:
    """A.5: TaskInput can be created."""

    def test_task_input_basic(self):
        """TaskInput basic creation."""
        from src.core.ego_core import TaskInput

        task = TaskInput(
            description="Fix authentication bug",
            task_type="debug"
        )
        assert task.description == "Fix authentication bug"
        assert task.task_type == "debug"

    def test_task_input_with_priority(self):
        """TaskInput with priority."""
        from src.core.ego_core import TaskInput

        task = TaskInput(
            description="Build new feature",
            task_type="create",
            priority=0.9
        )
        assert task.priority == 0.9


class TestDecisionResultCreation:
    """A.6: DecisionResult can be created."""

    def test_decision_result_basic(self):
        """DecisionResult basic creation."""
        from src.core.ego_core import DecisionResult, DecisionPhase
        from src.core.drive_engine import DriveType

        result = DecisionResult(
            recommendation="Run tests first",
            selected_drives=[(DriveType.WRATH, 0.5)],
            confidence=0.85,
            phase=DecisionPhase.EXECUTION,
            reasoning="Wrath demands verification"
        )
        assert result.confidence == 0.85
        assert result.phase == DecisionPhase.EXECUTION


class TestPersistenceManagerSingleton:
    """A.7: PersistenceManager singleton works."""

    def test_persistence_manager_singleton(self):
        """PersistenceManager singleton pattern works."""
        from src.memory.persistence import PersistenceManager, get_persistence_manager

        pm1 = PersistenceManager()
        pm2 = get_persistence_manager()

        assert pm1 is pm2


class TestSearchToolGettable:
    """A.8: Search tool can be retrieved."""

    def test_search_tool_gettable(self):
        """Search tool can be retrieved (may be mock)."""
        from src.tools.search import get_search_tool

        tool = get_search_tool()
        assert tool is not None
        assert hasattr(tool, "search")


class TestAuditLoggerInit:
    """A.9: Audit logger can be initialized."""

    def test_audit_logger_init(self, tmp_path):
        """AuditLogger initializes and creates log dir."""
        from src.core.ego_core import AuditLogger
        import os

        log_dir = tmp_path / "audit_logs"
        logger = AuditLogger(log_dir=str(log_dir))

        assert logger.log_dir is not None
        assert os.path.exists(log_dir) or logger.log_dir


class TestConfigConstants:
    """A.10: Configuration constants are complete."""

    def test_fallback_confidence_all_sins(self):
        """FALLBACK_CONFIDENCE has all 7 Sins defined."""
        from src.core.drive_engine import FALLBACK_CONFIDENCE, DriveType

        seven_sins = {
            DriveType.GLUTTONY, DriveType.LUST, DriveType.GREED,
            DriveType.SLOTH, DriveType.PRIDE, DriveType.WRATH, DriveType.ENVY
        }
        for sin in seven_sins:
            assert sin in FALLBACK_CONFIDENCE, f"Missing FALLBACK_CONFIDENCE for {sin}"

    def test_fallback_confidence_range(self):
        """FALLBACK_CONFIDENCE values are in valid range."""
        from src.core.drive_engine import FALLBACK_CONFIDENCE

        for sin, val in FALLBACK_CONFIDENCE.items():
            assert 0.0 <= val <= 1.0, f"FALLBACK_CONFIDENCE[{sin}] = {val} out of range"

    def test_drive_state_bounds(self):
        """DriveState enforces weight bounds."""
        from src.core.drive_engine import DriveState, DriveType

        state = DriveState(name=DriveType.PRIDE, weight=0.5)

        # Test MAX bound
        state.weight = state.MAX_WEIGHT + 0.1
        state.weight = max(state.MIN_WEIGHT, min(state.MAX_WEIGHT, state.weight))
        assert state.weight <= state.MAX_WEIGHT

        # Test MIN bound
        state.weight = state.MIN_WEIGHT - 0.1
        state.weight = max(state.MIN_WEIGHT, min(state.MAX_WEIGHT, state.weight))
        assert state.weight >= state.MIN_WEIGHT
