/*
 * PROYECTO IoT CON MQTT A BROKER LOCAL
 * ESP32 + DHT22 + LDR + Boton + LED
 * 
 * Caracteristicas:
 * - Multitarea cooperativa (sin delay)
 * - Maquina de estados con histéresis
 * - Protocolo MQTT a broker local propio
 * - Formato JSON para la API
 */

#include "DHT.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACION PINES ====================
const int LDR = 34;
const int DHT_PIN = 4;
const int LED = 2;
const int BOTON = 15;

// ==================== CONFIGURACION WiFi ====================
const char* ssid = "INTELRED_FLIA_PEREZ";
const char* password = "70978983";

// ==================== CONFIGURACION BROKER MQTT LOCAL ====================
// IP de tu computadora donde corre el servidor Node.js
// Cambia esta IP por la de tu computadora en la red local
const char* mqtt_server = "192.168.56.1";  // ← AJUSTA ESTA IP
const int mqtt_port = 1883;

const char* mqtt_client_id = "ESP32_Sensor_01";
const char* mqtt_username = "";  // Dejar vacío si no hay autenticación
const char* mqtt_password = "";  // Dejar vacío si no hay autenticación

// Topics MQTT
const char* topic_sensores = "sensores/datos";
const char* topic_estado = "sensores/estado";
const char* topic_alertas = "sensores/alertas";

// ==================== UMBRALES E HISTERESIS ====================
// Temperatura
const float TEMP_UMBRAL_ALTO = 30.0;
const float TEMP_UMBRAL_BAJO = 28.0;

// Luz
const int LUZ_UMBRAL_BAJO = 20;
const int LUZ_UMBRAL_ALTO = 30;

// ==================== MAQUINA DE ESTADOS ====================
enum Estado { NORMAL, ALERTA_TEMP, ALERTA_LUZ, ALERTA_DOBLE };
Estado estadoActual = NORMAL;

bool alertaTempActiva = false;
bool alertaLuzActiva = false;

// ==================== MULTITAREA - TIMERS ====================
unsigned long lastSensorRead = 0;
const long INTERVALO_SENSORES = 2000;

unsigned long lastMqttSend = 0;
const long INTERVALO_MQTT = 5000;

unsigned long lastLedUpdate = 0;
const long INTERVALO_LED = 100;

// ==================== VARIABLES GLOBALES DE SENSORES ====================
float temperatura = 0.0;
float humedad = 0.0;
int porcentajeLuz = 0;
bool hayErrorDHT = false;

// ==================== OBJETOS ====================
DHT dht(DHT_PIN, DHT22);
WiFiClient espClient;
PubSubClient client(espClient);

// ==================== SETUP ====================
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    dht.begin();
    pinMode(LED, OUTPUT);
    pinMode(BOTON, INPUT_PULLUP);
    
    setup_wifi();
    
    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(mqtt_callback);
    
    Serial.println("\n========================================");
    Serial.println("Sistema IoT MQTT -> Broker Local");
    Serial.println("Modo: Multitarea + Maquina de Estados + JSON");
    Serial.println("========================================");
    Serial.print("Broker MQTT: ");
    Serial.print(mqtt_server);
    Serial.print(":");
    Serial.println(mqtt_port);
    Serial.println("========================================");
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
    unsigned long ahora = millis();
    
    mantenerConexiones();
    
    if (ahora - lastSensorRead >= INTERVALO_SENSORES) {
        lastSensorRead = ahora;
        tareaLeerSensores();
    }
    
    if (ahora - lastMqttSend >= INTERVALO_MQTT) {
        lastMqttSend = ahora;
        tareaEnviarMQTT();
    }
    
    if (ahora - lastLedUpdate >= INTERVALO_LED) {
        lastLedUpdate = ahora;
        tareaActualizarLEDs();
    }
    
    handleButton();
}

// ==================== CALLBACK MQTT ====================
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Mensaje recibido en topic: ");
    Serial.println(topic);
    
    String message = "";
    for (int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    Serial.println("Payload: " + message);
    
    // Procesar comandos desde el servidor
    if (String(topic) == "comandos/esp32") {
        if (message == "reset") {
            alertaTempActiva = false;
            alertaLuzActiva = false;
            estadoActual = NORMAL;
            Serial.println("Comando: Reset de alertas");
        } else if (message == "led_on") {
            digitalWrite(LED, HIGH);
            Serial.println("Comando: LED encendido");
        } else if (message == "led_off") {
            digitalWrite(LED, LOW);
            Serial.println("Comando: LED apagado");
        }
    }
}

// ==================== CONEXIONES ====================
void mantenerConexiones() {
    if (WiFi.status() != WL_CONNECTED) {
        setup_wifi();
    }
    
    if (!client.connected()) {
        reconnect_mqtt();
    }
    client.loop();
}

void setup_wifi() {
    delay(10);
    Serial.print("Conectando a WiFi");
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\n✅ WiFi conectado");
    Serial.print("📡 IP del ESP32: ");
    Serial.println(WiFi.localIP());
}

void reconnect_mqtt() {
    while (!client.connected()) {
        Serial.print("Conectando a MQTT...");
        
        if (client.connect(mqtt_client_id, mqtt_username, mqtt_password)) {
            Serial.println("✅ Conectado al broker");
            
            // Suscribirse a topic de comandos
            client.subscribe("comandos/esp32");
            Serial.println("Suscrito a: comandos/esp32");
            
            // Enviar mensaje de estado online
            client.publish(topic_estado, "online");
        } else {
            Serial.print("❌ Fallo, rc=");
            Serial.print(client.state());
            Serial.println(" reintentando en 5s");
            delay(5000);
        }
    }
}

