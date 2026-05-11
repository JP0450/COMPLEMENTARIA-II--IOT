# Manual del Sistema IoT - ESP32 + MQTT + FastAPI

## 1. Descripción General del Sistema

Este es un sistema IoT completo que consta de tres componentes principales:

- **ESP32** (hardware): Lee sensores y envía datos
- **Broker MQTT** (Mosquitto): Transporte de mensajes
- **API FastAPI** (servidor): Recibe, procesa y almacena datos

El sistema monitorea **temperatura**, **humedad** y **luz** en tiempo real, detecta condiciones anormales y genera alertas.

---

## 📋 MANUAL DE USUARIO - Cómo ejecutar en tu máquina

Esta guía te ayudará a configurar y ejecutar el sistema IoT completo en tu computadora desde cero.

### 🔧 Prerrequisitos

#### Hardware necesario:
- **ESP32** (cualquier modelo con WiFi)
- **Sensores**:
  - DHT22 (temperatura y humedad)
  - Fotoresistor/LDR (luz)
  - LED (indicador)
  - Botón pulsador
- **Computadora** con Windows/Linux/Mac

#### Software necesario:
- **Arduino IDE** (para programar el ESP32)
- **Python 3.8+** (para la API)
- **Mosquitto MQTT Broker**
- **Git** (opcional, para clonar repositorio)

---

### 🚀 PASO 1: Preparar el entorno de desarrollo

#### 1.1 Instalar Python
1. Ve a https://python.org
2. Descarga Python 3.8 o superior
3. Durante instalación, marca "Add Python to PATH"
4. Verifica instalación:
```bash
python --version
pip --version
```

#### 1.2 Instalar Arduino IDE
1. Ve a https://arduino.cc
2. Descarga e instala Arduino IDE
3. Instala el soporte para ESP32:
   - Abre Arduino IDE
   - Ve a **Archivo > Preferencias**
   - En "Gestor de URLs adicionales de tarjetas", agrega:
     ```
     https://dl.espressif.com/dl/package_esp32_index.json
     ```
   - Ve a **Herramientas > Placa > Gestor de tarjetas**
   - Busca "esp32" e instala "ESP32 by Espressif Systems"

#### 1.3 Instalar Mosquitto MQTT Broker

**Windows:**
1. Ve a https://mosquitto.org/download/
2. Descarga el instalador de Windows
3. Instala Mosquitto
4. Copia el archivo `mosquitto_local.conf` a `C:\Program Files\mosquitto\`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
```

---

### 📁 PASO 2: Obtener los archivos del proyecto

#### Opción A: Descargar archivos
1. Crea una carpeta en tu escritorio: `IoT_Proyecto`
2. Descarga todos los archivos de este proyecto y colócalos en la carpeta

#### Opción B: Usar Git (recomendado)
```bash
cd Desktop
git clone [URL_DEL_REPOSITORIO] IoT_Proyecto
cd IoT_Proyecto
```

La estructura final debe ser:
```
IoT_Proyecto/
├── MANUAL_DEL_SISTEMA.md
├── segundaversion_local.ino
└── api_fastapi/
    ├── main.py
    ├── database.py
    ├── mqtt_client.py
    ├── requirements.txt
    ├── simulador.py
    ├── mosquitto_local.conf
    ├── mosquitto.conf
    ├── grafana-dashboard.json
    └── README.md
```

---

### 🌐 PASO 3: Configurar la API FastAPI

1. **Abrir terminal/cmd en la carpeta del proyecto:**
```bash
cd Desktop/IoT_Proyecto/api_fastapi
```

2. **Crear entorno virtual:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Verificar instalación:**
```bash
python -c "import fastapi, uvicorn, paho.mqtt, aiosqlite; print('✅ Todas las dependencias instaladas')"
```

---

### 📡 PASO 4: Iniciar el Broker MQTT

