"""
PROYECTO SIPA - Motor de Configuración Global
Hito 1.1: Fusión Nuclear SIPAdel + BApp Legacy
---------------------------------------------------------
Este fichero centraliza TODAS las constantes necesarias para:
1. SIPAbap (Arranque e infraestructura)
2. SIPAdel (Kernel y Persistencia)
3. UI (Estilos y Ventanas)
4. Logger (Handlers y Configuración de registros)
"""

import logging
from pathlib import Path

# =====================================================================
# BLOQUE 1: IDENTIDAD Y METADATOS (Marca SIPA)
# =====================================================================
APP_TITLE = "PROYECTO SIPA"
PROJECT_NAME = "SIPA"
APP_DESCRIPTION = "Sistema de Inteligencia de Perfil Automatizado"
AUTHOR = "Daniel Miñana Montero"
NUMBER_VERSION = "0.2.5"
ENVIRONMENT = "DEVELOPMENT"  # Cambiar a PRODUCTION para despliegue en Arsys

# =====================================================================
# BLOQUE 2: FILESYSTEM (Arquitectura de Rutas Absolutas)
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorios de Nivel 1 (FHS SIPA)
DIR_CORE      = BASE_DIR / "core"
DIR_DATA      = BASE_DIR / "data"
DIR_LOGS      = BASE_DIR / "logs"
DIR_INTERFACE = BASE_DIR / "interface"
DIR_EXTERNAL  = DIR_CORE / "external"
DIR_SCRIPTS   = BASE_DIR / "scripts"

# Sub-directorios Críticos (Estructura de Datos)
DIR_DB        = DIR_DATA / "db"
DIR_INBOX     = DIR_DATA / "inbox"
DIR_ARCHIVE   = DIR_DATA / "archive"
DIR_KNOWLEDGE = DIR_DATA / "knowledge"

# Directorios heredados de BApp (Mantenemos compatibilidad)
LOGGER_DIR = DIR_CORE / "logger"
UI_DIR     = DIR_INTERFACE  # En SIPA, UI vive en interface
UTILS_DIR  = DIR_CORE / "utils"

# Listas para el Guardián (SIPAbap)
CRITICAL_DIRS = [DIR_LOGS, DIR_DATA, DIR_DB, DIR_CORE, DIR_INTERFACE]
STRUCTURE_DIRS = [DIR_INBOX, DIR_ARCHIVE, DIR_KNOWLEDGE, DIR_EXTERNAL, LOGGER_DIR]

# =====================================================================
# BLOQUE 3: PERSISTENCIA Y FICHEROS CRÍTICOS
# =====================================================================
DB_NAME = "sistema.db"
DB_PATH = DIR_DB / DB_NAME
LOG_FILE = DIR_LOGS / "SIPA_execution.log"

# Ficheros testigo de integridad
SIPA_ROOT_ANCHOR = BASE_DIR / ".sipa_root"
IDENTITY_FILE    = DIR_DATA / "identity.json"

# Listas de verificación de ficheros para SIPAbap
CRITICAL_FILES = [
    BASE_DIR / "main.py",
    DIR_CORE / "config.py",
    SIPA_ROOT_ANCHOR,
    IDENTITY_FILE,
    DB_PATH
]

# =====================================================================
# BLOQUE 4: SISTEMA DE LOGGING Y HANDLERS (BApp Legacy)
# =====================================================================
# Nombres de Loggers para que tus Handlers actuales funcionen
NAME_LOGGER_ESTRUCTURA = "SIPA_init"
NAME_LOGGER_ARRANQUE   = "SIPA_Boot"
NAME_LOGGER_DASHBOARD  = "SIPA_Dashboard"
NAME_LOGGER_API        = "SIPA_API"

LOG_LEVEL  = logging.DEBUG
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# =====================================================================
# BLOQUE 5: CONFIGURACIÓN DE INTERFAZ (UI/UX)
# =====================================================================
BG_COLOR_PRIMARY = "#08527A"  # Tu azul corporativo
UI_TITLE = f"{APP_TITLE} v{NUMBER_VERSION} - Daniel Miñana"
UI_WIDTH = 1024
UI_HEIGHT = 768

# =====================================================================
# BLOQUE 6: SERVICIOS Y MÓDULOS (API & Módulos Externos)
# =====================================================================
API_PORT = 5000
API_HOST = '127.0.0.1'

# Registro de disponibilidad de módulos
MODULES_STATE = {
    "SIPAbap": True,   # Infraestructura (ACTIVO)
    "SIPAdel": True,   # Kernel (ACTIVO)
    "BApp_UI": True,   # Interfaz PySide6 (ACTIVO)
    "SIPAsaf": False,  # CyberAudit (EN ESPERA)
    "SIPAcur": False   # Curator (EN ESPERA)
}