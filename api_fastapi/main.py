"""
API IoT con FastAPI + MQTT + Grafana
Servidor completo para recepción de datos de ESP32 y visualización
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import db
from mqtt_client import mqtt_client


def _timestamp_to_epoch_ms(ts: Optional[str]) -> Optional[int]:
    """Convierte timestamp ISO/SQLite a milisegundos UNIX (compatible con Grafana Infinity)."""
    if ts is None or str(ts).strip() == "":
        return None
    raw = str(ts).strip()
    try:
        normalized = raw.replace("Z", "+00:00")
        if "T" not in normalized and " " in normalized:
            normalized = normalized.replace(" ", "T", 1)
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError, OSError):
        return None


# Codificación de estado para paneles Grafana (valor numérico + etiqueta en JSON separado)
_ESTADO_A_CODE = {
    "NORMAL": 0,
    "ALERTA_TEMP": 1,
    "ALERTA_LUZ": 2,
    "ALERTA_DOBLE": 3,
}


# ==================== MODELOS PYDANTIC ====================

class MetricData(BaseModel):
    """Modelo de datos de métrica"""
    id: Optional[int] = None
    device_id: str
    topic: str
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    luz: Optional[int] = None
    estado: Optional[str] = None
    timestamp: Optional[str] = None


class CurrentMetricsResponse(BaseModel):
    """Respuesta con métricas actuales"""
    device_id: Optional[str] = None
    topic: Optional[str] = None
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    luz: Optional[int] = None
    estado: Optional[str] = None
    timestamp: Optional[str] = None


class DeviceInfo(BaseModel):
    """Información de un dispositivo"""
    device_id: str
    total_readings: int
    last_seen: Optional[str] = None


class StatsResponse(BaseModel):
    """Respuesta con estadísticas"""
    total_readings: int
    total_devices: int
    first_reading: Optional[str] = None
    last_reading: Optional[str] = None
    avg_temp: Optional[float] = None
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    avg_hum: Optional[float] = None
    avg_luz: Optional[float] = None


class HealthResponse(BaseModel):
    """Respuesta de estado del servidor"""
    status: str
    timestamp: str
    mqtt_connected: bool
    db_records: int


# ==================== MODELOS GRAFANA ====================

class GrafanaTarget(BaseModel):
    """Target de consulta de Grafana"""
    target: str
    refId: Optional[str] = "A"
    type: Optional[str] = "timeseries"


class GrafanaTimeRange(BaseModel):
    """Rango de tiempo de Grafana"""
    model_config = {"populate_by_name": True}
    
    from_: str = Field(..., alias="from")
    to: str
    raw: Optional[Dict] = None


class GrafanaQueryRequest(BaseModel):
    """Request de consulta de Grafana"""
    panelId: Optional[int] = None
    range: GrafanaTimeRange
    interval: Optional[str] = None
    targets: List[GrafanaTarget]
    adhocFilters: Optional[List] = []


class GrafanaQueryResponse(BaseModel):
    """Respuesta de consulta de Grafana"""
    target: str
    datapoints: List[List[float]]


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Iniciando servidor IoT...")
    
    # Inicializar base de datos
    await db.initialize()
    
    # Conectar cliente MQTT en un thread separado
    mqtt_client.connect()
    
    print("✅ Servidor listo")
    print("📋 Documentación disponible en: http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    print("🛑 Cerrando servidor...")
    mqtt_client.disconnect()
    print("👋 Servidor detenido")


# ==================== APP FASTAPI ====================

app = FastAPI(
    title="API IoT con MQTT",
    description="""
    API REST para recepción de datos de sensores ESP32 vía MQTT.
    
    ## Características
    
    * 📡 **MQTT**: Recibe datos del ESP32 en tiempo real
    * 💾 **Base de datos**: Almacenamiento SQLite persistente
    * 📊 **Grafana**: Endpoints compatibles con SimpleJSON
    * 🌐 **WebSocket**: Comunicación en tiempo real
    * 📖 **Documentación**: Swagger UI automático
    
    ## Endpoints principales
    
    * `/api/health` - Estado del servidor
    * `/api/metrics/current` - Últimas métricas
    * `/api/metrics/history` - Historial de datos
    * `/api/devices` - Lista de dispositivos
    * `/api/grafana/*` - Endpoints para Grafana
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS para permitir acceso desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== ENDPOINTS GENERALES ====================

