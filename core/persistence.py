# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: persistence.py | Módulo: SIPAdel (Kernel)
# Versión: 0.2.5 (Protocolo Tabla 0) | Fecha: 11/01/2026
# ==========================================================

import sqlite3
import os
import sys
import json
from datetime import datetime

try:
    from core.config import DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)
    from core.config import DB_PATH

class PersistenceManager:
    """
    Motor de persistencia de SIPA. Gestiona el ciclo de vida de los datos,
    la identidad del Root y la telemetría de rendimiento.
    """
    def __init__(self):
        self.db_path = str(DB_PATH)
        self._conn = None
        self._cursor = None 
        self.connect()

    def connect(self):
        """Establece conexión con Row Factory y aplica el Schema."""
        try:
            db_dir = os.path.dirname(self.db_path)
            os.makedirs(db_dir, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._cursor = self._conn.cursor()
            
            self.create_tables()
            self._poblar_tipos_maestros() # Única adición al flujo original
            
            return True
        except Exception as e:
            print(f"\n[-] ERROR CRÍTICO EN EL KERNEL: {e}")
            return False

    def create_tables(self):
        """Implementación del SCHEMA DEFINITIVO y Estructuras de Control."""
        # 1. ROLES Y USUARIO
        self._cursor.execute("CREATE TABLE IF NOT EXISTS type_user (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, descripcion TEXT)")
        
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_user_id INTEGER,
                nombre_completo TEXT,
                profesion_principal TEXT,
                biografia_corta TEXT,
                datos_legales_json TEXT,
                dni TEXT UNIQUE,
                n_seg_soc TEXT UNIQUE,
                carnet_conducir TEXT,
                datos_finanzas_json TEXT,
                cta_banco_1 TEXT UNIQUE,
                cta_banco_2 TEXT UNIQUE,
                card_number_1 TEXT UNIQUE,
                card_number_2 TEXT UNIQUE,
                datos_contacto_json TEXT,
                email_1 TEXT NOT NULL UNIQUE CHECK (email_1 LIKE '%@%.%'),
                email_2 TEXT NOT NULL UNIQUE CHECK (email_2 LIKE '%@%.%'),
                redes_sociales_json TEXT,
                red_1 TEXT, red_2 TEXT, red_3 TEXT,
                config_seguridad TEXT,
                vinculo_master_md TEXT,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (type_user_id) REFERENCES type_user(id)
            )""")

        # 2. AUDITORÍA, SESIONES Y LOGS (Estructura original para SIPAbap)
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS sys_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario_afectado INTEGER,
                accion TEXT,
                time_log DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

        self._cursor.execute("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, start_time TEXT, version TEXT, status TEXT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS app_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, session_id INTEGER, level TEXT, name TEXT, message TEXT, context_json TEXT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS metricas_arranque (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, duracion REAL, estado TEXT)")

        # 3. TRIGGER AUTOMÁTICO
        self._cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS audit_perfil_update AFTER UPDATE ON user
            BEGIN
                INSERT INTO sys_audit (id_usuario_afectado, accion) 
                VALUES (NEW.id, 'Perfil actualizado por el sistema');
            END;""")
        
        self._conn.commit()

    def _poblar_tipos_maestros(self):
        """Inyecta los 4 pilares de identidad SIPA si la tabla está vacía."""
        tipos = [
            (1, 'PROPIETARIO', 'Acceso Root Total. Daniel Miñana.'),
            (2, 'DESARROLLADOR', 'Permisos técnicos y arquitectura.'),
            (3, 'USUARIO', 'Perfil público Beta.'),
            (4, 'IA', 'Entidad de procesamiento autónomo.')
        ]
        self._cursor.executemany("INSERT OR IGNORE INTO type_user (id, nombre, descripcion) VALUES (?, ?, ?)", tipos)
        self._conn.commit()

    # --- MÉTODOS ORIGINALES (SIN CAMBIOS) ---
    def register_session(self, version="0.2.5"):
        try:
            sql = "INSERT INTO sessions (start_time, version, status) VALUES (datetime('now','localtime'), ?, 'ACTIVE')"
            self._cursor.execute(sql, (version,))
            self._conn.commit()
            return self._cursor.lastrowid
        except: return 0

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def registrar_metrica_arranque(self, duracion_actual):
        try:
            self._cursor.execute("SELECT AVG(duracion) FROM (SELECT duracion FROM metricas_arranque ORDER BY id DESC LIMIT 20)")
            res = self._cursor.fetchone()[0]
            media = res if res is not None else duracion_actual
            estado = "OPTIMO" if duracion_actual <= (media * 1.30) else "IRREGULAR"
            self._cursor.execute("INSERT INTO metricas_arranque (timestamp, duracion, estado) VALUES (?, ?, ?)", 
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), duracion_actual, estado))
            self._conn.commit()
            return estado, media
        except: return "ERROR", 0

    def get_user_profile(self):
        try:
            self._cursor.execute("SELECT * FROM user WHERE id = 1")
            res = self._cursor.fetchone()
            return dict(res) if res else None
        except: return None

    def is_connected(self):
        try: return self._conn is not None and self._conn.execute("SELECT 1")
        except: return False

db_engine = PersistenceManager()

if __name__ == "__main__":
    # Ignición controlada
    db_engine._cursor.execute("""
        INSERT OR IGNORE INTO user (id, type_user_id, nombre_completo, profesion_principal, biografia_corta, email_1, email_2)
        VALUES (1, 1, 'Daniel Miñana Montero', 'Ingeniero de Sistemas SIPA', 
        'Perfil automatizado bajo protocolo FORTRESS.', 'daniel@sipa.local', 'soporte@sipa.local')
    """)
    db_engine._conn.commit()
    print("[+] Enchufe con corriente: Estructura SIPA verificada.")