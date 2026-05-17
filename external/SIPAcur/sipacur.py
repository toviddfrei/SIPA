# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: sipacur.py
# Módulo: SIPAcur (IA personal)
# Versión: 3.2.2.0 | Fecha: 17/05/2026
# Autor: Daniel Miñana Montero & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Refresco instantáneo tras procesado y 
# optimización de carga inicial.
# ==========================================================

import os
import json
import psutil
import getpass
import subprocess
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                               QLineEdit, QPushButton, QProgressBar, QTextEdit, 
                               QHeaderView, QTabWidget, QLabel, QFrame, QGridLayout,
                               QMessageBox, QAbstractItemView, QStyledItemDelegate, 
                               QComboBox)
from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, QThread, Signal, QTimer

# --- INTEGRACIÓN DEL SERVICIO CORE ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'core/services'))
try:
    from scsipacur_process_file import SIPAcurProcessorService
except ImportError:
    SIPAcurProcessorService = None

# --- CONFIGURACIÓN DE COLUMNAS ---
COLUMNAS_INBOX = [
    "id_interno", "pendiente", "revisado", "procesado", "registrado", 
    "nombre_fichero_original", "tipo", "path_actual", "unidad", "estado",
    "hash", "observaciones", "total_palabras", "palabras", "frase", 
    "path_publicado", "fecha_creación", "fecha_entrada", "fecha_publicación", 
    "tamaño_kB", "extensión", "enlace", "SIPAcur_Sugerencia"
]

COLUMNAS_CAPTURA = [
    "Selección", "id_interno", "pendiente", "revisado", "nombre_fichero_original", 
    "estado", "tamaño_kB", "fecha_entrada", "unidad", "path_actual"
]

# --- RUTAS ESTRUCTURALES ---
USER_NAME = getpass.getuser()
BASE_SIPA = f"/home/{USER_NAME}/SIPA"
INBOX_DIR = os.path.join(BASE_SIPA, "data/inbox")
PROCESADOS_DIR = os.path.join(BASE_SIPA, "data/knowledge/procesados")
DB_DIR = os.path.join(BASE_SIPA, "data/db")
SIPACUR_DIR = os.path.join(BASE_SIPA, "external/SIPAcur")

JSON_MASTER_PATH = os.path.join(SIPACUR_DIR, "indice_maestro.json")
SIPA_ACTIVOS_JSON = os.path.join(DB_DIR, "sipa_activos.json")

# --- DELEGADO PARA DESPLEGABLES ---
class ComboDelegate(QStyledItemDelegate):
    def __init__(self, opciones, parent=None):
        super().__init__(parent)
        self.opciones = opciones

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.opciones)
        return editor

    def setEditorData(self, editor, index):
        valor = index.data(Qt.ItemDataRole.EditRole)
        idx = editor.findText(str(valor))
        if idx >= 0: editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

# --- MODELO DE DATOS ---
class GenericModel(QAbstractTableModel):
    def __init__(self, dataset, columnas, editable=False):
        super().__init__()
        self._data = dataset
        self.columnas = columnas
        self.seleccionados = set()
        self.editable = editable

    def rowCount(self, p=None): return len(self._data)
    def columnCount(self, p=None): return len(self.columnas) + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)): return None
        row_data = self._data[index.row()]
        
        if index.column() == 0:
            if role == Qt.ItemDataRole.CheckStateRole:
                return Qt.CheckState.Checked if row_data.get('path_actual') in self.seleccionados else Qt.CheckState.Unchecked
            return None
        
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            col_key = self.columnas[index.column() - 1]
            return str(row_data.get(col_key, " "))
        return None

    def setData(self, index, value, role):
        if index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            row_path = self._data[index.row()].get('path_actual')
            if value == Qt.CheckState.Checked.value: self.seleccionados.add(row_path)
            else: self.seleccionados.discard(row_path)
            self.dataChanged.emit(index, index)
            return True
        
        if self.editable and role == Qt.ItemDataRole.EditRole:
            col_key = self.columnas[index.column() - 1]
            if self._data[index.row()].get(col_key) == value: return True

            self._data[index.row()][col_key] = value
            try:
                with open(SIPA_ACTIVOS_JSON, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=4, ensure_ascii=False)
                self.actualizar_fichero_fisico(self._data[index.row()])
            except: pass
            self.dataChanged.emit(index, index)
            return True
        return False

    def actualizar_fichero_fisico(self, item):
        ruta = item.get('path_actual')
        if not ruta or not os.path.exists(ruta): return
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                full_text = f.read()
            match = re.search(r'^---\s*\n(.*?)\n---\s*', full_text, re.DOTALL)
            body = full_text[match.end():] if match else full_text
            cabecera = ["---"]
            for col in COLUMNAS_INBOX:
                val = item.get(col, " ")
                if col in ["id_interno", "total_palabras", "hash", "tamaño_kB"]:
                    cabecera.append(f'{col}: {val},')
                else:
                    cabecera.append(f'{col}: "{val}",')
            cabecera.append("---")
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("\n".join(cabecera) + "\n" + body)
        except: pass

    def flags(self, index):
        fl = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 0: return fl | Qt.ItemFlag.ItemIsUserCheckable
        if self.editable:
            col_name = self.columnas[index.column() - 1]
            if col_name in ["nombre_fichero_original", "tipo", "estado", "observaciones", "enlace"]:
                return fl | Qt.ItemFlag.ItemIsEditable
        return fl

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section == 0: return "SEL"
            return self.columnas[section - 1].replace("_", " ").upper()
        return None

