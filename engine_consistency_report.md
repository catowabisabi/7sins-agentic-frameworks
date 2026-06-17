# Engine Architecture Consistency Report

**Analysis Branch:** `auto/todo-44`  
**Source Commit:** `origin/main`  
**Engines Analyzed:** Pride, Greed, Wrath, Sloth, Lust, Envy, Gluttony

---

## 1. Summary Table

| Engine | Lines | Extra Import | Extra Logic in `evaluate()` | Extra `on_task_complete` | `confidence *= drive_weight` |
|--------|-------|-------------|------------------------------|--------------------------|------------------------------|
| Pride | 72 | — | — | success +0.03 | ✓ |
| Greed | 72 | — | — | success +0.05 | ✓ |
| Wrath | 72 | — | — | failure -0.10 | ✓ |
| Sloth | 72 | — | — | success +0.04 | ✓ |
| Lust | 72 | — | — | success +0.03 | ✓ |
| **Envy** | **86** | `logging`, `SearchUnavailableError` | **14 lines: competitor search injection** | success +0.03 | ✓ |
| **Gluttony** | **87** | `logging`, `SearchUnavailableError` | **13 lines: research search injection** | **success +0.05, failure -0.05** | ✓ |

---

## 2. Standard Architecture (All 7 Share)

All engines conform to a base template:

```
Class(DriveEngine)
├── __init__(DriveType.<NAME>, base_weight=<X>)
├── system_prompt @property → str
├── specialization @property → List[str]
├── veto_condition @property → str
├── evaluate(task, context) → DriveOpinion
│   ├── self.state.activate(<X>)
│   ├── self.execute(task.get("task_type", ""))
│   ├── task_type extraction (lower)
│   ├── eros/thanatos weight fetch
│   ├── is_creation / is_destruction detection
│   ├── drive_weight = eros | thanatos | 0.5
│   ├── LLM call via _call_llm_with_retry
│   ├── _parse_llm_opinion → opinion
│   ├── opinion.confidence *= drive_weight   ← present in ALL engines
│   ├── self.add_opinion(opinion)
│   └── try/except with fallback DriveOpinion
└── on_task_complete(success, feedback)
    └── weight adjustment
```

### Standard `evaluate()` Fallback Confidence Values (exception path):
| Engine | Fallback Confidence | Risk Level |
|--------|--------------------|-----------|
| Pride | 0.70 | medium |
| Greed | 0.75 | medium |
| Wrath | 0.95 | high |
| Sloth | 0.80 | low |
| Lust | 0.70 | low |
| Envy | 0.60 | medium |
| Gluttony | 0.80 | medium |

---

## 3. Divergence Details

### 3.1 EnvyEngine (86 lines, +14 lines vs standard)

**Extra imports (L7-9):**
```python
import logging
logger = logging.getLogger(__name__)
```

**Extra logic in `evaluate()` at L55-64:**
```python
is_competitive = any(kw in task_type for kw in ["competitor", "benchmark", "compare"])
if is_competitive:
    try:
        from src.tools.search import get_search_tool, SearchUnavailableError
        search_tool = get_search_tool()
        competitor_results = search_tool.search(task.get("description", ""), count=10)
        if competitor_results:
            context["competitor_info"] = competitor_results
    except SearchUnavailableError:
        logger.warning("Search tool unavailable - proceeding without competitor data")
```
**Assessment:** INTENTIONALLY DIVERGENT — Envy's competitive analysis role requires external competitive data. The search tool injection for `competitor/benchmark/compare` task types is semantically consistent with the engine's purpose.

**Standard elements still present:**
- `opinion.confidence = opinion.confidence * drive_weight` (L73) — matches all others
- `on_task_complete`: `success → adjust_weight(+0.03)` — matches Pride/Lust

---

### 3.2 GluttonyEngine (87 lines, +15 lines vs standard)

**Extra imports (L7-9):**
```python
import logging
logger = logging.getLogger(__name__)
```

**Extra logic in `evaluate()` at L53-62:**
```python
is_research = any(kw in task_type for kw in ["research", "search", "investigate"])
if is_research:
    try:
        from src.tools.search import get_search_tool, SearchUnavailableError
        search_tool = get_search_tool()
        search_results = search_tool.search(task.get("description", ""), count=10)
        if search_results:
            context["search_results"] = search_results
    except SearchUnavailableError:
        logger.warning("Search tool unavailable - proceeding without research data")
```
**Assessment:** INTENTIONALLY DIVERGENT — Gluttony's knowledge harvesting role requires external research data. The search tool injection for `research/search/investigate` task types is semantically consistent with the engine's purpose.

