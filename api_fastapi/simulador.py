"""
Simulador de ESP32 para probar la API sin hardware
Envía datos ficticios de temperatura, humedad y luz cada 5 segundos
"""

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import json
import random
import time
import sys

# Configuración
BROKER = "localhost"
PORT = 1883
TOPIC = "sensores/datos"
DEVICE_ID = "ESP32_Simulado"

# Valores iniciales
temp = 25.0
humidity = 60
light = 50

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado al broker MQTT")
    else:
        print(f"❌ Error de conexión: {rc}")

def on_publish(client, userdata, mid):
    print(f"📤 Mensaje publicado (ID: {mid})")

def simular_lecturas():
    """Generar lecturas simuladas con variación realista"""
    global temp, humidity, light
    
    # Variar temperatura ±1°C
    temp += random.uniform(-1.0, 1.0)
    temp = max(20, min(40, temp))  # Mantener entre 20-40°C
    
    # Variar humedad ±3%
    humidity += random.randint(-3, 3)
    humidity = max(30, min(90, humidity))  # Mantener entre 30-90%
    
    # Variar luz ±10%
    light += random.randint(-10, 10)
    light = max(0, min(100, light))  # Mantener entre 0-100%
    
    # Determinar estado
    if temp > 30 and light < 20:
        estado = "ALERTA_DOBLE"
    elif temp > 30:
        estado = "ALERTA_TEMP"
    elif light < 20:
        estado = "ALERTA_LUZ"
    else:
        estado = "NORMAL"
    
    return {
        "dispositivo": DEVICE_ID,
        "temperatura": round(temp, 2),
        "humedad": round(humidity, 2),
        "luz": light,
        "estado": estado,
        "timestamp": int(time.time() * 1000)
    }

def main():
    print("="*60)
    print("🔌 Simulador de ESP32 para MQTT")
    print("="*60)
    print(f"📡 Broker: mqtt://{BROKER}:{PORT}")
    print(f"📨 Topic: {TOPIC}")
    print(f"🔁 Intervalo: 5 segundos")
    print("="*60)
    print("Presiona Ctrl+C para detener\n")
    
    # Crear cliente MQTT
    client = mqtt.Client(CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        # Conectar al broker
        print(f"Conectando a {BROKER}:{PORT}...")
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        
        # Esperar conexión
        time.sleep(1)
        
        # Loop de envío
        while True:
            data = simular_lecturas()
            payload = json.dumps(data)
            
            print(f"\n📊 Enviando datos:")
            print(f"   🌡️  Temperatura: {data['temperatura']}°C")
            print(f"   💧 Humedad: {data['humedad']}%")
            print(f"   ☀️  Luz: {data['luz']}%")
            print(f"   🚦 Estado: {data['estado']}")
            
            result = client.publish(TOPIC, payload, qos=0)
            
            if result.rc == 0:
                print(f"   ✅ Enviado correctamente")
            else:
                print(f"   ❌ Error al enviar (código {result.rc})")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo simulador...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nAsegúrate de que:")
        print("1. Mosquitto está corriendo (mosquitto -v)")
        print("2. La API FastAPI está iniciada (python main.py)")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Simulador detenido")

if __name__ == "__main__":
    main()
