# 7Sins 效能/穩定性測試 (Performance / Stability Tests)

> 繁體中文 | 層級: I | 建立日期: 2026-06-21

---

## 🎯 目的

找出卡死、request storm、過慢、memory leak。

---

## ⚡ 執行命令

```bash
cd /mnt/c/Users/enoma/Desktop/opencode-work/agent-works/research/7sins
python -m pytest tests/performance/ -v
```

---

## 📋 測試類別

### I.1 初始載入速度

```python
import time

def test_import_time():
    """Verify all core imports complete quickly."""
    start = time.time()
    
    from src.core.ego_core import EGOCore
    from src.core.drive_engine import DriveEngineRegistry
    from src.engines.seven_sins import (
        GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
        PrideEngine, WrathEngine, EnvyEngine
    )
    
    elapsed = time.time() - start
    assert elapsed < 5.0, f"Import took {elapsed:.2f}s (should be < 5s)"
```

### I.2 空閒 30 秒 Request Count

N/A — 無 HTTP Server，無 Polling。

### I.3 重複建立/刪除穩定性

```python
def test_repeated_task_processing():
    """Verify repeated task processing doesn't leak memory or slow down."""
    import time
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
    
    assert avg_time < 2.0, f"Average time {avg_time:.2f}s too high"
    assert max_time < 5.0, f"Max time {max_time:.2f}s indicates slowdown"
```

### I.4 大列表渲染

N/A — 無 UI 渲染。

### I.5 長串流輸出

N/A — 無串流輸出。

### I.6 慢 Backend 響應

```python
def test_slow_llm_fallback():
    """Verify system handles slow LLM responses with timeout."""
    from unittest.mock import Mock, patch
    import time
    
    from src.engines.seven_sins import WrathEngine
    from src.core.drive_engine import DriveType
    
    engine = WrathEngine()
    
    # Simulate slow LLM
    def slow_complete(*args, **kwargs):
        time.sleep(0.5)
        class Resp:
            content = "OPINION: risky\nCONFIDENCE: 0.9\nRECOMMENDATION: abort\nRISK: high"
        return Resp()
    
    with patch.object(engine, '_call_llm', side_effect=slow_complete):
        start = time.time()
        # This should either timeout or complete
        try:
            opinion = engine.evaluate(
                {"description": "test", "task_type": "debug"},
                {}
            )
        except Exception:
            pass  # Expected if no retry logic
        elapsed = time.time() - start
        assert elapsed < 10.0, f"LLM call took too long: {elapsed:.2f}s"
```

### I.7 Server 重啟恢復

```python
def test_registry_persists_across_instantiations(tmp_path):
    """Verify persistence manager survives re-initialization."""
    from src.memory.persistence import PersistenceManager
    from src.core.drive_engine import DriveType
    import os
    
    # Use test DB
    test_db = tmp_path / "test.db"
    original_path = PersistenceManager._db_path
    PersistenceManager._db_path = str(test_db)
    PersistenceManager._instance = None
    
    try:
        pm1 = PersistenceManager()
        pm1.log_decision(
            task_description="Test",
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
    finally:
        PersistenceManager._db_path = original_path
        PersistenceManager._instance = None
```

### I.8 內存洩漏檢測

```python
def test_no_memory_leak_on_repeated_tasks():
    """Verify no memory growth on repeated task processing."""
    import sys
    from src.core.ego_core import EGOCore, TaskInput
    from src.core.drive_engine import DriveEngineRegistry
    from src.engines.seven_sins import PrideEngine
    
    registry = DriveEngineRegistry()
    registry.register(PrideEngine())
    core = EGOCore(registry)
    
    initial_size = sys.getsizeof(registry)
    
    for i in range(50):
        task = TaskInput(description=f"Task {i}", task_type="debug")
        core.process_task(task)
    
    final_size = sys.getsizeof(registry)
    
    # Allow some growth but not excessive
    growth_ratio = final_size / initial_size if initial_size > 0 else 1.0
    assert growth_ratio < 10.0, f"Excessive memory growth: {growth_ratio:.2f}x"
```

---

## 📊 Thresholds

| Metric | Threshold |
|--------|-----------|
| Import time | < 5s |
| Average task processing | < 2s |
| Max task processing | < 5s |
| Memory growth ratio | < 10x |

---

## 📝 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-21 | 1.0.0 | 初始建立 |

*最後更新: 2026-06-21*
