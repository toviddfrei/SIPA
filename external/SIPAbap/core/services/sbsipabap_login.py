# =====================================================================
# MÓDULO: sbsipabap_login.py (v0.2.6 - Frame Integrado SPA)
# UBICACIÓN: /home/toviddfrei/SIPA/external/SIPAbap/core/services/
# DESCRIPCIÓN: Pasarela de Identidad integrada en la Ventana Única de Qt.
#              Lado Izquierdo: Branding, identidad (.md) y pitch de venta.
#              Lado Derecho: Formulario de autenticación técnica y bypass.
# AUTOR: Daniel Miñana Montero & Gemini
# =====================================================================

import json
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QCheckBox, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger("SIPA.Core")

class SIPALoginManager:
    """Controlador lógico para verificar el estado de 'Recordarme' en la DB."""
    @classmethod
    def comprobar_bypass(cls, db_manager):
        """Devuelve True si el usuario tiene el acceso automatizado activo."""
        user_row = db_manager.get_user_profile()
        if not user_row:
            return False, None
        
        config_raw = user_row.get("config_seguridad")
        if config_raw:
            try:
                config_json = json.loads(config_raw)
                if config_json.get("remember_me", False):
                    logger.info(f"🔑 Bypass SPA: Identidad Root certificada -> {user_row['nombre_completo']}")
                    return True, dict(user_row)
            except json.JSONDecodeError:
                pass
        return False, dict(user_row)


