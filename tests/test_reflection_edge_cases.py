"""
Tests for reflection.py edge cases
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.reflection import ReflectionAgent, DecisionRecord, WeightHistoryEntry


class TestGetWeightCorrelationZeroVariance:
    """Tests for get_weight_correlation() with zero variance edge cases."""
    
    def test_identical_weights_returns_empty(self):
        """When all weights are identical, variance is 0 - should return empty dict."""
        agent = ReflectionAgent()
        
        # Manually add weight history with identical weights
        identical_weights = {"pride": 0.5, "gluttony": 0.5}
        for i in range(5):
            agent.weight_history.append(WeightHistoryEntry(
                timestamp=float(i),
                drive_weights=identical_weights.copy(),
                winning_drive="pride",
                outcome="success"
            ))
        
        result = agent.get_weight_correlation()
        assert result == {}, "Should return empty dict when variance is 0"
    
    def test_mixed_variance_returns_correlations(self):
        """When weights vary, should return valid correlations."""
        agent = ReflectionAgent()
        
        weights_list = [
            {"pride": 0.1, "gluttony": 0.9},
            {"pride": 0.2, "gluttony": 0.8},
            {"pride": 0.3, "gluttony": 0.7},
            {"pride": 0.4, "gluttony": 0.6},
            {"pride": 0.5, "gluttony": 0.5},
        ]
        
        for i, w in enumerate(weights_list):
            agent.weight_history.append(WeightHistoryEntry(
                timestamp=float(i),
                drive_weights=w,
                winning_drive="pride" if i % 2 == 0 else "gluttony",
                outcome="success"
            ))
        
        result = agent.get_weight_correlation()
        assert "pride_gluttony" in result


class TestAnalyzeWeightTrendEdgeCases:
    """Tests for analyze_weight_trend() with empty history and window=0."""
    
    def test_empty_history_returns_insufficient_data(self):
        """With no weight history, should return insufficient_data status."""
        agent = ReflectionAgent()
        
        result = agent.analyze_weight_trend("pride")
        
        assert result["status"] == "insufficient_data"
        assert result["reason"] == "no_history"
    
    def test_window_zero_returns_invalid_window(self):
        """With window=0, should return invalid_window reason."""
        agent = ReflectionAgent()
        agent.weight_history.append(WeightHistoryEntry(
            timestamp=1.0,
            drive_weights={"pride": 0.5},
            winning_drive="pride",
            outcome="success"
        ))
        
        result = agent.analyze_weight_trend("pride", window=0)
        
        assert result["status"] == "insufficient_data"
        assert result["reason"] == "invalid_window"
    
    def test_window_larger_than_history(self):
        """Window larger than history should still work (uses available data)."""
        agent = ReflectionAgent()
        agent.weight_history.append(WeightHistoryEntry(
            timestamp=1.0,
            drive_weights={"pride": 0.5, "gluttony": 0.5},
            winning_drive="pride",
            outcome="success"
        ))
        
        result = agent.analyze_weight_trend("pride", window=100)
        
        assert result["status"] == "insufficient_data"
        assert result["reason"] == "insufficient_entries"
    
    def test_single_entry_returns_insufficient(self):
        """With only 1 entry, should return insufficient_data."""
        agent = ReflectionAgent()
        agent.weight_history.append(WeightHistoryEntry(
            timestamp=1.0,
            drive_weights={"pride": 0.5},
            winning_drive="pride",
            outcome="success"
        ))
        
        result = agent.analyze_weight_trend("pride", window=10)
        
        assert result["status"] == "insufficient_data"
        assert result["reason"] == "insufficient_entries"


class TestDetectBiasConfigurableWindow:
    """Tests for detect_bias() with configurable window."""
    
    def test_default_bias_window(self):
        """Default window should be 20 (from __init__)."""
        agent = ReflectionAgent()
        assert agent.bias_window == 20
    
    def test_custom_bias_window(self):
        """Should accept custom bias_window in constructor."""
        agent = ReflectionAgent(bias_window=50)
        assert agent.bias_window == 50
    
    def test_detect_bias_small_sample(self):
        """With small sample and small window, should work correctly."""
        agent = ReflectionAgent(bias_window=5)
        
        for i in range(5):
            agent.decision_history.append(DecisionRecord(
                task_id=f"task_{i}",
                task_description=f"task desc {i}",
                winning_drive="pride" if i < 4 else "gluttony",
                drive_weights={"pride": 0.6, "gluttony": 0.4},
                outcome="success",
                outcome_confidence=0.8,
                timestamp=float(i)
            ))
        
        result = agent.detect_bias()
        # "pride" won 4/5 = 80% which exceeds 60% threshold (3/5) - over-dominance
        # "gluttony" won 1/5 - possible suppression
        assert len(result) == 2
        assert any("over-dominance" in r for r in result)
        assert any("suppression" in r for r in result)
    
    def test_detect_bias_window_override(self):
        """detect_bias() should accept window override parameter."""
        agent = ReflectionAgent(bias_window=20)
        
        for i in range(30):
            agent.decision_history.append(DecisionRecord(
                task_id=f"task_{i}",
                task_description=f"task desc {i}",
                winning_drive="pride",
                drive_weights={"pride": 0.6, "gluttony": 0.4},
                outcome="success",
                outcome_confidence=0.8,
                timestamp=float(i)
            ))
        
        # With window=10, pride at 10/10 = 100% - over threshold
        result = agent.detect_bias(window=10)
        assert len(result) == 1
        assert "pride" in result[0]
    
    def test_detect_bias_zero_window(self):
        """With window=0, should return empty bias report."""
        agent = ReflectionAgent(bias_window=20)
        
        for i in range(20):
            agent.decision_history.append(DecisionRecord(
                task_id=f"task_{i}",
                task_description=f"task desc {i}",
                winning_drive="pride",
                drive_weights={"pride": 0.6, "gluttony": 0.4},
                outcome="success",
                outcome_confidence=0.8,
                timestamp=float(i)
            ))
        
        result = agent.detect_bias(window=0)
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
