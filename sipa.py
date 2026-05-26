# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: sipa.py
# Módulo: Core Dashboard / SPA Manager
# Versión: 2.1.0.0 | Fecha: 26/05/2026
# Autor: Daniel Miñana Montero & Gemini
# ==========================================================

import sys
import os
import re
import subprocess
import getpass 
import random
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, \
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, \
                             QFrame, QTextEdit, QStackedWidget)
from PySide6.QtCore import Qt, QTimer

# =================================================================
# FASE 0: IGNICIÓN DEL GATEWAY SEGURIDAD (RDDR, CAJA NEGRA Y FORENSE)
# =================================================================

# Puente temporal para acoplar el Router transversal en el milisegundo cero
RUTA_BOOTSTRAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "services")
if RUTA_BOOTSTRAP not in sys.path:
    sys.path.insert(0, RUTA_BOOTSTRAP)

try:
    from ssipa_router import SIPARouterGateway
    # 1. El Router calcula la raíz en RAM, monta directorios y arranca basicConfig
    ROOT_SIPA = SIPARouterGateway.inicializar_entorno()
except ImportError as e:
    print(f"❌ CRITICAL: No se pudo acoplar el Gateway de Enrutamiento: {e}")
    sys.exit(1)

# 2. IGNICIÓN DEL SISTEMA DE LOGS AVANZADO (Nuevo Servicio Unificado)
try:
    from external.SIPAbap.core.services.sbsipabap_log import setup_logger, setup_advanced_logging
    logger_estructura, log_messages = setup_logger()
except Exception as e:
    print(f"⚠️ Alerta Core: Sistema de logs avanzado en standby: {e}")

# 3. VERIFICACIÓN Y COMPROBACIÓN DE ENTRAÑAS (Tus nuevos servicios)
try:
    from external.SIPAbap.core.services.sbsipabap_env import EnvironmentManager
    guardian = EnvironmentManager()
    if not guardian.check_all():
        logger_estructura.critical("Fallo catastrófico en la certificación de infraestructura FHS.")
        sys.exit(1)
        
    from external.SIPAbap.core.services.sbsipabap_sentinel import sonda
    if not sonda.ejecutar_auditoria(__file__):
        logger_estructura.critical("Bloqueo preventivo: Firma digital o árbol AST corrupto.")
        sys.exit(1)

except ImportError as e:
    print(f"⚠️ Nota de desarrollo: Motores SIPAbap en proceso de acople: {e}")

# =================================================================
# CONFIGURACIÓN DE RUTAS CENTRALIZADA (VÍA GATEWAY)
# =================================================================
RUTA_SIPACUR   = SIPARouterGateway.obtener_ruta("external", "SIPAcur")
RUTA_SERVICIOS = SIPARouterGateway.obtener_ruta("core", "services")
# =================================================================

print("\n" + "="*60)
print("             SISTEMA INTEGRAL SIPA - CORE SPA")
print("="*60)

# Importaciones dinámicas de módulos gráficos SIPA (Mapeo de Trazabilidad)
try:
    from sipacur import SIPAcurDashboard
    print("🟢 Interfaz Módulo: 'SIPAcurDashboard' acoplada con éxito.")
except ImportError:
    print("⚠️  Componente Visual: 'SIPAcurDashboard' no disponible.")
    SIPAcurDashboard = None

try:
    from ssipa_servicios import VistaServicios
    print("🟢 Componente Core: 'VistaServicios' acoplado con éxito.")
except ImportError:
    print("⚠️  Componente Visual: 'VistaServicios' no disponible.")
    VistaServicios = None

try:
    from ssipa_edit_markdown import SIPAMarkdownEditor
    print("🟢 Componente Core: 'SIPAMarkdownEditor' acoplado con éxito.")
except ImportError:
    print("⚠️  Componente Visual: 'SIPAMarkdownEditor' no disponible.")
    SIPAMarkdownEditor = None

try:
    from ssipa_identif import HuellaDigitalFrame
    print("🟢 Componente Core: 'HuellaDigitalFrame' acoplado con éxito.")
except ImportError:
    print("⚠️  Componente Visual: 'HuellaDigitalFrame' no disponible.")
    HuellaDigitalFrame = None

try:
    from ssipa_config import ConfigEditorNode
    print("🟢 Componente Core: 'ConfigEditorNode' acoplado con éxito.")
