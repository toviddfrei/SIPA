# ---
# logger/handlers.py -> Crea una lista de log en memoria y Database Handler
# ---

import logging
from logging import Handler
import json

# El ListHandler ya lo tienes implementado
class ListHandler(Handler):
    """Manejador de Logs personalizado que escribe los registros en una lista de Python."""
    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list

    def emit(self, record):
        """Formatea el registro y lo añade a la lista."""
        msg = self.format(record)
        self.log_list.append(msg)

# --- Nuevo Database Handler ---

class DatabaseHandler(Handler):
    """
    Manejador de Logs personalizado que escribe registros en la tabla app_logs de SQLite.
    Acepta logs de nivel INFO o superior por defecto.
    """
    def __init__(self, db_manager, session_id=None):
        # Establece el nivel mínimo de logs a manejar a INFO
        super().__init__(logging.INFO) 
        self.db_manager = db_manager
        # session_id será establecido más tarde al registrar la sesión.
        self.session_id = session_id

    def emit(self, record):
        """Prepara el registro y lo inserta en la base de datos."""
        
        # Si la conexión no existe o el handler no está listo, salimos.
        if not self.db_manager or not self.db_manager.is_connected:
            return

        # Prepara los datos del registro para la inserción
        record_data = {
            # El tiempo formateado por defecto de Python logging
            'timestamp': self.formatter.formatTime(record, self.formatter.datefmt), 
            'session_id': self.session_id,
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            
            # Datos de origen/traza
            'pathname': record.pathname,
            'lineno': record.lineno,
            'funcName': record.funcName,
            
            # Contexto de Ejecución
            'process': record.process,
            'thread': record.threadName,
            
            # Contexto Extensible (usando el dict 'extra' si existe)
            'context_json': json.dumps(getattr(record, 'context', None))
        }

        try:
            # Llama a la función de inserción del DatabaseManager
            self.db_manager.insert_log(record_data)
        except Exception as e:
            # Si la inserción falla, informamos por consola (no queremos que el fallo de log crashee la app)
            print(f"Error al insertar log en la DB. Log fallido: {record.message}. Error: {e}")
