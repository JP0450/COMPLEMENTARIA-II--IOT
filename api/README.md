# 🤖 API IoT con MQTT y Grafana

Sistema completo para recibir datos de ESP32 vía MQTT, almacenarlos en SQLite y visualizarlos en Grafana.

## 📁 Estructura del Proyecto

```
api/
├── server.js           # Servidor principal (MQTT Broker + API REST)
├── database.js         # Módulo de base de datos SQLite
├── package.json        # Dependencias Node.js
├── grafana-dashboard.json  # Configuración del dashboard
└── README.md           # Este archivo

segundaversion.ino      # Código original (ThingSpeak)
segundaversion_local.ino # Código para broker local
```

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
cd api
npm install
```

### 2. Iniciar el servidor

```bash
npm start
```

El servidor iniciará:
- 📡 MQTT Broker TCP en puerto `1883`
- 📡 MQTT Broker WebSocket en puerto `8883`
- 🌐 API REST en puerto `3000`

### 3. Configurar el ESP32

Edita `segundaversion_local.ino` y cambia la IP del broker:

```cpp
const char* mqtt_server = "192.168.1.100";  // IP de tu computadora
```

Sube el código al ESP32.

### 4. Configurar Grafana

#### Instalar plugin SimpleJSON

```bash
grafana-cli plugins install grafana-simple-json-datasource
```

#### Agregar Data Source

1. Ir a **Configuration > Data Sources**
2. Click **Add data source**
3. Buscar "SimpleJSON"
4. Configurar:
   - **URL**: `http://localhost:3000/api/grafana`
   - **Access**: Server (default)

#### Importar Dashboard

1. Ir a **Dashboards > Import**
2. Subir archivo `grafana-dashboard.json`

## 📡 Endpoints API

### Endpoints Generales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/health` | GET | Estado del servidor |
| `/api/metrics/current` | GET | Últimas métricas |
| `/api/metrics/history?hours=24` | GET | Historial de métricas |
| `/api/devices` | GET | Lista de dispositivos |
| `/api/stats` | GET | Estadísticas resumidas |

### Endpoints Grafana (SimpleJSON)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/grafana/search` | GET | Lista de métricas disponibles |
| `/api/grafana/query` | POST | Consultar datos para gráficos |
| `/api/grafana/annotations` | POST | Anotaciones (vacío) |

### Ejemplos de uso

```bash
# Ver estado del servidor
curl http://localhost:3000/api/health

# Obtener últimas métricas
curl http://localhost:3000/api/metrics/current

# Obtener historial de últimas 24 horas
curl http://localhost:3000/api/metrics/history?hours=24

# Ver dispositivos conectados
curl http://localhost:3000/api/devices
```

## 📊 Métricas Disponibles

- `temperatura` - Temperatura en °C
- `humedad` - Humedad relativa en %
- `luz` - Nivel de iluminación en %
- `estado` - Estado del sistema (NORMAL, ALERTA_TEMP, ALERTA_LUZ, ALERTA_DOBLE)

## 🔧 Configuración del ESP32

### Conexión WiFi

```cpp
const char* ssid = "REDMI Note 15";
const char* password = "emilia05";
```

### Conexión MQTT

```cpp
const char* mqtt_server = "192.168.1.100";  // IP del servidor
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP32_Sensor_01";
```

### Topics MQTT

- `sensores/datos` - Datos de sensores en formato JSON
- `sensores/estado` - Estado de conexión del dispositivo
- `sensores/alertas` - Alertas del sistema
- `comandos/esp32` - Comandos desde el servidor (opcional)

### Formato de Mensajes JSON

```json
{
  "dispositivo": "ESP32_Sensor_01",
  "temperatura": 25.5,
  "humedad": 60.0,
  "luz": 85,
  "estado": "NORMAL",
  "timestamp": 123456789
}
```

## 🗄️ Base de Datos

La base de datos SQLite (`iot_data.db`) almacena:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | ID autoincremental |
| device_id | TEXT | ID del dispositivo |
| topic | TEXT | Topic MQTT |
| temperatura | REAL | Valor de temperatura |
| humedad | REAL | Valor de humedad |
| luz | INTEGER | Valor de luz (0-100) |
| estado | TEXT | Estado del sistema |
| timestamp | DATETIME | Fecha y hora del registro |

## 🌐 WebSocket en Tiempo Real

El servidor expone WebSocket en `ws://localhost:3000` para dashboards en tiempo real.

Mensajes broadcast cuando llegan nuevos datos:

```json
{
  "type": "new_data",
  "device": "ESP32_Sensor_01",
  "topic": "sensores/datos",
  "data": { /* datos del sensor */ },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## 🐛 Solución de Problemas

### El ESP32 no se conecta al broker MQTT

1. Verificar que la IP del servidor sea correcta:
   ```bash
   # En Windows
   ipconfig
   
   # Buscar la IP de tu adaptador WiFi
   ```

2. Verificar que el puerto 1883 esté abierto en el firewall.

3. Verificar que el ESP32 y la computadora estén en la misma red WiFi.

### Grafana no muestra datos

1. Verificar que el data source esté configurado correctamente:
   ```bash
   curl http://localhost:3000/api/grafana/search
   ```

2. Verificar que hay datos en la base de datos:
   ```bash
   curl http://localhost:3000/api/metrics/current
   ```

3. Revisar los logs del servidor Node.js.

### Error "Cannot find module"

```bash
cd api
rm -rf node_modules
npm install
```

## 📚 Tecnologías Utilizadas

- **Node.js** - Runtime de JavaScript
- **Express** - Framework web
- **Aedes** - Broker MQTT
- **SQLite3** - Base de datos local
- **WebSocket** - Comunicación en tiempo real

## 📝 Licencia

Proyecto académico para la asignatura Complementaria II (IoT y Domótica).

---

## 🔄 Diferencias entre versiones del ESP32

| Característica | segundaversion.ino | segundaversion_local.ino |
|----------------|-------------------|-------------------------|
| Broker MQTT | ThingSpeak | Broker local propio |
| Formato datos | Formato ThingSpeak | JSON |
| Autenticación | Sí (API Key) | No (opcional) |
| Tópicos | Único por canal | Múltiples tópicos |
| Comandos remotos | No | Sí (suscripción) |
| Dashboard | ThingSpeak | Grafana propio |