@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz con información básica"""
    return {
        "message": "API IoT con FastAPI",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Verificar estado del servidor"""
    count = await db.get_count()
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        mqtt_connected=mqtt_client.connected,
        db_records=count
    )


# ==================== ENDPOINTS DE MÉTRICAS ====================

@app.get(
    "/api/metrics/current",
    response_model=CurrentMetricsResponse,
    tags=["Métricas"]
)
async def get_current_metrics(device_id: Optional[str] = None):
    """
    Obtener las métricas más recientes.
    
    - **device_id**: Opcional, filtrar por dispositivo específico
    """
    metrics = await db.get_latest_metrics(device_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="No hay métricas disponibles")
    return CurrentMetricsResponse(**metrics)


@app.get(
    "/api/metrics/history",
    response_model=List[MetricData],
    tags=["Métricas"]
)
async def get_metrics_history(
    hours: int = Query(24, ge=1, le=168, description="Horas de historial (1-168)"),
    device_id: Optional[str] = None
):
    """
    Obtener historial de métricas.
    
    - **hours**: Cantidad de horas hacia atrás (default: 24, max: 168)
    - **device_id**: Opcional, filtrar por dispositivo
    """
    history = await db.get_metrics_history(hours, device_id)
    return [MetricData(**row) for row in history]


# ==================== ENDPOINTS DE DISPOSITIVOS ====================

@app.get(
    "/api/devices",
    response_model=List[DeviceInfo],
    tags=["Dispositivos"]
)
async def get_devices():
    """Obtener lista de dispositivos registrados"""
    devices = await db.get_devices()
    return [DeviceInfo(**device) for device in devices]


# ==================== ENDPOINTS DE ESTADÍSTICAS ====================

@app.get(
    "/api/stats",
    response_model=StatsResponse,
    tags=["Estadísticas"]
)
async def get_stats():
    """Obtener estadísticas resumidas de las últimas 24 horas"""
    stats = await db.get_stats()
    return StatsResponse(**stats)


# ==================== ENDPOINTS GRAFANA (SimpleJSON) ====================

@app.get(
    "/api/grafana/search",
    response_model=List[str],
    tags=["Grafana"]
)
async def grafana_search():
    """
    Endpoint de búsqueda de métricas para Grafana SimpleJSON.
    
    Devuelve la lista de métricas disponibles:
    - temperatura
    - humedad
    - luz
    - estado
    """
    return ["temperatura", "humedad", "luz", "estado"]


@app.post(
    "/api/grafana/query",
    response_model=List[GrafanaQueryResponse],
    tags=["Grafana"]
)
async def grafana_query(request: GrafanaQueryRequest):
    """
    Endpoint de consulta de datos para Grafana SimpleJSON.
    
    Recibe un rango de tiempo y lista de métricas solicitadas,
    devuelve los datos en formato que Grafana puede graficar.
    """
    results = []
    
    for target in request.targets:
        metric = target.target
        
        try:
            data = await db.get_metric_series(
                metric,
                request.range.from_,
                request.range.to
            )
            
            # Convertir a formato de puntos de datos de Grafana
            # [valor, timestamp_en_ms]
            datapoints = []
            for row in data:
                if row.get('value') is not None:
                    ts = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                    ts_ms = int(ts.timestamp() * 1000)
                    datapoints.append([row['value'], ts_ms])
            
            results.append(GrafanaQueryResponse(
                target=metric,
                datapoints=datapoints
            ))
            
        except ValueError as e:
            # Métrica no válida
            print(f"⚠️ Métrica no válida: {metric}")
            continue
        except Exception as e:
            print(f"❌ Error consultando {metric}: {e}")
            continue
    
    return results


@app.post("/api/grafana/annotations", tags=["Grafana"])
async def grafana_annotations():
    """
    Endpoint de anotaciones para Grafana (no implementado).
    
    Devuelve lista vacía para compatibilidad.
    """
    return []


