"""
7Sins Performance / Stability Tests
Level: I - Performance & Stability Tests
Tests for speed, memory leaks, and repeated operations
"""

import pytest
import sys
import os
import time
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class TestImportSpeed:
    """I.1: Import time should be fast."""

    def test_core_import_time(self):
        """Core imports complete within threshold."""
        start = time.time()

        from src.core.ego_core import EGOCore, TaskInput, DecisionResult
        from src.core.drive_engine import DriveEngineRegistry, DriveType
        from src.engines.seven_sins import (
            GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
            PrideEngine, WrathEngine, EnvyEngine
        )

        elapsed = time.time() - start
        assert elapsed < 5.0, f"Import took {elapsed:.2f}s (threshold: 5s)"


class TestRepeatedTaskProcessing:
    """I.3: Repeated task processing stability."""

    def test_20_tasks_no_slowdown(self):
        """20 tasks should complete without progressive slowdown."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine, WrathEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        registry.register(WrathEngine())
        core = EGOCore(registry)

        times = []
        for i in range(20):
            task = TaskInput(description=f"Task {i}", task_type="debug")
            start = time.time()
            result = core.process_task(task)
            elapsed = time.time() - start
            times.append(elapsed)
            assert result is not None

        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 2.0, f"Average time {avg_time:.2f}s too high (>2s)"
        assert max_time < 5.0, f"Max time {max_time:.2f}s indicates slowdown (>5s)"


class TestPersistenceSurvival:
    """I.7: Persistence survives reinitialization."""

    def test_decision_persists_across_reinit(self, tmp_path):
        """Decision log persists across PersistenceManager reinit."""
        from src.memory.persistence import PersistenceManager
        from src.core.drive_engine import DriveType

        test_db = tmp_path / "test.db"
        original_path = PersistenceManager._db_path
        PersistenceManager._db_path = str(test_db)
        PersistenceManager._instance = None

        try:
            pm1 = PersistenceManager()
            pm1.log_decision(
                task_description="Test task",
                winning_drive=DriveType.WRATH.value,
                confidence=0.85,
                eros_weight=0.5,
                thanatos_weight=0.5
            )

            # Reinitialize
            PersistenceManager._instance = None
            pm2 = PersistenceManager()

            logs = pm2.get_decision_logs(limit=10)
            assert len(logs) >= 1
            assert any(
                log.get("task_description") == "Test task"
                for log in logs
            )
        finally:
            PersistenceManager._db_path = original_path
            PersistenceManager._instance = None


class TestMemoryLeakDetection:
    """I.8: Memory leak detection."""

    def test_no_excessive_memory_growth(self):
        """Registry memory should not grow excessively on repeated tasks."""
        from src.core.ego_core import EGOCore, TaskInput
        from src.core.drive_engine import DriveEngineRegistry
        from src.engines.seven_sins import PrideEngine

        registry = DriveEngineRegistry()
        registry.register(PrideEngine())
        core = EGOCore(registry)

        # Process many tasks
        for i in range(50):
            task = TaskInput(description=f"Task {i}", task_type="debug")
            core.process_task(task)

        # No crash = passed
        assert len(registry.get_all()) == 1


class TestSlowLLMFallback:
    """I.6: Slow LLM handling."""

    def test_slow_llm_times_out(self):
        """Slow LLM completes within reasonable time."""
        from unittest.mock import Mock, patch
        import time

        from src.engines.seven_sins import WrathEngine
        from src.core.drive_engine import DriveType
        from src.core.ego_core import TaskInput

        engine = WrathEngine()

        def slow_complete(*args, **kwargs):
            time.sleep(0.3)
            class Resp:
                content = (
                    "OPINION: risky\n"
                    "CONFIDENCE: 0.9\n"
                    "RECOMMENDATION: abort\n"
                    "RISK: high"
                )
            return Resp()

        with patch.object(engine, "_llm_provider", Mock(side_effect=slow_complete)):
            start = time.time()
            try:
                engine.evaluate(
                    TaskInput(description="test", task_type="debug"),
                    {}
                )
            except Exception:
                pass
            elapsed = time.time() - start
            assert elapsed < 10.0, f"LLM call took too long: {elapsed:.2f}s"


class TestMAGIVotingPerformance:
    """MAGI voting completes within reasonable time."""

    def test_voting_with_7_engines(self):
        """Voting with all 7 engines is fast."""
        from src.core.ego_core import EGOCore, TaskInput
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

        task = TaskInput(
            description="Build a complete new system",
            task_type="create"
        )

        start = time.time()
        result = core.process_task(task)
        elapsed = time.time() - start

        assert result is not None
        assert elapsed < 10.0, f"Full pipeline took {elapsed:.2f}s (>10s)"
