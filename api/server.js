/*
 * SERVIDOR API IoT + MQTT BROKER
 * - Recibe datos del ESP32 via MQTT
 * - Expone API REST para Grafana
 * - Almacena datos en SQLite
 */

const express = require('express');
const cors = require('cors');
const aedes = require('aedes')();
const net = require('net');
const http = require('http');
const WebSocket = require('ws');
const Database = require('./database');

const app = express();
const server = http.createServer(app);

// Configuración
const MQTT_PORT = 1883;
const WS_PORT = 8883;
const API_PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Inicializar base de datos
const db = new Database();

// ==================== MQTT BROKER ====================

// Broker TCP
const mqttServer = net.createServer(aedes.handle);

mqttServer.listen(MQTT_PORT, () => {
    console.log(`📡 MQTT Broker TCP escuchando en puerto ${MQTT_PORT}`);
});

// Broker WebSocket
const wsServer = new WebSocket.Server({ port: WS_PORT });
wsServer.on('connection', (ws, req) => {
    const stream = WebSocket.createWebSocketStream(ws);
    aedes.handle(stream);
});

console.log(`📡 MQTT Broker WebSocket escuchando en puerto ${WS_PORT}`);

// Eventos del broker
aedes.on('client', (client) => {
    console.log(`✅ Cliente conectado: ${client.id}`);
});

aedes.on('clientDisconnect', (client) => {
    console.log(`❌ Cliente desconectado: ${client.id}`);
});

aedes.on('publish', async (packet, client) => {
    if (!client) return; // Ignorar mensajes del sistema
    
    const topic = packet.topic;
    const payload = packet.payload.toString();
    
    console.log(`📨 Mensaje recibido - Topic: ${topic}, Payload: ${payload}`);
    
    // Procesar datos del ESP32
    if (topic.startsWith('sensores/')) {
        try {
            const data = JSON.parse(payload);
            await db.insertMetric({
                device_id: client.id,
                topic: topic,
                temperatura: data.temperatura || null,
                humedad: data.humedad || null,
                luz: data.luz || null,
                estado: data.estado || null
            });
            console.log('💾 Datos guardados en DB');
        } catch (e) {
            console.error('Error procesando mensaje:', e.message);
        }
    }
});

// ==================== API REST PARA GRAFANA ====================

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Obtener métricas actuales (último valor)
app.get('/api/metrics/current', async (req, res) => {
    try {
        const metrics = await db.getLatestMetrics();
        res.json(metrics);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Obtener historial de métricas (para Grafana)
app.get('/api/metrics/history', async (req, res) => {
    try {
        const { hours = 24, device_id } = req.query;
        const metrics = await db.getMetricsHistory(parseInt(hours), device_id);
        res.json(metrics);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Endpoint compatible con SimpleJSON de Grafana
app.get('/api/grafana/search', (req, res) => {
    res.json(['temperatura', 'humedad', 'luz', 'estado']);
});

app.post('/api/grafana/query', async (req, res) => {
    try {
        const { targets, range } = req.body;
        const results = [];
        
        for (const target of targets) {
            const metric = target.target;
            const data = await db.getMetricSeries(metric, range.from, range.to);
            
            results.push({
                target: metric,
                datapoints: data.map(row => [row.value, new Date(row.timestamp).getTime()])
            });
        }
        
        res.json(results);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/grafana/annotations', (req, res) => {
    res.json([]);
});

// ==================== API ADICIONAL ====================

// Lista de dispositivos
app.get('/api/devices', async (req, res) => {
    try {
        const devices = await db.getDevices();
        res.json(devices);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Estadísticas resumidas
app.get('/api/stats', async (req, res) => {
    try {
        const stats = await db.getStats();
        res.json(stats);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// WebSocket para dashboard en tiempo real
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
    console.log('🔌 Cliente WebSocket conectado');
    
    ws.on('close', () => {
        console.log('🔌 Cliente WebSocket desconectado');
    });
});

// Broadcast a todos los clientes WebSocket cuando llegan nuevos datos
const broadcast = (data) => {
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(data));
        }
    });
};

// Hook para notificar nuevos datos
aedes.on('publish', async (packet, client) => {
    if (!client) return;
    
    const topic = packet.topic;
    const payload = packet.payload.toString();
    
    if (topic.startsWith('sensores/')) {
        try {
            const data = JSON.parse(payload);
            broadcast({
                type: 'new_data',
                device: client.id,
                topic: topic,
                data: data,
                timestamp: new Date().toISOString()
            });
        } catch (e) {}
    }
});

// ==================== INICIAR SERVIDOR ====================

server.listen(API_PORT, () => {
    console.log(`🚀 API REST escuchando en http://localhost:${API_PORT}`);
    console.log('');
    console.log('📋 Endpoints disponibles:');
    console.log(`   - MQTT Broker: mqtt://localhost:${MQTT_PORT}`);
    console.log(`   - WebSocket: ws://localhost:${WS_PORT}`);
    console.log(`   - API: http://localhost:${API_PORT}/api`);
    console.log('');
    console.log('🔧 Endpoints Grafana:');
    console.log(`   - Search: GET  http://localhost:${API_PORT}/api/grafana/search`);
    console.log(`   - Query:  POST http://localhost:${API_PORT}/api/grafana/query`);
    console.log('');
    console.log('📊 Otros endpoints:');
    console.log(`   - Health:   http://localhost:${API_PORT}/api/health`);
    console.log(`   - Current:  http://localhost:${API_PORT}/api/metrics/current`);
    console.log(`   - History:  http://localhost:${API_PORT}/api/metrics/history`);
    console.log(`   - Devices:  http://localhost:${API_PORT}/api/devices`);
    console.log(`   - Stats:    http://localhost:${API_PORT}/api/stats`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Cerrando servidor...');
    await db.close();
    mqttServer.close();
    server.close();
    process.exit(0);
});
