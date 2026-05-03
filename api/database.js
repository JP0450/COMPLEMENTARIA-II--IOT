/*
 * MÓDULO DE BASE DE DATOS SQLITE
 * Gestiona el almacenamiento de métricas IoT
 */

const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
    constructor() {
        const dbPath = path.join(__dirname, 'iot_data.db');
        this.db = new sqlite3.Database(dbPath, (err) => {
            if (err) {
                console.error('Error al abrir la base de datos:', err.message);
            } else {
                console.log('💾 Conectado a la base de datos SQLite');
                this.initialize();
            }
        });
    }

    initialize() {
        const sql = `
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
        `;
        
        this.db.run(sql, (err) => {
            if (err) {
                console.error('Error creando tabla:', err.message);
            } else {
                console.log('✅ Tabla de métricas inicializada');
                this.createIndexes();
            }
        });
    }

    createIndexes() {
        const indexes = [
            'CREATE INDEX IF NOT EXISTS idx_metrics_device ON metrics(device_id)',
            'CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_metrics_topic ON metrics(topic)'
        ];
        
        indexes.forEach(sql => {
            this.db.run(sql, (err) => {
                if (err) console.error('Error creando índice:', err.message);
            });
        });
    }

    insertMetric(data) {
        return new Promise((resolve, reject) => {
            const sql = `
                INSERT INTO metrics (device_id, topic, temperatura, humedad, luz, estado)
                VALUES (?, ?, ?, ?, ?, ?)
            `;
            
            this.db.run(sql, [
                data.device_id,
                data.topic,
                data.temperatura,
                data.humedad,
                data.luz,
                data.estado
            ], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve({ id: this.lastID });
                }
            });
        });
    }

    getLatestMetrics(deviceId = null) {
        return new Promise((resolve, reject) => {
            let sql = `
                SELECT 
                    device_id,
                    topic,
                    temperatura,
                    humedad,
                    luz,
                    estado,
                    timestamp
                FROM metrics
                ${deviceId ? 'WHERE device_id = ?' : ''}
                ORDER BY timestamp DESC
                LIMIT 1
            `;
            
            const params = deviceId ? [deviceId] : [];
            
            this.db.get(sql, params, (err, row) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(row || null);
                }
            });
        });
    }

    getMetricsHistory(hours = 24, deviceId = null) {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT 
                    id,
                    device_id,
                    topic,
                    temperatura,
                    humedad,
                    luz,
                    estado,
                    timestamp
                FROM metrics
                WHERE timestamp >= datetime('now', '-${hours} hours')
                ${deviceId ? 'AND device_id = ?' : ''}
                ORDER BY timestamp ASC
            `;
            
            const params = deviceId ? [deviceId] : [];
            
            this.db.all(sql, params, (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
        });
    }

    getMetricSeries(metric, from, to) {
        return new Promise((resolve, reject) => {
            const validMetrics = ['temperatura', 'humedad', 'luz'];
            
            if (!validMetrics.includes(metric)) {
                reject(new Error('Métrica no válida'));
                return;
            }
            
            const sql = `
                SELECT 
                    ${metric} as value,
                    timestamp
                FROM metrics
                WHERE ${metric} IS NOT NULL
                    AND timestamp >= ?
                    AND timestamp <= ?
                ORDER BY timestamp ASC
            `;
            
            this.db.all(sql, [from, to], (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
        });
    }

    getDevices() {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT 
                    device_id,
                    COUNT(*) as total_readings,
                    MAX(timestamp) as last_seen
                FROM metrics
                GROUP BY device_id
                ORDER BY last_seen DESC
            `;
            
            this.db.all(sql, [], (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
        });
    }

    getStats() {
        return new Promise((resolve, reject) => {
            const sql = `
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
                WHERE timestamp >= datetime('now', '-24 hours')
            `;
            
            this.db.get(sql, [], (err, row) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(row);
                }
            });
        });
    }

    close() {
        return new Promise((resolve, reject) => {
            this.db.close((err) => {
                if (err) {
                    reject(err);
                } else {
                    console.log('💾 Base de datos cerrada');
                    resolve();
                }
            });
        });
    }
}

module.exports = Database;
