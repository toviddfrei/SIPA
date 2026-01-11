# =================================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: app.py | RUTA: ./web_engine/app.py
# Versión: 0.8.5 (SIPA SQL-Pure) | ESTADO: DEVELOPMENT
# DESCRIPCIÓN: Motor Web SIPA. Conexión directa con SIPAdel (Kernel).
# =================================================================

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, g, request

# --- 1. ANCLAJE AL NÚCLEO SIPA ---
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
sys.path.append(str(BASE_DIR))

# --- 2. IMPORTACIÓN DEL KERNEL SIPA ---
import core.config as sipa_config
from core.persistence import db_engine  # El "Enchufe" SIPAdel
from core.logger.config_loggers import setup_logger

# Configuración de Logger SIPA
logger_web, log_messages_list = setup_logger()

def log_sipa(modulo, mensaje):
    logger_web.info(f"[{modulo}] {mensaje}")
    # Registro en la base de datos SIPA
    db_engine.insert_log({'level': 'INFO', 'message': f"[{modulo}] {mensaje}"})

# --- 3. INSTANCIACIÓN FLASK (Beber de la fuente: core/config.py) ---
app = Flask(__name__, 
            template_folder=str(sipa_config.TEMPLATES_DIR), 
            static_folder=str(sipa_config.STATIC_DIR))

app.config.update(
    SECRET_KEY='sipa_secure_key_2026'
)

# --- 4. TELEMETRÍA DE RENDIMIENTO (Regla del 30%) ---
@app.before_request
def start_timer():
    g.start_time = time.perf_counter()

@app.context_processor
def inject_global_metrics():
    return {
        "brand": {
            "name": sipa_config.PROJECT_NAME,
            "version": sipa_config.NUMBER_VERSION,
            "author": sipa_config.AUTHOR
        },
        "now": datetime.now()
    }

# --- 5. RUTA MAESTRA (INDEX CONEXIÓN PURE SQL) ---
@app.route('/')
def index():
    perfil = db_engine.get_user_profile()
    
    # 1. Datos del Usuario
    user_data = {
        "nombre": perfil['nombre_completo'] if perfil else "Daniel Miñana Montero",
        "profesion": perfil['profesion_principal'] if perfil else "Ingeniero de Sistemas SIPA",
        "biografia": perfil['biografia_corta'] if perfil else "Sistema operativo v0.2.5",
        "ubicacion": "España",
        "email": perfil['email_1'] if perfil else "admin@sipa.local"
    }

    # 2. Datos de Sistema (Lo que el HTML pide como 'sys')
    sys_data = {
        "codename": "SIPA-EXCELLENCE",
        "version": sipa_config.NUMBER_VERSION,
        "status": "OPERATIONAL"
    }
    
    duracion = time.perf_counter() - g.start_time
    db_engine.registrar_metrica_arranque(duracion)
    
    # Enviamos ambos al template
    return render_template('index.html', context={"user": user_data}, sys=sys_data)

@app.route('/ayuda')
def ayuda_view():
    """Vista de ayuda del sistema SIPA."""
    return render_template('ayuda.html')

# --- 6. ARRANQUE DEL SISTEMA ---
if __name__ == '__main__':
    # Validación de la Persistencia SIPAdel
    if db_engine.is_connected():
        log_sipa("SQLITE", f"Kernel de persistencia vinculado correctamente.")
        # Registro de sesión de arranque SIPA
        session_id = db_engine.register_session(version=sipa_config.NUMBER_VERSION)
        log_sipa("SIPA", f"Sistema operativo. Sesión #{session_id} iniciada.")
    else:
        log_sipa("ERROR", "No se pudo establecer conexión con SIPAdel.")

    log_sipa("WEB", f"Servidor operativo en puerto {sipa_config.API_PORT}")
    
    try:
        app.run(debug=True, host=sipa_config.API_HOST, port=sipa_config.API_PORT)
    finally:
        # Cierre de seguridad SIPA
        db_engine.close()
        print("[SIPA] Conexión de persistencia cerrada.")