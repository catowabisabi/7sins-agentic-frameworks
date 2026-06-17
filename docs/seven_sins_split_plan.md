# seven_sins.py 拆分計劃

> **📋 驗收狀態**: `#33` ✅ (drive engine extraction) | `#34` ✅ (retry wrapper) | `#36` ✅ (Eros/Thanatos split) | `#37` ✅ (doc relocation) | `#41` ✅ (7-engine loading-order tests) | **7-engine split ✓**
> 


## 1. 現有架構描述

### 1.1 seven_sins.py 的當前角色

`six_sins.py`（實際位於 `src/engines/seven_sins.py`）目前承擔多重職責：

| 職責類型 | 具體內容 |
|---------|---------|
| **Facade 統一導出** | 重新導出 7 個獨立 engine class（PrideEngine, GreedEngine, LustEngine, EnvyEngine, GluttonyEngine, WrathEngine, SlothEngine）|
| **工具函數庫** | 提供 LLM 調用的輔助函數：`_get_llm_provider()`, `_build_task_prompt()`, `_parse_llm_opinion()`, `_call_llm_with_retry()` |
| **額外 Engine** | 定義 `ErosEngine` 和 `ThanatosEngine` 兩個 class |
| **Mock Provider** | 包含 `_MockLLMProvider` 類用於無 API Key 時的降級處理 |

### 1.2 現有 helper 函數清單

位於 `seven_sins.py` 的工具函數（行 24-229）：

| 函數名 | 功能描述 |
|-------|---------|
| `_is_transient_error(e)` | 判斷異常是否為短暫性錯誤（可重試） |
| `_call_llm_with_retry(provider, prompt, system_prompt, max_retries)` | 帶指數退避重試的 LLM 調用封裝 |
| `_MockLLMProvider` | 當無 API Key 時使用的 Mock LLM Provider |
| `_get_llm_provider()` | 獲取或創建 LLM Provider 單例 |
| `_build_task_prompt(task, context, engine_name, specialization)` | 根據任務和上下文構建 LLM prompt |
| `_parse_llm_opinion(response, drive_type)` | 解析 LLM 回應為 `DriveOpinion` 結構 |

### 1.3 當前依賴關係

**7 個獨立 Engine 文件都從 `seven_sins.py` 導入 helper：**

```
src/engines/pride_engine.py      → from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
src/engines/greed_engine.py      → 同上
src/engines/lust_engine.py       → 同上
src/engines/envy_engine.py       → 同上
src/engines/gluttony_engine.py   → 同上
src/engines/wrath_engine.py      → 同上
src/engines/sloth_engine.py      → 同上
```

**其他來源文件導入 Engine class：**

| 文件 | 導入內容 |
|-----|---------|
| `src/__init__.py` | 導入 9 個 Engine class（7 個 + ErosEngine + ThanatosEngine）|
| `src/cli.py` | 導入 9 個 Engine class |
| `tests/test_seven_sins.py` | 導入 Engine class 及相關函數 |
| `tests/test_multi_engine_veto.py` | 導入 Engine class |

---

## 2. Proposed Split — 重構方案

### 2.1 目標架構

```
src/
├── engines/
│   ├── __init__.py
│   ├── llm_helpers.py      ← 新增：LLM 工具函數模塊
│   ├── llm_provider.py
│   ├── minimax_provider.py
│   ├── pride_engine.py     → 修改：改為 from .llm_helpers import ...
│   ├── greed_engine.py     → 修改：改為 from .llm_helpers import ...
│   ├── lust_engine.py      → 修改：改為 from .llm_helpers import ...
│   ├── envy_engine.py       → 修改：改為 from .llm_helpers import ...
│   ├── gluttony_engine.py   → 修改：改為 from .llm_helpers import ...
│   ├── wrath_engine.py      → 修改：改為 from .llm_helpers import ...
│   ├── sloth_engine.py      → 修改：改為 from .llm_helpers import ...
│   ├── seven_sins.py        → 修改：保留Facade + 向後兼容
│   └── (other files)
└── utils/
    └── (future utility modules)
```

### 2.2 新增模塊：src/engines/llm_helpers.py

建議將以下內容從 `seven_sins.py` 提取到 `llm_helpers.py`：

| 內容 | 類型 | 說明 |
|-----|------|-----|
| `_is_transient_error()` | 函數 | 行 24-64 |
| `_call_llm_with_retry()` | 函數 | 行 67-116 |
| `_MockLLMProvider` | 類 | 行 119-140 |
| `_get_llm_provider()` | 函數 | 行 143-158 |
| `_build_task_prompt()` | 函數 | 行 161-179 |
| `_parse_llm_opinion()` | 函數 | 行 182-229 |
| `MAX_RETRIES`, `INITIAL_BACKOFF`, `MAX_BACKOFF`, `BACKOFF_MULTIPLIER` | 常量 | 行 17-21 |

### 2.3 seven_sins.py 精簡後的職責

