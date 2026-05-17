import os
import json
import hashlib
import threading
import time
import subprocess
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel, QMessageBox, QApplication)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont

# --- CONFIGURACIÓN DE RUTAS ---
SERVICIOS_PATH = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(SERVICIOS_PATH, ".sipa_manifest")

class VistaServicios(QWidget):
    datos_actualizados = Signal(dict)
    # Recibe respuesta de la interfaz (título, mensaje, nombre_servicio, nuevo_hash)
    solicitar_autorizacion = Signal(str, str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hashes_referencia = {}  
        self.servicios_registrados = set()  
        self.alertas_disparadas = {}  
        
        # Cargar o inicializar el manifiesto permanente de hashes
        self.cargar_o_crear_manifiesto()
        
        self.init_ui()
        
        self.monitor_activo = True
        self.hilo_check = threading.Thread(target=self.bucle_monitoreo, daemon=True)
        self.hilo_check.start()
        
        self.datos_actualizados.connect(self.refrescar_tabla)
        self.solicitar_autorizacion.connect(self.mostrar_alerta_decision)

    def cargar_o_crear_manifiesto(self):
        """Carga los hashes seguros desde el disco o los crea por primera vez si no existen."""
        try:
            archivos = [f for f in os.listdir(SERVICIOS_PATH) if f.endswith('.py') and f != "ssipa_servicios.py"]
        except:
            archivos = []

        if os.path.exists(MANIFEST_PATH):
            try:
                with open(MANIFEST_PATH, 'r') as f:
                    self.hashes_referencia = json.load(f)
                # Sincronizar la lista de lo que DEBERÍA existir basado en el manifiesto guardado
                for nombre in self.hashes_referencia.keys():
                    self.servicios_registrados.add(nombre)
                    self.alertas_disparadas[nombre] = {"existencia": False, "integridad": False}
            except:
                pass
        
        # Si hay archivos nuevos en la carpeta que no estaban en el manifiesto, se indexan ahora
        modificado = False
        for nombre in archivos:
            if nombre not in self.hashes_referencia:
                ruta = os.path.join(SERVICIOS_PATH, nombre)
                h = self.calcular_sha256(ruta)
                if h:
                    self.hashes_referencia[nombre] = h
                    self.servicios_registrados.add(nombre)
                    self.alertas_disparadas[nombre] = {"existencia": False, "integridad": False}
                    modificado = True
        
        if modificado:
            self.guardar_manifiesto_en_disco()

    def guardar_manifiesto_en_disco(self):
        """Guarda la base de datos de hashes de forma física en el almacenamiento."""
        try:
            with open(MANIFEST_PATH, 'w') as f:
                json.dump(self.hashes_referencia, f, indent=4)
        except Exception as e:
            print(f"Error guardando manifiesto de seguridad: {e}")

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_titulo = QLabel("MONITOR DE ALTA SEGURIDAD: INTEGRIDAD DE NÚCLEO")
        self.lbl_titulo.setObjectName("AppTitle")
        layout.addWidget(self.lbl_titulo)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "SERVICIO", "HASH SHA-256", "PASO 1: EXISTE", "PASO 2: INTEGRIDAD", "PASO 3: PROCESO OS", "ESTADO FINAL"
        ])
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        
        layout.addWidget(self.tabla)

    def calcular_sha256(self, ruta):
        hasher = hashlib.sha256()
        try:
            with open(ruta, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return None

    def verificar_proceso_activo(self, nombre_archivo):
        """Paso 3 Infalible: Verifica la presencia del archivo de latido (.live)."""
        nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
        ruta_live = os.path.join(SERVICIOS_PATH, f".{nombre_sin_ext}.live")
        return os.path.exists(ruta_live)

    def bucle_monitoreo(self):
        """Bucle permanente en hilo secundario."""
        while self.monitor_activo:
            dict_actual = {}
            
            # Analizamos basándonos estrictamente en el Manifiesto Permanente
            for nombre in list(self.servicios_registrados):
                ruta = os.path.join(SERVICIOS_PATH, nombre)
                existe = os.path.exists(ruta)
                
                if not existe:
                    p1_str = "🔴 ELIMINADO"
                    p2_str = "🔴 CRÍTICO"
                    p3_str = "🔴 INACTIVO"
                    estado_final = "🔴 ALERTA FALTANTE"
                    hash_mostrar = "BORRADO"
                    global_ok = False
                    
                    if not self.alertas_disparadas[nombre]["existencia"]:
                        self.alertas_disparadas[nombre]["existencia"] = True
                        self.datos_actualizados.emit(dict_actual) 
                else:
                    self.alertas_disparadas[nombre]["existencia"] = False
                    p1_str = "🟢 SÍ"
                    
                    hash_actual = self.calcular_sha256(ruta)
                    hash_mostrar = hash_actual[:16] + "..." if hash_actual else "ERROR"
                    
                    hash_original = self.hashes_referencia.get(nombre)
                    hash_valido = (hash_actual is not None and hash_actual == hash_original)
                    
                    if not hash_valido:
                        p2_str = "🔴 ALTERADO"
                        p3_str = "🔴 RECHAZADO"
                        estado_final = "🔴 ALERTA INTEGRIDAD"
                        global_ok = False
                        
                        # Disparar Ventana Interactiva si es un cambio no controlado aún
                        if not self.alertas_disparadas[nombre]["integridad"]:
                            self.alertas_disparadas[nombre]["integridad"] = True
                            self.solicitar_autorizacion.emit(
                                "VIOLACIÓN DE INTEGRIDAD DETECTADA",
                                f"El servicio '{nombre}' ha sido modificado o reemplazado de forma externa.\n\n"
                                f"Hash Esperado: {hash_original[:16]}...\n"
                                f"Hash Detectado: {hash_actual[:16]}...\n\n"
                                "¿Desea AUTORIZAR este cambio y registrar el nuevo Hash como legítimo?",
                                nombre,
                                hash_actual
                            )
                    else:
                        self.alertas_disparadas[nombre]["integridad"] = False
                        p2_str = "🟢 ÍNTEGRO"
                        
                        proceso_vivo = self.verificar_proceso_activo(nombre)
                        p3_str = "🟢 ACTIVO" if proceso_vivo else "🔴 APAGADO"
                        estado_final = "🟢 CORRIENDO" if proceso_vivo else "🔴 DETENIDO"
                        global_ok = proceso_vivo

                dict_actual[nombre] = {
                    "hash": hash_mostrar,
                    "p1": p1_str,
                    "p2": p2_str,
                    "p3": p3_str,
                    "estado": estado_final,
                    "ok": global_ok
                }
            
            self.datos_actualizados.emit(dict_actual)
            time.sleep(1.5)

    @Slot(dict)
    def refrescar_tabla(self, datos):
        self.tabla.setRowCount(0)
        for fila, (nombre, info) in enumerate(datos.items()):
            self.tabla.insertRow(fila)
            
            item_nombre = QTableWidgetItem(nombre)
            item_hash = QTableWidgetItem(info["hash"])
            item_p1 = QTableWidgetItem(info["p1"])
            item_p2 = QTableWidgetItem(info["p2"])
            item_p3 = QTableWidgetItem(info["p3"])
            item_estado = QTableWidgetItem(info["estado"])

            for item in [item_p1, item_p2, item_p3, item_estado]:
                item.setTextAlignment(Qt.AlignCenter)

            if not info["ok"]:
                font_alerta = QFont()
                font_alerta.setBold(True)
                for item in [item_nombre, item_p1, item_p2, item_p3, item_estado]:
                    item.setForeground(QColor("#FF3333"))
                    item.setFont(font_alerta)

            self.tabla.setItem(fila, 0, item_nombre)
            self.tabla.setItem(fila, 1, item_hash)
            self.tabla.setItem(fila, 2, item_p1)
            self.tabla.setItem(fila, 3, item_p2)
            self.tabla.setItem(fila, 4, item_p3)
            self.tabla.setItem(fila, 5, item_estado)
            
        QApplication.processEvents()

    @Slot(str, str, str, str)
    def mostrar_alerta_decision(self, titulo, mensaje, nombre_servicio, nuevo_hash):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        
        btn_aceptar = msg_box.addButton("Sí, Autorizar cambio", QMessageBox.YesRole)
        btn_rechazar = msg_box.addButton("No, Bloquear Servicio", QMessageBox.NoRole)
        
        msg_box.setStyleSheet("""
            QMessageBox { background-color: #1A1A1A; color: #E0E0E0; }
            QLabel { color: #E0E0E0; font-size: 13px; }
            QPushButton { background-color: #333; color: white; padding: 6px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #444; }
        """)
        
        btn_aceptar.setStyleSheet("background-color: #228B22; font-weight: bold; color: white;")
        btn_rechazar.setStyleSheet("background-color: #FF3333; font-weight: bold; color: white;")
        
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_aceptar:
            self.hashes_referencia[nombre_servicio] = nuevo_hash
            self.guardar_manifiesto_en_disco()
            self.alertas_disparadas[nombre_servicio]["integridad"] = False
            
            info_box = QMessageBox(self)
            info_box.setIcon(QMessageBox.Information)
            info_box.setWindowTitle("MANIFIESTO ACTUALIZADO")
            info_box.setText(f"El nuevo hash para '{nombre_servicio}' ha sido registrado como seguro de forma permanente.")
            info_box.setStyleSheet("QMessageBox { background-color: #1A1A1A; color: #E0E0E0; } QLabel{color:#e0e0e0;}")
            info_box.exec()
        else:
            pass