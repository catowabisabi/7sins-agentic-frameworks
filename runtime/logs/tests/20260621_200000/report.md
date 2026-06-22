# 7Sins 測試報告
**生成時間**: 2026-06-21 20:00
**測試範圍**: 全層級測試執行 (Level A-I)
**測試環境**: Python 3.11, SQLite (隔離臨時數據庫)
**Commit**: 0c961d1

---

## 執行摘要

|| 層級 | 測試組 | 通過 | 失敗 | 跳過 | 總計 |
||------|--------|------|------|------|------|
|| A | 煙霧測試 | 19 | 0 | 0 | 19 |
|| B | 後端單元測試 | 43 | 31 | 0 | 74 |
|| C | API 契約測試 | 19 | 1 | 0 | 20 |
|| F | 用戶流程 E2E 測試 | 0 | 9 | 0 | 9 |
|| G | Provider 測試 | 2 | 8 | 1 | 11 |
|| I | 效能/穩定性測試 | 1 | 5 | 0 | 6 |
|| **總計** | | **83** | **54** | **1** | **138** |

---

## Level A — 煙霧測試 ✅ 19/19 通過

所有核心模組可正常導入，7 個引擎均可實例化，Registry 運作正常。

---

## Level B — 後端單元測試 ⚠️ 43/74 通過，31 失敗

### 失敗根本原因：dict vs TaskInput dataclass 混用

**症狀**：`AttributeError: 'dict' object has no attribute 'task_type'`

**原因分析**：
引擎 `evaluate()` 方法已更新為使用 `task.task_type`（屬性訪問），但多個現有測試仍傳入 dict：

```python
# 測試中仍使用 dict（錯誤）：
task = {"description": "Research AI safety", "task_type": "research"}
opinion = gluttony_engine.evaluate(task, context)

# 引擎現在期望（正確方式）：
task = TaskInput(description="Research AI safety", task_type="research")
opinion = gluttony_engine.evaluate(task, context)
```

**受影響檔案（共 31 個測試失敗）**：
- `tests/test_seven_sins.py` — 多個引擎測試使用 dict
- `tests/test_envy_gluttony_helpers.py` — helpers 函數期望 dict 但接收 TaskInput
- `tests/test_multi_engine_veto.py` — 測試傳入 dict

**同時存在的問題**：`envy_gluttony_helpers.py` 第 32、53 行仍使用 `task.get("description", "")`：
```python
competitor_results = search_tool.search(task.get("description", ""), count=10)
```
當傳入 TaskInput dataclass 時會失敗。

---

## Level C — API 契約測試 ⚠️ 19/20 通過，1 失敗

### 失敗：`TestPersistenceManagerContract::test_required_methods_exist`

```
AssertionError: Missing method: save_state
```

`PersistenceManager` 缺少 `save_state()` 方法（上次報告已記錄此問題）。

---

## Level F — 用戶流程 E2E 測試 ❌ 0/9 通過，9 失敗

### 失敗根本原因：LLMProviderRegistry 无限递归

**症狀**：`RecursionError: maximum recursion depth exceeded`

**Call Chain**：
```
process_task(task)
  → engine.evaluate(task, task.context)
    → _get_llm_provider()
      → LLMProviderRegistry.get("minimax")
        → classmethod get() line 136
          → cls.get_instance().get(name)  ← 无限递归！
```

**根本原因（Critical Bug）**：

`LLMProviderRegistry` 同時定義了：
1. **Instance method** `get(self, name)` (line 117-120)
2. **Class method** `get(cls, name)` (line 133-136)

當調用 `inst.get('minimax')`（在 instance 上調用），Python 屬性查找時 classmethod 綁定了 class，shadow 了 instance method。結果 `inst.get()` 實際執行 classmethod，導致：

```python
# classmethod get():
return cls.get_instance().get(name)  # 又調用到 get() 自身！
```

**受影響測試**：所有 E2E 和需要真實 LLM  provider 的測試均受影響。

---

## Level G — Provider 測試 ⚠️ 2/11 通過，8 失敗，1 跳過

### 通過的測試
- `test_mock_response_has_content` ✅
- `test_all_7_engines_together` ✅

### 失敗原因分類
- **RecursionError**（LLMProviderRegistry bug）— 5 個測試
- **dict vs TaskInput** — 3 個測試
- **真實 API 需要網絡** — 1 個測試（預期 skip）

---

