/*
 * PROYECTO IoT CON MQTT A THINGSPEAK
 * ESP32 + DHT22 + LDR + Boton + LED
 * 
 * Caracteristicas:
 * - Multitarea cooperativa (sin delay)
 * - Maquina de estados con histéresis
 * - Protocolo MQTT
 */

#include "DHT.h"
#include <WiFi.h>
#include <PubSubClient.h>

// ==================== CONFIGURACION PINES ====================
const int LDR = 34;
const int DHT_PIN = 4;
const int LED = 2;
const int BOTON = 15;

// ==================== CONFIGURACION WiFi ====================
const char* ssid = "REDMI Note 15";
const char* password = "emilia05";

// ==================== CONFIGURACION THINGSPEAK MQTT ====================
const char* mqtt_server = "mqtt3.thingspeak.com";
const int mqtt_port = 1883;

const char* mqtt_client_id = "OgUkOz01MiMeIysdIAA9FBk";
const char* mqtt_username = "OgUkOz01MiMeIysdIAA9FBk";
const char* mqtt_password = "mgasKh11lEthWDKuToEp8n0o";

const long channelID = 3311634;

// ==================== UMBRALES E HISTERESIS ====================
// Temperatura
const float TEMP_UMBRAL_ALTO = 30.0;   // Entra en alerta
const float TEMP_UMBRAL_BAJO = 28.0;   // Sale de alerta (histéresis de 2°C)

// Luz
const int LUZ_UMBRAL_BAJO = 20;        // Entra en alerta (luz baja)
const int LUZ_UMBRAL_ALTO = 30;        // Sale de alerta (histéresis de 10%)

// ==================== MAQUINA DE ESTADOS ====================
enum Estado { NORMAL, ALERTA_TEMP, ALERTA_LUZ, ALERTA_DOBLE };
Estado estadoActual = NORMAL;

// Flags de alerta con histéresis
bool alertaTempActiva = false;
bool alertaLuzActiva = false;

// ==================== MULTITAREA - TIMERS ====================
unsigned long lastSensorRead = 0;
const long INTERVALO_SENSORES = 2000;   // 2 segundos

unsigned long lastApiSend = 0;
const long INTERVALO_API = 20000;       // 20 segundos

unsigned long lastLedUpdate = 0;
const long INTERVALO_LED = 100;         // 100 ms

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
    
    Serial.println("\nSistema IoT MQTT -> ThingSpeak iniciado");
    Serial.println("Modo: Multitarea + Maquina de Estados + Histeresis");
}

// ==================== LOOP PRINCIPAL (MULTITAREA) ====================
void loop() {
    unsigned long ahora = millis();
    
    // TAREA 0: Mantener conexiones (siempre)
    mantenerConexiones();
    
    // TAREA 1: Leer sensores cada 2 segundos
    if (ahora - lastSensorRead >= INTERVALO_SENSORES) {
        lastSensorRead = ahora;
        tareaLeerSensores();
    }
    
    // TAREA 2: Enviar a API cada 20 segundos
    if (ahora - lastApiSend >= INTERVALO_API) {
        lastApiSend = ahora;
        tareaEnviarAPI();
    }
    
    // TAREA 3: Actualizar LEDs cada 100 ms
    if (ahora - lastLedUpdate >= INTERVALO_LED) {
        lastLedUpdate = ahora;
        tareaActualizarLEDs();
    }
    
    // TAREA CONTINUA: Botón (respuesta inmediata)
    handleButton();
}

// ==================== TAREA 0: MANTENER CONEXIONES ====================
void mantenerConexiones() {
    if (WiFi.status() != WL_CONNECTED) {
        setup_wifi();
    }
    
    if (!client.connected()) {
        reconnect();
    }
    client.loop();
}

// ==================== TAREA 1: LEER SENSORES ====================
void tareaLeerSensores() {
    // Leer DHT22
    float tempLeida = dht.readTemperature();
    float humLeida = dht.readHumidity();
    
    if (isnan(tempLeida) || isnan(humLeida)) {
        Serial.println("Error leyendo DHT22");
        hayErrorDHT = true;
    } else {
        temperatura = tempLeida;
        humedad = humLeida;
        hayErrorDHT = false;
    }
    
    // Leer LDR
    int valorLDR = analogRead(LDR);
    porcentajeLuz = map(valorLDR, 0, 4095, 0, 100);
    
    // Actualizar máquina de estados con histéresis
    actualizarMaquinaEstados();
    
    // Mostrar en Serial
    Serial.println("\n--- Lectura Sensores ---");
    if (!hayErrorDHT) {
        Serial.println("Temp: " + String(temperatura) + " C");
        Serial.println("Hum: " + String(humedad) + " %");
    }
    Serial.println("Luz: " + String(porcentajeLuz) + " %");
    Serial.print("Estado: ");
    imprimirEstado();
    Serial.println("------------------------");
}

