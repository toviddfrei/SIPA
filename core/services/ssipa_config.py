import sys
import os
import socket
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, QFrame)
from PySide6.QtCore import Qt

# --- 1. SEGURIDAD SENTINEL (Manteniendo tu lógica) ---
try:
    from external.sentinel_fhs_CA import sentinel_v002_fhs_CA as sentinel
    if not sentinel.sonda.ejecutar_auditoria(sys.argv[0]):
        sys.exit(1)
except ImportError:
    pass

# --- 2. CONFIGURACIÓN DE RUTAS (Escalada a Raíz) ---

# Ubicación actual: /home/toviddfrei/SIPA/core/services/tu_script.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Subimos dos niveles para llegar a SIPA/
# Nivel 1: de /services/ a /core/
# Nivel 2: de /core/ a /SIPA/
ROOT_SIPA = os.path.dirname(os.path.dirname(CURRENT_DIR))

# Construimos la ruta apuntando a la raíz real
CONFIG_FILE = os.path.join(ROOT_SIPA, "data", "archive", "template_propietario.md")

print(f"🔍 Buscando configuración en: {CONFIG_FILE}")

# --- 3. ESTILO COHERENTE (Cyber-Dark Esmeralda) ---
STYLE_SHEET = """
    QMainWindow { background-color: #121212; }
    #MainPanel { background-color: #1A1A1A; border: 1px solid #2D2D2D; border-radius: 10px; }
    
    QTextEdit { 
        background-color: #050505; 
        color: #E0E0E0; 
        font-family: 'Consolas', monospace; 
        font-size: 13px;
        border: 1px solid #333;
        border-radius: 5px;
        padding: 10px;
    }
    
    QLabel#Title { color: #00FF95; font-size: 18px; font-weight: bold; }
    
    QPushButton#SaveBtn {
        background-color: #00FF95;
        color: #000;
        font-weight: bold;
        border-radius: 5px;
        padding: 12px;
    }
    QPushButton#SaveBtn:hover { background-color: #00CC78; }
    
    QPushButton#CancelBtn {
        background-color: transparent;
        color: #888;
        border: 1px solid #444;
    }
    QPushButton#CancelBtn:hover { color: #FFF; border: 1px solid #888; }
"""

class ConfigEditorNode(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIPA | Nodo de Configuración de Propietario")
        self.resize(800, 600)
        self.setStyleSheet(STYLE_SHEET)

        # Contenedor Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)

        panel = QFrame()
        panel.setObjectName("MainPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)

        # Cabecera
        header = QLabel("⚙️ CONFIGURACIÓN DE IDENTIDAD")
        header.setObjectName("Title")
        panel_layout.addWidget(header)
        
        info = QLabel("Edite los metadatos de su ficha personal. Los cambios requieren reinicio.")
        info.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
        panel_layout.addWidget(info)

        # Editor de Texto
        self.editor = QTextEdit()
        panel_layout.addWidget(self.editor)

        # Botonera
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("DESCARTAR")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_save = QPushButton("💾 GUARDAR Y SINCRONIZAR")
        self.btn_save.setObjectName("SaveBtn")
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        panel_layout.addLayout(btn_layout)

        layout.addWidget(panel)

        # Cargar datos e inicializar eventos
        self.load_config()
        self.btn_save.clicked.connect(self.save_config)
        self.btn_cancel.clicked.connect(self.close)

    def load_config(self):
        """Carga el fichero MD forzado."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.editor.setPlainText(f.read())
        except Exception as e:
            self.editor.setPlainText(f"Error al cargar ficha: {e}")

    def save_config(self):
        """Guarda y notifica vía Socket (tu lógica de main_ev.py)."""
        try:
            content = self.editor.toPlainText()
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Notificación de Socket (IPC)
            self.notify_launcher("CONFIG_UPDATED", "Ficha de propietario modificada.")
            self.close()
        except Exception as e:
            print(f"Error al guardar: {e}")

    def notify_launcher(self, event_type, details):
        """Mantiene tu arquitectura de comunicación por socket."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect(('127.0.0.1', 65432))
                message = json.dumps({"event": event_type, "data": details})
                s.sendall(message.encode('utf-8'))
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ConfigEditorNode()
    editor.show()
    sys.exit(app.exec())