# --- THREADS DE TRABAJO ---
class ScannerWorker(QThread):
    progreso = Signal(int); log_msg = Signal(str); finalizado = Signal(list)
    def __init__(self, existentes):
        super().__init__()
        self.existentes = {item['path_actual'] for item in existentes}
        self.datos = existentes

    def run(self):
        self.log_msg.emit("🔍 Escaneo global iniciado...")
        contador = len(self.datos) + 1
        puntos = [str(Path.home())] + [p.mountpoint for p in psutil.disk_partitions() if p.mountpoint.startswith(('/media', '/mnt'))]
        for i, base in enumerate(list(set(puntos))):
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in ['node_modules', 'cache']]
                for f in files:
                    if f.lower().endswith(".md"):
                        ruta = os.path.join(root, f)
                        if ruta not in self.existentes:
                            try:
                                self.datos.append({
                                    "id_interno": contador, "pendiente": "Si", "nombre_fichero_original": f,
                                    "path_actual": ruta, "unidad": base, "estado": "FUERA",
                                    "tamaño_kB": round(os.stat(ruta).st_size/1024, 2),
                                    "fecha_entrada": datetime.now().strftime('%d/%m/%y')
                                })
                                self.existentes.add(ruta); contador += 1
                            except: continue
            self.progreso.emit(int(((i+1)/len(puntos))*100))
        self.finalizado.emit(self.datos)

class ProcessWorker(QThread):
    msg = Signal(str); finalizado = Signal()
    def __init__(self, rutas):
        super().__init__(); self.rutas = rutas
    def run(self):
        os.makedirs(PROCESADOS_DIR, exist_ok=True)
        rutas_destino = []
        for r in self.rutas:
            try:
                nombre = os.path.basename(r)
                destino = os.path.join(PROCESADOS_DIR, nombre)
                shutil.move(r, destino)
                rutas_destino.append(destino)
                self.msg.emit(f"📦 Movido: {nombre}")
            except Exception as e: self.msg.emit(f"❌ Error moviendo {r}: {e}")

        if SIPAcurProcessorService and rutas_destino:
            try:
                self.msg.emit("⚙️ Procesando etiquetas según plantilla...")
                servicio = SIPAcurProcessorService()
                servicio.procesar_lote(rutas_destino)
                self.msg.emit("✅ Sincronizado.")
            except Exception as e: self.msg.emit(f"❌ Error servicio: {e}")
        self.finalizado.emit()

