# 7-Engines Architecture Tradeoffs

## Drift as Architecture Cost

Drift is the expected cost of the 7-independent-engines copy pattern, not individual engineer negligence. When seven engines are maintained as independent codebases that happen to share similar structure, any common pattern that should be centralized will instead be independently invented by each engine's developer. This is not negligence — it is the natural consequence of a copy-paste architecture where shared intent is never formally codified. The cost manifests as parallel work, conflicting implementations, and the eventual need to reconcile divergent copies back to a canonical form.

## Known Drift Patterns

### 1. FALLBACK_CONFIDENCE
- **Trigger**: #44 engine consistency → #47 FALLBACK_CONFIDENCE comments → #48 redundancy cleanup
- **Root cause**: Multiple engineers independently adding similar fallback confidence logic across 7 engine files — copy-paste architecture pattern
- **Status**: Resolved

### 2. VETO_CONDITIONS
- **Trigger**: #56 remove dead code → #58 re-introduced → #59 removed again  
- **Root cause**: One engineer re-introduced a pattern another engineer had deliberately removed — architecture decision not propagated
- **Status**: Resolved

### 3. TaskInput Migration
- **Trigger**: #63 task.get() fix → #65/#68 unified normalization
- **Root cause**: Dict-based vs dataclass attribute access — boundary functions need backward-compat bridge
- **Status**: Resolved

## Prevention Strategies

- **Shared base class or mixin** for common engine lifecycle patterns (fallback confidence, veto conditions) so changes propagate automatically rather than requiring parallel edits
- **Architecture decision log** (ADR-style) committed alongside code changes so that removed patterns carry their removal reason forward and cannot be unknowingly re-introduced
- **Consistency CI check** that compares the 7 engine files for structural parity and alerts on divergence before it accumulates across multiple engineers and multiple TODOs