# ---
# logger/config_loggers.py -> Fichero que mantiene los logger necesarios para la aplicación
# ---

import logging
from .handlers import ListHandler, DatabaseHandler # Importación DatabaseHandler

from core.config import (
    NAME_LOGGER_ESTRUCTURA,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE # Necesario para el FileHandler
)

# Inicializamos el formatter que usaremos en todos los handlers
BASIC_FORMATTER = logging.Formatter(LOG_FORMAT)

def setup_logger():
    """
    Configura el logger de la aplicación con el ListHandler (en memoria).
    
    Retorna:
        tuple: (logging.Logger, list) - El objeto logger y la lista de mensajes.
    """
    log_messages = [] # La lista en memoria que contendrá los logs

    logger = logging.getLogger(NAME_LOGGER_ESTRUCTURA)
    logger.setLevel(LOG_LEVEL) # Usa el nivel definido en settings.py

    # 1. ListHandler (Logs en memoria, siempre activo al inicio)
    list_handler = ListHandler(log_messages)
    list_handler.setFormatter(BASIC_FORMATTER)
    logger.addHandler(list_handler)
    
    # Previene que los logs se propaguen a los handlers raíz (si existieran)
    logger.propagate = False 
    
    return logger, log_messages

def setup_advanced_logging(db_manager, session_id):
    """
    Añade los handlers de persistencia (Archivo y DB) al logger principal.
    
    Argumentos:
        db_manager: Instancia de DatabaseManager ya conectada.
        session_id: ID de la sesión recién creada.
    """
    logger = logging.getLogger(NAME_LOGGER_ESTRUCTURA)
    
    # 1. FileHandler (Para logs DEBUG o superior)
    # Escribe todos los logs en el archivo BApp_log.log
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG) # Guarda logs DEBUG
    file_handler.setFormatter(BASIC_FORMATTER)
    logger.addHandler(file_handler)
    logger.info(f"FileHandler configurado. Logs guardados en: {LOG_FILE}")
    
    # 2. DatabaseHandler (Para logs INFO o superior)
    # Escribe logs estructurados en la tabla app_logs
    db_handler = DatabaseHandler(db_manager, session_id)
    db_handler.setLevel(logging.INFO) # Guarda logs INFO o superiores en la DB
    # El DatabaseHandler no necesita Formatter para el mensaje, pero sí para el timestamp.
    # Usaremos el Formatter básico para que obtenga el formato de tiempo consistente.
    db_handler.setFormatter(BASIC_FORMATTER) 
    logger.addHandler(db_handler)
    logger.info("DatabaseHandler configurado y listo para registrar sesiones.")

# --- Funciones de otros loggers pendientes de trabajar ---
""" 
def logger_arranque():
# ...
"""

""" Pendiente de trabajar en futuro NO TOCAR
def logger_arranque():
    logger = logging.getLogger(NAME_LOGGER_ARRANQUE)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.info("Logger configurado")


def logger_dashboard():
    logger = logging.getLogger(NAME_LOGGER_DASHBOARD)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.info("Logger configurado")
"""