except ImportError:
    print("⚠️  Componente Visual: 'ConfigEditorNode' no disponible.")
    ConfigEditorNode = None

# IMPORTACIÓN DE LA PASARELA DE ACCESO AUTORIZADO (SIPAbap Services)
try:
    from external.SIPAbap.core.services.sbsipabap_login import SIPALoginFrame, SIPALoginManager
    from core.persistence import db_engine
    print("🟢 Pasarela de Identidad: 'SIPALoginFrame' integrada correctamente.")
except ImportError as e:
    print(f"❌ CRITICAL: No se pudo acoplar el módulo de autenticación: {e}")
    sys.exit(1)

print("="*60 + "\n")

USER_NAME = getpass.getuser()
if not os.path.exists(ROOT_SIPA) or "SIPA" not in ROOT_SIPA:
    CONFIG_FILE = f"/home/{USER_NAME}/SIPA/data/archive/template_propietario.md"
    SERVICE_CONFIG_PATH = f"/home/{USER_NAME}/SIPA/core/services/ssipa_config.py"
else:
    CONFIG_FILE = os.path.join(ROOT_SIPA, "data", "archive", "template_propietario.md")
    SERVICE_CONFIG_PATH = os.path.join(ROOT_SIPA, "core/services/ssipa_config.py")

QSS_FILE_PATH = SIPARouterGateway.obtener_ruta("sipa_styles.qss")

MATRIZ_PERMISOS = {
    0: 0,  # Dashboard
    1: 2,  # Editor MD
    2: 1,  # IA SIPAcur
    3: 3,  # Servicios / Monitor
    4: 2,  # Huella Digital
    5: 5   # Configuración del Sistema
}

def extraer_identidad():
    datos = {
        "nombre": "Invitado", "apellido_1": "User", "apellido_2": "",
        "tipo_user": 0, "nombre_app": "SIPA SYSTEM", "dni": ""
    }
    logs = []
    logs.append(f"🔍 Buscando núcleo en: {CONFIG_FILE}")
    
    if not os.path.exists(CONFIG_FILE):
        logs.append(f"❌ ERROR: Fichero de identidad no encontrado.")
        return datos, logs

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            meta_match = re.search(r'---\s*\n(.*?)\n---', content, re.DOTALL)
            if meta_match:
                block = meta_match.group(1)
                for line in block.split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        key, val = key.strip(), val.strip().strip('"').strip("'")
                        if key in datos:
                            if key == "tipo_user":
                                try: datos[key] = int(val)
                                except: datos[key] = 0
                            else: datos[key] = val
                logs.append(f"✅ Identidad verificada: {datos['nombre']} (Nivel {datos['tipo_user']})")
    except Exception as e:
        logs.append(f"❌ ERROR IDENTIDAD: {str(e)}")
        return datos, logs

    try:
        if db_engine and db_engine.is_connected():
            nombre_completo = f"{datos['nombre']} {datos['apellido_1']} {datos['apellido_2']}".strip()
            type_user_id = 1 if datos["tipo_user"] == 5 else 3
            
            sql_update = """
                UPDATE user 
                SET nombre_completo = ?, 
                    type_user_id = ?, 
                    biografia_corta = ?
                WHERE id = 1
            """
            biografia = f"Perfil automatizado bajo protocolo BOLARDO. App: {datos['nombre_app']}"
            db_engine._cursor.execute(sql_update, (nombre_completo, type_user_id, biografia))
            db_engine._conn.commit()
            logs.append("💾 [Sincronizador] Base de datos SQLite unificada con los cambios del Markdown.")
    except Exception as e:
        logs.append(f"⚠️ [Sincronizador] No se pudo replicar al almacén relacional: {e}")

    return datos, logs


class ServiceCard(QFrame):
    def __init__(self, title, status, details, level_required=1, user_level=0, callback=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(180)
        layout = QVBoxLayout(self)
        
        self.lbl_title = QLabel(f"<b>{title.upper()}</b>")
        self.lbl_title.setObjectName("CardTitle")
        
        color_status = "#00FF95" if "ACTIVO" in status or "OK" in status else "#888888"
        self.lbl_status = QLabel(f"● {status}")
        self.lbl_status.setStyleSheet(f"color: {color_status}; font-weight: bold;")
        
        self.lbl_details = QLabel(details)
        self.lbl_details.setStyleSheet("color: #888888;")
        self.lbl_details.setWordWrap(True)
        
        self.btn_manage = QPushButton("GESTIONAR SERVICIO")
        if user_level < level_required:
            self.btn_manage.setText(f"🔒 NIVEL {level_required}")
            self.btn_manage.setObjectName("BtnLocked")
            self.btn_manage.setEnabled(False)
        else:
            self.btn_manage.setObjectName("BtnManage")
            self.btn_manage.setCursor(Qt.PointingHandCursor)
            if callback:
                self.btn_manage.clicked.connect(callback)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.lbl_details)
        layout.addStretch()
        layout.addWidget(self.btn_manage)


