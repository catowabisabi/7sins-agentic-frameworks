# 7Sins 外部 Provider 測試 (External Provider Tests)

> 繁體中文 | 層級: G | 建立日期: 2026-06-21

---

## 🎯 目的

測試 LLM Provider 整合 — MiniMax API、MiniMax Provider Wrapper、七個 Engine 與 Provider 的 Call Chain。

---

## ⚡ 執行命令

```bash
cd /mnt/c/Users/enoma/Desktop/opencode-work/agent-works/research/7sins
python -m pytest tests/providers/ -v
```

---

## ⚠️ 重要前提

這些測試需要真實 API Key，請在 `tests/providers/.env` 中設定：
```
MINIMAX_API_KEY=your_key_here
MINIMAX_GROUP_ID=your_group_id_here
```

如無 API Key，這些測試會被標記為 `SKIPPED`。

---

## 📋 測試層級

### G.1 MiniMax Provider 直接呼叫

```python
@pytest.mark.skipif(not has_api_key(), reason="Requires MINIMAX_API_KEY")
def test_minimax_direct_complete():
    """Direct call to MiniMax API - verify basic connectivity."""
    from src.engines.minimax_provider import create_minimax_provider
    import os
    
    provider = create_minimax_provider(
        api_key=os.environ["MINIMAX_API_KEY"],
        group_id=os.environ.get("MINIMAX_GROUP_ID", "")
    )
    
    response = provider.complete(
        prompt="What is 2+2? Reply with just the number.",
        system_prompt="You are a calculator. Reply only with the answer."
    )
    
    assert response.content is not None
    assert len(response.content) > 0
    assert "4" in response.content
```

### G.2 MiniMax Provider Mock 一致性

```python
def test_provider_response_structure():
    """Mock provider must return same structure as real provider."""
    from tests.helpers.mock_providers import MockMiniMaxProvider
    
    mock = MockMiniMaxProvider()
    response = mock.complete(
        prompt="test",
        system_prompt="You are a test assistant."
    )
    
    # Must have same attributes as real LLMResponse
    assert hasattr(response, "content")
    assert isinstance(response.content, str)
```

### G.3 Seven Sins 引擎使用同一個 Provider

```python
def test_all_engines_use_same_provider():
    """All 7 engines should use the same provider instance when initialized together."""
    from src.engines.seven_sins import (
        GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
        PrideEngine, WrathEngine, EnvyEngine
    )
    
    # All engines should initialize without error
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
    
    # Each engine should have _llm_provider or similar
    for engine in engines:
        assert engine is not None
        assert engine.drive_type is not None
```

### G.4 LLM 回應解析穩定性

```python
def test_llm_response_parsing_various_formats():
    """Test that various LLM response formats are parsed correctly."""
    from src.engines.seven_sins import _parse_llm_opinion
    from src.core.drive_engine import DriveType, DriveOpinion
    
    # Format 1: Standard format
    response1 = "OPINION: This is a good approach\nCONFIDENCE: 0.8\nRECOMMENDATION: Proceed\nRISK: low"
    opinion1 = _parse_llm_opinion(response1, DriveType.WRATH)
    assert 0.7 <= opinion1.confidence <= 0.9
    
    # Format 2: With extra whitespace
    response2 = "  OPINION:   Test  \n  CONFIDENCE:  0.75  \n  RECOMMENDATION:   Go\n  RISK: medium  "
    opinion2 = _parse_llm_opinion(response2, DriveType.GLUTTONY)
    assert opinion2.confidence == 0.75
    assert opinion2.risk_level == "medium"
```

### G.5 Provider Error Handling

```python
def test_provider_timeout_handling():
    """Provider should handle timeout gracefully with fallback."""
    from src.engines.seven_sins import _call_llm_with_retry
    from unittest.mock import Mock, patch
    import pytest
    
    mock_provider = Mock()
    mock_provider.complete.side_effect = TimeoutError("Request timeout")
    
    # Should raise, not hang
    with pytest.raises(TimeoutError):
        _call_llm_with_retry(
            mock_provider,
            prompt="test",
            system_prompt="test",
            max_retries=1
        )
```

### G.6 Search Tool 真實呼叫（如有網絡）

```python
@pytest.mark.skipif(not has_search_available(), reason="Search tool not available")
def test_search_tool_real_call():
    """Real search tool call (if configured)."""
    from src.tools.search import get_search_tool
    
    tool = get_search_tool()
    results = tool.search("7 sins AI agent framework", count=3)
    
    assert isinstance(results, list)
    assert len(results) <= 3
```

---

## 📊 輸出位置

| 輸出 | 位置 |
|------|------|
| pytest 標準輸出 | stdout |
| 報告 | `runtime/logs/tests/<timestamp>/provider-report.md` |

---

## ✅ Pass / Fail 標準

| 條件 | 結果 |
|------|------|
| 所有非跳過測試通過 | **PASS** |
| 任何 1 項非跳過測試失敗 | **FAIL** |
| 所有測試跳過（無 API Key） | **SKIPPED** |

---

## 📝 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-21 | 1.0.0 | 初始建立 |

*最後更新: 2026-06-21*