class SIPALoginFrame(QWidget):
    """
    Frame de Login de Alta Densidad Visual con maquetación asimétrica.
    Se incrusta en la ventana única de sipa.py antes de cargar el Dashboard.
    """
    # Señal personalizada para avisar a sipa.py de que el acceso ha sido autorizado
    login_concedido = Signal(dict)

    def __init__(self, db_manager, app_name_from_md="TOVID DFREI"):
        super().__init__()
        self.db = db_manager
        self.app_name = app_name_from_md
        self.init_ui()

    def init_ui(self):
        # Aseguramos que el Frame principal no tenga márgenes para encajar en sipa.py
        self.setObjectName("LoginWindow")
        
        master_layout = QHBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        # ==========================================================
        # BLOQUE IZQUIERDO: BRANDING, IDENTIDAD (.md) Y VENTA
        # ==========================================================
        left_frame = QFrame(self)
        left_frame.setObjectName("Sidebar") # Toma fondo #1A1A1A y bordes de sipa_styles.qss
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(15)

        # 1. Icono de Seguridad Superior
        self.lbl_logo = QLabel("🔒", left_frame)
        self.lbl_logo.setStyleSheet("font-size: 50px; margin-bottom: 10px;")
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.lbl_logo)

        # 2. Título de la Aplicación Base
        self.lbl_app_title = QLabel("SIPA SYSTEM", left_frame)
        self.lbl_app_title.setObjectName("AppTitle") # font-size: 26px del QSS
        self.lbl_app_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.lbl_app_title)

        # 3. Identidad dinámica inyectada en caliente desde el Markdown
        self.lbl_md_identity = QLabel(f"Instancia: {self.app_name}", left_frame)
        self.lbl_md_identity.setObjectName("UserName") # Color verde #00FF95 del QSS
        self.lbl_md_identity.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.lbl_md_identity)

        left_layout.addSpacing(25)

        # 4. Presentación Comercial / Pitch de Venta de la Herramienta
        self.lbl_pitch_title = QLabel("Capa de Integridad & Seguridad", left_frame)
        self.lbl_pitch_title.setObjectName("CardTitle") # Color azul #3A86FF
        self.lbl_pitch_title.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self.lbl_pitch_title)

        pitch_text = (
            "Ecosistema de control avanzado con arquitectura híbrida.\n\n"
            "• Métodos propios de análisis sintáctico AST.\n"
            "• Sincronización transparente MD ➔ SQLite.\n"
            "• Protocolo BOLARDO para blindaje de identidad."
        )
        self.lbl_pitch_desc = QLabel(pitch_text, left_frame)
        self.lbl_pitch_desc.setStyleSheet("color: #888888; font-size: 12px; line-height: 16px;")
        self.lbl_pitch_desc.setWordWrap(True)
        left_layout.addWidget(self.lbl_pitch_desc)

        left_layout.addStretch()
        master_layout.addWidget(left_frame, stretch=45) # 45% del ancho

        # ==========================================================
        # BLOQUE DERECHO: FORMULARIO DE ACCESO Y AUTENTICACIÓN
        # ==========================================================
        right_frame = QFrame(self)
        right_frame.setStyleSheet("background-color: #121212;") # Fondo base oscuro
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(50, 50, 50, 50)
        right_layout.setSpacing(12)

        # Cabecera del Formulario
        self.lbl_form_title = QLabel("AUTENTICACIÓN DE OPERADOR", right_frame)
        self.lbl_form_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #E0E0E0; letter-spacing: 1px;")
        right_layout.addWidget(self.lbl_form_title)
        
        self.lbl_form_subtitle = QLabel("Verificación de firma digital y base relacional", right_frame)
        self.lbl_form_subtitle.setStyleSheet("color: #666666; font-size: 11px; margin-bottom: 5px;")
        right_layout.addWidget(self.lbl_form_subtitle)

        # Campos de Credenciales (Estructura real para rellenar o usar el botón directo)
        self.lbl_user = QLabel("OPERADOR ELECTRÓNICO / DNI", right_frame)
        self.lbl_user.setStyleSheet("font-size: 10px; color: #3A86FF; font-weight: bold;")
        right_layout.addWidget(self.lbl_user)
        
        self.txt_user = QLineEdit(right_frame)
        self.txt_user.setPlaceholderText("Introduce tu DNI o email")
        self.txt_user.setStyleSheet(
            "background-color: #1A1A1A; color: #E0E0E0; border: 1px solid #333333; "
            "padding: 8px; border-radius: 5px; font-family: 'Consolas', monospace;"
        )
        right_layout.addWidget(self.txt_user)

        self.lbl_password = QLabel("CLAVE DE ACCESO CRÍPTICA", right_frame)
        self.lbl_password.setStyleSheet("font-size: 10px; color: #3A86FF; font-weight: bold;")
        right_layout.addWidget(self.lbl_password)
        
        self.txt_password = QLineEdit(right_frame)
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setPlaceholderText("••••••••••••")
        self.txt_password.setStyleSheet(
            "background-color: #1A1A1A; color: #E0E0E0; border: 1px solid #333333; "
            "padding: 8px; border-radius: 5px; font-family: 'Consolas', monospace;"
        )
        right_layout.addWidget(self.txt_password)

        # Botón de Validación de Identidad Certificada (Un clic)
        try:
            profile = self.db.get_user_profile()
            btn_text = f"ACCEDER COMO: {profile['nombre_completo']}" if profile else "ACCEDER AL SISTEMA"
        except Exception:
            btn_text = "ACCEDER AL DASHBOARD"

        self.btn_login = QPushButton(btn_text, right_frame)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setStyleSheet(
            "QPushButton { background-color: #333333; padding: 12px; font-size: 11px; margin-top: 10px; } "
            "QPushButton:hover { background-color: #00FF95; color: #121212; }"
        )
        self.btn_login.clicked.connect(self.procesar_login)
        right_layout.addWidget(self.btn_login)

        # Checkbox: Recordar Identidad (Bypass para arranques directos futuros)
        self.chk_remember = QCheckBox("Mantener mi identidad autorizada en este equipo (Bypass)", right_frame)
        self.chk_remember.setChecked(True)
        self.chk_remember.setStyleSheet("color: #888888; font-size: 11px; margin-top: 5px;")
        right_layout.addWidget(self.chk_remember)

        # Consola Inferior del Frame (Usa ID #Console del QSS)
        self.lbl_status = QLabel("● NÚCLEO CONFIGURADO Y ESPERANDO FIRMA", right_frame)
        self.lbl_status.setObjectName("Console")
        self.lbl_status.setStyleSheet("padding: 6px; border-radius: 4px; font-size: 10px; margin-top: 10px;")
        right_layout.addWidget(self.lbl_status)

        right_layout.addStretch()
        master_layout.addWidget(right_frame, stretch=55) # 55% del ancho

    def procesar_login(self):
        """Registra la elección del usuario en DB y emite la señal de éxito."""
        config_data = {"remember_me": self.chk_remember.isChecked()}
        config_str = json.dumps(config_data)
        
        try:
            self.db._cursor.execute("UPDATE user SET config_seguridad = ? WHERE id = 1", (config_str,))
            self.db._conn.commit()
            
            user_data = dict(self.db.get_user_profile())
            logger.info(f"🟢 Acceso Manual Autorizado para: {user_data['nombre_completo']}")
            
            self.lbl_status.setText("✅ ACCESO CONCEDIDO. Cargando entorno de trabajo...")
            self.lbl_status.setStyleSheet("color: #00FF95; background-color: #050505; padding: 6px;")
            
            # Emitimos la señal hacia sipa.py pasando el diccionario del usuario
            self.login_concedido.emit(user_data)
        except Exception as e:
            logger.error(f"Fallo crítico al asentar configuración de Login: {e}")
            self.lbl_status.setText(f"❌ FALLO DE ESCRITURA: {str(e)}")
            self.lbl_status.setStyleSheet("color: #FF0055; background-color: #050505; padding: 6px;")