| 職責 | 說明 |
|-----|-----|
| **Engine 重新導出** | 保留 `__all__` 導出（9 個 Engine class）|
| **向後兼容** | 提供 `from src.engines.seven_sins import` 的兼容層 |
| **ErosEngine / ThanatosEngine** | 保留這兩個 class（因為它們使用 helpers）|
| **可選：legacy aliases** | 將 helpers 重新導出以保持 `from seven_sins import _get_llm_provider` 依然有效 |

### 2.4 Engine 文件的修改

每個 engine 文件（7 個）需要修改 import：

**修改前：**
```python
from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
```

**修改後：**
```python
from .llm_helpers import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
```

---

## 3. Migration Steps — 遷移步驟

### Phase 1：創建新模塊（不影響現有功能）

1. **創建 `src/engines/llm_helpers.py`**
   - 複製 `_is_transient_error()`, `_call_llm_with_retry()`, `_MockLLMProvider`, `_get_llm_provider()`, `_build_task_prompt()`, `_parse_llm_opinion()`
   - 複製相關常量和 import 語句

2. **驗證新模塊可獨立導入**
   ```bash
   python -c "from src.engines.llm_helpers import _get_llm_provider, _build_task_prompt; print('OK')"
   ```

### Phase 2：更新 Engine 文件（7 個）

按順序修改（任意順序，，互不影響）：

3. **修改 `pride_engine.py`** — 將 `from src.engines.seven_sins import ...` 改為 `from .llm_helpers import ...`
4. **修改 `greed_engine.py`** — 同上
5. **修改 `lust_engine.py`** — 同上
6. **修改 `envy_engine.py`** — 同上
7. **修改 `gluttony_engine.py`** — 同上
8. **修改 `wrath_engine.py`** — 同上
9. **修改 `sloth_engine.py`** — 同上

### Phase 3：精簡 seven_sins.py

10. **更新 `seven_sins.py`**
    - 刪除已搬遷的 helper 函數（原行 17-229）
    - 從 `llm_helpers.py` 重新導出 helpers 保持向後兼容（可選）
    - 保留 ErosEngine 和 ThanatosEngine（它們依賴 helpers）
    - 保留 `__all__` 導出

11. **驗證 seven_sins.py 仍然可正常導入**
    ```bash
    python -c "from src.engines.seven_sins import PrideEngine, ErosEngine, ThanatosEngine; print('OK')"
    ```

### Phase 4：外部調用者適配

12. **驗證 `src/__init__.py` 和 `src/cli.py`**
    - 這兩個文件導入 Engine class，理論上不受影響
    - 確認 `from .engines.seven_sins import (EngineClasses)` 依然有效

13. **驗證測試文件**
    - `tests/test_seven_sins.py`
    - `tests/test_multi_engine_veto.py`
    - 確認 import 依然有效

---

## 4. Backwards Compatibility — 向後兼容性計劃

### 4.1 外部調用者不受影響的策略

| 調用方式 | 現狀 | 重構後 | 影響 |
|---------|------|-------|-----|
| `from src.engines.seven_sins import PrideEngine` | ✅ 有效 | ✅ 依然有效（重新導出）| 無 |
| `from src.engines.seven_sins import _get_llm_provider` | ✅ 有效 | ✅ 依然有效（通過 `llm_helpers` 重新導出）| 無 |
| `from src.engines.seven_sins import ErosEngine` | ✅ 有效 | ✅ 依然有效 | 無 |
| `from src.engines.pride_engine import PrideEngine` | ✅ 有效 | ✅ 依然有效 | 無 |

### 4.2 向後兼容實現方式

在 `seven_sins.py` 中新增向後兼容層：

```python
# seven_sins.py 末尾
from .llm_helpers import (
    _is_transient_error,
    _call_llm_with_retry,
    _MockLLMProvider,
    _get_llm_provider,
    _build_task_prompt,
    _parse_llm_opinion,
)

# 重新導出以保持舊的 import 方式依然有效
__all__ = [
    # Engine classes
    'PrideEngine', 'GreedEngine', 'LustEngine', 'EnvyEngine',
    'GluttonyEngine', 'WrathEngine', 'SlothEngine', 'ErosEngine', 'ThanatosEngine',
    # Legacy helper functions (for backwards compatibility)
    '_get_llm_provider', '_build_task_prompt', '_parse_llm_opinion', '_call_llm_with_retry',
]
```

### 4.3 內部 engine 文件的 import 策略

Engine 文件的 import 推薦兩種方式同時支援：

```python
# pride_engine.py (和其他 engine)
try:
    from .llm_helpers import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
except ImportError:
    # Fallback to seven_sins for backwards compatibility during migration
    from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
```

---

## 5. Risks & Dependencies — 風險與依賴

### 5.1 需要同步修改的檔案清單