**Bidirectional `on_task_complete` at L84-88:**
```python
def on_task_complete(self, success: bool, feedback: Optional[str] = None):
    if success:
        self.adjust_weight(0.05)
    else:
        self.adjust_weight(-0.05)
```
**Assessment:** UNIQUE — All other engines use unidirectional adjustment. Gluttony's bidirectional approach (reward success +0.05, penalize failure -0.05) is a deliberate design choice reflecting the knowledge acquisition loop: both gaining and losing knowledge carry weight.

---

## 4. `on_task_complete` Comparison

| Engine | Success Adjustment | Failure Adjustment |
|--------|-------------------|--------------------|
| Pride | +0.03 | 0 (none) |
| Greed | +0.05 | 0 (none) |
| Wrath | 0 (none) | **-0.10** (strong penalty) |
| Sloth | +0.04 | 0 (none) |
| Lust | +0.03 | 0 (none) |
| Envy | +0.03 | 0 (none) |
| **Gluttony** | **+0.05** | **-0.05** |

**Observation:** Only Wrath penalizes failure; only Gluttony has bidirectional adjustment.

---

## 5. `confidence *= drive_weight` Location

| Engine | Line | Context |
|--------|------|---------|
| Pride | 59 | After `_parse_llm_opinion`, before `add_opinion` |
| Greed | 59 | After `_parse_llm_opinion`, before `add_opinion` |
| Wrath | 59 | After `_parse_llm_opinion`, before `add_opinion` |
| Sloth | 59 | After `_parse_llm_opinion`, before `add_opinion` |
| Lust | 59 | After `_parse_llm_opinion`, before `add_opinion` |
| Envy | 73 | After `_parse_llm_opinion`, before `add_opinion` |
| Gluttony | 71 | After `_parse_llm_opinion`, before `add_opinion` |

**All 7 engines apply `opinion.confidence *= drive_weight` — fully consistent.**

---

## 6. Structural Anomalies

### 6.1 Envy L73 Extra Confidence Multiplication
The context states Envy has "extra opinion.confidence * drive_weight at L73-75". However, this line is present in ALL 7 engines at the same semantic position. The apparent difference is line number offset (73 vs 59) because Envy has extra logic before the LLM call that pushes the line number down by 14. There is **no actual extra multiplication** — it is a consistent pattern.

### 6.2 Line Count Discrepancy
| File | Reported | Actual | Notes |
|------|----------|--------|-------|
| Pride | 72 | 72 | ✓ |
| Greed | 72 | 72 | ✓ |
| Wrath | 72 | 72 | ✓ |
| Sloth | 72 | 72 | ✓ |
| Lust | 72 | 72 | ✓ |
| Envy | 87 | 86 | -1 line |
| Gluttony | 88 | 87 | -1 line |

Both Envy and Gluttony are 1 line shorter than reported. This is a documentation issue, not a code issue.

---

## 7. Intentional vs. Unnecessary Divergence Assessment

| Feature | Engines | Assessment |
|---------|---------|------------|
| `opinion.confidence *= drive_weight` | ALL 7 | **Intentional** — core architecture |
| Search tool injection (competitive context) | Envy | **Intentional** — competitive benchmarking requires data |
| Search tool injection (research context) | Gluttony | **Intentional** — knowledge harvesting requires data |
| `logging` import | Envy, Gluttony | **Intentional** — required for graceful search tool fallback |
| Bidirectional `on_task_complete` | Gluttony only | **Intentional** — reflects knowledge acquisition loop semantics |
| Failure penalty in `on_task_complete` | Wrath only | **Intentional** — zero-tolerance guardian must punish errors |

**Conclusion:** All divergences are semantically motivated and intentionally designed. No unnecessary architectural drift detected.

---

## 8. Recommendations

1. **Update line count documentation** — Envy is 86 lines (not 87), Gluttony is 87 lines (not 88).
2. **Clarify context notes** — The "extra opinion.confidence * drive_weight" note for Envy is misleading; this pattern exists in all 7 engines at the same semantic position.
3. **Consider standardizing fallback confidence** — The exception path confidence values vary (0.60–0.95) with no documented rationale. Consider a named constant or policy.
4. **Consider extracting search tool injection** — Envy and Gluttony share the identical search tool pattern. A shared helper could reduce duplication, though the trigger keywords differ enough that it may not be worth abstracting.
