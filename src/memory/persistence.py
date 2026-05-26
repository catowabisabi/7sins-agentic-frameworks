"""
7Sins Project - Persistence Layer
SQLite-based storage for decision history and drive weight evolution
"""

import sqlite3
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime


class PersistenceManager:
    """SQLite persistence for decision logs and drive weight history"""
    
    _instance: Optional['PersistenceManager'] = None
    _db_path: str = "7Sins_manager_state/persistence.db"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._ensure_db_dir()
        self._init_tables()
    
    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self._db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)
    
    def _init_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                task_description TEXT,
                winning_drive TEXT,
                confidence REAL,
                eros_weight REAL,
                thanatos_weight REAL,
                weight_snapshot TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drive_weight_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                drive_type TEXT,
                weight REAL,
                change_delta REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_decision(
        self,
        task_description: str,
        winning_drive: str,
        confidence: float,
        eros_weight: float,
        thanatos_weight: float,
        weight_snapshot: Dict[str, float]
    ):
        """Log a decision to the DecisionLog table"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO decision_log 
            (timestamp, task_description, winning_drive, confidence, eros_weight, thanatos_weight, weight_snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            task_description,
            winning_drive,
            confidence,
            eros_weight,
            thanatos_weight,
            json.dumps(weight_snapshot)
        ))
        
        conn.commit()
        conn.close()
    
    def log_weight_change(self, drive_type: str, new_weight: float, delta: float):
        """Log a drive weight change to the DriveWeightHistory table"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO drive_weight_history
            (timestamp, drive_type, weight, change_delta)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            drive_type,
            new_weight,
            delta
        ))
        
        conn.commit()
        conn.close()
    
    def get_decision_history(self, limit: int = 100) -> list:
        """Retrieve recent decision history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, task_description, winning_drive, confidence, 
                   eros_weight, thanatos_weight, weight_snapshot
            FROM decision_log
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "timestamp": r[1],
                "task_description": r[2],
                "winning_drive": r[3],
                "confidence": r[4],
                "eros_weight": r[5],
                "thanatos_weight": r[6],
                "weight_snapshot": json.loads(r[7]) if r[7] else {}
            }
            for r in rows
        ]
    
    def get_weight_history(self, drive_type: Optional[str] = None, limit: int = 100) -> list:
        """Retrieve drive weight history, optionally filtered by drive type"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if drive_type:
            cursor.execute("""
                SELECT id, timestamp, drive_type, weight, change_delta
                FROM drive_weight_history
                WHERE drive_type = ?
                ORDER BY id DESC
                LIMIT ?
            """, (drive_type, limit))
        else:
            cursor.execute("""
                SELECT id, timestamp, drive_type, weight, change_delta
                FROM drive_weight_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "timestamp": r[1],
                "drive_type": r[2],
                "weight": r[3],
                "change_delta": r[4]
            }
            for r in rows
        ]


def get_persistence_manager() -> PersistenceManager:
    """Get the singleton persistence manager instance"""
    return PersistenceManager()