@app.api_route("/api/grafana/timeseries", methods=["GET", "POST"], tags=["Grafana"])
async def grafana_timeseries(
    metric: str = Query(
        "temperatura",
        description="Métrica: temperatura, humedad, luz, estado (alertas como texto + código)",
    ),
    limit: int = Query(1000, ge=1, le=5000, description="Cantidad máxima de registros"),
):
    """
    Endpoint para Grafana Infinity - TODOS los datos con formato correcto.
    Devuelve datos en formato compatible con Time Series de Grafana.
    Para metric=estado incluye campo texto \"estado\" (State timeline) y \"value\" 0-3 (series numéricas).
    """
    valid_metrics = ["temperatura", "humedad", "luz", "estado"]
    
    if metric not in valid_metrics:
        return []
    
    try:
        # Obtener todos los datos (sin filtro de tiempo)
        metrics = await db.get_all_metrics(limit=limit)
        
        # Formatear para Grafana Infinity: array de objetos con campos específicos
        result = []
        for m in metrics:
            ts_ms = _timestamp_to_epoch_ms(m.get("timestamp"))
            if ts_ms is None:
                continue
            if metric == "estado":
                est = m.get("estado")
                if est is None or str(est).strip() == "":
                    continue
                est_key = str(est).strip()
                code = _ESTADO_A_CODE.get(est_key)
                if code is None:
                    continue
                result.append({
                    "time": ts_ms,
                    "Time": ts_ms,
                    "metric": metric,
                    "estado": est_key,
                    "value": float(code),
                })
                continue
            val = m.get(metric)
            if val is None:
                continue
            # Campos "time" y "Time": Infinity / Grafana a veces solo detectan uno u otro
            # Tipo de columna en el panel: Timestamp (UNIX ms). Evitar JSONata vacío: usar parser Simple.
            result.append({
                "time": ts_ms,
                "Time": ts_ms,
                "metric": metric,
                "value": float(val)
            })
        
        return result
        
    except Exception as e:
        print(f"❌ Error en timeseries: {e}")
        return []


@app.api_route("/api/grafana/data", methods=["GET", "POST"], tags=["Grafana"])
async def grafana_data(
    metric: str = Query(
        "temperatura",
        description="Métrica: temperatura, humedad, luz, estado",
    ),
    hours: int = Query(24, ge=1, le=168, description="Horas de historial"),
):
    """
    Endpoint simple para Grafana Infinity - compatible con formato JSON/Table.
    """
    valid_metrics = ["temperatura", "humedad", "luz", "estado"]
    
    if metric not in valid_metrics:
        return []
    
    try:
        # Obtener datos de las últimas N horas (timestamps ya vienen en ISO 8601 UTC)
        metrics = await db.get_metrics_history(hours)
        
        # Formatear para Infinity - devolver array directo
        result = []
        for m in metrics:
            ts_ms = _timestamp_to_epoch_ms(m.get("timestamp"))
            if ts_ms is None:
                continue
            if metric == "estado":
                est = m.get("estado")
                if est is None or str(est).strip() == "":
                    continue
                est_key = str(est).strip()
                code = _ESTADO_A_CODE.get(est_key)
                if code is None:
                    continue
                result.append({
                    "time": ts_ms,
                    "Time": ts_ms,
                    "metric": metric,
                    "estado": est_key,
                    "value": float(code),
                })
                continue
            val = m.get(metric)
            if val is None:
                continue
            result.append({
                "time": ts_ms,
                "Time": ts_ms,
                "value": float(val),
                "metric": metric
            })
        
        return result
        
    except Exception as e:
        print(f"❌ Error en grafana_data: {e}")
        return []


# ==================== COMANDOS MQTT ====================

@app.post("/api/commands/{device_id}", tags=["Comandos"])
async def send_command(device_id: str, command: str):
    """
    Enviar comando a un dispositivo vía MQTT.
    
    - **device_id**: ID del dispositivo destino
    - **command**: Comando a enviar (reset, led_on, led_off)
    """
    topic = f"comandos/{device_id}"
    mqtt_client.publish(topic, command)
    return {"message": f"Comando '{command}' enviado a {device_id}", "topic": topic}


# ==================== INICIAR SERVIDOR ====================

if __name__ == "__main__":
    import uvicorn
    
    print("="*60)
    print("               🚀 API IoT con FastAPI")
    print("="*60)
    print("  📡 MQTT Broker:  mqtt://localhost:1883")
    print("  🌐 API:          http://localhost:8000")
    print("  📖 Docs:         http://localhost:8000/docs")
    print("  🔍 Redoc:        http://localhost:8000/redoc")
    print("="*60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
