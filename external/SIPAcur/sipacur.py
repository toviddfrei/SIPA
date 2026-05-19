# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: sipacur.py (VERSIÓN COMPLETA REESTRUCTURADA)
# Módulo: SIPAcur (Dashboard IA Personal)
# Versión: 3.9.2 | Fecha: 19/05/2026
# ==========================================================

import os
import json
import getpass
import subprocess
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                               QLineEdit, QPushButton, QProgressBar, QTextEdit, 
                               QTabWidget, QLabel, QFrame, QGridLayout,
                               QMessageBox, QAbstractItemView, QStyledItemDelegate, 
                               QComboBox, QApplication)
from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, QTimer

# --- INTEGRACIÓN DEL SERVICIO CORE ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'core/services'))
try:
    from scsipacur_process_file import SIPAcurProcessorService
    from scsipacur_learn_file import SIPA_Learn_Service # <-- Nuevo
except ImportError:
    SIPAcurProcessorService = None
    SIPA_Learn_Service = None

# ==========================================================
# COMPONENTES DE INTERFAZ (Delegados y Modelos)
# ==========================================================

class ComboDelegate(QStyledItemDelegate):
    def __init__(self, opciones, parent=None):
        super().__init__(parent)
        self.opciones = opciones
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.opciones)
        return editor
    def setEditorData(self, editor, index):
        idx = editor.findText(str(index.data(Qt.ItemDataRole.EditRole)))
        if idx >= 0: editor.setCurrentIndex(idx)
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

class GenericModel(QAbstractTableModel):
    def __init__(self, dataset, columnas, editable=False, servicio=None):
        super().__init__()
        self._data = dataset
        self.columnas = columnas
        self.seleccionados = set()
        self.editable = editable
        self.servicio = servicio

    def rowCount(self, p=None): return len(self._data)
    def columnCount(self, p=None): return len(self.columnas) + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)): return None
        row_data = self._data[index.row()]
        
        if index.column() == 0:
            if role == Qt.ItemDataRole.CheckStateRole:
                path = row_data.get('path_actual')
                if path: return Qt.CheckState.Checked if path in self.seleccionados else Qt.CheckState.Unchecked
            return None
            
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            col_key = self.columnas[index.column() - 1]
            val = row_data.get(col_key, " ")
            if isinstance(val, bool) and col_key == "verificado":
                return "✅ VERIFICADO" if val else "❌ PENDIENTE"
            return str(val)
        
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
            
        return None

    def setData(self, index, value, role):
        if index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            path = self._data[index.row()].get('path_actual')
            if path:
                if value == Qt.CheckState.Checked.value: self.seleccionados.add(path)
                else: self.seleccionados.discard(path)
                self.dataChanged.emit(index, index); return True
        
        if self.editable and role == Qt.ItemDataRole.EditRole:
            col_key = self.columnas[index.column() - 1]
            
            if col_key == "verificado":
                value = True if value in ["✅ VERIFICADO", "Verificado", "True", True] else False
                
            self._data[index.row()][col_key] = value
            
            if self.servicio and hasattr(self.servicio, 'actualizar_item_completo'):
                self.servicio.actualizar_item_completo(self._data[index.row()])
            elif hasattr(self, 'guardar_callback') and self.guardar_callback:
                self.guardar_callback()
                
            self.dataChanged.emit(index, index); return True
        return False

    def flags(self, index):
        fl = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 0: 
            if self._data and self._data[0].get('path_actual'):
                return fl | Qt.ItemFlag.ItemIsUserCheckable
            return fl
        if self.editable:
            col_actual = self.columnas[index.column()-1]
            if col_actual in ["tipo", "estado", "observaciones", "palabras", "frase", "nombre", "anotaciones", "verificado"]:
                return fl | Qt.ItemFlag.ItemIsEditable
        return fl

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return "SEL" if section == 0 else self.columnas[section-1].replace("_", " ").upper()
        return None

