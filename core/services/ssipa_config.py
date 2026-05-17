# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: ssipa_config.py
# Módulo: Configuración del Sistema (Ecosistema Shell/Terminal)
# Versión: 2.0.1.2 | Fecha: 17/05/2026
# Autor: Daniel Miñana Montero & Gemini
# ==========================================================

import sys
import os
import socket
import json
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QFrame, QApplication)
from PySide6.QtCore import Qt, QTimer

# --- CONFIGURACIÓN DE RUTAS DE LATIDO (Heartbeat) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
NOMBRE_SCRIPT = os.path.splitext(os.path.basename(__file__))[0]
ARCHIVO_LIVE = os.path.join(CURRENT_DIR, f".{NOMBRE_SCRIPT}.live")

# --- RESOLUCIÓN DE RUTA DE IDENTIDAD ---
ROOT_SIPA = os.path.dirname(os.path.dirname(CURRENT_DIR))
CONFIG_FILE = os.path.join(ROOT_SIPA, "data", "archive", "template_propietario.md")


class ConfigEditorNode(QWidget):
    """Nodo de configuración optimizado con estética de consola Shell de seguridad"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SipaConfigTerminal")
        
        # Generar señal de vida para el Dashboard
        self.crear_senal_vida()
        self.init_ui()
        self.load_config_file()

    def crear_senal_vida(self):
        try:
            with open(ARCHIVO_LIVE, 'w', encoding='utf-8') as f:
                f.write("RUNNING")
        except Exception as e:
            print(f"Error al escribir señal de vida: {e}")

    def borrar_senal_vida(self):
        try:
            if os.path.exists(ARCHIVO_LIVE):
                os.remove(ARCHIVO_LIVE)
        except Exception as e:
            print(f"Error al limpiar señal de vida: {e}")

    def closeEvent(self, event):
        self.borrar_senal_vida()
        event.accept()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Contenedor Principal estilo Terminal / Consola
        self.terminal_frame = QFrame()
        self.terminal_frame.setObjectName("TerminalFrame")
        
        self.terminal_frame.setStyleSheet("""
            QFrame#TerminalFrame {
                background-color: #0A0A0A;
                border: 1px solid #1F1F1F;
                border-radius: 6px;
            }
            QLabel#TerminalPrompt {
                color: #00FF95;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                font-weight: bold;
            }
            QLabel#TerminalPath {
                color: #00BCFF;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
            QTextEdit#ConsoleEditor {
                background-color: #050505;
                color: #00FF95;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #1A1A1A;
                border-radius: 4px;
                padding: 12px;
            }
            QPushButton#TerminalSaveBtn {
                background-color: #00FF95;
                color: #000000;
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton#TerminalSaveBtn:hover {
                background-color: #00CC78;
            }
            QPushButton#TerminalSaveBtn:pressed {
                background-color: #00995A;
            }
        """)
        
        terminal_layout = QVBoxLayout(self.terminal_frame)
        terminal_layout.setContentsMargins(15, 15, 15, 15)
        terminal_layout.setSpacing(12)

        # --- CABECERA DE LA CONSOLA ---
        header_layout = QHBoxLayout()
        
        prompt_symbol = QLabel("sipa-system@root:~#")
        prompt_symbol.setObjectName("TerminalPrompt")
        
        ruta_display = f" nano ../data/archive/{os.path.basename(CONFIG_FILE)}"
        path_lbl = QLabel(ruta_display)
        path_lbl.setObjectName("TerminalPath")
        
        header_layout.addWidget(prompt_symbol)
        header_layout.addWidget(path_lbl)
        header_layout.addStretch()
        
        time_lbl = QLabel(f"SYS_SESSION: {datetime.now().strftime('%H:%M:%S')}")
        time_lbl.setStyleSheet("color: #444444; font-family: 'Consolas', monospace; font-size: 11px;")
        header_layout.addWidget(time_lbl)
        
        terminal_layout.addLayout(header_layout)

        # --- EDITOR DE TEXTO EN MODO CÓDIGO ---
        self.editor = QTextEdit()
        self.editor.setObjectName("ConsoleEditor")
        self.editor.setTabStopDistance(32)
        terminal_layout.addWidget(self.editor)

        # --- BARRA DE ACCIONES INFERIOR ---
        footer_layout = QHBoxLayout()
        
        # Guardamos la etiqueta de información como atributo de clase para poder cambiar su texto dinámicamente
        self.info_foot = QLabel("[ F2: Exit ]  [ Ctrl+O: Save ]  ||  Status: Root Access Verified")
        self.info_foot.setStyleSheet("color: #555555; font-family: 'Consolas', monospace; font-size: 11px;")
        footer_layout.addWidget(self.info_foot)
        footer_layout.addStretch()
        
        self.btn_save = QPushButton("⚡ DEPLOY & SYNC")
        self.btn_save.setObjectName("TerminalSaveBtn")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_config_file)
        
        footer_layout.addWidget(self.btn_save)
        terminal_layout.addLayout(footer_layout)

        layout.addWidget(self.terminal_frame)

    def load_config_file(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.editor.setPlainText(f.read())
            else:
                os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                default_content = (
                    "---\n"
                    "nombre: \"Propietario\"\n"
                    "apellido_1: \"User\"\n"
                    "apellido_2: \"\"\n"
                    "tipo_user: 5\n"
                    "nombre_app: \"SIPA SYSTEM\"\n"
                    "---\n\n"
                    "# FICHA DE IDENTIDAD CENTRAL\n"
                    "Edite los campos anteriores respetando el formato YAML.\n"
                )
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    f.write(default_content)
                self.editor.setPlainText(default_content)
        except Exception as e:
            self.editor.setPlainText(f"❌ ERROR DE ACCESO AL NODO:\n{str(e)}")

    def save_config_file(self):
        """Guarda cambios, muestra log de éxito en consola y cierra diferido"""
        try:
            content = self.editor.toPlainText()
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Notificación Socket IPC
            self.notify_ipc_server("CONFIG_UPDATED", "Identity profile synchronized.")
            
            # --- FEEDBACK VISUAL ESTILO TERMINAL ---
            self.info_foot.setText("✨ [ SUCCESS ] Cambios desplegados. Sincronizando core de SIPA...")
            self.info_foot.setStyleSheet("color: #00FF95; font-family: 'Consolas', monospace; font-size: 11px; font-weight: bold;")
            
            # Bloqueamos el botón temporalmente para evitar doble clic convulsivo
            self.btn_save.setEnabled(False)
            self.btn_save.setText("⏳ SYNCED")
            
            # --- CIERRE / REINICIO DIFERIDO (3 Segundos) ---
            # Le da margen al usuario para ver el mensaje verde y cierra el nodo
            QTimer.singleShot(3000, self.ejecutar_salida_modulo)
            
        except Exception as e:
            self.info_foot.setText(f"❌ [ DEPLOY FAILED ]: {str(e)}")
            self.info_foot.setStyleSheet("color: #FF0055; font-family: 'Consolas', monospace; font-size: 11px;")

    def ejecutar_salida_modulo(self):
        """Cierra el widget de forma limpia o fuerza el comportamiento de ocultación"""
        print("⚙️ [SIPA SHELL] Módulo de configuración cerrado tras guardado exitoso.")
        self.close()
        
        # Si tu sipa.py maneja un QStackedWidget o pestañas en el panel derecho,
        # intentamos decirle al parent que cambie a la pestaña 0 (Dashboard principal)
        parent_widget = self.parent()
        while parent_widget is not None:
            if hasattr(parent_widget, 'setCurrentIndex'): # Si encontramos el StackedWidget intermedio
                parent_widget.setCurrentIndex(0) # Forzar retorno al Dashboard principal
                break
            parent_widget = parent_widget.parent()

    def notify_ipc_server(self, event_type, details):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect(('127.0.0.1', 65432))
                message = json.dumps({"event": event_type, "data": details})
                s.sendall(message.encode('utf-8'))
        except: 
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigEditorNode()
    window.setWindowFlags(Qt.Window)
    window.setWindowTitle("SIPA | Terminal Config Node")
    window.resize(900, 650)
    window.show()
    sys.exit(app.exec())