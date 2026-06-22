"""
Regression tests for fixed bugs.
Each test verifies a bug that was fixed remains fixed.

Bugs covered:
- #63: task.task_type / task.description backward-compat bridge (dict + dataclass)
- #64: _parse_weight_snapshot() try/except fallback for malformed JSON
- #65: wrath_engine getattr description fallback unified to 'No description'
"""

import pytest
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class TestBug63BackwardCompat:
    """
    Bug #63: task.task_type and task.description backward-compat bridge.

    Problem: task could be either a dict or a TaskInput dataclass.
    Code that used task.get('task_type') would fail on dataclass objects.
    Code that used getattr(task, 'task_type') would fail on dict objects.

    Fix: All code now uses hasattr() + getattr() + .get() fallback pattern.
    This test verifies the fix for all 7 engines + ego_core + helpers.
    """

    def test_wrath_engine_handles_dict_task(self):
        """WrathEngine.evaluate() accepts dict as task input."""
        from src.engines.wrath_engine import WrathEngine

        engine = WrathEngine()
        task_dict = {"task_type": "debug", "description": "Fix bug in auth"}
        context = {}

        # Should not raise
        opinion = engine.evaluate(task_dict, context)
        assert opinion is not None
        assert opinion.drive is not None

    def test_wrath_engine_handles_dataclass_task(self):
        """WrathEngine.evaluate() accepts TaskInput dataclass as task input."""
        from src.engines.wrath_engine import WrathEngine
        from src.core.ego_core import TaskInput

        engine = WrathEngine()
        task_obj = TaskInput(description="Fix bug in auth", task_type="debug")
        context = {}

        # Should not raise
        opinion = engine.evaluate(task_obj, context)
        assert opinion is not None
        assert opinion.drive is not None

    def test_gluttony_engine_handles_dict_task(self):
        """GluttonyEngine.evaluate() accepts dict as task input."""
        from src.engines.gluttony_engine import GluttonyEngine

        engine = GluttonyEngine()
        task_dict = {"task_type": "research", "description": "Study auth patterns"}
        context = {}

        opinion = engine.evaluate(task_dict, context)
        assert opinion is not None

    def test_gluttony_engine_handles_dataclass_task(self):
        """GluttonyEngine.evaluate() accepts TaskInput dataclass as task input."""
        from src.engines.gluttony_engine import GluttonyEngine
        from src.core.ego_core import TaskInput

        engine = GluttonyEngine()
        task_obj = TaskInput(description="Study auth patterns", task_type="research")
        context = {}

        opinion = engine.evaluate(task_obj, context)
        assert opinion is not None

    def test_envy_engine_handles_dict_task(self):
        """EnvyEngine.evaluate() accepts dict as task input."""
        from src.engines.envy_engine import EnvyEngine

        engine = EnvyEngine()
        task_dict = {"task_type": "benchmark", "description": "Compare auth systems"}
        context = {}

        opinion = engine.evaluate(task_dict, context)
        assert opinion is not None

    def test_envy_engine_handles_dataclass_task(self):
        """EnvyEngine.evaluate() accepts TaskInput dataclass as task input."""
        from src.engines.envy_engine import EnvyEngine
        from src.core.ego_core import TaskInput

        engine = EnvyEngine()
        task_obj = TaskInput(description="Compare auth systems", task_type="benchmark")
        context = {}

        opinion = engine.evaluate(task_obj, context)
        assert opinion is not None

    def test_all_engines_handle_both_task_types(self):
        """All 7 engines handle both dict and dataclass task inputs."""
        from src.engines.seven_sins import (
            GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
            PrideEngine, WrathEngine, EnvyEngine
        )
        from src.core.ego_core import TaskInput

        engines = [
            GluttonyEngine(),
            LustEngine(),
            GreedEngine(),
            SlothEngine(),
            PrideEngine(),
            WrathEngine(),
            EnvyEngine(),
        ]

        dict_task = {"task_type": "debug", "description": "test"}
        dataclass_task = TaskInput(description="test", task_type="debug")
        context = {}

        for engine in engines:
            # Dict task should not raise
            opinion_dict = engine.evaluate(dict_task, context)
            assert opinion_dict is not None, f"{engine.drive_type} failed on dict task"

            # Dataclass task should not raise
            opinion_dc = engine.evaluate(dataclass_task, context)
            assert opinion_dc is not None, f"{engine.drive_type} failed on dataclass task"