// ==================== TAREAS ====================
void tareaLeerSensores() {
    float tempLeida = dht.readTemperature();
    float humLeida = dht.readHumidity();
    
    if (isnan(tempLeida) || isnan(humLeida)) {
        Serial.println("⚠️ Error leyendo DHT22");
        hayErrorDHT = true;
    } else {
        temperatura = tempLeida;
        humedad = humLeida;
        hayErrorDHT = false;
    }
    
    int valorLDR = analogRead(LDR);
    porcentajeLuz = map(valorLDR, 0, 4095, 0, 100);
    
    actualizarMaquinaEstados();
    
    Serial.println("\n--- 📊 Lectura Sensores ---");
    if (!hayErrorDHT) {
        Serial.println("🌡️ Temp: " + String(temperatura) + " C");
        Serial.println("💧 Hum:  " + String(humedad) + " %");
    }
    Serial.println("☀️  Luz:  " + String(porcentajeLuz) + " %");
    Serial.print("🚦 Estado: ");
    imprimirEstado();
    Serial.println("---------------------------");
}

void actualizarMaquinaEstados() {
    // Histéresis temperatura
    if (temperatura >= TEMP_UMBRAL_ALTO) {
        alertaTempActiva = true;
    } else if (temperatura <= TEMP_UMBRAL_BAJO) {
        alertaTempActiva = false;
    }
    
    // Histéresis luz
    if (porcentajeLuz <= LUZ_UMBRAL_BAJO) {
        alertaLuzActiva = true;
    } else if (porcentajeLuz >= LUZ_UMBRAL_ALTO) {
        alertaLuzActiva = false;
    }
    
    // Determinar estado
    if (alertaTempActiva && alertaLuzActiva) {
        estadoActual = ALERTA_DOBLE;
    } else if (alertaTempActiva) {
        estadoActual = ALERTA_TEMP;
    } else if (alertaLuzActiva) {
        estadoActual = ALERTA_LUZ;
    } else {
        estadoActual = NORMAL;
    }
}

void imprimirEstado() {
    switch (estadoActual) {
        case NORMAL:       Serial.println("✅ NORMAL"); break;
        case ALERTA_TEMP:  Serial.println("🌡️  ALERTA_TEMP"); break;
        case ALERTA_LUZ:   Serial.println("🌑 ALERTA_LUZ"); break;
        case ALERTA_DOBLE: Serial.println("🚨 ALERTA_DOBLE"); break;
    }
}

void tareaEnviarMQTT() {
    if (hayErrorDHT) {
        Serial.println("⚠️ No se envia: Error DHT");
        return;
    }
    
    if (!client.connected()) {
        Serial.println("⚠️ No se envia: Sin conexion MQTT");
        return;
    }
    
    // Crear objeto JSON
    StaticJsonDocument<256> doc;
    doc["dispositivo"] = mqtt_client_id;
    doc["temperatura"] = round(temperatura * 100) / 100.0;  // 2 decimales
    doc["humedad"] = round(humedad * 100) / 100.0;
    doc["luz"] = porcentajeLuz;
    doc["estado"] = getEstadoString();
    // Nota: La API agregará el timestamp automáticamente al recibir
    
    String payload;
    serializeJson(doc, payload);
    
    Serial.println("\n>>> 📤 Enviando a MQTT <<<");
    Serial.println("Payload: " + payload);
    
    if (client.publish(topic_sensores, payload.c_str())) {
        Serial.println("✅ Datos enviados OK");
        
        // Si hay alerta, enviar también al topic de alertas
        if (estadoActual != NORMAL) {
            String alertaMsg = "Alerta: " + getEstadoString();
            client.publish(topic_alertas, alertaMsg.c_str());
        }
    } else {
        Serial.println("❌ Error al enviar");
    }
}

String getEstadoString() {
    switch (estadoActual) {
        case NORMAL: return "NORMAL";
        case ALERTA_TEMP: return "ALERTA_TEMP";
        case ALERTA_LUZ: return "ALERTA_LUZ";
        case ALERTA_DOBLE: return "ALERTA_DOBLE";
        default: return "UNKNOWN";
    }
}

void tareaActualizarLEDs() {
    switch (estadoActual) {
        case NORMAL:
            digitalWrite(LED, LOW);
            break;
        case ALERTA_TEMP:
            digitalWrite(LED, !digitalRead(LED));
            break;
        case ALERTA_LUZ:
            digitalWrite(LED, HIGH);
            break;
        case ALERTA_DOBLE:
            digitalWrite(LED, HIGH);
            break;
    }
}

void handleButton() {
    static bool lastButtonState = HIGH;
    static unsigned long lastDebounce = 0;
    const long DEBOUNCE_DELAY = 50;
    
    bool currentState = digitalRead(BOTON);
    unsigned long ahora = millis();
    
    if (currentState != lastButtonState) {
        lastDebounce = ahora;
    }
    
    if ((ahora - lastDebounce) > DEBOUNCE_DELAY) {
        if (lastButtonState == HIGH && currentState == LOW) {
            Serial.println("🔘 Boton presionado - Reset alertas");
            alertaTempActiva = false;
            alertaLuzActiva = false;
            estadoActual = NORMAL;
            
            // Notificar reset
            if (client.connected()) {
                client.publish(topic_estado, "alertas_reset");
            }
        }
    }
    
    lastButtonState = currentState;
}