**Windows:**
1. Abrir CMD como administrador
2. Ir a la carpeta de Mosquitto:
```bash
cd "C:\Program Files\mosquitto"
```
3. Iniciar Mosquitto con configuración local:
```bash
mosquitto -c "C:\Users\[TU_USUARIO]\Desktop\IoT_Proyecto\api_fastapi\mosquitto_local.conf" -v
```

**Linux:**
```bash
cd Desktop/IoT_Proyecto/api_fastapi
mosquitto -c mosquitto_local.conf -v
```

Deberías ver algo como:
```
1666612800: mosquitto version 2.0.15 starting
1666612800: Config loaded from mosquitto_local.conf
1666612800: Opening ipv4 listen socket on port 1883.
1666612800: Opening ipv6 listen socket on port 1883.
```

**Importante:** Mantén esta terminal abierta. El broker debe estar corriendo siempre.

---

### 🚀 PASO 5: Iniciar la API FastAPI

1. **Abrir nueva terminal** en la carpeta del proyecto:
```bash
cd Desktop/IoT_Proyecto/api_fastapi
```

2. **Activar entorno virtual:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Iniciar el servidor:**
```bash
python main.py
```

Deberías ver:
```
🚀 Iniciando servidor IoT...
💾 Base de datos inicializada
🔌 Conectando a MQTT (localhost:1883)...
✅ Conectado al broker MQTT
📡 Suscrito a: ['sensores/datos', 'sensores/estado', 'sensores/alertas']
✅ Servidor listo
📋 Documentación disponible en: http://localhost:8000/docs
==================================================
               🚀 API IoT con FastAPI
==================================================
  📡 MQTT Broker:  mqtt://localhost:1883
  🌐 API:          http://localhost:8000
  📖 Docs:         http://localhost:8000/docs
  🔍 Redoc:        http://localhost:8000/redoc
==================================================
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Importante:** Mantén esta terminal abierta también.

---

### 🔌 PASO 6: Configurar y programar el ESP32

#### 6.1 Conectar el hardware
Conecta los sensores al ESP32 según la tabla:

| Componente | Pin GPIO |
|------------|----------|
| DHT22 | 4 |
| LDR | 34 |
| LED | 2 |
| Botón | 15 |

#### 6.2 Configurar el código
1. Abre `segundaversion_local.ino` en Arduino IDE
2. **Cambia la IP del broker:**
   - Busca la línea: `const char* mqtt_server = "192.168.56.1";`
   - Cámbiala por la IP de tu computadora
   - Para encontrar tu IP:
     ```bash
     # Windows
     ipconfig
     
     # Linux/Mac
     ip addr show
     ```
     Busca la IP de tu red local (ej: 192.168.1.100)

3. **Cambia el WiFi si es necesario:**
   - Busca: `const char* ssid = "INTELRED_FLIA_PEREZ";`
   - Cámbialo por el nombre de tu red WiFi
   - Busca: `const char* password = "70978983";`
   - Cámbialo por la contraseña de tu WiFi

#### 6.3 Subir el código al ESP32
1. Conecta el ESP32 por USB
2. En Arduino IDE:
   - **Herramientas > Placa > ESP32 Dev Module**
   - **Herramientas > Puerto > [puerto del ESP32]**
3. **Compilar y subir** (botón →)
4. Abre el **Monitor Serie** (Herramientas > Monitor Serie)
5. Configura **115200 baudios**

Deberías ver logs como:
```
=======================================
Sistema IoT MQTT -> Broker Local
Modo: Multitarea + Maquina de Estados + JSON
=======================================
Broker MQTT: 192.168.1.100:1883
✅ WiFi conectado
📡 IP del ESP32: 192.168.1.150
✅ Conectado al broker
Suscrito a: comandos/esp32
```

---

### 🧪 PASO 7: Probar el sistema

#### 7.1 Verificar que todo funciona
1. **Abrir navegador** en http://localhost:8000/docs
2. **Probar endpoint de health:**
   - Click en `/api/health` > Try it out > Execute
   - Deberías ver estado "ok" y mqtt_connected: true

3. **Ver lecturas actuales:**
   - Click en `/api/metrics/current` > Execute
   - Deberías ver datos del ESP32

#### 7.2 Usar el simulador (sin hardware)
Si no tienes ESP32, puedes probar con el simulador:
```bash
cd Desktop/IoT_Proyecto/api_fastapi
python simulador.py
```

Esto enviará datos ficticios cada 5 segundos.

#### 7.3 Probar comandos al ESP32
Desde Swagger UI:
- `/api/commands/{device_id}` > Try it out
- device_id: `ESP32_Sensor_01`
- command: `reset` o `led_on` o `led_off`

---

### 📊 PASO 8: Configurar Grafana (opcional)

#### 8.1 Instalar Grafana
1. Ve a https://grafana.com/grafana/download
2. Descarga e instala Grafana
3. Inicia Grafana (suele ser http://localhost:3000)
4. Usuario/contraseña por defecto: admin/admin

#### 8.2 Agregar data source
1. **Configuration > Data Sources > Add data source**
2. Buscar "SimpleJSON"
3. Configurar:
   - URL: `http://localhost:8000/api/grafana`
   - Access: Server
