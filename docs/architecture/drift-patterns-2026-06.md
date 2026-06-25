# Architecture Drift Patterns (2026-06)

**Date:** 2026-06-25  
**Status:** Documented for Future Prevention  
**Branch:** auto/todo-72

---

## Overview

Drift is the expected cost of the 7-independent-engines copy pattern, **not individual engineer negligence**. When seven engines are maintained as independent codebases that happen to share similar structure, any common pattern that should be centralized will instead be independently invented by each engine's developer. This document records three complete drift cycles that were identified, fixed, and closed.

---

## Pattern 1: FALLBACK_CONFIDENCE (#44→#48)

### Description

Seven engine files had hardcoded fallback confidence values used when LLM calls fail after retries. Each engine's value was independently invented, resulting in inconsistent risk tolerance across the system (Wrath=0.95, Envy=0.60).

### Trigger Conditions

- Multiple engineers working in parallel on different engines
- No centralized policy document for fallback confidence
- Each engine's fallback was a "local decision" with no shared rationale
- Inline comments (if any) were engine-local and not propagated

### Fix Approach (#44→#48)

1. **Centralize**: Created `FALLBACK_CONFIDENCE` dict in `src/core/drive_engine.py`
2. **Document**: Added 28-line policy docstring explaining each value's philosophy
3. **Propagate**: Replaced all 7 engine hardcoded values with `FALLBACK_CONFIDENCE[self.drive_type]`
4. **Verify**: Smoke test confirms all 7 engines import and use the centralized dict

### Prevention

- Policy docstrings in shared modules serve as source-of-truth
- CI consistency check comparing engine files for structural parity
- ADR (Architecture Decision Record) for any future shared constants

### Code Locations

| File | Lines | Purpose |
|------|-------|---------|
| `src/core/drive_engine.py` | 28–56 | Policy docstring (source of truth) |
| `src/core/drive_engine.py` | 57–65 | `FALLBACK_CONFIDENCE` dict definition |
| `src/engines/lust_engine.py` | 69 | Usage: `confidence=FALLBACK_CONFIDENCE[self.drive_type]` |
| `src/engines/wrath_engine.py` | 69 | Usage |
| `src/engines/gluttony_engine.py` | 71 | Usage |
| `src/engines/greed_engine.py` | 69 | Usage |
| `src/engines/sloth_engine.py` | 69 | Usage |
| `src/engines/envy_engine.py` | 72 | Usage |
| `src/engines/pride_engine.py` | 69 | Usage |
| `docs/testing/smoke-tests.md` | 177–183 | Smoke test verifying all 7 sins defined |

---

## Pattern 2: VETO_CONDITIONS Registry (#55→#59)

### Description

A `VETO_CONDITIONS` dict was introduced to document each engine's veto conditions in a registry table for human inspection. The dict was removed (#56), then re-introduced by another engineer (#58), then removed again (#59) after debate concluded the dict was redundant — `veto_condition` property is the source of truth, not a separate registry.

### Trigger Conditions

- One engineer removed dead code (VETO_CONDITIONS dict)
- Another engineer re-introduced the pattern without knowing the removal rationale
- Architecture decision not propagated via ADR or code comments
- "Registry for inspection" motivation didn't justify the maintenance burden

### Fix Approach (#55→#59)

1. **Identify**: Engineer noticed VETO_CONDITIONS dict reappeared
2. **Debate**: Discussed whether registry pattern had value vs. `veto_condition` property
3. **Decide**: Removed VETO_CONDITIONS dict; `veto_condition` property is single source of truth
4. **Verify**: `grep` confirms no VETO_CONDITIONS残留

### Prevention

- ADR-style comments on removed code explaining why it was removed
- Architecture decision log committed alongside code changes
- Periodic "removed patterns" review to prevent re-introduction

### Code Locations

