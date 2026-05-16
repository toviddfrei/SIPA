# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: sipacur.py
# Módulo: SIPAcur (IA personal)
# Versión: 1.4.9.1 | Fecha: 14/05/2026
# Autor: Daniel Miñana Montero & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Dashboard del módulo SIPAcur, puntos de inicio
# de los distintos servios, y punto visual del funcionamiento
# ==========================================================

import sys
import os
import json
import psutil
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QTableView, QLineEdit, 
                             QPushButton, QLabel, QProgressBar, QTextEdit, 
                             QFrame, QHeaderView)
from PyQt6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# --- CONFIGURACIÓN DE COLUMNAS ---
COLUMNAS = [
    "Selección", "id_interno", "pendiente", "revisado", "nombre_fichero_original", 
    "estado", "tamaño_kB", "fecha_entrada", "unidad", "path_actual"
]

# --- CARGADOR DE ESTILO ---
def aplicar_estilo(app):
    ruta_qss = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.qss")
    if os.path.exists(ruta_qss):
        with open(ruta_qss, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            print("🎨 Estilo QSS cargado correctamente.")

# --- MODELO DE LA TABLA (Integrado para evitar ModuleNotFoundError) ---
class MarkdownModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.seleccionados = set()

    def data(self, index, role):
        if not index.isValid(): return None
        row_data = self._data[index.row()]
        col_key = COLUMNAS[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            if col_key == "Selección": return ""
            return str(row_data.get(col_key, ""))

        if role == Qt.ItemDataRole.CheckStateRole and col_key == "Selección":
            return Qt.CheckState.Checked if row_data['id_interno'] in self.seleccionados else Qt.CheckState.Unchecked

        return None

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.CheckStateRole and COLUMNAS[index.column()] == "Selección":
            row_id = self._data[index.row()]['id_interno']
            if value == Qt.CheckState.Checked.value:
                self.seleccionados.add(row_id)
            else:
                self.seleccionados.discard(row_id)
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        base_flags = super().flags(index)
        if COLUMNAS[index.column()] == "Selección":
            return base_flags | Qt.ItemFlag.ItemIsUserCheckable
        return base_flags

    def rowCount(self, index=None): return len(self._data)
    def columnCount(self, index=None): return len(COLUMNAS)
    
    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return COLUMNAS[section].replace("_", " ").upper()
        return None

# --- MOTOR DE ESCANEO (Hilo secundario) ---
class ScannerWorker(QThread):
    progreso = pyqtSignal(int)
    log_msg = pyqtSignal(str)
    finalizado = pyqtSignal(list)

    def __init__(self, datos_existentes):
        super().__init__()
        self.existentes = {item['path_actual'] for item in datos_existentes}
        self.datos_acumulados = datos_existentes

    def run(self):
        self.log_msg.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Escaneo iniciado...")
        contador = len(self.datos_acumulados) + 1
        rutas_inicio = [str(Path.home())]
        
        # Detectar unidades en Linux
        for p in psutil.disk_partitions():
            if p.mountpoint.startswith(('/media', '/mnt')):
                rutas_inicio.append(p.mountpoint)

        for i, punto_base in enumerate(list(set(rutas_inicio))):
            for root, dirs, files in os.walk(punto_base):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in ['node_modules', 'cache']]
                for file in files:
                    if file.lower().endswith(".md"):
                        ruta = os.path.join(root, file)
                        if ruta not in self.existentes:
                            try:
                                stat = os.stat(ruta)
                                item = {
                                    "id_interno": contador, "pendiente": "Si", "revisado": "No",
                                    "nombre_fichero_original": file, "path_actual": ruta,
                                    "unidad": punto_base, "estado": "FUERA",
                                    "tamaño_kB": round(stat.st_size / 1024, 2),
                                    "fecha_entrada": datetime.now().strftime('%d/%m/%y')
                                }
                                self.datos_acumulados.append(item)
                                self.existentes.add(ruta)
                                contador += 1
                            except: continue
            self.progreso.emit(int(((i + 1) / len(rutas_inicio)) * 100))
        self.finalizado.emit(self.datos_acumulados)

# --- DASHBOARD PRINCIPAL ---
class SIPAcurDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIPAcur v2.0 - Dashboard de Captura")
        self.setMinimumSize(1400, 850)
        self.datos_json = []
        self.cargar_datos()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        lyt = QHBoxLayout(main_widget)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        side_lyt = QVBoxLayout(self.sidebar)
        
        self.btn_scan = QPushButton("🔍 ESCANEO GLOBAL")
        self.btn_import = QPushButton("📥 TRAER A SIPA")
        self.btn_delete = QPushButton("🗑️ BORRAR SELECCIÓN")
        
        for b in [self.btn_scan, self.btn_import, self.btn_delete]:
            side_lyt.addWidget(b)
        
        side_lyt.addStretch()
        lyt.addWidget(self.sidebar)

        # Tabs
        self.tabs = QTabWidget()
        lyt.addWidget(self.tabs)

        # Tab Registro
        self.tab_reg = QWidget()
        self.tab_reg.setObjectName("AreaContenido")
        reg_lyt = QVBoxLayout(self.tab_reg)
        
        search_lyt = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filtrar archivos...")
        self.p_bar = QProgressBar()
        search_lyt.addWidget(self.search_bar, 3)
        search_lyt.addWidget(self.p_bar, 1)
        reg_lyt.addLayout(search_lyt)

        self.table = QTableView()
        self.proxy = QSortFilterProxyModel()
        reg_lyt.addWidget(self.table)
        self.tabs.addTab(self.tab_reg, "REGISTRO DE CAPTURA")

        # Tab Log
        self.log_txt = QTextEdit()
        self.log_txt.setObjectName("ConsoleLog")
        self.log_txt.setReadOnly(True)
        self.tabs.addTab(self.log_txt, "LOG DE PROCESO")

        self.refresh_table()
        self.btn_scan.clicked.connect(self.run_scanner)
        self.search_bar.textChanged.connect(self.proxy.setFilterFixedString)

    def cargar_datos(self):
        if os.path.exists("indice_maestro.json"):
            try:
                with open("indice_maestro.json", "r", encoding="utf-8") as f:
                    self.datos_json = json.load(f)
            except: self.datos_json = []

    def refresh_table(self):
        self.model = MarkdownModel(self.datos_json)
        self.proxy.setSourceModel(self.model)
        self.table.setModel(self.proxy)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    def run_scanner(self):
        self.btn_scan.setEnabled(False)
        self.worker = ScannerWorker(self.datos_json)
        self.worker.progreso.connect(self.p_bar.setValue)
        self.worker.log_msg.connect(self.log_txt.append)
        self.worker.finalizado.connect(self.on_finish)
        self.worker.start()

    def on_finish(self, data):
        self.datos_json = data
        with open("indice_maestro.json", "w", encoding="utf-8") as f:
            json.dump(self.datos_json, f, indent=4, ensure_ascii=False)
        self.refresh_table()
        self.btn_scan.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    aplicar_estilo(app) 
    win = SIPAcurDashboard()
    win.show()
    sys.exit(app.exec())