4. **Save & Test**

#### 8.3 Importar dashboard
1. **Dashboards > Import**
2. Subir `grafana-dashboard.json`
3. Seleccionar el data source creado

---

### 🔧 Solución de problemas comunes

#### "Error: ModuleNotFoundError"
```bash
# Asegúrate de activar el entorno virtual
venv\Scripts\activate
pip install -r requirements.txt
```

#### "Connection refused" en MQTT
- Verifica que Mosquitto esté corriendo
- Verifica que uses la IP correcta en el ESP32
- Verifica firewall (puerto 1883 debe estar abierto)

#### ESP32 no conecta a WiFi
- Verifica nombre y contraseña de WiFi en el código
- Verifica que ESP32 y PC estén en la misma red
- Prueba con otro puerto USB

#### No llegan datos a la API
- Verifica logs del ESP32 en Monitor Serie
- Verifica logs de FastAPI en terminal
- Prueba con el simulador: `python simulador.py`

#### Grafana no muestra datos
- Verifica que la API esté corriendo
- Verifica data source URL
- Prueba endpoints manualmente en navegador

---

### 📱 Usando el sistema

#### Estados del LED en ESP32:
- **APAGADO**: Todo normal
- **ENCENDIDO FIJO**: Luz baja (ALERTA_LUZ)
- **PARPADEANTE**: Temperatura alta (ALERTA_TEMP)
- **ENCENDIDO FIJO**: Ambos problemas (ALERTA_DOBLE)

#### Reset de alertas:
- **Botón físico**: Presiona el botón conectado al GPIO 15
- **Comando MQTT**: Envía "reset" al tópico `comandos/esp32`

#### Umbrales de alerta:
- **Temperatura**: >30°C (activa), <28°C (desactiva)
- **Luz**: <20% (activa), >30% (desactiva)

---

### 🎯 Próximos pasos

Una vez funcionando:
1. **Experimenta** cambiando umbrales en el código del ESP32
2. **Agrega más sensores** al sistema
3. **Crea dashboards personalizados** en Grafana
4. **Implementa notificaciones** por email/SMS
5. **Despliega en la nube** (AWS/Heroku/Raspberry Pi)

---

## 2. Hardware - ESP32 (segundaversion_local.ino)

---

## 2. Hardware - ESP32 (segundaversion_local.ino)

### 2.1 Sensores y Componentes Conectados

| Componente | Pin GPIO | Función |
|------------|----------|---------|
| DHT22 (Temp/Humedad) | 4 | Lee temperatura y humedad |
| LDR (Fotoresistencia) | 34 | Detecta nivel de luz ambiental |
| LED | 2 | Indicador visual de alertas |
| Botón | 15 | Reset manual de alertas |

### 2.2 Conectividad

