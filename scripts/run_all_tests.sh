#!/bin/bash
# 7Sins Test Runner - Run All Tests
# Usage: bash scripts/run_all_tests.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="$REPO_ROOT/runtime/logs/tests/$TIMESTAMP"
mkdir -p "$REPORT_DIR"

echo "=========================================="
echo "7Sins Test Runner"
echo "Timestamp: $TIMESTAMP"
echo "Report dir: $REPORT_DIR"
echo "=========================================="

# Run all tests with pytest
echo ""
echo "Running all tests..."
python -m pytest tests/ -v --tb=short 2>&1 | tee "$REPORT_DIR/pytest.log"

# Capture exit code
EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "=========================================="
echo "Test run complete"
echo "Exit code: $EXIT_CODE"
echo "Full log: $REPORT_DIR/pytest.log"
echo "=========================================="

exit $EXIT_CODE