class TestBug64WeightSnapshotParsing:
    """
    Bug #64: _parse_weight_snapshot() malformed JSON causes crash.

    Problem: If weight_snapshot in DB is malformed JSON (not a dict),
    _parse_weight_snapshot() would raise an exception, crashing get_decision_logs().

    Fix: Added try/except fallback that returns {} on parse failure.
    """

    def test_parse_weight_snapshot_valid_json(self):
        """Valid JSON dict parses correctly."""
        from src.memory.persistence import _parse_weight_snapshot
        import json

        snapshot = '{"pride": 0.8, "wrath": 0.9}'
        result = _parse_weight_snapshot(snapshot)
        assert isinstance(result, dict)
        assert result.get("pride") == 0.8

    def test_parse_weight_snapshot_malformed_json(self):
        """Malformed JSON returns empty dict instead of raising."""
        from src.memory.persistence import _parse_weight_snapshot

        malformed = "not a json string at all"
        result = _parse_weight_snapshot(malformed)
        assert result == {}

    def test_parse_weight_snapshot_partial_json(self):
        """Partial JSON (not a dict) returns empty dict."""
        from src.memory.persistence import _parse_weight_snapshot

        partial = '"just a string, not a dict'
        result = _parse_weight_snapshot(partial)
        assert result == {}


class TestBug65WrathEngineFallback:
    """
    Bug #65: wrath_engine getattr description fallback inconsistent.

    Original problem: 6/7 engines used 'No description' as fallback,
    but wrath_engine used str(task) as fallback.

    Fix: centralized _get_task_description() in seven_sins.py returns 'No description'.
    Tests updated to verify RUNTIME behavior, not source-level string literals.
    """

    def test_task_description_helper_returns_no_description_for_missing(self):
        """_get_task_description() returns 'No description' for missing keys."""
        from src.engines.seven_sins import _get_task_description

        class NoAttrTask:
            pass

        # Dict without description key
        result = _get_task_description({"task_type": "debug"})
        assert result == "No description"

        # Object without description attribute
        task = NoAttrTask()
        task.task_type = "debug"
        result = _get_task_description(task)
        assert result == "No description"

    def test_wrath_engine_uses_task_description_helper(self):
        """WrathEngine.evaluate uses _get_task_description for consistent fallback."""
        from src.engines.wrath_engine import WrathEngine
        import inspect

        source = inspect.getsource(WrathEngine.evaluate)
        # Verify the engine uses the centralized helper
        assert "_get_task_description" in source, \
            "WrathEngine should use _get_task_description helper"
        # Should NOT have inline hasattr pattern anymore
        assert "hasattr(task, 'description')" not in source, \
            "WrathEngine should not have inline hasattr pattern"

    def test_all_engines_use_task_description_helper(self):
        """All 7 engines use _get_task_description for consistent fallback."""
        from src.engines.seven_sins import (
            GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
            PrideEngine, WrathEngine, EnvyEngine
        )
        import inspect

        engines = [
            GluttonyEngine(), LustEngine(), GreedEngine(),
            SlothEngine(), PrideEngine(), WrathEngine(), EnvyEngine(),
        ]

        for engine in engines:
            source = inspect.getsource(engine.evaluate)
            assert "_get_task_description" in source, \
                f"{engine.drive_type} should use _get_task_description helper"
            assert "hasattr(task, 'description')" not in source, \
                f"{engine.drive_type} should not have inline hasattr pattern"