class VistaDashboard(QWidget):
    def __init__(self, identidad, user_level, callback_config, parent=None):
        super().__init__(parent)
        self.identidad = identidad
        self.user_level = user_level
        self.callback_config = callback_config
        
        layout_visual = QVBoxLayout(self)
        layout_visual.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_app_title = QLabel(self.identidad["nombre_app"])
        self.lbl_app_title.setObjectName("AppTitle")
        layout_visual.addWidget(self.lbl_app_title)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        layout_visual.addWidget(self.grid_container)
        layout_visual.addStretch()
        
        self.refresh_cards()
        
    def refresh_cards(self):
        for i in reversed(range(self.grid_layout.count())): 
            if self.grid_layout.itemAt(i).widget():
                self.grid_layout.itemAt(i).widget().setParent(None)
            
        service_exists = os.path.exists(SERVICE_CONFIG_PATH)
        status_serv = "ACTIVO (OK)" if service_exists else "DESCONECTADO"
        detail_serv = f"Ruta: core/services/ssipa_config.py\nEntorno: Reutilización Markdown Activa"
        
        cards_data = [
            ("Identidad Propietario", "ACTIVO", f"Operador: {self.identidad['nombre']}", 0, None),
            ("Configuración Sistema", status_serv, detail_serv, 5, self.callback_config),
            ("Motor de Vigilancia", "STANDBY", "Escaneando procesos...", 1, None),
            ("Análisis Forense", "DENEGADO", "Requiere nivel 4+", 4, None),
            ("Backup de Núcleo", "LISTO", "Protección de datos activa", 3, None)
        ]
        
        positions = [(0,0), (0,1), (1,0), (1,1), (2,0)]
        for i, (title, status, desc, req, func) in enumerate(cards_data):
            card = ServiceCard(title, status, desc, req, self.user_level, callback=func)
            self.grid_layout.addWidget(card, positions[i][0], positions[i][1])


# ==========================================================
# CORTAFUEGOS GRÁFICO / CONTENEDOR MAESTRO DE VENTANA ÚNICA
# ==========================================================

