"""
Cliente MQTT para recibir datos del ESP32
"""

import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import asyncio
from typing import Callable, Optional
from database import db


class MQTTClient:
    """Cliente MQTT que recibe datos de sensores y los almacena"""
    
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        on_message_callback: Optional[Callable] = None
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.on_message_callback = on_message_callback
        
        self.client = mqtt.Client(CallbackAPIVersion.VERSION1)
        self.connected = False
        self._loop = None  # Referencia al event loop principal
        
        # Configurar callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Autenticación si se proporciona
        if username and password:
            self.client.username_pw_set(username, password)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            self.connected = True
            print(f"✅ Conectado al broker MQTT ({self.broker_host}:{self.broker_port})")
            
            # Suscribirse a los tópicos de sensores
            topics = [
                ("sensores/datos", 0),
                ("sensores/estado", 0),
                ("sensores/alertas", 0)
            ]
            client.subscribe(topics)
            print(f"📡 Suscrito a: {[t[0] for t in topics]}")
        else:
            print(f"❌ Error de conexión MQTT, código: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        self.connected = False
        print(f"⚠️ Desconectado del broker MQTT (código: {rc})")
    
    def _on_message(self, client, userdata, msg):
        """Callback cuando llega un mensaje"""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        print(f"📨 Mensaje recibido - Topic: {topic}")
        print(f"   Payload: {payload}")
        
        # Procesar mensajes de datos
        if topic == "sensores/datos":
            self._process_sensor_data(payload)
        
        # Llamar al callback externo si existe
        if self.on_message_callback:
            self.on_message_callback(topic, payload)
    
    def _process_sensor_data(self, payload: str):
        """Procesar datos de sensores y guardarlos en la base de datos"""
        try:
            data = json.loads(payload)
            
            # Preparar datos para la base de datos
            # Nota: No enviamos timestamp, la DB usará CURRENT_TIMESTAMP (hora del servidor)
            metric_data = {
                'device_id': data.get('dispositivo', 'unknown'),
                'topic': 'sensores/datos',
                'temperatura': data.get('temperatura'),
                'humedad': data.get('humedad'),
                'luz': data.get('luz'),
                'estado': data.get('estado')
                # timestamp: la base de datos lo agrega automáticamente
            }
            
            # Guardar en base de datos usando el event loop principal
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self._save_metric(metric_data), self._loop)
            else:
                # Fallback: guardar de forma síncrona si no hay loop
                import threading
                threading.Thread(target=self._save_metric_sync, args=(metric_data,), daemon=True).start()
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Error decodificando JSON: {e}")
        except Exception as e:
            print(f"⚠️ Error procesando datos: {e}")
    
    async def _save_metric(self, data: dict):
        """Guardar métrica en la base de datos (async)"""
        try:
            await db.insert_metric(data)
            print("💾 Datos guardados en la base de datos")
        except Exception as e:
            print(f"❌ Error guardando en base de datos: {e}")
    
    def _save_metric_sync(self, data: dict):
        """Guardar métrica en la base de datos (sync fallback)"""
        try:
            import asyncio
            # Crear un nuevo event loop para este thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(db.insert_metric(data))
            loop.close()
            print("💾 Datos guardados en la base de datos (sync)")
        except Exception as e:
            print(f"❌ Error guardando en base de datos (sync): {e}")
    
    def connect(self):
        """Conectar al broker MQTT (bloqueante, ejecutar en thread)"""
        try:
            # Guardar referencia al event loop principal
            self._loop = asyncio.get_event_loop()
            print(f"🔌 Conectando a MQTT ({self.broker_host}:{self.broker_port})...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"❌ Error conectando al broker: {e}")
    
    def disconnect(self):
        """Desconectar del broker"""
        self.client.loop_stop()
        self.client.disconnect()
        print("🔌 Cliente MQTT desconectado")
    
    def publish(self, topic: str, message: str, qos: int = 0):
        """Publicar mensaje a un tópico"""
        if self.connected:
            self.client.publish(topic, message, qos)
            print(f"📤 Publicado en {topic}: {message}")
        else:
            print(f"⚠️ No conectado, no se pudo publicar en {topic}")


# Instancia global del cliente
mqtt_client = MQTTClient()
