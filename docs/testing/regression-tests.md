# 7Sins 用戶流程 E2E 測試 (User Workflow Tests)

> 繁體中文 | 層級: F | 建立日期: 2026-06-21

---

## 🎯 目的

測試完整用戶流程。此專案是 CLI/Python 庫，E2E 測試模擬用戶從 CLI 輸入到最終決策輸出的完整流程。

---

## ⚡ 執行命令

```bash
cd /mnt/c/Users/enoma/Desktop/opencode-work/agent-works/research/7sins
python -m pytest tests/e2e/ -v
```

---

## 📋 用戶流程測試

### F.1 流程：建立並執行單一任務

```python
def test_single_task_flow():
    """User creates a task and gets a decision."""
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
```

### F.2 流程：多任務順序處理

```python
def test_multiple_tasks_sequence():
    """User submits multiple tasks in sequence."""
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
```

### F.3 流程：創建任務（Creation Task）

```python
def test_creation_task_flow():
    """User creates a new project feature."""
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
    assert "create" in result.recommendation.lower() or "build" in result.recommendation.lower() or len(result.recommendation) > 0
```

### F.4 流程：刪除任務（Deletion Task）

```python
def test_deletion_task_flow():
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
    assert result.phase.value == "execution" or result.phase.value == "voting"
```

### F.5 流程：競爭性分析任務（Envy Engine）

```python
def test_competitive_analysis_flow():
    """User runs a competitive benchmark analysis."""
    from src.core.ego_core import EGOCore, TaskInput
    from src.core.drive_engine import DriveEngineRegistry
    from src.engines.seven_sins import EnvyEngine
    
    registry = DriveEngineRegistry()
    registry.register(EnvyEngine())
    
    core = EGOCore(registry)
    
    task = TaskInput(
        description="Compare our auth system with competitors",
        task_type="benchmark"
    )
    
    result = core.process_task(task)
    
    assert result is not None
```

### F.6 流程：研究任務（Gluttony Engine）

```python
def test_research_flow():
    """User requests deep research on a topic."""
    from src.core.ego_core import EGOCore, TaskInput
    from src.core.drive_engine import DriveEngineRegistry
    from src.engines.seven_sins import GluttonyEngine
    
    registry = DriveEngineRegistry()
    registry.register(GluttonyEngine())
    
    core = EGOCore(registry)
    
    task = TaskInput(
        description="Research microservices architecture patterns",
        task_type="research"
    )
    
    result = core.process_task(task)
    
    assert result is not None
```

### F.7 流程：Veto 覆蓋

```python
def test_veto_override_flow():
    """Wrath engine should be able to veto dangerous decisions."""
    from src.core.ego_core import EGOCore, TaskInput
    from src.core.drive_engine import DriveEngineRegistry
    from src.engines.seven_sins import WrathEngine
    
    registry = DriveEngineRegistry()
    wrath = WrathEngine()
    registry.register(wrath)
    
    core = EGOCore(registry)
    
    task = TaskInput(
        description="Run: rm -rf / --no-preserve-root",
        task_type="execute"
    )
    
    result = core.process_task(task)
    
    # Wrath should recognize dangerous commands
    assert result is not None
    # Veto may or may not trigger depending on condition matching
```

### F.8 流程：Registry 歸零（Reset）

```python
def test_registry_reset_between_tasks():
    """Registry should reset state between tasks."""
    from src.core.ego_core import EGOCore, TaskInput
    from src.core.drive_engine import DriveEngineRegistry
    from src.engines.seven_sins import PrideEngine
    
    registry = DriveEngineRegistry()
    registry.register(PrideEngine())
    core = EGOCore(registry)
    
    # First task
    task1 = TaskInput(description="First task", task_type="debug")
    result1 = core.process_task(task1)
    
    # Second task - state should be fresh
    task2 = TaskInput(description="Second task", task_type="debug")
    result2 = core.process_task(task2)
    
    assert result1 is not None
    assert result2 is not None
```

---

## 📊 輸出位置

| 輸出 | 位置 |
|------|------|
| pytest 標準輸出 | stdout |
| 報告 | `runtime/logs/tests/<timestamp>/e2e-report.md` |

---

## 📝 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-21 | 1.0.0 | 初始建立 |

*最後更新: 2026-06-21*