class SIPADashboard(QMainWindow):
    """El Dashboard Principal de SIPA (Se despliega tras validación exitosa)"""
    def __init__(self, user_profile_db=None, app_name_md="SIPA SYSTEM"):
        super().__init__()
        self.identidad = {"nombre": "Cargando...", "apellido_1": "", "tipo_user": 0, "nombre_app": app_name_md}
        self.user_level = 0
        
        self.init_ui()
        self.cargar_sistema()

        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.simular_log)
        self.log_timer.start(4000)

    def init_ui(self):
        self.setObjectName("SipaMainWindow")
        self.resize(1280, 850)
        
        if os.path.exists(QSS_FILE_PATH):
            with open(QSS_FILE_PATH, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        
        self.lbl_header = QLabel("OPERADOR ACREDITADO")
        self.lbl_header.setObjectName("SidebarHeader")
        self.lbl_user_name = QLabel("Cargando...")
        self.lbl_user_name.setObjectName("UserName")
        self.lbl_rango = QLabel("Rango: Nivel -")
        self.lbl_rango.setObjectName("UserRange")
        
        self.sidebar_layout.addWidget(self.lbl_header)
        self.sidebar_layout.addWidget(self.lbl_user_name)
        self.sidebar_layout.addWidget(self.lbl_rango)
        self.sidebar_layout.addSpacing(30)

        self.btn_dash = QPushButton("📊  Dashboard")
        self.btn_editor = QPushButton("📝  Editor MD")
        self.btn_sipacur = QPushButton("🧠  IA SIPAcur")
        self.btn_serv = QPushButton("⚙️  Servicios")
        self.btn_huella = QPushButton("🛡️  Huella Digital") 
        self.btn_conf = QPushButton("🛠  Configuración")
        
        self.menu_items = [
            (self.btn_dash, 0),
            (self.btn_editor, 1),
            (self.btn_sipacur, 2),
            (self.btn_serv, 3),
            (self.btn_huella, 4), 
            (self.btn_conf, 5)
        ]

        for btn, idx in self.menu_items:
            btn.setObjectName("BtnSidebar")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=idx: self.navegar_a(i))
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()
        self.btn_exit = QPushButton("CIERRE SEGURO")
        self.btn_exit.setObjectName("BtnCierre")
        # .window() busca hacia arriba en el árbol de Qt hasta encontrar el QMainWindow real activo
        self.btn_exit.clicked.connect(lambda: self.window().close()) 
        self.sidebar_layout.addWidget(self.btn_exit)

        # --- ZONA DERECHA ---
        self.zona_derecha = QWidget()
        layout_derecho = QVBoxLayout(self.zona_derecha)
        layout_derecho.setContentsMargins(30, 30, 30, 20)

        self.contenedor_paginas = QStackedWidget()
        layout_derecho.addWidget(self.contenedor_paginas, stretch=1)

        self.console = QTextEdit()
        self.console.setObjectName("Console")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(140)
        layout_derecho.addWidget(self.console)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.zona_derecha)

    def aplicar_control_accesos(self):
        self.add_log(f"🛡️ Evaluando matriz de privilegios para nivel de seguridad: {self.user_level}")
        for btn, idx in self.menu_items:
            nivel_requerido = MATRIZ_PERMISOS.get(idx, 0)
            if self.user_level < nivel_requerido:
                btn.setEnabled(False)
                btn.setStyleSheet("color: #555555; background-color: rgba(40, 40, 40, 0.3); border: 1px dashed #444;")
                texto_original = btn.text().split(" [")[0]
                btn.setText(f"{texto_original} [🔒 Lvl {nivel_requerido}]")
            else:
                btn.setEnabled(True)

    def cargar_sistema(self):
        self.identidad, logs_iniciales = extraer_identidad()
        self.user_level = self.identidad["tipo_user"]
        
        for msg in logs_iniciales: 
            self.add_log(msg)
        
        self.setWindowTitle(self.identidad["nombre_app"])
        self.lbl_user_name.setText(f"{self.identidad['nombre']} {self.identidad['apellido_1']}")
        self.lbl_rango.setText(f"Rango: Nivel {self.user_level}")
        
        self.vista_dashboard = VistaDashboard(self.identidad, self.user_level, self.ir_a_configuracion_directa)
        
        if SIPAMarkdownEditor:
            self.vista_editor = SIPAMarkdownEditor()
            self.add_log("📝 Editor MD: Acoplado al núcleo correctamente.")
        else:
            self.vista_editor = QLabel("❌ Error: No se pudo cargar 'ssipa_edit_markdown.py'.")
            self.vista_editor.setAlignment(Qt.AlignCenter)

        if SIPAcurDashboard:
            self.vista_sipacur = SIPAcurDashboard()
            self.add_log("🧠 SIPAcur: Módulo de IA activo.")
        else:
            self.vista_sipacur = QLabel("❌ Error: 'sipacur.py' no encontrado.")
            self.vista_sipacur.setAlignment(Qt.AlignCenter)
            
        if VistaServicios:
            self.vista_servicios = VistaServicios()
            self.add_log("⚙️ Servicios: Monitor de estado activo.")
        else:
            self.vista_servicios = QLabel("❌ Error: 'ssipa_servicios.py' no disponible.")
            self.vista_servicios.setAlignment(Qt.AlignCenter)
            
        if HuellaDigitalFrame:
            self.vista_huella = HuellaDigitalFrame()
            self.add_log("🛡️ Huella Digital: Módulo OSINT/Dorks acoplado con éxito.")
        else:
            self.vista_huella = QLabel("❌ Error: Fichero 'ssipa_identif.py' no encontrado en el árbol.")
            self.vista_huella.setAlignment(Qt.AlignCenter)

        if ConfigEditorNode:
            self.vista_config = ConfigEditorNode()
            self.add_log("🛠 Configuración: Editor Markdown unificado y asignado al perfil del Propietario.")
        else:
            self.vista_config = QLabel("❌ Error: 'ssipa_config.py' no pudo instanciarse.")
            self.vista_config.setAlignment(Qt.AlignCenter)
        
        self.contenedor_paginas.addWidget(self.vista_dashboard) # 0
        self.contenedor_paginas.addWidget(self.vista_editor)    # 1
        self.contenedor_paginas.addWidget(self.vista_sipacur)   # 2
        self.contenedor_paginas.addWidget(self.vista_servicios) # 3
        self.contenedor_paginas.addWidget(self.vista_huella)    # 4 
        self.contenedor_paginas.addWidget(self.vista_config)    # 5
        
        self.aplicar_control_accesos()

    def navegar_a(self, indice):
        self.contenedor_paginas.setCurrentIndex(indice)
        nombres = {
            0: "Dashboard", 1: "Editor Markdown", 2: "IA SIPAcur", 
            3: "Servicios", 4: "Huella Digital", 5: "Configuración"
        }
        self.add_log(f"📂 Navegando a módulo: {nombres.get(indice)}")

    def ir_a_configuracion_directa(self):
        if self.user_level >= MATRIZ_PERMISOS[5]:
            self.navegar_a(5)
        else:
            self.add_log("🚨 ACCESO DENEGADO: Nivel insuficiente para gestionar la configuración central.")

    def add_log(self, message):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{time_str}] {message}")

    def simular_log(self):
        frases = ["Pulso de red estable", "Integridad del núcleo OK", "Monitorización pasiva activa", "Escaneo de seguridad periódico"]
        self.add_log(random.choice(frases))