- **WiFi**: Se conecta a red local (INTELRED_FLIA_PEREZ)
- **MQTT**: Envía datos al broker en `192.168.56.1:1883`

### 2.3 Tópicos MQTT que Publica el ESP32

| Tópico | Contenido | Frecuencia |
|--------|-----------|------------|
| `sensores/datos` | JSON con temperatura, humedad, luz, estado | Cada 5 segundos |
| `sensores/estado` | "online" o "alertas_reset" | Eventos |
| `sensores/alertas` | Mensaje de alerta cuando hay condición anormal | Solo en alertas |

**Ejemplo de payload JSON:**
```json
{
  "dispositivo": "ESP32_Sensor_01",
  "temperatura": 25.45,
  "humedad": 60.20,
  "luz": 75,
  "estado": "NORMAL"
}
```

### 2.4 Tópicos MQTT que Escucha el ESP32

| Tópico | Comando | Acción |
|--------|---------|--------|
| `comandos/esp32` | "reset" | Resetea todas las alertas |
| `comandos/esp32` | "led_on" | Enciende el LED manualmente |
| `comandos/esp32` | "led_off" | Apaga el LED manualmente |

---

## 3. Máquina de Estados del ESP32

El sistema tiene 4 estados posibles que determinan el comportamiento del LED:

### Estados y Umbrales

```
TEMPERATURA:
  - ALERTA_TEMP se activa cuando temp >= 30.0°C
  - ALERTA_TEMP se desactiva cuando temp <= 28.0°C
  (Histéresis: evita oscilaciones rápidas)

LUZ:
  - ALERTA_LUZ se activa cuando luz <= 20%
  - ALERTA_LUZ se desactiva cuando luz >= 30%
  (Histéresis: evita parpadeos)
```

| Estado | Condición | LED | Descripción |
|--------|-----------|-----|-------------|
| **NORMAL** | Temperatura OK + Luz OK | **APAGADO** | Todo en rango normal |
| **ALERTA_TEMP** | Temperatura alta | **PARPADEANTE** (cada 100ms) | Solo temperatura elevada |
| **ALERTA_LUZ** | Luz baja | **ENCENDIDO FIJO** | Solo oscuridad detectada |
| **ALERTA_DOBLE** | Temp alta + Luz baja | **ENCENDIDO FIJO** | Ambas condiciones anormales |

### Comportamiento del LED Detallado

```c
// Del código: tareaActualizarLEDs()
switch (estadoActual) {
    case NORMAL:        // → LED APAGADO (LOW)
    case ALERTA_TEMP:   // → LED PARPADEANTE (toggle cada 100ms)
    case ALERTA_LUZ:    // → LED ENCENDIDO (HIGH)
    case ALERTA_DOBLE:  // → LED ENCENDIDO (HIGH)
}
```

> **IMPORTANTE**: El LED solo enciende cuando hay poca luz (ALERTA_LUZ) o cuando hay doble alerta (ALERTA_DOBLE). En alerta de temperatura sola, parpadea. En estado normal, permanece apagado.

### Reset de Alertas

Las alertas se pueden resetear de dos formas:
1. **Presionar el botón físico** (GPIO 15)
2. **Enviar comando MQTT** "reset" al tópico `comandos/esp32`

---

## 4. Servidor - API FastAPI

### 4.1 Arquitectura del Servidor

```
┌─────────────────────────────────────────┐
│           FastAPI Server                │
│  ┌─────────────┐    ┌──────────────┐   │
│  │   MQTT      │    │   SQLite     │   │
│  │   Client    │◄──►│   Database   │   │
│  └─────────────┘    └──────────────┘   │
│         │                              │
│    (recibe datos del ESP32)            │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     Endpoints REST API + Grafana        │
└─────────────────────────────────────────┘
```

### 4.2 Base de Datos SQLite

**Ubicación:** `api_fastapi/iot_data.db`

