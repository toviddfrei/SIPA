# =====================================================================
# MÓDULO: sbsipabap_log.py (v0.2.5 - Core Infr)
# UBICACIÓN: /home/toviddfrei/SIPA/external/SIPAbap/core/services/
# DESCRIPCIÓN: Servicio Unificado de Logs de Alta Intensidad (Caja Negra).
#              Gestiona ListHandler en memoria y DatabaseHandler persistente.
# AUTOR: Daniel Miñana Montero & Gemini
# =====================================================================

import logging
from logging import Handler
import json

# Absorción de la Fuente de Verdad (RAM del Router)
from core.config import (
    NAME_LOGGER_ESTRUCTURA,
    LOG_LEVEL,
    LOG_FORMAT
)

# Inicializamos el formatter único que usaremos en todos los handlers
BASIC_FORMATTER = logging.Formatter(LOG_FORMAT)

# =====================================================================
# 🎛️ SECCIÓN 1: MANEJADORES DE LOGS (HANDLERS)
# =====================================================================

class ListHandler(Handler):
    """Manejador de Logs personalizado que escribe los registros en una lista de Python."""
    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list

    def emit(self, record):
        """Formatea el registro y lo añade a la lista en memoria."""
        msg = self.format(record)
        self.log_list.append(msg)


class DatabaseHandler(Handler):
    """
    Manejador de Logs personalizado que escribe registros en la tabla app_logs de SQLite.
    Acepta logs de nivel INFO o superior por defecto.
    """
    def __init__(self, db_manager, session_id=None):
        super().__init__(logging.INFO) 
        self.db_manager = db_manager
        self.session_id = session_id

    def emit(self, record):
        """Prepara el registro de auditoría forense y lo inserta en la base de datos."""
        # Si la conexión no existe o el handler no está listo, salimos discretamente.
        if not self.db_manager or not self.db_manager.is_connected:
            return

        # Prepara los datos estructurados para la inserción en la tabla app_logs
        record_data = {
            'timestamp': self.formatter.formatTime(record, self.formatter.datefmt), 
            'session_id': self.session_id,
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'pathname': record.pathname,
            'lineno': record.lineno,
            'funcName': record.funcName,
            'process': record.process,
            'thread': record.threadName,
            'context_json': json.dumps(getattr(record, 'context', None))
        }

        try:
            # Llama a la función de inserción de tu DatabaseManager
            self.db_manager.insert_log(record_data)
        except Exception as e:
            # Si la inserción falla, informamos por consola para no tumbar la ejecución principal
            print(f"Error al insertar log en la DB. Log fallido: {record.message}. Error: {e}")


# =====================================================================
# ⚙️ SECCIÓN 2: ORQUESTADORES DE CONFIGURACIÓN (SETUP LOGGERS)
# =====================================================================

def setup_logger():
    """
    Fase 1: Configura el logger con el ListHandler (En memoria).
    Activo desde el milisegundo cero del arranque.
    """
    log_messages = [] 

    logger = logging.getLogger(NAME_LOGGER_ESTRUCTURA)
    logger.setLevel(LOG_LEVEL)

    # Acoplamos el manejador de memoria
    list_handler = ListHandler(log_messages)
    list_handler.setFormatter(BASIC_FORMATTER)
    logger.addHandler(list_handler)
    
    # Previene la propagación de logs duplicados al handler raíz de Python
    logger.propagate = False 
    
    return logger, log_messages


def setup_advanced_logging(db_manager, session_id):
    """
    Fase 2: Segunda marcha. Acopla el DatabaseHandler al logger principal
    una vez que la persistencia SQLite se ha despertado.
    """
    logger = logging.getLogger(NAME_LOGGER_ESTRUCTURA)
    
    # Instanciamos el manejador de base de datos pasándole tu gestor conectado
    db_handler = DatabaseHandler(db_manager, session_id)
    db_handler.setLevel(logging.INFO) 
    db_handler.setFormatter(BASIC_FORMATTER) 
    
    logger.addHandler(db_handler)
    logger.info("DatabaseHandler configurado y acoplado al búnker SQLite con éxito.")