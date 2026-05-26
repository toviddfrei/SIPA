# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: sipa.py
# Módulo: Core Dashboard / SPA Horizontal Manager (Browser Style)
# Versión: 2.5.0.0 | Fecha: 26/05/2026
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
                             QFrame, QStackedWidget)
from PySide6.QtCore import Qt

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
print("             SISTEMA INTEGRAL SIPA - CORE SPA (HORIZONTAL)")
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
        "tipo_user": 0, "nombre_app": "SIPA SYSTEM", "dni": "", "fecha_nacimiento": "03/03/1972"
    }
    logs = []
    
    if not os.path.exists(CONFIG_FILE):
        return datos, logs

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extraer Metadatos del Front Matter
            meta_match = re.search(r'---\s*\n(.*?)\n---', content, re.DOTALL)
            if meta_match:
                block = meta_match.group(1)
                for line in block.split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        key, val = key.strip(), val.strip().strip('"').strip("'")
                        if key in datos:
                            if key == "tipo_user": datos[key] = int(val)
                            else: datos[key] = val
            
            # Buscar Fecha Nacimiento en el cuerpo del Markdown
            nac_match = re.search(r'Fecha nacimiento:\s*([\d/]+)', content)
            if nac_match:
                datos["fecha_nacimiento"] = nac_match.group(1)
                
    except Exception as e:
        print(f"❌ Error leyendo identidad: {e}")

    try:
        if db_engine and db_engine.is_connected():
            nombre_completo = f"{datos['nombre']} {datos['apellido_1']} {datos['apellido_2']}".strip()
            type_user_id = 1 if datos["tipo_user"] == 5 else 3
            sql_update = "UPDATE user SET nombre_completo = ?, type_user_id = ? WHERE id = 1"
            db_engine._cursor.execute(sql_update, (nombre_completo, type_user_id))
            db_engine._conn.commit()
    except Exception:
        pass

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
        layout_visual.setContentsMargins(0, 10, 0, 0)
        
        self.lbl_app_title = QLabel(f"Dashboard Corporativo — {self.identidad['nombre_app']}")
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
            ("Identidad Propietario", "ACTIVO", f"Operador: {self.identidad['nombre']} {self.identidad['apellido_1']}\nNivel Acreditado: Lvl {self.user_level}", 0, None),
            ("Configuración Sistema", status_serv, detail_serv, 5, self.callback_config),
            ("Motor de Vigilancia", "STANDBY", "Escaneando procesos en segundo plano...", 1, None),
            ("Análisis Forense", "DENEGADO", "Módulo restringido. Requiere nivel 4+", 4, None),
            ("Backup de Núcleo", "LISTO", "Protección de datos asíncrona activa", 3, None)
        ]
        
        positions = [(0,0), (0,1), (1,0), (1,1), (2,0)]
        for i, (title, status, desc, req, func) in enumerate(cards_data):
            card = ServiceCard(title, status, desc, req, self.user_level, callback=func)
            self.grid_layout.addWidget(card, positions[i][0], positions[i][1])


