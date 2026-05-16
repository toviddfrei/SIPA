# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: sipa.py
# Módulo: Core Dashboard / SPA Manager
# Versión: 2.0.0.1 | Fecha: 16/05/2026
# Autor: Daniel Miñana Montero & Gemini
# ==========================================================

import sys
import os
import re
import subprocess
import getpass 
import random
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QFrame, QTextEdit, QStackedWidget)
from PySide6.QtCore import Qt, QTimer

# --- CONFIGURACIÓN DE RUTAS ---
USER_NAME = getpass.getuser()
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_SIPA = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

# 1. Resolver e inyectar la ruta del submódulo ANTES del import
RUTA_SIPACUR = os.path.join(CURRENT_DIR, "external", "SIPAcur")
if RUTA_SIPACUR not in sys.path:
    sys.path.append(RUTA_SIPACUR)

# 2. Intentar importar una vez que sys.path ya está actualizado
try:
    from sipacur import SIPAcurDashboard
except ImportError:
    SIPAcurDashboard = None

# --- LOG DE DIAGNÓSTICO ESTRICTO ---
print(def_path := os.path.join(CURRENT_DIR, "external", "SIPAcur"))
print("¿Existe la carpeta?:", os.path.exists(def_path))
if os.path.exists(def_path):
    print("Contenido:", os.listdir(def_path))

try:
    from sipacur import SIPAcurDashboard
except ImportError as e:
    print(f"❌ ERROR REAL DE IMPORTACIÓN: {e}") # Esto saldrá en tu terminal de VSCode/Consola
    SIPAcurDashboard = None

if not os.path.exists(ROOT_SIPA) or "SIPA" not in ROOT_SIPA:
    CONFIG_FILE = f"/home/{USER_NAME}/SIPA/data/archive/template_propietario.md"
    SERVICE_CONFIG_PATH = f"/home/{USER_NAME}/SIPA/core/services/ssipa_config.py"
else:
    CONFIG_FILE = os.path.join(ROOT_SIPA, "data", "archive", "template_propietario.md")
    SERVICE_CONFIG_PATH = os.path.join(ROOT_SIPA, "core/services/ssipa_config.py")

QSS_FILE_PATH = os.path.join(CURRENT_DIR, "sipa_styles.qss")


def extraer_identidad():
    datos = {
        "nombre": "Invitado", "apellido_1": "User", "apellido_2": "",
        "tipo_user": 0, "nombre_app": "SIPA SYSTEM"
    }
    logs = []
    logs.append(f"🔍 Buscando núcleo en: {CONFIG_FILE}")
    
    if not os.path.exists(CONFIG_FILE):
        logs.append(f"❌ ERROR: Fichero no encontrado.")
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
        logs.append(f"❌ ERROR: {str(e)}")
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
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        service_exists = os.path.exists(SERVICE_CONFIG_PATH)
        status_serv = "ACTIVO (OK)" if service_exists else "DESCONECTADO"
        detail_serv = f"Ruta: core/services/ssipa_config.py\nEstado: {'Listo' if service_exists else 'No hallado'}"
        
        cards_data = [
            ("Identidad Propietario", "ACTIVO", f"Operador: {self.identidad['nombre']}", 5, None),
            ("Configuración Sistema", status_serv, detail_serv, 5, self.callback_config),
            ("Motor de Vigilancia", "STANDBY", "Escaneando...", 1, None),
            ("Análisis Forense", "DENEGADO", "Solo nivel 4+", 4, None),
            ("Backup de Núcleo", "LISTO", "Protección de datos", 3, None)
        ]
        
        positions = [(0,0), (0,1), (1,0), (1,1), (2,0)]
        for i, (title, status, desc, req, func) in enumerate(cards_data):
            card = ServiceCard(title, status, desc, req, self.user_level, callback=func)
            self.grid_layout.addWidget(card, positions[i][0], positions[i][1])


class SIPADashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.identidad = {"nombre": "Cargando...", "apellido_1": "", "tipo_user": 0, "nombre_app": "SIPA"}
        self.user_level = 0
        
        self.init_ui()
        self.cargar_sistema()

        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.simular_log)
        self.log_timer.start(4000)

    def init_ui(self):
        self.setWindowTitle("SIPA SYSTEM")
        self.resize(1200, 800)
        
        if os.path.exists(QSS_FILE_PATH):
            with open(QSS_FILE_PATH, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"⚠️ Alerta: No se encontró el archivo de estilos en {QSS_FILE_PATH}. Usando diseño nativo.")

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
        
        lbl_header = QLabel("OPERADOR ACREDITADO")
        lbl_header.setObjectName("SidebarHeader")
        
        self.lbl_user_name = QLabel("Invitado")
        self.lbl_user_name.setObjectName("UserName")
        
        self.lbl_rango = QLabel("Rango: Nivel 0")
        self.lbl_rango.setObjectName("UserRange")
        
        self.sidebar_layout.addWidget(lbl_header)
        self.sidebar_layout.addWidget(self.lbl_user_name)
        self.sidebar_layout.addWidget(self.lbl_rango)
        self.sidebar_layout.addSpacing(30)

        # Botones de la barra lateral (Actualizados con SIPAcur)
        self.btn_dash = QPushButton("📊  Dashboard")
        self.btn_sipacur = QPushButton("🧠  IA SIPAcur")
        self.btn_serv = QPushButton("⚙️  Servicios")
        self.btn_conf = QPushButton("🛠  Configuración")
        
        for b in [self.btn_dash, self.btn_sipacur, self.btn_serv, self.btn_conf]:
            b.setObjectName("BtnSidebar")
            b.setCursor(Qt.PointingHandCursor)
            self.sidebar_layout.addWidget(b)

        # Eventos de navegación asignados a los nuevos índices
        self.btn_dash.clicked.connect(lambda: self.navegar_a(0))
        self.btn_sipacur.clicked.connect(lambda: self.navegar_a(1))
        self.btn_serv.clicked.connect(lambda: self.navegar_a(2))
        self.btn_conf.clicked.connect(lambda: self.navegar_a(3))

        self.sidebar_layout.addStretch()
        self.btn_exit = QPushButton("CIERRE SEGURO")
        self.btn_exit.setObjectName("BtnCierre")
        self.btn_exit.clicked.connect(self.close)
        self.sidebar_layout.addWidget(self.btn_exit)

        # --- ÁREA CENTRAL DERECHA ---
        self.zona_derecha = QWidget()
        layout_derecho = QVBoxLayout(self.zona_derecha)
        layout_derecho.setContentsMargins(30, 30, 30, 20)

        self.contenedor_paginas = QStackedWidget()
        layout_derecho.addWidget(self.contenedor_paginas, stretch=1)

        # Consola persistente
        self.console = QTextEdit()
        self.console.setObjectName("Console")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(140)
        layout_derecho.addWidget(self.console)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.zona_derecha)

    def cargar_sistema(self):
        self.identidad, logs_iniciales = extraer_identidad()
        self.user_level = self.identidad["tipo_user"]
        
        for msg in logs_iniciales: 
            self.add_log(msg)
        
        app_name = self.identidad["nombre_app"]
        self.setWindowTitle(app_name)
        
        self.lbl_user_name.setText(f"{self.identidad['nombre']} {self.identidad['apellido_1']}")
        self.lbl_rango.setText(f"Rango: Nivel {self.user_level}")
        
        # --- INSTANCIACIÓN DE LAS PÁGINAS (QStackedWidget) ---
        self.vista_dashboard = VistaDashboard(self.identidad, self.user_level, self.abrir_configuracion_personalizada)
        
        if SIPAcurDashboard:
            self.vista_sipacur = SIPAcurDashboard()
            self.add_log("🧠 Módulo SIPAcur acoplado con éxito.")
        else:
            self.vista_sipacur = QLabel("❌ Error: 'sipacur.py' no encontrado en la ruta de extensiones.")
            self.vista_sipacur.setAlignment(Qt.AlignCenter)
            self.add_log("⚠️ Advertencia: No se pudo cargar SIPAcur.")
            
        self.vista_servicios_placeholder = QWidget() 
        self.vista_config_placeholder = QWidget()    
        
        self.contenedor_paginas.addWidget(self.vista_dashboard)             # Índice 0
        self.contenedor_paginas.addWidget(self.vista_sipacur)               # Índice 1
        self.contenedor_paginas.addWidget(self.vista_servicios_placeholder)   # Índice 2
        self.contenedor_paginas.addWidget(self.vista_config_placeholder)      # Índice 3
        
        if self.user_level < 5:
            self.btn_conf.setEnabled(False)
            self.btn_conf.setObjectName("BtnSidebarDisabled")

    def navegar_a(self, indice):
        self.contenedor_paginas.setCurrentIndex(indice)
        nombres_modulos = {0: "Dashboard", 1: "IA SIPAcur", 2: "Servicios", 3: "Configuración"}
        self.add_log(f"📂 Navegando a módulo: {nombres_modulos.get(indice)}")

    def abrir_configuracion_personalizada(self):
        self.add_log(f"⚙️ Iniciando ejecutable externo: {os.path.basename(SERVICE_CONFIG_PATH)}...")
        if os.path.exists(SERVICE_CONFIG_PATH):
            try:
                subprocess.Popen([sys.executable, SERVICE_CONFIG_PATH])
                self.add_log("✅ Servicio desplegado en proceso independiente.")
            except Exception as e:
                self.add_log(f"❌ ERROR: {str(e)}")
        else:
            self.add_log(f"❌ ERROR: Fichero no encontrado.")

    def add_log(self, message):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{time_str}] {message}")

    def simular_log(self):
        frases = ["Pulso de red estable", "Integridad del núcleo verificada", "Monitorización pasiva activa"]
        self.add_log(random.choice(frases))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SIPADashboard()
    window.show()
    sys.exit(app.exec())