class SPAWindowsManager(QMainWindow):
    """
    Contenedor Raíz de Intercambio de Testigos. 
    Gobierna la Ventana Única alternando entre el Login y el Dashboard.
    """
    def __init__(self, bypass_profile=None, app_name_md="TOVID DFREI"):
        super().__init__()
        self.app_name = app_name_md
        self.setWindowTitle(self.app_name)
        self.resize(1280, 850) # Dimensiones unificadas de la terminal
        
        # Base SPA
        self.base_container = QWidget(self)
        self.setCentralWidget(self.base_container)
        self.spa_layout = QVBoxLayout(self.base_container)
        self.spa_layout.setContentsMargins(0, 0, 0, 0)
        self.spa_layout.setSpacing(0)
        
        # Enrutamiento inicial
        if bypass_profile:
            self.conmutar_a_dashboard(bypass_profile)
        else:
            self.cargar_login_pasarela()

    def cargar_login_pasarela(self):
        # Instanciamos el frame asimétrico de sbsipabap_login.py
        self.login_frame = SIPALoginFrame(db_manager=db_engine, app_name_from_md=self.app_name)
        # Escuchamos la señal de concesión manual
        self.login_frame.login_concedido.connect(self.conmutar_a_dashboard)
        self.spa_layout.addWidget(self.login_frame)

    def conmutar_a_dashboard(self, user_profile):
        # Limpieza atómica del Login para evitar fugas de memoria
        if hasattr(self, 'login_frame') and self.login_frame:
            self.spa_layout.removeWidget(self.login_frame)
            self.login_frame.deleteLater()
            self.login_frame = None
            
        # Instanciamos tu Dashboard completo dentro de la misma ventana
        self.dashboard_core = SIPADashboard(user_profile_db=user_profile, app_name_md=self.app_name)
        
        # Extraemos el widget central del QMainWindow del Dashboard para embeberlo de forma limpia
        widget_embebido = self.dashboard_core.centralWidget()
        widget_embebido.setParent(self.base_container)
        
        # Sincronizamos la barra de menús o títulos de la ventana raíz con el Dashboard
        self.setWindowTitle(self.dashboard_core.windowTitle())
        
        self.spa_layout.addWidget(widget_embebido)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplicar estilos QSS globales desde el primer milisegundo
    if os.path.exists(QSS_FILE_PATH):
        with open(QSS_FILE_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # Ejecución forzada de la sincronización en caliente (Fase 0)
    meta_datos, _ = extraer_identidad()
    instancia_nombre = meta_datos.get("nombre_app", "TOVID DFREI")
    
    # Evaluación del Bypass en base de datos mediante el campo 'config_seguridad'
    bypass_detectado, perfil_relacional = SIPALoginManager.comprobar_bypass(db_engine)
    
    # Lanzamiento del Administrador de Ventana Única SPA
    if bypass_detectado:
        launcher = SPAWindowsManager(bypass_profile=perfil_relacional, app_name_md=instancia_nombre)
    else:
        launcher = SPAWindowsManager(bypass_profile=None, app_name_md=instancia_nombre)
        
    launcher.show()
    sys.exit(app.exec())