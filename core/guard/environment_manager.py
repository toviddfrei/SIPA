# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: environment_manager.py
# Módulo: SIPAbap (Auditoría de Infraestructura)
# Versión: 0.2.5 | Fecha: 05/01/2026
# Autor: Daniel Miñana
# ----------------------------------------------------------
# DESCRIPCIÓN: Motor de validación por MANIFIESTO. 
# Certifica la integridad de directorios y archivos vitales
# garantizando que cada componente del Kernel esté en su sitio.
# ==========================================================

import os
import logging
from core.config import (
    CRITICAL_DIRS,
    STRUCTURE_DIRS,
    CRITICAL_FILES,
    NAME_LOGGER_ESTRUCTURA
)

class InfrastructureError(Exception):
    """Excepción para errores críticos detectados por SIPAbap."""
    pass

class EnvironmentManager:
    """
    Guardián de infraestructura de SIPA. Implementa auditoría 
    detallada de rutas y archivos según el manifiesto operativo.
    """
    def __init__(self):
        self.logger = logging.getLogger(NAME_LOGGER_ESTRUCTURA)

    def _check_write_permission(self, directory):
        """Verifica permisos de escritura para asegurar la persistencia."""
        if not os.access(directory, os.W_OK):
            error_msg = f"ERROR CRÍTICO: Sin permisos de escritura en '{directory}'."
            self.logger.critical(error_msg)
            raise InfrastructureError(error_msg)
        self.logger.debug(f"Integridad de acceso OK: {directory}")

    def check_all(self):
        """
        Ejecuta la auditoría integral (Directorios + Ficheros Vitales).
        """
        try:
            self.logger.info("SIPAbap: Iniciando auditoría detallada por manifiesto...")
            
            # 1. VALIDACIÓN DE DIRECTORIOS (Estructura FHS)
            # Combinamos críticos y estructurales para una pasada limpia
            all_dirs = list(set(CRITICAL_DIRS + STRUCTURE_DIRS))
            for directory in all_dirs:
                if not os.path.exists(directory):
                    # Si es crítico de datos, lo creamos; si es de código, fallamos
                    if directory in CRITICAL_DIRS:
                        os.makedirs(directory, exist_ok=True)
                        self.logger.info(f"Directorio persistente creado: {directory}")
                    else:
                        raise InfrastructureError(f"Directorio de estructura faltante: {directory}")
                
                self._check_write_permission(directory)

            # 2. VALIDACIÓN DE FICHEROS VITALES (Manifiesto de Archivos)
            # Aquí es donde verás los nuevos logs de archivos específicos
            for file_path in CRITICAL_FILES:
                if os.path.isfile(file_path):
                    self.logger.debug(f"Fichero vital certificado: {file_path}")
                else:
                    # Excepción para la DB en el primer arranque absoluto
                    if "sistema.db" in file_path:
                        self.logger.warning(f"Certificación pendiente (DB Inicial): {file_path}")
                        continue
                    
                    msg_error = f"Fichero vital ausente: {file_path}"
                    self.logger.error(msg_error)
                    raise InfrastructureError(msg_error)
            
            self.logger.info("SIPAbap: Manifiesto de infraestructura certificado [OK].")
            return True

        except InfrastructureError as ie:
            self.logger.error(f"Fallo de integridad: {ie}")
            return False
        except Exception as e:
            self.logger.error(f"Error sistémico en validación: {e}")
            return False