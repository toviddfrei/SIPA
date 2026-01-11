# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: config.py
# Módulo: SIPA-CORE (Motor de Configuración Global)
# Versión: 0.2.5 | Fecha: 06/01/2026
# Autor: Daniel Miñana Montero & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Única Fuente de Verdad (SSoT) para el sistema.
# Centraliza rutas absolutas, constantes de UI y taxonomía
# de datos para garantizar la integridad del ecosistema.
# ==========================================================

import logging
import os
from pathlib import Path

# =====================================================================
# BLOQUE 1: IDENTIDAD Y METADATOS (Marca SIPA)
# =====================================================================
APP_TITLE = "PROYECTO SIPA"
PROJECT_NAME = "SIPA"
APP_DESCRIPTION = "Sistema de Inteligencia de Perfil Automático"
AUTHOR = "Daniel Miñana Montero"
NUMBER_VERSION = "0.2.5"
ENVIRONMENT = "DEVELOPMENT"

# =====================================================================
# BLOQUE 2: FILESYSTEM (Arquitectura de Rutas Absolutas)
# =====================================================================
# BASE_DIR es la raíz: /home/toviddfrei/SIPA_PROJECT
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorios de Nivel 1 (FHS SIPA)
DIR_CORE      = BASE_DIR / "core"
DIR_DATA      = BASE_DIR / "data"
DIR_LOGS      = BASE_DIR / "logs"
DIR_INTERFACE = BASE_DIR / "interface"
DIR_SCRIPTS   = BASE_DIR / "scripts"
DIR_COMPONENTS = BASE_DIR / "components"

# Módulos y Extensiones (Crítico para FHS-CyberAudit y Legacy)
DIR_EXTERNAL  = BASE_DIR / "external"

# Sub-directorios Críticos (Estructura de Datos) - Construidos sobre DIR_DATA
DIR_DB        = DIR_DATA / "db"
DIR_INBOX     = DIR_DATA / "inbox"
DIR_ARCHIVE   = DIR_DATA / "archive"
DIR_KNOWLEDGE = DIR_DATA / "knowledge"

# Directorios de Evidencias (Trayectoria) - CORRECCIÓN: Colgando de DIR_DATA directamente
DIR_EVIDENCE     = DIR_DATA / "evidences"
DIR_EVID_LABORAL = DIR_EVIDENCE / "laboral"
DIR_EVID_FORMAT  = DIR_EVIDENCE / "formativa"

# Directorios heredados de BApp (Mantenemos compatibilidad)
LOGGER_DIR = DIR_CORE / "logger"
UI_DIR     = DIR_INTERFACE
UTILS_DIR  = DIR_CORE / "utils"

# Variable Maestra para compatibilidad con sistemas legados u os.path
PROJECT_ROOT = str(BASE_DIR)

# --- NUEVO: Mapeo para el Motor Web SIPA ---
DIR_WEB_ENGINE = BASE_DIR / "web_engine"
TEMPLATES_DIR  = DIR_WEB_ENGINE / "templates"
STATIC_DIR     = DIR_WEB_ENGINE / "static"

# Listas para el Guardián (SIPAbap)
CRITICAL_DIRS = [DIR_LOGS, DIR_DATA, DIR_DB, DIR_CORE, DIR_INTERFACE, DIR_EVIDENCE, DIR_EXTERNAL]
STRUCTURE_DIRS = [
    DIR_INBOX, DIR_ARCHIVE, DIR_KNOWLEDGE, 
    LOGGER_DIR, DIR_EVID_LABORAL, DIR_EVID_FORMAT, DIR_COMPONENTS, DIR_WEB_ENGINE, TEMPLATES_DIR, STATIC_DIR
]

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
# BLOQUE 4: SISTEMA DE LOGGING Y HANDLERS
# =====================================================================
NAME_LOGGER_ESTRUCTURA = "SIPA_init"
NAME_LOGGER_ARRANQUE   = "SIPA_Boot"
NAME_LOGGER_DASHBOARD  = "SIPA_Dashboard"
NAME_LOGGER_API        = "SIPA_API"

LOG_LEVEL  = logging.DEBUG
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# =====================================================================
# BLOQUE 5: CONFIGURACIÓN DE INTERFAZ (UI/UX)
# =====================================================================
BG_COLOR_PRIMARY = "#08527A"  # Azul corporativo SIPA
UI_TITLE = f"{APP_TITLE} v{NUMBER_VERSION} - {AUTHOR}"
UI_WIDTH = 1024
UI_HEIGHT = 768

# =====================================================================
# BLOQUE 6: SERVICIOS Y MÓDULOS (API & Módulos Externos)
# =====================================================================
API_PORT = 5000
API_HOST = '127.0.0.1'

# Registro de disponibilidad de módulos
MODULES_STATE = {
    "SIPAbap": True,   # Infraestructura
    "SIPAdel": True,   # Kernel
    "BApp_UI": True,   # Interfaz
    "FHS_CyberAudit": True, # Activado
    "SIPAcur": False   # Curator
}

# =====================================================================
# BLOQUE 7: ETIQUETADO DOCUMENTOS (Taxonomía SIPA)
# =====================================================================

# Nivel 1: El Contexto (Context)
SIPA_LEVEL_1 = ["PERSONAL", "PROYECTO SIPA", "TRAYECTORIA", "PROYECTO FHS-CYBERAUDIT"]

# Nivel 2: La Acción (Action)
SIPA_LEVEL_2 = [
    "BUG", "MEJORA", "DOC", "PENDIENTE", "COMPLETADO", 
    "TAREA", "NOTA", "DAILY", "SPEC", "CHAT", 
    "LABORAL", "FORMATIVA", "HITO", "PERFIL", "LOGRO"
]

# ==========================================================
# FIRMADO: Daniel Miñana | SIPA v0.2.5 - Excellence Nucleus
# ==========================================================