# 🐍 API IoT con FastAPI + MQTT + Grafana

API REST moderna construida con **FastAPI** para recepción de datos ESP32 vía MQTT, almacenamiento en SQLite y visualización en Grafana.

## ✨ Ventajas de FastAPI

- 🚀 **Alto rendimiento** - Async/await nativo
- 📖 **Documentación automática** - Swagger UI en `/docs`
- 🔍 **Validación automática** - Pydantic models
- 🎯 **Type hints** - Código más claro y mantenible
- 🧪 **Fácil testing** - Cliente integrado

## 📁 Estructura

```
api_fastapi/
├── main.py              # FastAPI - endpoints principales
├── database.py          # SQLite async con aiosqlite
├── mqtt_client.py       # Cliente MQTT (paho-mqtt)
├── requirements.txt   # Dependencias Python
├── mosquitto.conf       # Configuración del broker MQTT
├── grafana-dashboard.json  # Dashboard preconfigurado
└── README.md            # Este archivo
```

## 🚀 Instalación Rápida

### 1. Instalar Mosquitto (Broker MQTT)

**Windows:**
```powershell
# Descargar de: https://mosquitto.org/download/
# Instalar y ejecutar:
"C:\Program Files\mosquitto\mosquitto.exe" -c mosquitto.conf -v
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

### 2. Crear entorno virtual Python

```bash
cd api_fastapi

# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Iniciar el servidor

```bash
# Desarrollo con auto-reload
python main.py

# O con uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor iniciará:
- 🌐 **API**: http://localhost:8000
- 📖 **Swagger UI**: http://localhost:8000/docs
- 🔍 **ReDoc**: http://localhost:8000/redoc

### 5. Configurar ESP32

Usa el archivo `segundaversion_local.ino` y cambia la IP:

```cpp
const char* mqtt_server = "192.168.1.100";  // IP de tu computadora
```

Descubre tu IP:
```bash
# Windows
ipconfig

# Linux/Mac
ip addr show
```

### 6. Configurar Grafana

#### Instalar plugin SimpleJSON
```bash
grafana-cli plugins install grafana-simple-json-datasource
# Reiniciar Grafana después
```

#### Agregar Data Source
1. Ir a **Configuration > Data Sources**
2. Click **Add data source**
3. Buscar "SimpleJSON"
4. Configurar:
   - **URL**: `http://localhost:8000/api/grafana`
   - **Access**: Server (default)
5. Click **Save & Test**

#### Importar Dashboard
1. Ir a **Dashboards > Import**
2. Subir archivo `grafana-dashboard.json`

## 📡 Endpoints API

### Swagger UI
Visita `http://localhost:8000/docs` para probar todos los endpoints interactivamente.

### Endpoints Generales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Info del API |
| `/api/health` | GET | Estado del servidor |
| `/api/metrics/current` | GET | Últimas métricas |
| `/api/metrics/history?hours=24` | GET | Historial |
| `/api/devices` | GET | Lista dispositivos |
| `/api/stats` | GET | Estadísticas 24h |
| `/api/commands/{device_id}` | POST | Enviar comando MQTT |

### Endpoints Grafana (SimpleJSON)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/grafana/search` | GET | Métricas disponibles |
| `/api/grafana/query` | POST | Datos para gráficos |
| `/api/grafana/annotations` | POST | Anotaciones |

## 🔧 Ejemplos de uso

### Verificar estado
```bash
curl http://localhost:8000/api/health
```

### Obtener métricas actuales
```bash
curl http://localhost:8000/api/metrics/current
```

### Obtener historial (últimas 6 horas)
```bash
curl "http://localhost:8000/api/metrics/history?hours=6"
```

### Enviar comando al ESP32
```bash
curl -X POST "http://localhost:8000/api/commands/ESP32_Sensor_01?command=reset"
```

