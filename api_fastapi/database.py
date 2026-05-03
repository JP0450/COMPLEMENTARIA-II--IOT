"""
Módulo de base de datos SQLite para almacenar métricas IoT
"""

import aiosqlite
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

DB_PATH = Path(__file__).parent / "iot_data.db"


class Database:
    """Gestión de base de datos SQLite para métricas IoT"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    async def initialize(self):
        """Inicializar la base de datos y crear tablas"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    temperatura REAL,
                    humedad REAL,
                    luz INTEGER,
                    estado TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear índices para mejorar rendimiento
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_device 
                ON metrics(device_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON metrics(timestamp)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_topic 
                ON metrics(topic)
            """)
            
            await db.commit()
            print("💾 Base de datos inicializada")
    
    async def insert_metric(self, data: Dict[str, Any]) -> int:
        """Insertar una nueva métrica"""
        async with aiosqlite.connect(self.db_path) as db:
            # La base de datos usa CURRENT_TIMESTAMP automáticamente
            cursor = await db.execute("""
                INSERT INTO metrics (device_id, topic, temperatura, humedad, luz, estado)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.get('device_id', 'unknown'),
                data.get('topic', 'unknown'),
                data.get('temperatura'),
                data.get('humedad'),
                data.get('luz'),
                data.get('estado')
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def get_latest_metrics(self, device_id: Optional[str] = None) -> Optional[Dict]:
        """Obtener las métricas más recientes"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if device_id:
                cursor = await db.execute("""
                    SELECT * FROM metrics 
                    WHERE device_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (device_id,))
            else:
                cursor = await db.execute("""
                    SELECT * FROM metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
            
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_metrics_history(
        self, 
        hours: int = 24, 
        device_id: Optional[str] = None
    ) -> List[Dict]:
        """Obtener historial de métricas"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            since = datetime.now() - timedelta(hours=hours)
            
            if device_id:
                cursor = await db.execute("""
                    SELECT * FROM metrics 
                    WHERE timestamp >= ? AND device_id = ?
                    ORDER BY timestamp ASC
                """, (since.isoformat(), device_id))
            else:
                cursor = await db.execute("""
                    SELECT * FROM metrics 
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                """, (since.isoformat(),))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_all_metrics(
        self, 
        limit: int = 1000,
        device_id: Optional[str] = None
    ) -> List[Dict]:
        """Obtener TODAS las métricas sin filtro de tiempo (para Grafana)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Usar strftime para convertir timestamp a formato ISO 8601
            if device_id:
                cursor = await db.execute("""
                    SELECT 
                        id, device_id, topic, temperatura, humedad, luz, estado,
                        strftime('%Y-%m-%dT%H:%M:%SZ', timestamp) as timestamp
                    FROM metrics 
                    WHERE device_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (device_id, limit))
            else:
                cursor = await db.execute("""
                    SELECT 
                        id, device_id, topic, temperatura, humedad, luz, estado,
                        strftime('%Y-%m-%dT%H:%M:%SZ', timestamp) as timestamp
                    FROM metrics 
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (limit,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_metric_series(
        self,
        metric: str,
        date_from: str,
        date_to: str
    ) -> List[Dict]:
        """Obtener serie temporal de una métrica específica (para Grafana)"""
        valid_metrics = ['temperatura', 'humedad', 'luz']
        
        if metric not in valid_metrics:
            raise ValueError(f"Métrica no válida. Opciones: {valid_metrics}")
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(f"""
                SELECT {metric} as value, timestamp
                FROM metrics
                WHERE {metric} IS NOT NULL
                    AND timestamp >= ?
                    AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (date_from, date_to))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_devices(self) -> List[Dict]:
        """Obtener lista de dispositivos"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT 
                    device_id,
                    COUNT(*) as total_readings,
                    MAX(timestamp) as last_seen
                FROM metrics
                GROUP BY device_id
                ORDER BY last_seen DESC
            """)
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_stats(self) -> Dict:
        """Obtener estadísticas resumidas"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            since = (datetime.now() - timedelta(hours=24)).isoformat()
            
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_readings,
                    COUNT(DISTINCT device_id) as total_devices,
                    MIN(timestamp) as first_reading,
                    MAX(timestamp) as last_reading,
                    AVG(temperatura) as avg_temp,
                    MIN(temperatura) as min_temp,
                    MAX(temperatura) as max_temp,
                    AVG(humedad) as avg_hum,
                    AVG(luz) as avg_luz
                FROM metrics
                WHERE timestamp >= ?
            """, (since,))
            
            row = await cursor.fetchone()
            return dict(row) if row else {}
    
    async def get_count(self) -> int:
        """Obtener cantidad total de registros"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM metrics")
            row = await cursor.fetchone()
            return row[0] if row else 0


# Instancia global de la base de datos
db = Database()