| 檔案路徑 | 修改類型 | 修改內容 |
|---------|---------|---------|
| `src/engines/llm_helpers.py` | **新增** | 創建新模塊，複製 helper 函數 |
| `src/engines/pride_engine.py` | 修改 | 更新 import 語句 |
| `src/engines/greed_engine.py` | 修改 | 更新 import 語句 |
| `src/engines/lust_engine.py` | 修改 | 更新 import 語句 |
| `src/engines/envy_engine.py` | 修改 | 更新 import 語句 |
| `src/engines/gluttony_engine.py` | 修改 | 更新 import 語句 |
| `src/engines/wrath_engine.py` | 修改 | 更新 import 語句 |
| `src/engines/sloth_engine.py` | 修改 | 更新 import 語句 |
| `src/engines/seven_sins.py` | 修改 | 刪除 helper 函數 + 新增 re-export |
| `src/__init__.py` | 驗證 | 確認 import 不受影響 |
| `src/cli.py` | 驗證 | 確認 import 不受影響 |
| `tests/test_seven_sins.py` | 驗證 | 確認 import 不受影響 |
| `tests/test_multi_engine_veto.py` | 驗證 | 確認 import 不受影響 |

### 5.2 風險評估

| 風險 | 嚴重程度 | 緩解措施 |
|-----|---------|---------|
| **Import 迴圈依賴** | 高 | `llm_helpers.py` 不應 import 任何 engine 模塊 |
| **測試失敗** | 中 | 在修改前確保現有測試通過；修改後運行完整測試套件 |
| **臨時 ImportError** | 中 | 採用 try/except fallback 機制 |
| **ErosEngine/ThanatosEngine 依賴** | 低 | 這兩個 class 保留在 `seven_sins.py`，需要確保 helpers 可正常導入 |
| **第三方依賴** | 低 | 檢查是否有其他專案依賴 `src.engines.seven_sins` 中的 helper |

### 5.3 依賴關係圖

```
┌─────────────────────────────────────────────────────────────┐
│                    src/__init__.py                          │
│                 (導入 9 個 Engine classes)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   seven_sins.py                              │
│  ┌─────────────────┐    ┌─────────────────────────────────┐│
│  │ ErosEngine      │    │ 向後兼容re-export:               ││
│  │ ThanatosEngine  │    │ _get_llm_provider, etc.         ││
│  └────────┬────────┘    └────────────┬────────────────────┘│
│           │                           │                      │
│           ▼                           ▼                      │
│  ┌────────────────────────────────────────────┐             │
│  │         llm_helpers.py (新增)               │             │
│  │  _is_transient_error()                      │             │
│  │  _call_llm_with_retry()                     │             │
│  │  _MockLLMProvider                           │             │
│  │  _get_llm_provider()                        │             │
│  │  _build_task_prompt()                       │             │
│  │  _parse_llm_opinion()                       │             │
│  └────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
                      ▲
                      │ import helpers
    ┌─────────────────┼─────────────────┬─────────────────┐
    │                 │                 │                 │
    ▼                 ▼                 ▼                 ▼
┌────────┐      ┌────────┐        ┌────────┐        ┌────────┐
│ Pride  │      │ Greed  │        │ Lust   │        │ Envy   │
│Engine  │      │Engine  │        │Engine  │        │Engine  │
└────────┘      └────────┘        └────────┘        └────────┘
    │                 │                 │                 │
    └─────────────────┴────────┬────────┴─────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │ GluttonyEngine  │
                    │ WrathEngine     │
                    │ SlothEngine     │
                    └─────────────────┘
```

### 5.4 遷移後的 import 鏈

**Engine 文件的 import 將從：**
```python
from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
```

**改為：**
```python
from .llm_helpers import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
```

---

## 6. 驗證檢查清單

完成遷移後，確認以下命令都能成功執行：

```bash
# 1. 新模塊可獨立導入
python -c "from src.engines.llm_helpers import _get_llm_provider, _build_task_prompt; print('llm_helpers OK')"

# 2. Engine 文件可正常導入
python -c "from src.engines.pride_engine import PrideEngine; print('PrideEngine OK')"
python -c "from src.engines.sloth_engine import SlothEngine; print('SlothEngine OK')"

# 3. seven_sins.py 向後兼容
python -c "from src.engines.seven_sins import PrideEngine, ErosEngine, ThanatosEngine, _get_llm_provider; print('seven_sins backwards OK')"

# 4. 頂層模組可正常導入
python -c "from src import create_7sins_system; print('src init OK')"

# 5. 測試通過
python -m pytest tests/test_seven_sins.py -v
python -m pytest tests/test_multi_engine_veto.py -v
```

---

## 7. 總結

| 項目 | 內容 |
|-----|-----|
| **新建模塊** | `src/engines/llm_helpers.py` |
| **修改的 engine 檔案** | 7 個（pride, greed, lust, envy, gluttony, wrath, sloth）|
| **修改的 seven_sins.py** | 刪除 helper 函數 + 保留 re-export |
| **向後兼容** | 通過 re-export 保持舊 import 方式有效 |
| **測試驗證** | 需驗證 4 個測試檢查點 |
