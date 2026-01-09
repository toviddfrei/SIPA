# =================================================================
# LICENCIA: MIT | MARCA: BApp-CITADEL | PROTOCOLO: FORTRESS
# DOCUMENTO: app.py | RUTA: ./web_engine/app.py
# VERSIÓN: 0.8.0 (SIPA Edition) | ESTADO: DEVELOPMENT
# DESCRIPCIÓN: Motor Web del PROYECTO SIPA. Sincronizado con SIPAdoc.
# =================================================================

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, g, request

# --- 1. ANCLAJE AL NÚCLEO SIPA ---
# Localizamos la raíz desde /web_engine/ para importar el CORE
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
sys.path.append(str(BASE_DIR))

# --- 2. IMPORTACIÓN Y CAPTURA DEL LOGGER (SIPA NUCLEUS) ---
import core.config as sipa_config
from web_engine.models import db, PerfilProfesional, NoticiaSeguridad, CronogramaRoadmap
from core.logger.config_loggers import setup_logger

# Capturamos el logger y la lista en memoria que devuelve tu función
logger_web, log_messages_list = setup_logger()

def log_sipa(modulo, mensaje):
    # Usamos el objeto logger que nos ha devuelto tu función
    logger_web.info(f"[{modulo}] {mensaje}")

# --- 3. INSTANCIACIÓN DEL KERNEL FLASK ---
app = Flask(__name__, 
            template_folder=str(CURRENT_DIR / "templates"), 
            static_folder=str(CURRENT_DIR / "static"))

app.config.update(
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{sipa_config.DB_PATH}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='citadel_secure_key_2025'
)

db.init_app(app)

# --- 4. TELEMETRÍA DE LATENCIA (Protocolo Fortress) ---
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

# --- 5. RUTA MAESTRA (HITO 1: CONEXIÓN INDEX) ---
@app.route('/')
def index():
    # Leemos directamente lo que guardaste en SIPAdoc
    perfil = PerfilProfesional.query.first()
    
    # Preparamos los datos para el index.html
    user_data = {
        "nombre": perfil.nombre if perfil else "Daniel Miñana",
        "profesion": perfil.profesion if perfil else "Especialista en IT",
        "biografia": perfil.biografia_corta if perfil else "Cargando perfil desde SIPA...",
        "ubicacion": perfil.ubicacion if perfil else "España",
        "email": perfil.email if perfil else ""
    }
    
    return render_template('index.html', context={"user": user_data})

# --- 6. ARRANQUE CONTROLADO ---
if __name__ == '__main__':
    with app.app_context():
        try:
            db.engine.connect()
            log_sipa("SQLITE", f"Persistencia vinculada en {sipa_config.DB_PATH}")
        except Exception as e:
            log_sipa("ERROR", f"Fallo de conexión DB: {e}")

    log_sipa("FLASK", f"Motor operativo en http://{sipa_config.API_HOST}:{sipa_config.API_PORT}")
    app.run(debug=True, host=sipa_config.API_HOST, port=sipa_config.API_PORT)