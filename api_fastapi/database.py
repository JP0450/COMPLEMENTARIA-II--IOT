"""
Módulo de base de datos SQLite para almacenar métricas IoT
"""

import aiosqlite
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

DB_PATH = Path(__file__).parent / "iot_data.db"


def _normalize_incoming_timestamp(ts: Any) -> Optional[str]:
    """
    Convierte timestamp del ESP/simulador a texto UTC 'YYYY-MM-DD HH:MM:SS' para SQLite.
    Acepta: ms Unix (int), seg Unix (int), o cadena ISO.
    """
    if ts is None:
        return None
    if isinstance(ts, bool):
        return None
    try:
        if isinstance(ts, (int, float)):
            x = float(ts)
            if x <= 0:
                return None
            if x > 1e12:
                x = x / 1000.0
            dt = datetime.fromtimestamp(x, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(ts, str):
            s = ts.strip()
            if not s:
                return None
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return None
    return None


# Expresión SQL: columna timestamp puede ser TEXT (correcto), o entero s/ms (legado ESP/simulador).
_TS_CANONICAL = """(
    CASE
        WHEN typeof(timestamp) = 'integer' AND CAST(timestamp AS REAL) > 1e12
            THEN datetime(CAST(timestamp AS INTEGER) / 1000, 'unixepoch')
        WHEN typeof(timestamp) = 'integer' AND CAST(timestamp AS REAL) > 1e9
            THEN datetime(CAST(timestamp AS INTEGER), 'unixepoch')
        ELSE timestamp
    END
)"""


def _ts_iso_select(alias: str = "timestamp") -> str:
    return f"strftime('%Y-%m-%dT%H:%M:%SZ', {_TS_CANONICAL}) AS {alias}"


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
        """Insertar una nueva métrica.
        
        Si el ESP32 envía 'timestamp' en el payload, se usa ese valor.
        Si no, la base de datos usa CURRENT_TIMESTAMP (comportamiento por defecto del manual).
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Verificar si el ESP32 envió su propio timestamp
            esp_timestamp = data.get('timestamp')
            normalized_ts = _normalize_incoming_timestamp(esp_timestamp)
            
            if normalized_ts:
                # Timestamp explícito ya normalizado a DATETIME SQLite (UTC)
                cursor = await db.execute("""
                    INSERT INTO metrics (device_id, topic, temperatura, humedad, luz, estado, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('device_id', 'unknown'),
                    data.get('topic', 'unknown'),
                    data.get('temperatura'),
                    data.get('humedad'),
                    data.get('luz'),
                    data.get('estado'),
                    normalized_ts
                ))
            else:
                # Comportamiento según manual: usar CURRENT_TIMESTAMP del servidor
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
            
            # Usar UTC para ser consistente con CURRENT_TIMESTAMP de SQLite
            # Formato: 'YYYY-MM-DD HH:MM:SS' (igual que SQLite CURRENT_TIMESTAMP)
            since = (datetime.utcnow() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            if device_id:
                cursor = await db.execute(f"""
                    SELECT 
                        id, device_id, topic, temperatura, humedad, luz, estado,
                        {_ts_iso_select()}
                    FROM metrics 
                    WHERE {_TS_CANONICAL} >= ? AND device_id = ?
                    ORDER BY {_TS_CANONICAL} ASC
                """, (since, device_id))
            else:
                cursor = await db.execute(f"""
                    SELECT 
                        id, device_id, topic, temperatura, humedad, luz, estado,
                        {_ts_iso_select()}
                    FROM metrics 
                    WHERE {_TS_CANONICAL} >= ?
                    ORDER BY {_TS_CANONICAL} ASC
                """, (since,))
            
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
                cursor = await db.execute(f"""
                    SELECT 
                        id, device_id, topic, temperatura, humedad, luz, estado,
                        {_ts_iso_select()}
                    FROM metrics 
                    WHERE device_id = ?
                    ORDER BY {_TS_CANONICAL} ASC
                    LIMIT ?
                """, (device_id, limit))
            else:
                cursor = await db.execute(f"""
                    SELECT 
                        id, device_id, topic, temperatura, humedad, luz, estado,
                        {_ts_iso_select()}
                    FROM metrics 
                    ORDER BY {_TS_CANONICAL} ASC
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
                SELECT {metric} as value, 
                       {_ts_iso_select()}
                FROM metrics
                WHERE {metric} IS NOT NULL
                    AND datetime({_TS_CANONICAL}) >= datetime(?)
                    AND datetime({_TS_CANONICAL}) <= datetime(?)
                ORDER BY datetime({_TS_CANONICAL}) ASC
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
            
            # Usar UTC para ser consistente con CURRENT_TIMESTAMP de SQLite
            since = (datetime.utcnow() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            
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