class SIPADashboard(QWidget):
    """
    Cascarón Visual Mutado de SIPA. 
    Arquitectura Horizontal Tipo Navegador (Top Navbar).
    Ocupa el 100% de la pantalla útil sin sidebars verticales.
    """
    def __init__(self, parent_window=None, app_name_md="SIPA SYSTEM"):
        super().__init__()
        self.parent_window = parent_window  # Guardamos la referencia de la ventana raíz real
        self.identidad = {"nombre": "Cargando...", "apellido_1": "", "tipo_user": 0, "nombre_app": app_name_md, "fecha_nacimiento": "-"}
        self.user_level = 0
        
        self.init_ui()
        self.cargar_sistema()

    def init_ui(self):
        # Layout Estructural Absoluto (Vertical: Cabecera -> Contenido -> Footer)
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # ==========================================================
        # 1. CABECERA SUPERIOR (DOUBLE-DECK NAVBAR)
        # ==========================================================
        self.navbar_container = QFrame()
        self.navbar_container.setStyleSheet("background-color: #1A1A1A; border-bottom: 1px solid #2D2D2D;")
        layout_navbar_completo = QVBoxLayout(self.navbar_container)
        layout_navbar_completo.setContentsMargins(15, 10, 15, 10)
        layout_navbar_completo.setSpacing(8)

        # --- FILA SUPERIOR: MARCA Y CONTROLES CRÍTICOS ---
        fila_superior = QHBoxLayout()
        
        # Lado Izquierdo: Identidad de Marca
        self.lbl_logo = QLabel("🛡️")
        self.lbl_logo.setStyleSheet("font-size: 18px; margin-right: 5px;")
        self.lbl_brand_name = QLabel("SIPA")
        self.lbl_brand_name.setStyleSheet("font-weight: bold; font-size: 15px; color: #00FF95; font-family: 'Consolas';")
        
        self.lbl_separador = QLabel("|")
        self.lbl_separador.setStyleSheet("color: #444; font-size: 14px;")
        
        self.lbl_operador_acred = QLabel("OPERADOR:")
        self.lbl_operador_acred.setStyleSheet("color: #666; font-size: 10px; font-weight: bold;")
        self.lbl_user_identity = QLabel("Cargando...")
        self.lbl_user_identity.setStyleSheet("color: #E0E0E0; font-size: 11px; font-weight: bold;")
        
        fila_superior.addWidget(self.lbl_logo)
        fila_superior.addWidget(self.lbl_brand_name)
        fila_superior.addWidget(self.lbl_separador)
        fila_superior.addWidget(self.lbl_operador_acred)
        fila_superior.addWidget(self.lbl_user_identity)
        fila_superior.addStretch()

        # Lado Derecho: Utilidades de Sistema
        self.btn_menu = QPushButton("☰")
        self.btn_menu.setFixedWidth(40)
        self.btn_menu.setCursor(Qt.PointingHandCursor)
        self.btn_menu.setStyleSheet("background-color: #262626; border: 1px solid #333; color: #888;")
        
        self.btn_shutdown = QPushButton("🔒 APAGAR")
        self.btn_shutdown.setFixedWidth(100)
        self.btn_shutdown.setCursor(Qt.PointingHandCursor)
        self.btn_shutdown.setStyleSheet("background-color: #721C24; color: #F8D7DA; border: 1px solid #F5C6CB; font-size: 11px;")
        # Vinculación directa al close() de la ventana física real en RAM
        self.btn_shutdown.clicked.connect(lambda: self.parent_window.close() if self.parent_window else sys.exit(0))

        fila_superior.addWidget(self.btn_menu)
        fila_superior.addWidget(self.btn_shutdown)
        layout_navbar_completo.addLayout(fila_superior)

        # --- FILA INFERIOR: BOTONERA DE PESTAÑAS (TIPO NAVEGADOR) ---
        self.fila_pestanas = QHBoxLayout()
        self.fila_pestanas.setSpacing(5)
        
        self.btn_dash = QPushButton("📊  Dashboard")
        self.btn_editor = QPushButton("📝  Editor MD")
        self.btn_sipacur = QPushButton("🧠  IA SIPAcur")
        self.btn_serv = QPushButton("⚙️  Servicios")
        self.btn_huella = QPushButton("🛡️  Huella Digital") 
        self.btn_conf = QPushButton("🛠  Configuración")
        
        self.menu_items = [
            (self.btn_dash, 0), (self.btn_editor, 1), (self.btn_sipacur, 2),
            (self.btn_serv, 3), (self.btn_huella, 4), (self.btn_conf, 5)
        ]

        for btn, idx in self.menu_items:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #242424; color: #AAA; border: 1px solid #2D2D2D; 
                    border-bottom: none; border-radius: 4px 4px 0px 0px; padding: 0 15px; font-size: 12px;
                }
                QPushButton:hover { background-color: #2D2D2D; color: #FFF; }
                QPushButton:checked { background-color: #121212; color: #00FF95; border: 1px solid #333; border-bottom: 1px solid #121212; }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, i=idx: self.navegar_a(i))
            self.fila_pestanas.addWidget(btn)
            
        self.fila_pestanas.addStretch()
        layout_navbar_completo.addLayout(self.fila_pestanas)
        
        self.layout_principal.addWidget(self.navbar_container)

        # ==========================================================
        # 2. CONTENEDOR CENTRAL (ÁREA DE TRABAJO COMPLETA)
        # ==========================================================
        self.zona_central = QWidget()
        self.zona_central.setStyleSheet("background-color: #121212;")
        layout_zona_central = QVBoxLayout(self.zona_central)
        layout_zona_central.setContentsMargins(30, 20, 30, 20)

        self.contenedor_paginas = QStackedWidget()
        layout_zona_central.addWidget(self.contenedor_paginas)
        
        self.layout_principal.addWidget(self.zona_central, stretch=1)

        # ==========================================================
        # 3. ZÓCALO TÉCNICO (FOOTER UNIFICADO)
        # ==========================================================
        self.footer_frame = QFrame()
        self.footer_frame.setFixedHeight(28)
        self.footer_frame.setStyleSheet("background-color: #161616; border-top: 1px solid #222; padding: 0 15px;")
        layout_footer = QHBoxLayout(self.footer_frame)
        layout_footer.setContentsMargins(15, 0, 15, 0)
        
        self.lbl_foot_app = QLabel("Instancia: Loading...")
        self.lbl_foot_app.setStyleSheet("color: #555; font-family: 'Consolas'; font-size: 11px;")
        
        self.lbl_foot_propietario = QLabel("Nacimiento Propietario: --/--/----")
        self.lbl_foot_propietario.setStyleSheet("color: #555; font-family: 'Consolas'; font-size: 11px;")
        
        self.lbl_foot_version = QLabel("Kernel Core: SIPA v1.5")
        self.lbl_foot_version.setStyleSheet("color: #00FF95; font-family: 'Consolas'; font-size: 11px; font-weight: bold;")
        
        layout_footer.addWidget(self.lbl_foot_app)
        layout_footer.addStretch()
        layout_footer.addWidget(self.lbl_foot_propietario)
        layout_footer.addStretch()
        layout_footer.addWidget(self.lbl_foot_version)
        
        self.layout_principal.addWidget(self.footer_frame)

        # Activar el primer botón por defecto
        self.btn_dash.setChecked(True)

    def aplicar_control_accesos(self):
        for btn, idx in self.menu_items:
            nivel_requerido = MATRIZ_PERMISOS.get(idx, 0)
            if self.user_level < nivel_requerido:
                btn.setEnabled(False)
                btn.setToolTip(f"Restringido: Requiere Nivel {nivel_requerido}")
                btn.setStyleSheet("background-color: #1A1A1A; color: #444; border: 1px dashed #2D2D2D; border-bottom: none;")
                texto_original = btn.text().split(" [")[0]
                btn.setText(f"{texto_original} 🔒")
            else:
                btn.setEnabled(True)

    def cargar_sistema(self):
        self.identidad, _ = extraer_identidad()
        self.user_level = self.identidad["tipo_user"]
        
        # Volcar datos al Header y Footer
        self.lbl_user_identity.setText(f"{self.identidad['nombre']} {self.identidad['apellido_1']} [Lvl {self.user_level}]")
        self.lbl_foot_app.setText(f"Instancia: {self.identidad['nombre_app'].upper()}")
        self.lbl_foot_propietario.setText(f"Nacimiento Propietario: {self.identidad['fecha_nacimiento']}")
        
        # --- ACOPLAMIENTO DE MÓDULOS AL STACKED WIDGET ---
        self.vista_dashboard = VistaDashboard(self.identidad, self.user_level, self.ir_a_configuracion_directa)
        
        if SIPAMarkdownEditor: self.vista_editor = SIPAMarkdownEditor()
        else: self.vista_editor = QLabel("❌ Error: No se pudo cargar 'ssipa_edit_markdown.py'.")

        if SIPAcurDashboard: self.vista_sipacur = SIPAcurDashboard()
        else: self.vista_sipacur = QLabel("❌ Error: 'sipacur.py' no encontrado.")
            
        if VistaServicios: self.vista_servicios = VistaServicios()
        else: self.vista_servicios = QLabel("❌ Error: 'ssipa_servicios.py' no disponible.")
            
        if HuellaDigitalFrame: self.vista_huella = HuellaDigitalFrame()
        else: self.vista_huella = QLabel("❌ Error: Fichero 'ssipa_identif.py' no encontrado.")

        if ConfigEditorNode: self.vista_config = ConfigEditorNode()
        else: self.vista_config = QLabel("❌ Error: 'ssipa_config.py' no pudo instanciarse.")
        
        self.contenedor_paginas.addWidget(self.vista_dashboard) # 0
        self.contenedor_paginas.addWidget(self.vista_editor)    # 1
        self.contenedor_paginas.addWidget(self.vista_sipacur)   # 2
        self.contenedor_paginas.addWidget(self.vista_servicios) # 3
        self.contenedor_paginas.addWidget(self.vista_huella)    # 4 
        self.contenedor_paginas.addWidget(self.vista_config)    # 5
        
        self.aplicar_control_accesos()

    def navegar_a(self, indice):
        self.contenedor_paginas.setCurrentIndex(indice)
        
        # Mantener sincronizado el estado checked exclusivo de los botones (estilo tabs)
        for btn, idx in self.menu_items:
            btn.setChecked(idx == indice)

    def ir_a_configuracion_directa(self):
        if self.user_level >= MATRIZ_PERMISOS[5]:
            self.navegar_a(5)


class SPAWindowsManager(QMainWindow):
    """
    Contenedor Maestro de Ventana Única. 
    Gobierna el ciclo de vida en RAM alternando entre la Pasarela de Login y el Dashboard.
    """
    def __init__(self, bypass_profile=None, app_name_md="TOVID DFREI"):
        super().__init__()
        self.app_name = app_name_md
        self.setWindowTitle(self.app_name)
        self.resize(1280, 850)
        
        self.base_container = QWidget(self)
        self.setCentralWidget(self.base_container)
        self.spa_layout = QVBoxLayout(self.base_container)
        self.spa_layout.setContentsMargins(0, 0, 0, 0)
        self.spa_layout.setSpacing(0)
        
        if bypass_profile:
            self.conmutar_a_dashboard(bypass_profile)
        else:
            self.cargar_login_pasarela()

    def cargar_login_pasarela(self):
        self.login_frame = SIPALoginFrame(db_manager=db_engine, app_name_from_md=self.app_name)
        self.login_frame.login_concedido.connect(self.conmutar_a_dashboard)
        self.spa_layout.addWidget(self.login_frame)

    def conmutar_a_dashboard(self, user_profile):
        if hasattr(self, 'login_frame') and self.login_frame:
            self.spa_layout.removeWidget(self.login_frame)
            self.login_frame.deleteLater()
            self.login_frame = None
            
        # Desplegar el nuevo panel horizontal pasándole la instancia física de esta ventana (self)
        self.dashboard_core = SIPADashboard(parent_window=self, app_name_md=self.app_name)
        self.spa_layout.addWidget(self.dashboard_core)
        self.setWindowTitle(f"{self.app_name} — Panel Operativo")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    if os.path.exists(QSS_FILE_PATH):
        with open(QSS_FILE_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    meta_datos, _ = extraer_identidad()
    instancia_nombre = meta_datos.get("nombre_app", "TOVID DFREI")
    
    bypass_detectado, perfil_relacional = SIPALoginManager.comprobar_bypass(db_engine)
    
    if bypass_detectado:
        launcher = SPAWindowsManager(bypass_profile=perfil_relacional, app_name_md=instancia_nombre)
    else:
        launcher = SPAWindowsManager(bypass_profile=None, app_name_md=instancia_nombre)
        
    launcher.show()
    sys.exit(app.exec())