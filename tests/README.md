# Tests

## Test Environment Setup

`conftest.py` automatically injects the repo root into `sys.path` at session start, so test files can import project modules without hardcoded paths.

## Fixtures

### `reset_sys_path` (autouse)

- **Purpose**: Prevent `sys.path` pollution between tests
- **Behavior**: Before each test, saves the current `sys.path`. After the test completes (whether passed or failed), restores it to the saved state.
- **Why**: Individual tests may add/remove paths from `sys.path` for imports. Without this fixture, those changes could leak into subsequent tests and cause unexpected import failures or behavior.

This is an `autouse=True` fixture — it runs automatically for **every** test without needing explicit inclusion.