import sys
import os
import re
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QFrame, QTextEdit)
from PySide6.QtCore import Qt, QTimer

# --- CONFIGURACIÓN DE RUTAS ---
import getpass 

USER_NAME = getpass.getuser()
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_SIPA = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

if not os.path.exists(ROOT_SIPA) or "SIPA" not in ROOT_SIPA:
    CONFIG_FILE = f"/home/{USER_NAME}/SIPA/data/archive/template_propietario.md"
    SERVICE_CONFIG_PATH = f"/home/{USER_NAME}/SIPA/core/services/ssipa_config.py"
else:
    CONFIG_FILE = os.path.join(ROOT_SIPA, "data", "archive", "template_propietario.md")
    SERVICE_CONFIG_PATH = os.path.join(ROOT_SIPA, "core/services/ssipa_config.py")

class SIPAStyle:
    """Configuración de estilos Cyber-Dark"""
    MAIN_BG = "#121212"
    SIDEBAR_BG = "#1A1A1A"
    CARD_BG = "#242424"
    ACCENT_BLUE = "#3A86FF"
    ACCENT_RED = "#E63946"
    ACCENT_GREEN = "#00FF95"
    TEXT_PRIMARY = "#E0E0E0"
    TEXT_DIM = "#888888"
    CONSOLE_BG = "#050505"

    SHEET = f"""
    QMainWindow {{ background-color: {MAIN_BG}; }}
    #Sidebar {{ background-color: {SIDEBAR_BG}; border-right: 1px solid #2D2D2D; }}
    #Card {{ background-color: {CARD_BG}; border: 1px solid #333333; border-radius: 12px; }}
    
    QPushButton {{
        background-color: #333333;
        color: {TEXT_PRIMARY};
        border: none;
        padding: 10px;
        border-radius: 6px;
        font-weight: bold;
    }}
    QPushButton:hover {{ background-color: {ACCENT_BLUE}; }}
    #BtnManage {{ background-color: {ACCENT_BLUE}; }}
    #BtnLocked {{ background-color: #222; color: #555; border: 1px dashed #444; }}
    #BtnCierre {{ background-color: #442222; color: {ACCENT_RED}; border: 1px solid {ACCENT_RED}; }}
    
    #Console {{
        background-color: {CONSOLE_BG};
        color: {ACCENT_GREEN};
        font-family: 'Consolas', monospace;
        font-size: 11px;
        border: 1px solid #222;
    }}
    QLabel {{ color: {TEXT_PRIMARY}; }}
    """

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
        self.lbl_title.setStyleSheet(f"font-size: 13px; color: {SIPAStyle.ACCENT_BLUE};")
        
        color_status = SIPAStyle.ACCENT_GREEN if "ACTIVO" in status or "OK" in status else SIPAStyle.TEXT_DIM
        self.lbl_status = QLabel(f"● {status}")
        self.lbl_status.setStyleSheet(f"color: {color_status}; font-weight: bold;")
        
        self.lbl_details = QLabel(details)
        self.lbl_details.setStyleSheet(f"color: {SIPAStyle.TEXT_DIM};")
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
        # Título inicial antes de cargar el MD
        self.setWindowTitle("SIPA SYSTEM")
        self.resize(1200, 800)
        self.setStyleSheet(SIPAStyle.SHEET)

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
        
        self.lbl_user_name = QLabel("Invitado")
        self.lbl_user_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #00FF95;")
        self.lbl_rango = QLabel("Rango: Nivel 0")
        self.lbl_rango.setStyleSheet("color: #666; font-size: 11px;")
        
        self.sidebar_layout.addWidget(QLabel("OPERADOR ACCREDITADO", styleSheet="color: #888; font-size: 10px;"))
        self.sidebar_layout.addWidget(self.lbl_user_name)
        self.sidebar_layout.addWidget(self.lbl_rango)
        self.sidebar_layout.addSpacing(30)

        self.btn_dash = QPushButton("📊  Dashboard")
        self.btn_serv = QPushButton("⚙️  Servicios")
        self.btn_conf = QPushButton("🛠  Configuración")
        
        for b in [self.btn_dash, self.btn_serv, self.btn_conf]:
            b.setStyleSheet("text-align: left; background: transparent; font-size: 13px")
            b.setCursor(Qt.PointingHandCursor)
            self.sidebar_layout.addWidget(b)

        self.btn_conf.clicked.connect(self.abrir_configuracion_personalizada)

        self.sidebar_layout.addStretch()
        self.btn_exit = QPushButton("CIERRE SEGURO")
        self.btn_exit.setObjectName("BtnCierre")
        self.btn_exit.clicked.connect(self.close)
        self.sidebar_layout.addWidget(self.btn_exit)

        # --- CONTENIDO ---
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 0)

        self.lbl_app_title = QLabel("SIPA SYSTEM")
        self.lbl_app_title.setStyleSheet("font-size: 26px; font-weight: bold;")
        self.content_layout.addWidget(self.lbl_app_title)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.content_layout.addWidget(self.grid_container)
        self.content_layout.addStretch()

        self.console = QTextEdit()
        self.console.setObjectName("Console")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(140)
        self.content_layout.addWidget(self.console)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_area)

    def cargar_sistema(self):
        self.identidad, logs_iniciales = extraer_identidad()
        self.user_level = self.identidad["tipo_user"]
        for msg in logs_iniciales: self.add_log(msg)
        
        # ACTUALIZACIÓN DE TÍTULOS CON EL NOMBRE DE LA APP
        app_name = self.identidad["nombre_app"]
        self.setWindowTitle(app_name) # El nombre de la ventana ahora es el de la App
        self.lbl_app_title.setText(app_name)
        
        self.lbl_user_name.setText(f"{self.identidad['nombre']} {self.identidad['apellido_1']}")
        self.lbl_rango.setText(f"Rango: Nivel {self.user_level}")
        self.refresh_cards()
        
        if self.user_level < 5:
            self.btn_conf.setEnabled(False)
            self.btn_conf.setStyleSheet("text-align: left; background: transparent; color: #444;")

    def refresh_cards(self):
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        service_exists = os.path.exists(SERVICE_CONFIG_PATH)
        status_serv = "ACTIVO (OK)" if service_exists else "DESCONECTADO"
        detail_serv = f"Ruta: core/services/ssipa_config.py\nEstado: {'Listo' if service_exists else 'No hallado'}"
        
        cards_data = [
            ("Identidad Propietario", "ACTIVO", f"Operador: {self.identidad['nombre']}", 5, None),
            ("Configuración Sistema", status_serv, detail_serv, 5, self.abrir_configuracion_personalizada),
            ("Motor de Vigilancia", "STANDBY", "Escaneando...", 1, None),
            ("Análisis Forense", "DENEGADO", "Solo nivel 4+", 4, None),
            ("Backup de Núcleo", "LISTO", "Protección de datos", 3, None)
        ]
        
        positions = [(0,0), (0,1), (1,0), (1,1), (2,0)]
        for i, (title, status, desc, req, func) in enumerate(cards_data):
            card = ServiceCard(title, status, desc, req, self.user_level, callback=func)
            self.grid_layout.addWidget(card, positions[i][0], positions[i][1])

    def abrir_configuracion_personalizada(self):
        self.add_log(f"⚙️ Iniciando: {os.path.basename(SERVICE_CONFIG_PATH)}...")
        if os.path.exists(SERVICE_CONFIG_PATH):
            try:
                subprocess.Popen([sys.executable, SERVICE_CONFIG_PATH])
                self.add_log("✅ Servicio desplegado.")
            except Exception as e:
                self.add_log(f"❌ ERROR: {str(e)}")
        else:
            self.add_log(f"❌ ERROR: Fichero no encontrado.")

    def add_log(self, message):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{time_str}] {message}")

    def simular_log(self):
        import random
        frases = ["Pulso estable", "Integridad verificada", "Monitorización activa"]
        self.add_log(random.choice(frases))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SIPADashboard()
    window.show()
    sys.exit(app.exec())