**Estructura de la tabla `metrics`:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER (PK) | Identificador único autoincremental |
| `device_id` | TEXT | ID del dispositivo (ej: "ESP32_Sensor_01") |
| `topic` | TEXT | Tópico MQTT (ej: "sensores/datos") |
| `temperatura` | REAL | Valor de temperatura en °C |
| `humedad` | REAL | Valor de humedad en % |
| `luz` | INTEGER | Porcentaje de luz (0-100%) |
| `estado` | TEXT | Estado de la máquina (NORMAL, ALERTA_TEMP, etc.) |
| `timestamp` | DATETIME | **Hora del servidor cuando recibe el dato** |

> **Nota crucial**: El ESP32 **NO envía la hora**. La API agrega automáticamente `CURRENT_TIMESTAMP` cuando guarda el dato en la base de datos. Esto significa que la hora registrada es la hora del servidor, no del dispositivo.

### 4.3 Cómo Llegan los Datos a la Base de Datos

```
1. ESP32 lee sensores (cada 2 segundos)
         ↓
2. ESP32 crea JSON con los datos
         ↓
3. ESP32 publica en MQTT (cada 5 segundos) → topic: "sensores/datos"
         ↓
4. Broker MQTT recibe el mensaje
         ↓
5. API FastAPI (suscrita al topic) recibe el mensaje
         ↓
6. mqtt_client.py procesa el JSON
         ↓
7. database.py guarda en SQLite con timestamp automático
```

**Flujo en código (mqtt_client.py):**
```python
# 1. Llega mensaje MQTT
_on_message() → topic="sensores/datos", payload="{JSON}"

# 2. Procesa datos
_process_sensor_data() → decodifica JSON

# 3. Guarda en DB (sin timestamp - lo pone la DB)
_save_metric() → INSERT INTO metrics (...)
    # La base de datos usa: timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
```

---

## 5. Protocolo MQTT - Detalles Técnicos

### 5.1 Configuración del Broker

- **Host**: `localhost` (o IP de la computadora)
- **Puerto**: `1883` (puerto estándar MQTT sin TLS)
- **Autenticación**: Opcional (vacío en esta configuración)

### 5.2 Flujo de Comunicación MQTT

```
┌──────────┐      publica      ┌──────────┐      reenvía      ┌──────────┐
│   ESP32  │ ─────────────────► │  Broker  │ ─────────────────► │   API    │
│ (client) │   sensores/datos   │  MQTT    │   sensores/datos   │ (server) │
└──────────┘                    └──────────┘                    └──────────┘
     │                                                            │
     │      suscrito a comandos/esp32                             │
     │◄───────────────────────────────────────────────────────────┘
     │                         publica comandos
     ▼
  ejecuta
```

### 5.3 QoS (Quality of Service)

El sistema usa **QoS 0** (at most once):
- Los mensajes se envían una sola vez
- No hay confirmación de recepción
- Más rápido pero menos confiable
- Adecuado para datos de sensores que se envían frecuentemente

---

## 6. Endpoints de la API REST

### Endpoints Generales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Información básica de la API |
| `/api/health` | GET | Estado del servidor, conexión MQTT y conteo de registros |

### Endpoints de Métricas

| Endpoint | Método | Parámetros | Descripción |
|----------|--------|------------|-------------|
| `/api/metrics/current` | GET | `device_id` (opcional) | Última lectura registrada |
| `/api/metrics/history` | GET | `hours` (1-168), `device_id` | Historial de métricas |

### Endpoints de Dispositivos y Estadísticas

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/devices` | GET | Lista de dispositivos registrados |
| `/api/stats` | GET | Estadísticas de las últimas 24 horas |

### Endpoints para Grafana

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/grafana/search` | GET | Métricas disponibles para Grafana |
| `/api/grafana/query` | POST | Datos para graficar (SimpleJSON) |
| `/api/grafana/timeseries` | GET | Datos en formato TimeSeries |
| `/api/grafana/data` | GET | Datos para plugin Infinity |

