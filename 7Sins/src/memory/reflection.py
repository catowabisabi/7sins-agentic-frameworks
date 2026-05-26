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


class ReflectionAgent:
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.decision_history: List[DecisionRecord] = []
        self.growth_patterns: Dict[str, List[GrowthPattern]] = {}
        self.max_history = 1000
    
    def record_decision(self, record: DecisionRecord):
        self.decision_history.append(record)
        if len(self.decision_history) > self.max_history:
            self.decision_history.pop(0)
    
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
    
    def detect_bias(self) -> List[str]:
        bias_report = []
        recent = self.decision_history[-20:]
        if not recent:
            return bias_report
        
        drive_wins: Dict[str, int] = {}
        for record in recent:
            drive = record.winning_drive
            drive_wins[drive] = drive_wins.get(drive, 0) + 1
        
        for drive, count in drive_wins.items():
            if count > 12:
                bias_report.append(f"{drive} has won {count}/20 decisions (60%) - possible over-dominance")
            if count < 2:
                bias_report.append(f"{drive} has only won {count}/20 decisions - possible suppression")
        
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