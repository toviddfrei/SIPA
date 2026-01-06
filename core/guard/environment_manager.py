# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automatizado
# Archivo: environment_manager.py
# Módulo: SIPAbap (Auditoría de Infraestructura)
# Versión: 0.2.5 | Fecha: 06/01/2026
# Autor: Daniel Miñana & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Motor de validación y AUTORREPARACIÓN. 
# Certifica la integridad de directorios y archivos vitales.
# Si faltan elementos de datos o testigos, los genera para
# garantizar la continuidad del arranque (Ignición).
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
    detallada y recuperación automática de rutas.
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
        Implementa lógica de creación automática para elementos de datos.
        """
        try:
            self.logger.info("SIPAbap: Iniciando auditoría detallada por manifiesto...")
            
            # 1. VALIDACIÓN Y REPARACIÓN DE DIRECTORIOS
            all_dirs = list(set(CRITICAL_DIRS + STRUCTURE_DIRS))
            for directory in all_dirs:
                if not os.path.exists(directory):
                    # Excelencia: SIPA repara su propia estructura de datos
                    self.logger.warning(f"Infraestructura ausente: {directory}. Iniciando reparación...")
                    os.makedirs(directory, exist_ok=True)
                    self.logger.info(f"Directorio restaurado con éxito: {directory}")
                
                self._check_write_permission(directory)

            # 2. VALIDACIÓN Y GENERACIÓN DE FICHEROS VITALES
            for file_path in CRITICAL_FILES:
                f_str = str(file_path)
                
                if os.path.isfile(file_path):
                    self.logger.debug(f"Fichero vital certificado: {f_str}")
                else:
                    # CASO A: Ficheros Testigo o Metadatos (Autorreparables)
                    if ".sipa_root" in f_str or "identity.json" in f_str:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            if "identity.json" in f_str:
                                f.write('{"status": "initialized", "owner": "Daniel Miñana"}')
                            else:
                                f.write('') # .sipa_root vacío
                        self.logger.info(f"Fichero testigo generado automáticamente: {f_str}")
                        continue

                    # CASO B: Base de Datos (Se delega al PersistenceManager)
                    if "sistema.db" in f_str:
                        self.logger.warning(f"Certificación diferida (DB inicial): {f_str}")
                        continue
                    
                    # CASO C: Archivos de Código (Irreparables automáticamente)
                    msg_error = f"Fichero lógico ausente (Requiere intervención): {f_str}"
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

# ==========================================================
# FIRMADO: Daniel Miñana | SIPA v0.2.5 - Resilience Guard
# ==========================================================