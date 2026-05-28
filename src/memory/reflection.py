"""
7Sins Project - Memory and Reflection System
Self-growth reflective loop implementation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os


class ReflectionPhase(Enum):
    LOG_REVIEW = "log_review"
    ATTRIBUTION = "attribution"
    BIAS_DETECTION = "bias_detection"
    ADJUSTMENT = "adjustment"
    GROWTH_LOG = "growth_log"


@dataclass
class DecisionRecord:
    task_id: str
    task_description: str
    winning_drive: str
    drive_weights: Dict[str, float]
    outcome: str
    outcome_confidence: float
    timestamp: float
    reflection_notes: List[str] = field(default_factory=list)


@dataclass
class GrowthPattern:
    drive: str
    pattern_type: str
    description: str
    occurrence_count: int
    last_observed: float


@dataclass
class WeightHistoryEntry:
    """Track drive weights at a specific point in time."""
    timestamp: float
    drive_weights: Dict[str, float]
    winning_drive: str
    outcome: str


class GrowthInsight:
    """Insight generated from weight evolution analysis."""
    def __init__(self, insight_type: str, drive: str, description: str, magnitude: float = 0.0):
        self.insight_type = insight_type
        self.drive = drive
        self.description = description
        self.magnitude = magnitude
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.insight_type,
            "drive": self.drive,
            "description": self.description,
            "magnitude": self.magnitude
        }


class ReflectionAgent:
    
    def __init__(self, log_dir: str = "logs", bias_window: int = 20):
        self.log_dir = log_dir
        self.decision_history: List[DecisionRecord] = []
        self.growth_patterns: Dict[str, List[GrowthPattern]] = {}
        self.max_history = 1000
        self.weight_history: List[WeightHistoryEntry] = []
        self.max_weight_history = 100
        self.bias_window = bias_window
    
    def record_decision(self, record: DecisionRecord):
        self.decision_history.append(record)
        if len(self.decision_history) > self.max_history:
            self.decision_history.pop(0)
        # Record weight history entry
        self._record_weight_history(record)
    
    def _record_weight_history(self, record: DecisionRecord):
        """Record the current drive weights for historical tracking."""
        entry = WeightHistoryEntry(
            timestamp=record.timestamp,
            drive_weights=record.drive_weights.copy(),
            winning_drive=record.winning_drive,
            outcome=record.outcome
        )
        self.weight_history.append(entry)
        if len(self.weight_history) > self.max_weight_history:
            self.weight_history.pop(0)
    
    def get_weight_evolution(self, drive: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get weight evolution history for a specific drive or all drives.
        
        Args:
            drive: Specific drive to track (None for all drives)
            limit: Maximum number of history entries to return
            
        Returns:
            List of weight snapshots with timestamps and outcomes
        """
        history = self.weight_history[-limit:]
        if not history:
            return []
        
        result = []
        for entry in history:
            snapshot = {
                "timestamp": entry.timestamp,
                "winning_drive": entry.winning_drive,
                "outcome": entry.outcome,
                "weights": entry.drive_weights
            }
            if drive:
                snapshot["weight"] = entry.drive_weights.get(drive)
            result.append(snapshot)
        return result
    
    def analyze_weight_trend(self, drive: str, window: int = 10) -> Dict[str, Any]:
        """Analyze the weight trend for a specific drive over recent history.
        
        Args:
            drive: Drive to analyze
            window: Number of recent entries to consider
            
        Returns:
            Trend analysis with direction, stability, and pattern insights
        """
        if window <= 0:
            return {"status": "insufficient_data", "drive": drive, "reason": "invalid_window"}
        
        if not self.weight_history:
            return {"status": "insufficient_data", "drive": drive, "reason": "no_history"}
        
        recent = self.weight_history[-window:]
        if len(recent) < 2:
            return {"status": "insufficient_data", "drive": drive, "reason": "insufficient_entries"}
        
        weights = [entry.drive_weights.get(drive, 0.0) for entry in recent]
        
        # Calculate trend direction
        first_half_avg = sum(weights[:len(weights)//2]) / (len(weights)//2)
        second_half_avg = sum(weights[len(weights)//2:]) / (len(weights) - len(weights)//2)
        trend_direction = "increasing" if second_half_avg > first_half_avg else "decreasing" if second_half_avg < first_half_avg else "stable"
        
        # Calculate stability (variance)
        mean_weight = sum(weights) / len(weights)
        variance = sum((w - mean_weight) ** 2 for w in weights) / len(weights)
        stability = "high" if variance < 0.01 else "medium" if variance < 0.05 else "low"
        
        # Calculate overall change
        overall_change = weights[-1] - weights[0]
        
        return {
            "drive": drive,
            "window": window,
            "trend_direction": trend_direction,
            "stability": stability,
            "current_weight": weights[-1],
            "average_weight": mean_weight,
            "overall_change": overall_change,
            "min_weight": min(weights),
            "max_weight": max(weights)
        }
    
    def detect_growth_patterns(self) -> List[GrowthInsight]:
        """Detect patterns in weight evolution and generate insights.
        
        Returns:
            List of GrowthInsight objects describing detected patterns
        """
        insights = []
        drives = set()
        for entry in self.weight_history:
            drives.update(entry.drive_weights.keys())
        
        for drive in drives:
            window = min(10, len(self.weight_history)) if self.weight_history else 0
            if window < 2:
                continue
            trend = self.analyze_weight_trend(drive, window=window)
            if trend.get("status") == "insufficient_data":
                continue
            
            # Detect growth patterns
            if trend["trend_direction"] == "increasing" and trend["overall_change"] > 0.1:
                insights.append(GrowthInsight(
                    insight_type="growth",
                    drive=drive,
                    description=f"{drive} has been consistently growing (+{trend['overall_change']:.2f})",
                    magnitude=trend['overall_change']
                ))
            
            # Detect decline patterns
            if trend["trend_direction"] == "decreasing" and trend["overall_change"] < -0.1:
                insights.append(GrowthInsight(
                    insight_type="decline",
                    drive=drive,
                    description=f"{drive} has been declining ({trend['overall_change']:.2f})",
                    magnitude=abs(trend['overall_change'])
                ))
            
            # Detect instability
            if trend["stability"] == "low":
                insights.append(GrowthInsight(
                    insight_type="instability",
                    drive=drive,
                    description=f"{drive} shows unstable weight fluctuations",
                    magnitude=0.5
                ))
            
            # Detect dominance
            recent_entries = self.weight_history[-10:]
            if recent_entries:
                win_count = sum(1 for e in recent_entries if e.winning_drive == drive)
                if win_count >= 7:
                    insights.append(GrowthInsight(
                        insight_type="dominance",
                        drive=drive,
                        description=f"{drive} dominates {win_count}/10 recent decisions",
                        magnitude=win_count / 10
                    ))
        
        return insights
    
    def get_weight_correlation(self) -> Dict[str, Dict[str, float]]:
        """Calculate correlation between different drive weights over time.
        
        Returns:
            Dictionary mapping drive pairs to their correlation coefficient
        """
        if len(self.weight_history) < 3:
            return {}
        
        drives = list(self.weight_history[0].drive_weights.keys())
        correlations = {}
        
        for i, d1 in enumerate(drives):
            for d2 in drives[i+1:]:
                weights1 = [entry.drive_weights.get(d1, 0.0) for entry in self.weight_history]
                weights2 = [entry.drive_weights.get(d2, 0.0) for entry in self.weight_history]
                
                # Pearson correlation
                n = len(weights1)
                if n < 2:
                    continue
                
                mean1 = sum(weights1) / n
                mean2 = sum(weights2) / n
                
                variance1 = sum((w1 - mean1) ** 2 for w1 in weights1)
                variance2 = sum((w2 - mean2) ** 2 for w2 in weights2)
                
                # Guard against division by zero (zero variance means all weights identical)
                if variance1 == 0 or variance2 == 0:
                    continue
                
                numerator = sum((w1 - mean1) * (w2 - mean2) for w1, w2 in zip(weights1, weights2))
                denom1 = variance1 ** 0.5
                denom2 = variance2 ** 0.5
                
                correlation = numerator / (denom1 * denom2)
                correlations[f"{d1}_{d2}"] = round(correlation, 3)
        
        return correlations
    
    def get_growth_report(self) -> Dict[str, Any]:
        """Generate a comprehensive growth report with all insights.
        
        Returns:
            Dictionary containing weight evolution summary, patterns, and recommendations
        """
        patterns = self.detect_growth_patterns()
        correlation = self.get_weight_correlation()
        
        drive_trends = {}
        drives = set()
        for entry in self.weight_history:
            drives.update(entry.drive_weights.keys())
        
        for drive in drives:
            drive_trends[drive] = self.analyze_weight_trend(drive)
        
        # Generate recommendations based on insights
        recommendations = []
        for insight in patterns:
            if insight.insight_type == "dominance" and insight.magnitude >= 0.8:
                recommendations.append(f"Consider reducing {insight.drive} weight to balance decision-making")
            elif insight.insight_type == "decline" and insight.magnitude > 0.15:
                recommendations.append(f"Analyze why {insight.drive} is declining - may need attention")
        
        return {
            "total_weight_entries": len(self.weight_history),
            "drive_trends": drive_trends,
            "patterns": [p.to_dict() for p in patterns],
            "correlations": correlation,
            "recommendations": recommendations
        }
    
    def analyze_recent_decisions(self, limit: int = 10) -> Dict[str, Any]:
        recent = self.decision_history[-limit:]
        if not recent:
            return {"status": "no_history", "insights": []}
        
        drive_wins: Dict[str, int] = {}
        for record in recent:
            drive = record.winning_drive
            drive_wins[drive] = drive_wins.get(drive, 0) + 1
        
        total = len(recent)
        drive_percentages = {d: (c/total)*100 for d, c in drive_wins.items()}
        
        outcomes = [r.outcome for r in recent]
        success_rate = outcomes.count("success") / len(outcomes) if outcomes else 0
        
        return {
            "recent_count": len(recent),
            "drive_wins": drive_wins,
            "drive_percentages": drive_percentages,
            "success_rate": success_rate,
            "dominant_drive": max(drive_wins, key=drive_wins.get) if drive_wins else None
        }
    
    def detect_bias(self, window: Optional[int] = None) -> List[str]:
        """Detect bias in recent decisions.
        
        Args:
            window: Number of recent decisions to analyze (defaults to self.bias_window)
            
        Returns:
            List of bias report strings
        """
        bias_report = []
        window = window if window is not None else self.bias_window
        
        if window <= 0:
            return bias_report
        
        recent = self.decision_history[-window:]
        if not recent:
            return bias_report
        
        drive_wins: Dict[str, int] = {}
        for record in recent:
            drive = record.winning_drive
            drive_wins[drive] = drive_wins.get(drive, 0) + 1
        
        for drive, count in drive_wins.items():
            threshold_60 = int(window * 0.6)
            if count > threshold_60:
                bias_report.append(f"{drive} has won {count}/{window} decisions ({count/window*100:.0f}%) - possible over-dominance")
            if count < 2:
                bias_report.append(f"{drive} has only won {count}/{window} decisions - possible suppression")
        
        return bias_report
    
    def get_self_criticism(self) -> str:
        analysis = self.analyze_recent_decisions()
        biases = self.detect_bias()
        
        criticism = []
        criticism.append("Self-Criticism Analysis:")
        criticism.append(f"- Dominant drive: {analysis.get('dominant_drive', 'unknown')}")
        criticism.append(f"- Success rate: {analysis.get('success_rate', 0)*100:.1f}%")
        
        if biases:
            criticism.append("- Biases detected:")
            for b in biases:
                criticism.append(f"  * {b}")
        else:
            criticism.append("- No significant biases detected")
        
        return "\n".join(criticism)
    
    def suggest_weight_adjustments(self) -> Dict[str, float]:
        adjustments = {}
        analysis = self.analyze_recent_decisions()
        biases = self.detect_bias()
        
        dominant = analysis.get("dominant_drive")
        if dominant and dominant in str(analysis.get("drive_percentages", {})):
            if analysis["drive_percentages"].get(dominant, 0) > 70:
                adjustments[dominant] = -0.1
        
        success_rate = analysis.get("success_rate", 0)
        if success_rate < 0.6:
            for drive in ["gluttony", "pride", "wrath"]:
                adjustments[drive] = adjustments.get(drive, 0) + 0.05
        
        return adjustments
    
    def log_to_file(self, filepath: Optional[str] = None):
        if filepath is None:
            filepath = os.path.join(self.log_dir, f"reflection_{datetime.now().strftime('%Y%m%d')}.json")
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "decision_history_count": len(self.decision_history),
            "recent_analysis": self.analyze_recent_decisions(),
            "biases": self.detect_bias(),
            "self_criticism": self.get_self_criticism()
        }
        
        os.makedirs(self.log_dir, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


class DriveMemory:
    
    def __init__(self, drive_name: str):
        self.drive_name = drive_name
        self.opinions_given: List[Dict[str, Any]] = []
        self.wins: int = 0
        self.losses: int = 0
    
    def record_opinion(self, opinion: str, confidence: float, won: bool):
        self.opinions_given.append({
            "opinion": opinion,
            "confidence": confidence,
            "won": won,
            "timestamp": datetime.now().timestamp()
        })
        if won:
            self.wins += 1
        else:
            self.losses += 1
    
    def get_win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0
    
    def get_average_confidence(self) -> float:
        if not self.opinions_given:
            return 0.0
        return sum(o["confidence"] for o in self.opinions_given) / len(self.opinions_given)