// ==================== MAQUINA DE ESTADOS CON HISTERESIS ====================
void actualizarMaquinaEstados() {
    // HISTÉRESIS TEMPERATURA
    if (temperatura >= TEMP_UMBRAL_ALTO) {
        alertaTempActiva = true;
    } else if (temperatura <= TEMP_UMBRAL_BAJO) {
        alertaTempActiva = false;
    }
    // Si está entre 28 y 30, mantiene el estado anterior (histéresis)
    
    // HISTÉRESIS LUZ
    if (porcentajeLuz <= LUZ_UMBRAL_BAJO) {
        alertaLuzActiva = true;
    } else if (porcentajeLuz >= LUZ_UMBRAL_ALTO) {
        alertaLuzActiva = false;
    }
    // Si está entre 20 y 30, mantiene el estado anterior (histéresis)
    
    // DETERMINAR ESTADO ACTUAL
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
        case NORMAL:       Serial.println("NORMAL"); break;
        case ALERTA_TEMP:  Serial.println("ALERTA_TEMP"); break;
        case ALERTA_LUZ:   Serial.println("ALERTA_LUZ"); break;
        case ALERTA_DOBLE: Serial.println("ALERTA_DOBLE"); break;
    }
}

// ==================== TAREA 2: ENVIAR A API ====================
void tareaEnviarAPI() {
    if (hayErrorDHT) {
        Serial.println("No se envia: Error DHT");
        return;
    }
    
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("No se envia: Sin WiFi");
        return;
    }
    
    String payload = "field1=" + String(temperatura, 2);
    payload += "&field2=" + String(humedad, 2);
    payload += "&field3=" + String(porcentajeLuz);
    
    String topic = "channels/" + String(channelID) + "/publish";
    
    Serial.println("\n>>> Enviando a ThingSpeak <<<");
    Serial.println("Payload: " + payload);
    
    if (client.publish(topic.c_str(), payload.c_str())) {
        Serial.println("Datos enviados OK");
    } else {
        Serial.println("Error al enviar");
    }
}

// ==================== TAREA 3: ACTUALIZAR LEDs ====================
void tareaActualizarLEDs() {
    switch (estadoActual) {
        case NORMAL:
            // LED apagado en normal
            digitalWrite(LED, LOW);
            break;
            
        case ALERTA_TEMP:
            // LED parpadeo rápido (cada 100ms alterna, pero acá simplificado)
            // Como se llama cada 100ms, toggle cada vez = 5Hz aprox
            digitalWrite(LED, !digitalRead(LED));
            break;
            
        case ALERTA_LUZ:
            // LED encendido fijo
            digitalWrite(LED, HIGH);
            break;
            
        case ALERTA_DOBLE:
            // LED parpadeo muy rápido (siempre encendido en esta implementación)
            // Podría ser un patrón especial
            digitalWrite(LED, HIGH);
            break;
    }
}

// ==================== BOTÓN (INTERRUPCIÓN POR SOFTWARE) ====================
void handleButton() {
    static bool lastButtonState = HIGH;
    static unsigned long lastDebounce = 0;
    const long DEBOUNCE_DELAY = 50;
    
    bool currentState = digitalRead(BOTON);
    unsigned long ahora = millis();
    
    // Anti-rebote con millis (sin delay)
    if (currentState != lastButtonState) {
        lastDebounce = ahora;
    }
    
    if ((ahora - lastDebounce) > DEBOUNCE_DELAY) {
        if (lastButtonState == HIGH && currentState == LOW) {
            // Acción del botón: Resetear alertas o cambiar modo
            Serial.println("Boton presionado - Reset alertas");
            alertaTempActiva = false;
            alertaLuzActiva = false;
            estadoActual = NORMAL;
        }
    }
    
    lastButtonState = currentState;
}

// ==================== WiFi ====================
void setup_wifi() {
    delay(10);
    Serial.print("Conectando a WiFi");
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\nWiFi conectado");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}

// ==================== MQTT ====================
void reconnect() {
    while (!client.connected()) {
        Serial.print("Conectando MQTT...");
        
        if (client.connect(mqtt_client_id, mqtt_username, mqtt_password)) {
            Serial.println("Conectado");
        } else {
            Serial.print("fallo, rc=");
            Serial.print(client.state());
            Serial.println(" reintentando en 5s");
            delay(5000);
        }
    }
}