- **Removed**: `VETO_CONDITIONS` dict no longer exists
- **Source of truth**: Each engine's `veto_condition` property
- **Verification**: `grep -r "VETO_CONDITIONS"` returns no matches (post-#59)

---

## Pattern 3: TaskInput hasattr Bridge (#63→#69)

### Description

`TaskInput` objects arrive as either dicts (external API) or `TaskInput` dataclasses (internal). Consumer code uses `hasattr(task, 'field') else task.get('field', default)` bridge pattern at 9+ call sites. Adding a new TaskInput field requires updating all 9 bridge points.

### Trigger Conditions

- Dict-based and dataclass-based task representations coexist
- No normalization layer at TaskInput construction
- Each consumer independently implements the bridge pattern
- Field additions require parallel edits across all consumers

### Fix Approach (#63→#69)

1. **Identify**: Field additions to TaskInput required updating 9 bridge points
2. **Debate**: Consider TaskInput factory method or `.get()` method on dataclass
3. **Decide**: Keep bridge pattern but document normalization helpers in `seven_sins.py`
4. **Unify**: Helper functions `_get_task_type()` and `_get_task_description()` in `seven_sins.py`

### Prevention

- TaskInput dataclass could implement a `.get()` method for uniform access
- Factory function `TaskInput.from_dict()` to normalize external inputs at boundary
- CI check flagging new `hasattr` patterns in engine code

### Code Locations

| File | Lines | Pattern |
|------|-------|---------|
| `src/core/ego_core.py` | 164 | `task.task_type if hasattr(task, 'task_type') else task.get('task_type', '')` |
| `src/core/ego_core.py` | 633 | Same pattern for `current_task.task_type` |
| `src/engines/seven_sins.py` | 20 | `if hasattr(task, 'task_type')` |
| `src/engines/seven_sins.py` | 29 | `if hasattr(task, 'description')` |
| `src/engines/seven_sins.py` | 183 | `task.constraints if hasattr(task, 'constraints') else task.get('constraints', [])` |
| `src/engines/envy_gluttony_helpers.py` | 26–27 | Bridge in `inject_competitor_search()` |
| `src/engines/envy_gluttony_helpers.py` | 48–49 | Bridge in `inject_research_context()` |
| `src/core/ego_core.py` | 106–111 | `TaskInput` dataclass definition |

---

## user-intention.md LLM Boundary Review

### Current Status

- **Last updated:** 2026-05-26 (30+ days ago as of 2026-06-25)
- **Location:** `user-intention.md` (root directory)
- **Core description:** LLM as "不知疲倦的中級工程師" (tireless mid-level engineer) in Human-in-the-loop mode

### Alignment Assessment

| user-intention.md Principle | 7Sins Implementation | Alignment |
|----------------------------|----------------------|-----------|
| LLM needs explicit instructions | `drive_engine` prompting is explicit | ✅ Full |
| Human-in-the-loop required | `EGOCore.veto` power for PO override | ✅ Full |
| LLM cannot own outcomes | No autonomous production changes | ✅ Full |
| Reactive/passive tool model | 7 engines respond to task events | ✅ Full |

### Divergence Observed

The document describes a **reactive tool LLM** paradigm. 7Sins attempts to build a **driven LLM** where EGO/Drive engines let LLM decide "why to do" (Pride) or "why not to do" (Sloth/veto). This is a more autonomous model than user-intention.md describes.

### Recommendation

**Review needed.** The document should be updated to reflect:
1. 7Sins as a case study of "driven LLM" architecture
2. The EGO veto mechanism as implementation of human-in-the-loop
3. Whether the more autonomous model is intentional or needs course-correction

---

## Prevention Summary

| Pattern | Root Cause | Prevention |
|---------|------------|------------|
| FALLBACK_CONFIDENCE | No shared policy | Centralized dict + docstring + CI check |
| VETO_CONDITIONS | No ADR for removals | Architecture decision log with removal rationale |
| TaskInput hasattr | No normalization layer | TaskInput factory or `.get()` method |

---

## References

- `references/architecture-tradeoffs.md` — Prior summary of drift patterns
- `olivia-space/diary/2026-06-22.md` — Full #44→#48, #55→#59, #63→#69 closure notes
- `src/core/drive_engine.py` — FALLBACK_CONFIDENCE source of truth
- `user-intention.md` — LLM boundary document (needs review)