# --- CLASE PRINCIPAL ---
class SIPAcurDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.datos_json = []; self.ficheros_inbox_memoria = {}
        self.setObjectName("SIPAcurDashboard")
        
        lyt_principal = QVBoxLayout(self)
        lyt_sup = QHBoxLayout()

        self.btn_process = QPushButton("⚙️ PROCESAR Y MOVER")
        self.btn_scan = QPushButton("🔍 ESCANEO GLOBAL")
        self.search_bar = QLineEdit(); self.search_bar.setPlaceholderText("Filtrar registros...")
        self.p_bar = QProgressBar(); self.p_bar.setFixedWidth(120)

        for b in [self.btn_process, self.btn_scan]: lyt_sup.addWidget(b)
        lyt_sup.addWidget(self.search_bar); lyt_sup.addWidget(self.p_bar)
        lyt_principal.addLayout(lyt_sup)

        self.tabs = QTabWidget()
        lyt_principal.addWidget(self.tabs)
        self._setup_tabs()

        self.cargar_datos()
        # Forzar carga inmediata al arrancar
        QTimer.singleShot(100, self.monitorear_inbox)
        QTimer.singleShot(300, self.monitorear_seguimiento)
        
        # Eventos
        self.btn_scan.clicked.connect(self.run_scanner)
        self.btn_process.clicked.connect(self.lanzar_procesado)
        self.search_bar.textChanged.connect(self.filtrar)

        self.v_inbox.doubleClicked.connect(self.abrir_fichero_en_editor)
        self.v_seg.doubleClicked.connect(self.abrir_fichero_en_editor)

        # Timers Asíncronos
        self.timer_inbox = QTimer(self)
        self.timer_inbox.timeout.connect(self.monitorear_inbox)
        self.timer_inbox.start(5000)

        self.timer_seg = QTimer(self)
        self.timer_seg.timeout.connect(self.monitorear_seguimiento)
        self.timer_seg.start(30000) # 30 segundos para evitar "saltos" mientras editas

    def _setup_tabs(self):
        self.tabs.addTab(QLabel("SIPACUR Ready"), "SIPACUR (IA)")
        self.tab_inbox = QWidget(); l_inbox = QVBoxLayout(self.tab_inbox)
        self.v_inbox = QTableView(); self.px_inbox = QSortFilterProxyModel()
        self.v_inbox.setSelectionBehavior(QAbstractItemView.SelectRows)
        l_inbox.addWidget(self.v_inbox); self.tabs.addTab(self.tab_inbox, "📥 INBOX")

        self.tab_seg = QWidget(); l_seg = QVBoxLayout(self.tab_seg)
        self.v_seg = QTableView(); self.px_seg = QSortFilterProxyModel()
        self.v_seg.setAlternatingRowColors(True)
        self.v_seg.setSelectionBehavior(QAbstractItemView.SelectRows)
        l_seg.addWidget(self.v_seg); self.tabs.addTab(self.tab_seg, "📊 SEGUIMIENTO")

        self.tab_reg = QWidget(); l_reg = QVBoxLayout(self.tab_reg)
        self.v_reg = QTableView(); self.px_reg = QSortFilterProxyModel()
        l_reg.addWidget(self.v_reg); self.tabs.addTab(self.tab_reg, "REGISTRO")

        self.log_txt = QTextEdit(); self.log_txt.setReadOnly(True)
        self.tabs.addTab(self.log_txt, "LOG")

    def cargar_datos(self):
        if os.path.exists(JSON_MASTER_PATH):
            try:
                with open(JSON_MASTER_PATH, "r") as f: self.datos_json = json.load(f)
            except: self.datos_json = []
        self.model_reg = GenericModel(self.datos_json, COLUMNAS_CAPTURA)
        self.px_reg.setSourceModel(self.model_reg); self.v_reg.setModel(self.px_reg)

    def filtrar(self, t):
        for p in [self.px_inbox, self.px_seg, self.px_reg]: p.setFilterFixedString(t)

    def monitorear_inbox(self):
        if not os.path.exists(INBOX_DIR): return
        ficheros = {os.path.join(INBOX_DIR, f): os.path.getmtime(os.path.join(INBOX_DIR, f)) 
                    for f in os.listdir(INBOX_DIR) if f.endswith(".md")}
        if ficheros != self.ficheros_inbox_memoria:
            self.ficheros_inbox_memoria = ficheros
            datos = [extraer_frontmatter(p, i+1) for i, p in enumerate(ficheros.keys())]
            self.model_inbox = GenericModel(datos, COLUMNAS_INBOX)
            self.px_inbox.setSourceModel(self.model_inbox); self.v_inbox.setModel(self.px_inbox)

    def monitorear_seguimiento(self, forzar=False):
        # Si no es un refresco forzado, comprobamos el foco para no molestar al usuario
        if not forzar:
            if self.v_seg.hasFocus() or (self.v_seg.currentIndex().isValid() and self.v_seg.currentIndex().column() != 0):
                return 

        if not os.path.exists(SIPA_ACTIVOS_JSON): return
        try:
            if SIPAcurProcessorService:
                servicio = SIPAcurProcessorService()
                datos = servicio.sincronizar_ubicaciones_reales() 
            else:
                with open(SIPA_ACTIVOS_JSON, "r", encoding="utf-8") as f: datos = json.load(f)
            
            if not datos: return

            self.model_seg = GenericModel(datos, COLUMNAS_INBOX, editable=True)
            self.px_seg.setSourceModel(self.model_seg); self.v_seg.setModel(self.px_seg)
            
            # Re-aplicar delegados
            tipos = ["Nota", "Acta", "Bitácora", "Tprofesional", "Tformativa", "Post", "Bloque"]
            estados = ["Pendiente", "Abierto", "Cerrado", "Publicado"]
            self.v_seg.setItemDelegateForColumn(COLUMNAS_INBOX.index("tipo")+1, ComboDelegate(tipos, self))
            self.v_seg.setItemDelegateForColumn(COLUMNAS_INBOX.index("estado")+1, ComboDelegate(estados, self))
        except: pass

    def abrir_fichero_en_editor(self, index):
        current_tab = self.tabs.currentIndex()
        if current_tab == 1: source_index = self.px_inbox.mapToSource(index)
        elif current_tab == 2:
            source_index = self.px_seg.mapToSource(index)
            if COLUMNAS_INBOX[source_index.column()-1] != "enlace": return
        else: return

        model = source_index.model()
        ruta = model.index(source_index.row(), COLUMNAS_INBOX.index("path_actual")+1).data()
        if ruta and os.path.exists(ruta):
            parent = self.window()
            if hasattr(parent, 'vista_editor'):
                parent.vista_editor.cargar_archivo(ruta)
                parent.navegar_a(1)
            else: self._abrir_sistema(ruta)

    def _abrir_sistema(self, ruta):
        opener = "open" if sys.platform == "darwin" else ("start" if sys.platform == "win32" else "xdg-open")
        subprocess.call([opener, ruta], shell=(sys.platform == "win32"))

    def lanzar_procesado(self):
        if not hasattr(self, 'model_inbox') or not self.model_inbox.seleccionados:
            QMessageBox.information(self, "SIPA", "Selecciona archivos en el Inbox primero.")
            return
        rutas = list(self.model_inbox.seleccionados)
        self.btn_process.setEnabled(False)
        self.worker_p = ProcessWorker(rutas)
        self.worker_p.msg.connect(self.log_txt.append)
        self.worker_p.finalizado.connect(self.finalizar_flujo_procesado)
        self.worker_p.start()

    def finalizar_flujo_procesado(self):
        self.btn_process.setEnabled(True)
        self.log_txt.append("✨ Proceso completado. Sincronizando tablas...")
        
        # EL CAMBIO CLAVE: Refresco forzado inmediato
        self.monitorear_inbox()
        self.monitorear_seguimiento(forzar=True)
        
        self.tabs.setCurrentIndex(2) # Cambiar a la pestaña de seguimiento automáticamente

    def run_scanner(self):
        self.btn_scan.setEnabled(False)
        self.worker = ScannerWorker(self.datos_json)
        self.worker.progreso.connect(self.p_bar.setValue)
        self.worker.finalizado.connect(self.on_scan_fin); self.worker.start()

    def on_scan_fin(self, d):
        self.datos_json = d
        with open(JSON_MASTER_PATH, "w") as f: json.dump(d, f, indent=4)
        self.cargar_datos(); self.btn_scan.setEnabled(True)

def extraer_frontmatter(ruta, id_asignado=0):
    metadatos = {col: " " for col in COLUMNAS_INBOX}
    if not os.path.exists(ruta): return metadatos
    try:
        metadatos.update({
            "id_interno": str(id_asignado),
            "tamaño_kB": str(round(os.path.getsize(ruta)/1024, 2)),
            "nombre_fichero_original": os.path.basename(ruta),
            "path_actual": ruta,
            "extensión": os.path.splitext(ruta)[1].replace(".", "")
        })
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()
        match = re.search(r'^---\s*\n(.*?)\n---\s*', contenido, re.DOTALL)
        if match:
            for linea in match.group(1).split('\n'):
                if ':' in linea:
                    k, v = linea.split(':', 1)
                    k = k.strip()
                    if k in metadatos: metadatos[k] = v.strip().rstrip(',').strip('"').strip("'")
    except: pass
    return metadatos

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = SIPAcurDashboard()
    win.show()
    sys.exit(app.exec())