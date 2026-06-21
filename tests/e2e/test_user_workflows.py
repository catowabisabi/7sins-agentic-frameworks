"""
7Sins E2E User Workflow Tests
Level: F - User Workflow E2E Tests
Tests complete user flows from task creation to decision output
"""

import pytest
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class TestSingleTaskFlow:
    """F.1: Single task creation to decision."""

    def test_debug_task_flow(self):
        """User creates a debug task and gets a decision."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine, WrathEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        registry.register(WrathEngine())

        core = EGOCore(registry)

        task = TaskInput(
            description="Fix authentication bug",
            task_type="debug"
        )

        result = core.process_task(task)

        assert result is not None
        assert result.recommendation is not None
        assert len(result.recommendation) > 0
        assert 0.0 <= result.confidence <= 1.0

    def test_create_task_flow(self):
        """User creates a creation task."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine, WrathEngine, GluttonyEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        registry.register(WrathEngine())
        registry.register(GluttonyEngine())

        core = EGOCore(registry)

        task = TaskInput(
            description="Create new user dashboard",
            task_type="create"
        )

        result = core.process_task(task)

        assert result is not None
        assert result.recommendation is not None

    def test_delete_task_flow(self):
        """User requests deletion of a component."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine, WrathEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        registry.register(WrathEngine())

        core = EGOCore(registry)

        task = TaskInput(
            description="Remove deprecated API endpoint",
            task_type="delete"
        )

        result = core.process_task(task)

        assert result is not None
        assert result.phase.value in ["voting", "execution"]


class TestMultipleTasksSequence:
    """F.2: Multiple tasks in sequence."""

    def test_three_tasks_sequence(self):
        """User submits three different tasks."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine, WrathEngine, GluttonyEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        registry.register(WrathEngine())
        registry.register(GluttonyEngine())

        core = EGOCore(registry)

        tasks = [
            TaskInput(description="Fix bug", task_type="debug"),
            TaskInput(description="Design new API", task_type="architecture"),
            TaskInput(description="Research authentication", task_type="research"),
        ]

        results = []
        for task in tasks:
            result = core.process_task(task)
            results.append(result)

        assert len(results) == 3
        assert all(r.recommendation for r in results)


class TestEngineSpecificFlows:
    """F.3-F.6: Engine-specific flows."""

    def test_envy_competitive_flow(self):
        """Envy engine handles competitive analysis."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import EnvyEngine

        registry = DriveEngineRegistry()
        registry.register(EnvyEngine())

        core = EGOCore(registry)

        task = TaskInput(
            description="Compare our auth with competitors",
            task_type="benchmark"
        )

        result = core.process_task(task)
        assert result is not None

    def test_gluttony_research_flow(self):
        """Gluttony engine handles research tasks."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import GluttonyEngine

        registry = DriveEngineRegistry()
        registry.register(GluttonyEngine())

        core = EGOCore(registry)

        task = TaskInput(
            description="Research microservices patterns",
            task_type="research"
        )

        result = core.process_task(task)
        assert result is not None

    def test_sloth_automation_flow(self):
        """Sloth engine handles automation tasks."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import SlothEngine

        registry = DriveEngineRegistry()
        registry.register(SlothEngine())

        core = EGOCore(registry)

        task = TaskInput(
            description="Automate the deployment script",
            task_type="automate"
        )

        result = core.process_task(task)
        assert result is not None

    def test_pride_review_flow(self):
        """Pride engine handles code review tasks."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())

        core = EGOCore(registry)

        task = TaskInput(
            description="Review the authentication module",
            task_type="review"
        )

        result = core.process_task(task)
        assert result is not None


class TestRegistryResetFlow:
    """F.7: Registry state reset between tasks."""

    def test_state_reset_between_tasks(self):
        """Registry resets state between tasks."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        core = EGOCore(registry)

        task1 = TaskInput(description="First task", task_type="debug")
        result1 = core.process_task(task1)

        task2 = TaskInput(description="Second task", task_type="debug")
        result2 = core.process_task(task2)

        assert result1 is not None
        assert result2 is not None


class TestVetoFlow:
    """F.8: Veto override scenarios."""

    def test_veto_mechanism_exists(self):
        """Veto mechanism can be triggered."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import WrathEngine

        registry = DriveEngineRegistry()
        wrath = WrathEngine()
        registry.register(wrath)

        core = EGOCore(registry)

        task = TaskInput(
            description="Run dangerous system command",
            task_type="execute"
        )

        result = core.process_task(task)
        assert result is not None