### Endpoints de Comandos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/commands/{device_id}` | POST | Enviar comando al ESP32 (reset, led_on, led_off) |

---

## 7. Intervalos y Timings

| Componente | Intervalo | Descripción |
|------------|-----------|-------------|
| Lectura de sensores | 2 segundos | El ESP32 lee DHT22 y LDR |
| Envío MQTT | 5 segundos | El ESP32 publica datos al broker |
| Actualización LED | 100 ms | Control de parpadeo del LED |
| Reconexión WiFi | Inmediata | Si se pierde conexión |
| Reconexión MQTT | 5 segundos | Reintento si falla conexión |
| Debounce botón | 50 ms | Evita rebotes del botón físico |

---

## 8. Multitarea Cooperativa

El ESP32 no usa `delay()` bloqueante. En su lugar usa `millis()` para ejecutar tareas independientes:

```cpp
void loop() {
    unsigned long ahora = millis();
    
    // Tarea 1: Leer sensores (cada 2s)
    if (ahora - lastSensorRead >= INTERVALO_SENSORES) {
        tareaLeerSensores();
    }
    
    // Tarea 2: Enviar MQTT (cada 5s)
    if (ahora - lastMqttSend >= INTERVALO_MQTT) {
        tareaEnviarMQTT();
    }
    
    // Tarea 3: Actualizar LED (cada 100ms)
    if (ahora - lastLedUpdate >= INTERVALO_LED) {
        tareaActualizarLEDs();
    }
    
    // Tarea 4: Verificar botón (cada loop)
    handleButton();
}
```

Esto permite que el ESP32 responda rápidamente mientras maneja múltiples procesos.

---

## 9. Histéresis - Evitando Oscilaciones

El sistema usa histéresis para evitar que el estado cambie constantemente cuando un valor está cerca del umbral.

### Ejemplo con Temperatura:
```
Umbral alto: 30.0°C  ← Alerta se ACTIVA aquí
Umbral bajo: 28.0°C  ← Alerta se DESACTIVA aquí

Comportamiento:
- Temp sube a 29°C → NORMAL (no cruza umbral alto)
- Temp sube a 30.5°C → ALERTA_TEMP (cruza umbral alto)
- Temp baja a 29°C → ALERTA_TEMP (sigue activa, no bajó de 28)
- Temp baja a 27°C → NORMAL (cruza umbral bajo)
```

Sin histéresis, a 29.9°C estaría cambiando constantemente entre NORMAL y ALERTA.

---

## 10. Iniciar el Sistema

### Paso 1: Configurar la IP del Broker

Editar en `segundaversion_local.ino`:
```cpp
const char* mqtt_server = "192.168.56.1";  // ← Tu IP local
```

### Paso 2: Iniciar el Broker MQTT

```bash
# Windows - con Mosquitto
mosquitto -v
```

### Paso 3: Iniciar la API FastAPI

```bash
cd api_fastapi
pip install -r requirements.txt
python main.py
```

### Paso 4: Subir código al ESP32

1. Conectar ESP32 por USB
2. Seleccionar board: "ESP32 Dev Module"
3. Compilar y subir

### Paso 5: Verificar funcionamiento

- Abrir Monitor Serie del ESP32 (115200 baudios)
- Ver logs de la API en consola
- Acceder a `http://localhost:8000/docs` para probar la API

---

## 11. Resumen de Características Clave

| Característica | Implementación |
|----------------|----------------|
| **Protocolo de comunicación** | MQTT (puerto 1883) |
| **Formato de datos** | JSON |
| **Base de datos** | SQLite (`iot_data.db`) |
| **Timestamp** | Generado por el servidor (no por ESP32) |
| **Multitarea** | Cooperativa con `millis()` (no bloqueante) |
| **Histéresis** | Sí, en temperatura y luz |
| **LED en ALERTA_LUZ** | Encendido fijo (HIGH) |
| **LED en ALERTA_TEMP** | Parpadeo (toggle cada 100ms) |
| **LED en NORMAL** | Apagado (LOW) |
| **Reset de alertas** | Botón físico o comando MQTT |
| **API REST** | FastAPI con documentación automática |
| **Visualización** | Compatible con Grafana |