### Consulta Grafana (para pruebas)
```bash
curl -X POST http://localhost:8000/api/grafana/query \
  -H "Content-Type: application/json" \
  -d '{
    "range": {"from": "2024-01-01T00:00:00.000Z", "to": "2024-12-31T23:59:59.000Z"},
    "targets": [{"target": "temperatura"}]
  }'
```

## 📊 Dashboard incluido

El archivo `grafana-dashboard.json` incluye:
- 🌡️ **Gauge de Temperatura** - con umbrales de alerta
- 💧 **Gauge de Humedad**
- ☀️ **Gauge de Luz** - con indicadores de nivel bajo
- 🚦 **Estado del Sistema** - NORMAL/ALERTA
- 📈 **Gráficos de historial** - Temperatura, Humedad y Luz

## 🗄️ Esquema de Base de Datos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | PK autoincremental |
| device_id | TEXT | ID del ESP32 |
| topic | TEXT | Tópico MQTT |
| temperatura | REAL | °C |
| humedad | REAL | % |
| luz | INTEGER | 0-100% |
| estado | TEXT | NORMAL/ALERTA_* |
| timestamp | DATETIME | ISO 8601 |

## 🔍 Depuración

### Ver logs del servidor
```bash
# En otra terminal, ver mensajes MQTT
mosquitto_sub -h localhost -t "sensores/#" -v

# O con el cliente incluido en Mosquitto para Windows
"C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -t "sensores/#" -v
```

### Ver base de datos directamente
```bash
# Instalar cliente SQLite
pip install sqlite-utils

# Consultar
sqlite-utils iot_data.db "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 5"
```

### Probar MQTT desde línea de comandos
```bash
# Publicar mensaje de prueba
mosquitto_pub -h localhost -t "sensores/datos" -m '{"temperatura": 25.5, "humedad": 60}'

# Windows
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t "sensores/datos" -m "{\"temperatura\": 25.5}"
```

## 🐛 Solución de problemas

### Error: "No module named 'fastapi'"
```bash
# Asegúrate de activar el entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstalar
pip install -r requirements.txt
```

### Error: "Connection refused" MQTT
```bash
# Verificar que Mosquitto está corriendo
# Windows - ver en Services
services.msc

# Linux
sudo systemctl status mosquitto
sudo systemctl restart mosquitto
```

### El ESP32 no conecta
1. Verificar IP del servidor (`ipconfig`)
2. Verificar firewall - puerto 1883 debe estar abierto
3. Verificar que ESP32 y PC están en misma red WiFi
4. Probar con cliente MQTT en PC primero

### Grafana no muestra datos
1. Verificar data source: `curl http://localhost:8000/api/grafana/search`
2. Verificar datos en DB: `curl http://localhost:8000/api/metrics/current`
3. Revisar logs de FastAPI en consola

## 📚 Recursos

- **FastAPI**: https://fastapi.tiangolo.com
- **Pydantic**: https://docs.pydantic.dev
- **Mosquitto**: https://mosquitto.org/documentation/
- **Grafana SimpleJSON**: https://grafana.com/grafana/plugins/grafana-simple-json-datasource

## 📝 Diferencias con versión Node.js

| Característica | FastAPI (Python) | Node.js |
|----------------|-----------------|---------|
| Broker MQTT | Mosquitto externo | Aedes integrado |
| Documentación | Swagger automático | Manual |
| Código | Más legible | Más verboso |
| Async | Nativo Python | Callbacks |
| Validación | Pydantic automático | Manual |
| Instalación | Python + Mosquitto | Solo Node.js |

## 🎓 Para tu clase

FastAPI es excelente para aprender porque:
1. **Código limpio** - Python es más legible
2. **Type hints** - Ayuda a entender los tipos de datos
3. **Docs automáticas** - Puedes probar la API desde el navegador
4. **Estándar académico** - Python es más común en universidades

---

Hecho con ❤️ para la asignatura Complementaria II (IoT y Domótica)