## Level I — 效能/穩定性測試 ⚠️ 1/6 通過，5 失敗

所有依賴 `process_task()` 完整流程的效能測試均因 RecursionError 失敗。

---

## 仍未覆蓋的風險

|| 層級 | 風險 | 狀態 |
||------|------|------|
|| A | Smoke test 基本可啟動 | ✅ 已覆蓋 |
|| B | 引擎 task_type 屬性訪問 | ⚠️ 測試需要更新 |
|| C | PersistenceManager.save_state() | ⚠️ 仍未實現 |
|| F | E2E 真實流程 | ❌ LLMProviderRegistry bug 阻斷 |
|| G | 真實 MiniMax API 調用 | ⚠️ 網絡依賴 |
|| H | 回歸測試 | ⏸️ 等待 bug 修復後建立 |
|| I | 效能 threshold | ⚠️ 等待基本功能修復 |

---

## 關鍵 Bug 修復建議

### Bug 1 (Critical)：LLMProviderRegistry 无限递归
**檔案**：`src/engines/llm_provider.py`
**問題**：Classmethod `get()` 與 instance method `get()` 同名，導致 Python 屬性查找時 classmethod 遮蔽 instance method。
**修復**：將 classmethod 改名以避免衝突：
```python
# 舊（衝突）：
@classmethod
def get(cls, name: str) -> Optional[LLMProvider]:
    return cls.get_instance().get(name)

# 新（修復）：
@classmethod
def get_provider(cls, name: str) -> Optional[LLMProvider]:
    return cls.get_instance().providers.get(name)
```

### Bug 2 (High)：現有測試使用 dict 而非 TaskInput
**檔案**：`tests/test_seven_sins.py`、`tests/test_multi_engine_veto.py`
**問題**：引擎已改用 `task.task_type`，但測試仍傳入 dict。
**修復**：將所有 dict task 替換為 `TaskInput(description=..., task_type=...)`。

### Bug 3 (Medium)：helpers 仍使用 task.get()
**檔案**：`src/engines/envy_gluttony_helpers.py` 第 32、53 行
**問題**：傳入 TaskInput dataclass 時 `task.get()` 會失敗。
**修復**：
```python
# 舊：
task.get("description", "")

# 新：
task.description if hasattr(task, 'description') else task.get("description", "")
```

### Bug 4 (Medium)：PersistenceManager.save_state() 缺失
**檔案**：`src/memory/persistence.py`
**問題**：`test_required_methods_exist` 期望 `save_state()` 方法。
**修復**：在 `PersistenceManager` 類別中實現 `save_state()` 方法。

---

## 測試架構狀態

```
7sins/
├── docs/testing/                    # ✅ 7 份文件已建立
│   ├── README.md                     ✅
│   ├── smoke-tests.md               ✅
│   ├── backend-tests.md             ✅
│   ├── api-contract-tests.md        ✅ (但 PersistenceManager 未實現)
│   ├── user-workflow-tests.md       ✅
│   ├── provider-tests.md            ✅
│   ├── regression-tests.md          ⚠️ (待建立)
│   ├── performance-tests.md         ✅
│   └── test-database-strategy.md    ✅
├── tests/                           # ✅ 完整結構已建立
│   ├── smoke/test_smoke.py          ✅ 19 tests
│   ├── api/test_api_contracts.py    ⚠️ 20 tests (1 fail)
│   ├── e2e/test_user_workflows.py   ❌ 9 tests (blocked by recursion bug)
│   ├── providers/                   ⚠️ 部分通過
│   ├── performance/                ⚠️ 部分通過
│   └── helpers/                     ✅
├── scripts/run_all_tests.sh         ✅
└── runtime/logs/tests/              ✅
    └── 20260621_200000/report.md     本報告
```

---

## 建議修復順序

1. **立即修復 Bug 1**：重命名 `LLMProviderRegistry.get()` → `get_provider()`，解開 E2E 和 provider 測試的阻塞
2. **修復 Bug 3**：更新 `envy_gluttony_helpers.py` 中的 `task.get()` 調用
3. **修復 Bug 2**：更新舊測試使用 `TaskInput` dataclass
4. **實現 Bug 4**：`PersistenceManager.save_state()`
5. **重新運行測試**：驗證所有層級通過
6. **建立回歸測試 (Level H)**：為每個修復的 bug 建立回歸測試

---

*報告生成：7Sins Testing Agent | 2026-06-21 20:00*