---

## 12. Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HARDWARE (ESP32)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  DHT22   │  │   LDR    │  │   LED    │  │  Botón   │                  │
│  │  GPIO 4  │  │  GPIO 34 │  │  GPIO 2  │  │  GPIO 15 │                  │
│  └────┬─────┘  └────┬─────┘  └────▲─────┘  └────┬─────┘                  │
│       │              │               │            │                          │
│       └──────────────┴──────────────┴────────────┘                          │
│                      │                                                      │
│              ┌───────▼────────┐                                             │
│              │  Máquina de    │                                             │
│              │   Estados      │                                             │
│              └───────┬────────┘                                             │
│                      │                                                      │
│              ┌───────▼────────┐                                             │
│              │    WiFi +      │                                             │
│              │     MQTT       │◄─────────────────────────────────────┐       │
│              └───────┬────────┘                                      │       │
└──────────────────────┼──────────────────────────────────────────────┼───────┘
                       │                                              │
                       │      publica en "sensores/datos"           │
                       ▼                                              │
┌─────────────────────────────────────────────────────────────────────┼───────┐
│                         BROKER MQTT (Mosquitto)                     │       │
│                        Host: localhost, Puerto: 1883                 │       │
└─────────────────────────────────────────────────────────────────────┼───────┘
                                                                    │
                       suscrito a "sensores/datos"                    │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVIDOR (FastAPI)                              │
│                                                                              │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐        │
│   │  MQTT Client    │────►│  Procesamiento  │────►│  SQLite (iot_   │        │
│   │  (recibe datos) │     │     de JSON     │     │    data.db)     │        │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘        │
│                                                          │                   │
│   ┌──────────────────────────────────────────────────────┘                   │
│   │                                                                          │
│   ▼                                                                          │
│   ┌─────────────────┐     ┌─────────────────┐                                │
│   │   Endpoints     │     │    Grafana      │                                │
│   │   REST API      │     │  (dashboards)   │                                │
│   └─────────────────┘     └─────────────────┘                                │
│                                                                              │
│   • GET /api/metrics/current  → Última lectura                              │
│   • GET /api/metrics/history  → Historial                                     │
│   • GET /api/stats            → Estadísticas                                │
│   • POST /api/commands/{id} → Enviar comandos al ESP32                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Comandos Útiles

### Probar MQTT manualmente:

```bash
# Suscribirse a todos los tópicos
mosquitto_sub -t "sensores/#" -v

# Publicar comando al ESP32
mosquitto_pub -t "comandos/esp32" -m "reset"
mosquitto_pub -t "comandos/esp32" -m "led_on"
mosquitto_pub -t "comandos/esp32" -m "led_off"
```

### Ver base de datos SQLite:

```bash
sqlite3 api_fastapi/iot_data.db

# Dentro de sqlite3:
SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10;
.tables
.schema metrics
```

---

## 14. Troubleshooting

| Problema | Posible Causa | Solución |
|----------|---------------|----------|
| ESP32 no conecta a WiFi | Credenciales incorrectas | Verificar SSID y password |
| ESP32 no conecta a MQTT | IP del broker incorrecta | Ajustar `mqtt_server` a tu IP local |
| No llegan datos a la API | Broker no iniciado | Ejecutar `mosquitto -v` |
| LED no responde | Estado no cambia | Verificar umbrales de temperatura/luz |
| Datos duplicados en DB | Reconexiones MQTT | Normal, el ESP32 no tiene buffer persistente |
| API no inicia | Puerto 8000 ocupado | Cambiar puerto o cerrar proceso anterior |

---

**Versión del documento:** 1.0  
**Fecha:** Mayo 2026  
**Proyecto:** IoT con MQTT - Complementaria II