# ==========================================================
# DASHBOARD PRINCIPAL
# ==========================================================

class SIPAcurDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SIPAcur v3.9 - Dashboard de Activos")
        self.resize(1200, 800)
        
        self.service = SIPAcurProcessorService() if SIPAcurProcessorService else None
        self.service_learn = SIPA_Learn_Service() if SIPA_Learn_Service else None
        
        self.columnas_full = self.service.columnas_estandar if self.service else []
        self.cols_mapa = ["id_interno", "nombre", "fecha_detectado", "estado", 
                  "anotacion", "fecha_ingresado", "path_actual", "tamaño_kb", "ultima_modificacion"]
        self.cols_metricas = ["id", "nombre", "actual", "anterior", "anotaciones", "verificado"]
        
        # Ubicación en data/archive fuera de la base de conocimiento
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in locals() else os.getcwd()
        self.ruta_json_metricas = os.path.join(self.base_dir, "data", "archive", "metricas_config.json")
        self.cache_metricas = []

        lyt_principal = QVBoxLayout(self)
        
        # --- BARRA SUPERIOR DINÁMICA ---
        lyt_sup = QHBoxLayout()
        style_main_btns = "background-color: #2c3e50; color: white; font-weight: bold; border-radius: 4px; padding: 5px 15px;"
        
        self.btn_ingresar = QPushButton("📥 INGRESAR")
        self.btn_ingresar.setMinimumHeight(40)
        self.btn_ingresar.setStyleSheet(style_main_btns)
        
        self.btn_label = QPushButton("🏷️ ETIQUETAR")
        self.btn_label.setMinimumHeight(40)
        self.btn_label.setStyleSheet(style_main_btns)
        
        self.btn_procesar = QPushButton("⚙️ PROCESAR")
        self.btn_procesar.setMinimumHeight(40)
        self.btn_procesar.setStyleSheet(style_main_btns)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Filtrar globalmente...")
        self.search_bar.setMinimumHeight(40)
        self.search_bar.setStyleSheet("padding-left: 10px; border: 1px solid #bdc3c7; border-radius: 4px;")
        
        # Botones de Estado (Filtros Mapa)
        self.btn_f_seg = QPushButton("🔍")
        self.btn_f_seg.setFixedSize(40, 40)
        self.btn_f_seg.setToolTip("Ver solo SEGUIMIENTO")
        self.btn_f_seg.setStyleSheet("font-size: 16px; background-color: #ecf0f1; border-radius: 4px;")
        
        self.btn_f_pen = QPushButton("⏳")
        self.btn_f_pen.setFixedSize(40, 40)
        self.btn_f_pen.setToolTip("Ver solo PENDIENTES")
        self.btn_f_pen.setStyleSheet("font-size: 16px; background-color: #ecf0f1; border-radius: 4px;")
        
        self.btn_f_all = QPushButton("🌐")
        self.btn_f_all.setFixedSize(40, 40)
        self.btn_f_all.setToolTip("Ver TODOS los activos")
        self.btn_f_all.setStyleSheet("font-size: 16px; background-color: #ecf0f1; border-radius: 4px;")
        
        lyt_sup.addWidget(self.btn_ingresar)
        lyt_sup.addWidget(self.btn_label)
        lyt_sup.addWidget(self.btn_procesar)
        lyt_sup.addWidget(self.search_bar)
        lyt_sup.addWidget(self.btn_f_seg)
        lyt_sup.addWidget(self.btn_f_pen)
        lyt_sup.addWidget(self.btn_f_all)
        lyt_principal.addLayout(lyt_sup)

        # --- Tabs ---
        self.tabs = QTabWidget()
        lyt_principal.addWidget(self.tabs)
        self._setup_tabs()

        # --- Conexiones ---
        self.btn_label.clicked.connect(self.lanzar_etiquetado)
        self.search_bar.textChanged.connect(self.filtrar)
        
        self.btn_f_seg.clicked.connect(lambda: self.aplicar_filtro_mapa("Seguimiento"))
        self.btn_f_pen.clicked.connect(lambda: self.aplicar_filtro_mapa("Pendiente"))
        self.btn_f_all.clicked.connect(lambda: self.aplicar_filtro_mapa(""))

        # Cargar base persistente
        self._cargar_metricas_desde_disco()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_todo)
        self.timer.start(30000)
        QTimer.singleShot(500, self.actualizar_todo)

    def _setup_tabs(self):
        # 1. PESTAÑA PRESENTACIÓN
        self.tab_presentacion = QWidget()
        lyt_grid = QGridLayout(self.tab_presentacion)
        
        self.frame_logo = QFrame()
        self.frame_logo.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        lyt_logo = QVBoxLayout(self.frame_logo)
        self.lbl_status_ia = QLabel("● IA ENGINE: STANDBY")
        self.lbl_status_ia.setStyleSheet("color: gray; font-weight: bold; font-size: 10px;")
        lyt_logo.addWidget(self.lbl_status_ia)
        self.lbl_icono = QLabel("🧬")
        self.lbl_icono.setStyleSheet("font-size: 80px;")
        self.lbl_icono.setAlignment(Qt.AlignCenter)
        lyt_logo.addWidget(self.lbl_icono)
        lyt_logo.addWidget(QLabel("<b>SIPAcur v3.9</b><br>Identificación Personal Autorizada", alignment=Qt.AlignCenter))
        lyt_grid.addWidget(self.frame_logo, 0, 0, 2, 1)

        self.frame_prompt = QFrame()
        self.frame_prompt.setFrameStyle(QFrame.StyledPanel)
        lyt_prompt = QVBoxLayout(self.frame_prompt)
        lyt_prompt.addWidget(QLabel("💬 Comando rápido:"))
        self.txt_prompt = QLineEdit()
        self.txt_prompt.setPlaceholderText("Escribir instrucción...")
        lyt_prompt.addWidget(self.txt_prompt)
        lyt_grid.addWidget(self.frame_prompt, 0, 1)

        self.frame_stats = QFrame()
        self.frame_stats.setFrameStyle(QFrame.StyledPanel)
        self.lyt_stats = QVBoxLayout(self.frame_stats)
        self.lbl_titulo_stats = QLabel("📊 AUDITORÍA DE ACTIVOS")
        self.lbl_titulo_stats.setStyleSheet("font-weight: bold; color: #34495e; font-size: 12px;")
        self.lyt_stats.addWidget(self.lbl_titulo_stats)
        
        self.lbl_count_files = QLabel("") 
        self.lbl_metrica_control = QLabel("") 
        
        self.txt_evolucion = QTextEdit()
        self.txt_evolucion.setReadOnly(True)
        self.txt_evolucion.setMinimumHeight(220)
        self.txt_evolucion.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; padding: 10px;")
        self.lyt_stats.addWidget(self.txt_evolucion)
        lyt_grid.addWidget(self.frame_stats, 1, 1)

        self.tabs.addTab(self.tab_presentacion, "🏠 INICIO")

        # 2. PESTAÑA TABLA DE MÉTRICAS PEDAGÓGICAS (ORDEN CORREGIDO AQUÍ)
        self.v_metricas = QTableView()
        self.px_metricas = QSortFilterProxyModel()
        self.v_metricas.setSortingEnabled(True)
        self.v_metricas.setAlternatingRowColors(True)
        self.v_metricas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabs.addTab(self.v_metricas, "📈 MÈTRICAS")
        self.px_metricas.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # 3. PESTAÑA MAPA
        self.v_mapa = QTableView()
        self.px_mapa = QSortFilterProxyModel()
        self.v_mapa.setSortingEnabled(True)
        self.v_mapa.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.v_mapa.setAlternatingRowColors(True)
        self.v_mapa.doubleClicked.connect(self.abrir_fichero_mapa)
        self.tabs.addTab(self.v_mapa, "🗺️ MAPA")
        self.px_mapa.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # 4. PESTAÑA INBOX
        self.v_inbox = QTableView()
        self.px_inbox = QSortFilterProxyModel()
        self.v_inbox.setSortingEnabled(True)
        self.v_inbox.setAlternatingRowColors(True)
        self.v_inbox.doubleClicked.connect(self.abrir_fichero)
        self.tabs.addTab(self.v_inbox, "📥 INBOX")

        # 5. PESTAÑA SEGUIMIENTO
        self.v_seg = QTableView()
        self.px_seg = QSortFilterProxyModel()
        self.v_seg.setSortingEnabled(True)
        self.v_seg.setAlternatingRowColors(True)
        self.v_seg.doubleClicked.connect(self.abrir_fichero)
        self.tabs.addTab(self.v_seg, "📊 SEGUIMIENTO")

    def _obtener_peso_carpeta(self, ruta):
        total = 0
        if os.path.exists(ruta):
            if os.path.isdir(ruta):
                for dirpath, dirnames, filenames in os.walk(ruta):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp): total += os.path.getsize(fp)
            else:
                total = os.path.getsize(ruta)
        return total / (1024 * 1024)

    def _cargar_metricas_desde_disco(self):
        os.makedirs(os.path.dirname(self.ruta_json_metricas), exist_ok=True)
        
        if not os.path.exists(self.ruta_json_metricas):
            self.cache_metricas = [
                {"id": "MET-001", "nombre": "Control del Ecosistema", "anterior": "58.0%", "anotaciones": "Porcentaje de archivos bajo control estricto del radar SIPA.", "verificado": True},
                {"id": "MET-002", "nombre": "Estrés sobre SIPA (Inbox)", "anterior": "12.5%", "anotaciones": "Impacto de archivos acumulados en bandeja de entrada pendientes de procesar.", "verificado": True},
                {"id": "MET-003", "nombre": "Actividad Semanal", "anterior": "14 mods", "anotaciones": "Volumen de escrituras y modificaciones detectadas en los últimos 7 días.", "verificado": False},
                {"id": "MET-004", "nombre": "Gasto Estructural SIPA (Nueva)", "anterior": "0.0%", "anotaciones": "Porcentaje del peso total consumido exclusivamente por la estructura del sistema SIPA (sin datos).", "verificado": False}
            ]
            self._guardar_metricas_a_disco()
        else:
            try:
                with open(self.ruta_json_metricas, 'r', encoding='utf-8') as f:
                    self.cache_metricas = json.load(f)
            except Exception as e:
                print(f"⚠️ Error leyendo histórico de métricas: {e}")

    def _guardar_metricas_a_disco(self):
        try:
            with open(self.ruta_json_metricas, 'w', encoding='utf-8') as f:
                json.dump(self.cache_metricas, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"⚠️ Error persistiendo métricas en disco: {e}")

    def actualizar_todo(self):
        if not self.service: return
        
        s = {"porcentaje_control": 0, "recuento_global": 0, "recuento_sipa": 0, 
             "recuento_pendiente": 0, "inbox_cantidad": 0, "porcentaje_inbox_sipa": 0,
             "peso_total_mb": 1.0, "salud_fantasmas": 0, "actividad_semanal": 0, "mapa_calor": {}}

        if self.service_learn:
            try:
                datos_mapa = self.service_learn.escanear_entorno()
                self.model_mapa = GenericModel(datos_mapa, self.cols_mapa, editable=True) 
                self.px_mapa.setSourceModel(self.model_mapa)
                self.v_mapa.setModel(self.px_mapa)
                s = self.service_learn.calcular_auditoria_ecosistema(datos_mapa)
            except Exception as e: print(f"Error Auditoría: {e}")

        # Cálculos de espacio en caliente
        peso_sipa_total = self._obtener_peso_carpeta(self.base_dir)
        peso_data = self._obtener_peso_carpeta(os.path.join(self.base_dir, "data"))
        peso_sistema_puro = max(0, peso_sipa_total - peso_data)
        porcentaje_gasto_sipa = round((peso_sistema_puro / peso_sipa_total) * 100, 2) if peso_sipa_total > 0 else 0.0

        # Mapeo sobre la caché de configuración
        for metrica in self.cache_metricas:
            if metrica["id"] == "MET-001": metrica["actual"] = f"{s['porcentaje_control']}%"
            elif metrica["id"] == "MET-002": metrica["actual"] = f"{s['porcentaje_inbox_sipa']}%"
            elif metrica["id"] == "MET-003": metrica["actual"] = f"{s['actividad_semanal']} mods"
            elif metrica["id"] == "MET-004": metrica["actual"] = f"{porcentaje_gasto_sipa}%"

        # Cargar datos core estándar
        datos_inbox = self.service.obtener_datos_inbox() if self.service else []
        self.model_inbox = GenericModel(datos_inbox, self.columnas_full)
        self.px_inbox.setSourceModel(self.model_inbox)
        self.v_inbox.setModel(self.px_inbox)
        
        datos_seg = self.service.sincronizar_ubicaciones_reales() if self.service else []
        self.model_seg = GenericModel(datos_seg, self.columnas_full, editable=True, servicio=self.service)
        self.px_seg.setSourceModel(self.model_seg)
        self.v_seg.setModel(self.px_seg)

        # Enlace del modelo a la tabla de métricas
        self.model_metricas = GenericModel(self.cache_metricas, self.cols_metricas, editable=True)
        self.model_metricas.guardar_callback = self._guardar_metricas_a_disco
        self.px_metricas.setSourceModel(self.model_metricas)
        self.v_metricas.setModel(self.px_metricas)
        
        self.v_metricas.setItemDelegateForColumn(6, ComboDelegate(["✅ VERIFICADO", "❌ PENDIENTE"], self))
        self.v_metricas.resizeColumnsToContents()

        # --- DISEÑO VISUAL ORIGINAL RESTAURADO AL 100% ---
        html = f"""
        <div style='font-family: "Segoe UI", sans-serif; font-size: 11px; color: #2c3e50;'>
            <div style='text-align: center; padding: 10px; background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; margin-bottom: 10px;'>
                <span style='font-size: 10px; color: #7f8c8d; letter-spacing: 1px; font-weight: bold;'>CONTROL DEL ECOSISTEMA</span><br>
                <span style='font-size: 26px; font-weight: bold; color: #2980b9;'>{s['porcentaje_control']}%</span>
            </div>
            <div style='margin-bottom: 8px;'>
                <b style='color: #2980b9; font-size: 11px;'>📊 GESTIÓN DE ACTIVOS</b><br>
                <table style='width: 100%; margin-top: 2px;'>
                    <tr><td>• Total Detectados:</td><td style='text-align: right;'><b>{s['recuento_global']}</b></td></tr>
                    <tr><td>• En Seguimiento:</td><td style='text-align: right;'><b>{s['recuento_sipa']}</b> ({s['porcentaje_control']}%)</td></tr>
                    <tr><td>• Pendientes:</td><td style='text-align: right; color: #e67e22;'><b>{s['recuento_pendiente']}</b></td></tr>
                </table>
            </div>
            <hr style='border: 0; border-top: 1px solid #eee; margin: 6px 0;'>
            <div style='margin-bottom: 8px;'>
                <b style='color: #8e44ad; font-size: 11px;'>🔥 MAPA DE CALOR (Volumen | Esfuerzo 7d)</b><br>
                <table style='width: 100%; margin-top: 2px; font-size: 10px;'>
        """
        for area, val in s['mapa_calor'].items():
            color_esfuerzo = "#2ecc71" if val[1] > 0 else "#bdc3c7"
            html += f"<tr><td>• {area.capitalize()}:</td><td style='text-align: right;'><b>{val[0]}</b> | <span style='color: {color_esfuerzo};'>{val[1]} mod.</span></td></tr>"

        html += f"""
                </table>
            </div>
            <hr style='border: 0; border-top: 1px solid #eee; margin: 6px 0;'>
            <div style='margin-bottom: 8px;'>
                <b style='color: #c0392b; font-size: 11px;'>⚠️ CARGA INTERNA (INBOX)</b><br>
                <table style='width: 100%; margin-top: 2px;'>
                    <tr><td>• Ficheros en Inbox:</td><td style='text-align: right;'><b>{s['inbox_cantidad']}</b></td></tr>
                    <tr><td>• Estrés sobre SIPA:</td><td style='text-align: right; color: #c0392b;'><b>{s['porcentaje_inbox_sipa']}%</b></td></tr>
                </table>
            </div>
            <hr style='border: 0; border-top: 1px solid #eee; margin: 6px 0;'>
            <div>
                <b style='color: #27ae60; font-size: 11px;'>🔍 SALUD Y MANTENIMIENTO</b><br>
                <table style='width: 100%; margin-top: 2px;'>
                    <tr><td>• Peso Digital:</td><td style='text-align: right;'><b>{s['peso_total_mb']} MB</b></td></tr>
                    <tr><td>• Ruido (Fantasmas):</td><td style='text-align: right; color: {"#e67e22" if s["salud_fantasmas"] > 0 else "#27ae60"};'><b>{s['salud_fantasmas']}</b></td></tr>
                    <tr><td>• Actividad (7d):</td><td style='text-align: right;'><b>{s['actividad_semanal']} mods.</b></td></tr>
                </table>
            </div>
        </div>
        """
        self.txt_evolucion.setHtml(html)

        if self.service_learn:
            info = self.service_learn.get_ai_status()
            self.lbl_status_ia.setText(f"● {info['engine']}: {info['status']} | UP: {info['uptime']}")
            self.lbl_status_ia.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 11px;")

    def aplicar_filtro_mapa(self, texto):
        self.search_bar.clear()
        self.px_mapa.setFilterKeyColumn(4)
        self.px_mapa.setFilterFixedString(texto)

    def filtrar(self, t):
        for px in [self.px_inbox, self.px_seg, self.px_metricas]:
            px.setFilterKeyColumn(-1)
            px.setFilterFixedString(t)
        self.px_mapa.setFilterKeyColumn(-1)
        self.px_mapa.setFilterFixedString(t)

    def abrir_fichero(self, index):
        try:
            source_idx = index.model().mapToSource(index) if isinstance(index.model(), QSortFilterProxyModel) else index
            row = source_idx.row()
            col_path_idx = self.columnas_full.index("path_actual") + 1
            ruta = source_idx.model().index(row, col_path_idx).data()
            if ruta and os.path.exists(ruta):
                if sys.platform == "win32": os.startfile(ruta)
                else: subprocess.Popen(["xdg-open", ruta])
        except Exception as e: print(f"Error: {e}")

    def abrir_fichero_mapa(self, index):
        try:
            ruta = index.model().index(index.row(), 7).data()
            if ruta and os.path.exists(ruta):
                subprocess.Popen(["xdg-open", ruta])
        except Exception as e: print(f"Error Mapa: {e}")

    def lanzar_etiquetado(self):
        rutas = list(self.model_inbox.seleccionados)
        if not rutas: return
        self.btn_label.setText("⌛ PROCESANDO...")
        try:
            self.service.procesar_lote(rutas)
            self.actualizar_todo()
        except: pass
        self.btn_label.setText("🏷️ ETIQUETAR")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SIPAcurDashboard()
    win.show()
    sys.exit(app.exec())