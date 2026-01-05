# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: persistence.py
# Módulo: SIPAdel (Kernel / Persistencia)
# Versión: 0.2.5 | Fecha: 05/01/2026
# Autor: Daniel Miñana & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Gestión de la Capa de Persistencia (SQLite).
# Centraliza logs, sesiones y métricas de rendimiento 
# bajo normativa de seguridad y auditoría (Regla del 30%).
# ==========================================================

import sqlite3
import os
from datetime import datetime

# Definición de ruta centralizada
DB_PATH = os.path.join("data", "db", "sistema.db")

class PersistenceManager:
    """
    Motor de persistencia de SIPA. Gestiona el ciclo de vida
    de los datos y la inteligencia de rendimiento (SIPAdel).
    """
    def __init__(self):
        self.db_path = DB_PATH
        self._conn = None
        self._cursor = None # Atributo protegido

    def connect(self):
        """Establece conexión y asegura la integridad de tablas."""
        try:
            # Aseguramos que el directorio existe antes de conectar
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            self._conn = sqlite3.connect(self.db_path, timeout=10)
            self._cursor = self._conn.cursor()
            self.create_tables()
            return True
        except sqlite3.Error as e:
            print(f"[-] Error Crítico en DB: {e}")
            return False

    def create_tables(self):
        """Crea la estructura de tablas necesaria para el ecosistema SIPA."""
        # Logs de Telemetría
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                session_id INTEGER,
                level TEXT,
                name TEXT,
                message TEXT,
                context_json TEXT
            )
        """)
        
        # Historial de Sesiones
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                version TEXT,
                status TEXT
            )
        """)

        # Métricas de Rendimiento (Regla del 30%)
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS metricas_arranque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                duracion REAL,
                estado TEXT
            )
        """)
        self._conn.commit()

    def register_session(self, version="0.2.5"):
        """Registra el inicio de una nueva sesión de SIPAdel."""
        sql = "INSERT INTO sessions (start_time, version, status) VALUES (datetime('now','localtime'), ?, 'ACTIVE')"
        self._cursor.execute(sql, (version,))
        self._conn.commit()
        return self._cursor.lastrowid

    def registrar_metrica_arranque(self, duracion_actual):
        """
        Analiza el rendimiento del arranque comparándolo con la media histórica.
        Aplica la Regla del 30% de Daniel Miñana.
        """
        query_media = "SELECT AVG(duracion) FROM (SELECT duracion FROM metricas_arranque ORDER BY id DESC LIMIT 20)"
        self._cursor.execute(query_media)
        res = self._cursor.fetchone()[0]
        media_historica = res if res is not None else duracion_actual

        umbral_alerta = media_historica * 1.30
        estado = "OPTIMO" if duracion_actual <= umbral_alerta else "IRREGULAR"
        
        self._cursor.execute("INSERT INTO metricas_arranque (timestamp, duracion, estado) VALUES (?, ?, ?)", 
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), duracion_actual, estado))
        self._conn.commit()
        
        return estado, media_historica

    def obtener_metricas_recientes(self, limite=10):
        """
        Interfaz para el Panel Root: Recupera datos para visualización.
        """
        try:
            # CORRECCIÓN: Usamos self._cursor para mantener consistencia
            query = "SELECT timestamp, duracion, estado FROM metricas_arranque ORDER BY id DESC LIMIT ?"
            self._cursor.execute(query, (limite,))
            return self._cursor.fetchall()
        except Exception as e:
            print(f"Error recuperando métricas: {e}")
            return []

    def is_connected(self):
        return self._conn is not None