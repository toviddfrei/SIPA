# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: sipacur.py (BLINDAJE DE PARSEO DE FECHAS)
# Módulo: SIPAcur (Dashboard IA Personal)
# Versión: 4.5.3 | Fecha: 21/05/2026
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
from PySide6.QtGui import QColor

# --- INTEGRACIÓN DEL SERVICIO CORE ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'core/services'))
try:
    from scsipacur_process_file import SIPAcurProcessorService
    from scsipacur_learn_file import SIPA_Learn_Service
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
    def __init__(self, dataset, columnas, tipo_tabla="activos", editable=False, servicio=None):
        super().__init__()
        self._data = dataset
        self.columnas = columnas
        self.tipo_tabla = tipo_tabla  # "activos", "mapa" o "metricas"
        self.seleccionados = set()
        self.editable = editable
        self.servicio = servicio

    def rowCount(self, p=None): return len(self._data)
    def columnCount(self, p=None): return len(self.columnas) + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)): return None
        row_data = self._data[index.row()]
        
        # Columna 0: Selección Checkbox unificada para operar lotes
        if index.column() == 0:
            if role == Qt.CheckStateRole:
                path = row_data.get('path_actual')
                if path: return Qt.CheckState.Checked if path in self.seleccionados else Qt.CheckState.Unchecked
            return None
            
        if role in (Qt.DisplayRole, Qt.EditRole):
            col_key = self.columnas[index.column() - 1]
            
            if col_key == "tendencia":
                t_info = row_data.get("tendencia_calculada", {"simbolo": "▬", "txt": "est."})
                return f"{t_info['simbolo']} {t_info['txt']}"
            
            # --- TRADUCTOR TOLERANTE DE CLAVES INTERNAS ---
            val = " "
            if col_key == "observaciones":
                val = row_data.get("observaciones", row_data.get("anotacion", " "))
            elif col_key == "extensión":
                val = row_data.get("extensión", row_data.get("extension", ".md"))
            else:
                val = row_data.get(col_key, " ")
                
            if isinstance(val, bool) and col_key in ["verificado", "pendiente", "revisado", "procesado", "registrado"]:
                return "✅ SÍ" if val else "❌ NO"
            return str(val)
        
        # --- COLOR REACTIVO EXCLUSIVO Y SEGURO ---
        if role == Qt.ForegroundRole:
            col_key = self.columnas[index.column() - 1]
            
            # Enlace visual para Inbox y Seguimiento
            if self.tipo_tabla == "activos" and col_key == "nombre_fichero_original":
                return QColor("#2196F3")
                
            # Enlace visual para Tabla Mapa
            if self.tipo_tabla == "mapa" and col_key == "nombre":
                return QColor("#2196F3")

            # Resaltado verde en MAPA para estado y fecha de control
            if self.tipo_tabla == "mapa" and str(row_data.get("estado")).strip() == "Seguimiento":
                if col_key in ["estado", "fecha_entrada", "fecha_ingresado"]:
                    return QColor("#27ae60")

            if col_key == "tendencia":
                t_info = row_data.get("tendencia_calculada", {"estado": "STABLE"})
                if t_info["estado"] == "UP": return QColor("#2ecc71")
                if t_info["estado"] == "DOWN": return QColor("#e74c3c")
                return QColor("#7f8c8d")

        # ALINEACIÓN INTELIGENTE QUIRÚRGICA
        if role == Qt.TextAlignmentRole:
            col_key = self.columnas[index.column() - 1]
            if self.tipo_tabla in ["activos", "mapa"] and col_key in ["nombre_fichero_original", "nombre", "path_actual", "observaciones", "frase", "path_publicado", "enlace"]:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignCenter
            
        return None

    def setData(self, index, value, role):
        if index.column() == 0 and role == Qt.CheckStateRole:
            path = self._data[index.row()].get('path_actual')
            if path:
                if value == Qt.CheckState.Checked.value: self.seleccionados.add(path)
                else: self.seleccionados.discard(path)
                self.dataChanged.emit(index, index); return True
        
        if self.editable and role == Qt.EditRole:
            col_key = self.columnas[index.column() - 1]
            
            if col_key == "observaciones":
                self._data[index.row()]["observaciones"] = value
                self._data[index.row()]["anotacion"] = value
            else:
                self._data[index.row()][col_key] = value
            
            if self.servicio and hasattr(self.servicio, 'actualizar_item_completo'):
                self.servicio.actualizar_item_completo(self._data[index.row()])
            elif hasattr(self, 'guardar_callback') and self.guardar_callback:
                self.guardar_callback()
                
            self.dataChanged.emit(index, index); return True
        return False

    def flags(self, index):
        fl = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0: 
            if self._data and self._data[0].get('path_actual'): return fl | Qt.ItemIsUserCheckable
            return fl
        if self.editable:
            col_actual = self.columnas[index.column()-1]
            if col_actual in ["tipo", "estado", "observaciones", "palabras", "frase", "sipacur_sugerencia"]:
                return fl | Qt.ItemIsEditable
        return fl

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return "SEL" if section == 0 else self.columnas[section-1].replace("_", " ").upper()
        return None

# ==========================================================
# DASHBOARD PRINCIPAL
# ==========================================================

class SIPAcurDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SIPAcur v4.5.3 - Ecosistema Profesional")
        self.resize(1200, 800)
        
        self.service = SIPAcurProcessorService() if SIPAcurProcessorService else None
        self.service_learn = SIPA_Learn_Service() if SIPA_Learn_Service else None
        
        self.cols_prioritarias = [
            "id_interno", "nombre_fichero_original", "tipo", "estado", "path_actual",
            "pendiente", "revisado", "procesado", "registrado", "unidad", "hash", 
            "observaciones", "total_palabras", "palabras", "frase", "path_publicado", 
            "fecha_creación", "fecha_entrada", "fecha_publicación", "tamaño_kb", 
            "extensión", "enlace", "sipacur_sugerencia"
        ]
        
        self.cols_mapa = ["id_interno", "nombre", "fecha_entrada", "estado", 
                          "observaciones", "path_actual", "tamaño_kb", "ultima_modificacion", "extensión"]
                  
        self.cols_metricas = ["tendencia", "id", "nombre", "actual", "anterior", "anotaciones", "verificado"]
        
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
        self.btn_ingresar.clicked.connect(self.lanzar_ingreso)
        
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

        self.btn_label.clicked.connect(self.lanzar_etiquetado)
        self.search_bar.textChanged.connect(self.filtrar)
        
        self.btn_f_seg.clicked.connect(lambda: self.aplicar_filtro_mapa("Seguimiento"))
        self.btn_f_pen.clicked.connect(lambda: self.aplicar_filtro_mapa("Pendiente"))
        self.btn_f_all.clicked.connect(lambda: self.aplicar_filtro_mapa(""))

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
        lyt_logo.addWidget(QLabel("<b>SIPAcur v4.5.3</b><br>Identificación Personal Autorizada", alignment=Qt.AlignCenter))
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
        
        self.txt_evolucion = QTextEdit()
        self.txt_evolucion.setReadOnly(True)
        self.txt_evolucion.setMinimumHeight(220)
        self.txt_evolucion.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; padding: 10px;")
        self.lyt_stats.addWidget(self.txt_evolucion)
        lyt_grid.addWidget(self.frame_stats, 1, 1)

        self.tabs.addTab(self.tab_presentacion, "🏠 INICIO")

        # 2. PESTAÑA TABLA DE MÉTRICAS PEDAGÓGICAS
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
        self.v_mapa.doubleClicked.connect(self.abrir_fichero_default)
        self.tabs.addTab(self.v_mapa, "🗺️ MAPA")
        self.px_mapa.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # 4. PESTAÑA INBOX
        self.v_inbox = QTableView()
        self.px_inbox = QSortFilterProxyModel()
        self.v_inbox.setSortingEnabled(True)
        self.v_inbox.setAlternatingRowColors(True)
        self.v_inbox.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.v_inbox.doubleClicked.connect(self.abrir_fichero_default)
        self.tabs.addTab(self.v_inbox, "📥 INBOX")

        # 5. PESTAÑA SEGUIMIENTO
        self.v_seg = QTableView()
        self.px_seg = QSortFilterProxyModel()
        self.v_seg.setSortingEnabled(True)
        self.v_seg.setAlternatingRowColors(True)
        self.v_seg.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.v_seg.doubleClicked.connect(self.abrir_fichero_default)
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
                {"id": "MET-001", "nombre": "Control del Ecosistema", "anterior": "30.43%", "anotaciones": "Porcentaje de archivos bajo control estricto del radar SIPA.", "verificado": True},
                {"id": "MET-002", "nombre": "Total Detectados", "anterior": "966", "anotaciones": "Recuento bruto de ficheros escaneados in environment.", "verificado": True},
                {"id": "MET-003", "nombre": "En Seguimiento", "anterior": "294", "anotaciones": "Archivos indexados activos.", "verificado": True},
                {"id": "MET-004", "nombre": "Pendientes", "anterior": "672", "anotaciones": "Archivos fuera del radar pendientes de clasificar.", "verificado": False},
                {"id": "MET-H01", "nombre": "Mapa Calor: Económica", "anterior": "5 | 0 mod.", "anotaciones": "Volumen / Esfuerzo área Económica", "verificado": False},
                {"id": "MET-H02", "nombre": "Mapa Calor: Educación", "anterior": "12 | 2 mod.", "anotaciones": "Volumen / Esfuerzo área Educación", "verificado": False},
                {"id": "MET-H03", "nombre": "Mapa Calor: Justicia", "anterior": "0 | 0 mod.", "anotaciones": "Volumen / Esfuerzo área Justicia", "verificado": False},
                {"id": "MET-H04", "nombre": "Mapa Calor: Social", "anterior": "0 | 0 mod.", "anotaciones": "Volumen / Esfuerzo área Social", "verificado": False},
                {"id": "MET-H05", "nombre": "Mapa Calor: Constructor", "anterior": "157 | 2 mod.", "anotaciones": "Volumen / Esfuerzo área Constructor", "verificado": False},
                {"id": "MET-H06", "nombre": "Mapa Calor: Posts", "anterior": "42 | 0 mod.", "anotaciones": "Volumen / Esfuerzo área Posts", "verificado": False},
                {"id": "MET-IN01", "nombre": "Ficheros en Inbox", "anterior": "17", "anotaciones": "Cola de entrada esperando etiquetado manual o automático.", "verificado": True},
                {"id": "MET-IN02", "nombre": "Estrés sobre SIPA (Inbox)", "anterior": "5.78%", "anotaciones": "Impacto porcentual acumulado de la bandeja de entrada.", "verificado": True},
                {"id": "MET-ST01", "nombre": "Peso Digital", "anterior": "8.31 MB", "anotaciones": "Espacio ocupado por el repositorio analizado.", "verificado": True},
                {"id": "MET-ST02", "nombre": "Ruido (Fantasmas)", "anterior": "25", "anotaciones": "Referencias corruptas o archivos rotos detectados.", "verificado": False},
                {"id": "MET-ST03", "nombre": "Actividad (7d)", "anterior": "32 mods.", "anotaciones": "Volumen total de escrituras registradas en la última semana.", "verificado": False},
                {"id": "MET-ST04", "nombre": "Gasto Estructural SIPA", "anterior": "0.0%", "anotaciones": "Peso puro consumido por la estructura del software.", "verificado": False}
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
                guardable = []
                for m in self.cache_metricas:
                    copia = m.copy()
                    copia.pop("tendencia_calculada", None)
                    guardable.append(copia)
                json.dump(guardable, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"⚠️ Error persisting métricas en disco: {e}")

    def actualizar_todo(self):
        if not self.service: return
        
        s = {"porcentaje_control": 0, "recuento_global": 0, "recuento_sipa": 0, 
             "recuento_pendiente": 0, "inbox_cantidad": 0, "porcentaje_inbox_sipa": 0,
             "peso_total_mb": 1.0, "salud_fantasmas": 0, "actividad_semanal": 0, "mapa_calor": {}}

        if self.service_learn:
            try:
                datos_mapa = self.service_learn.escanear_entorno()
                
                # --- ESCUDO INTERCEPTOR DE FORMATO DE FECHAS (ANTI-CRASH) ---
                for item in datos_mapa:
                    # 1. Forzar presencia de claves críticas
                    if "fecha_entrada" not in item or str(item.get("fecha_entrada")).strip() in ["", "None", "N/A"]:
                        item["fecha_entrada"] = "01/01/1990"
                    
                    if "ultima_modificacion" not in item or str(item.get("ultima_modificacion")).strip() in ["", "None", "N/A"]:
                        item["ultima_modificacion"] = item["fecha_entrada"]
                    
                    # 2. Corregir formato si el core exige barra y viene con guiones
                    if "-" in str(item["fecha_entrada"]):
                        try:
                            partes = item["fecha_entrada"].split(" ")[0].split("-")
                            if len(partes) == 3:
                                if len(partes[0]) == 4: # YYYY-MM-DD
                                    item["fecha_entrada"] = f"{partes[2]}/{partes[1]}/{partes[0]}"
                                else: # DD-MM-YYYY
                                    item["fecha_entrada"] = f"{partes[0]}/{partes[1]}/{partes[2]}"
                        except:
                            item["fecha_entrada"] = "01/01/1990"
                            
                    if "-" in str(item["ultima_modificacion"]):
                        try:
                            partes = item["ultima_modificacion"].split(" ")[0].split("-")
                            if len(partes) == 3:
                                if len(partes[0]) == 4:
                                    item["ultima_modificacion"] = f"{partes[2]}/{partes[1]}/{partes[0]}"
                                else:
                                    item["ultima_modificacion"] = f"{partes[0]}/{partes[1]}/{partes[2]}"
                        except:
                            item["ultima_modificacion"] = item["fecha_entrada"]

                self.model_mapa = GenericModel(datos_mapa, self.cols_mapa, tipo_tabla="mapa", editable=True) 
                self.px_mapa.setSourceModel(self.model_mapa)
                self.v_mapa.setModel(self.px_mapa)
                
                # Ejecución protegida
                s = self.service_learn.calcular_auditoria_ecosistema(datos_mapa)
            except Exception as e: 
                print(f"Error Auditoría: {e}")

        peso_sipa_total = self._obtener_peso_carpeta(self.base_dir)
        peso_data = self._obtener_peso_carpeta(os.path.join(self.base_dir, "data"))
        peso_sistema_puro = max(0, peso_sipa_total - peso_data)
        porcentaje_gasto_sipa = round((peso_sistema_puro / peso_sipa_total) * 100, 2) if peso_sipa_total > 0 else 0.0

        # --- EXTRACTOR DE MAPA DE CALOR INSENSIBLE ---
        mc = s.get('mapa_calor', {}) if s else {}
        def normalizar_cadena(txt):
            import unicodedata
            return "".join(c for c in unicodedata.normalize('NFD', txt.lower()) if unicodedata.category(c) != 'Mn')
        
        mc_limpio = {normalizar_cadena(k): v for k, v in mc.items()}

        for metrica in self.cache_metricas:
            if not s: break
            if metrica["id"] == "MET-001": metrica["actual"] = f"{s.get('porcentaje_control', 0)}%"
            elif metrica["id"] == "MET-002": metrica["actual"] = str(s.get('recuento_global', 0))
            elif metrica["id"] == "MET-003": metrica["actual"] = f"{s.get('recuento_sipa', 0)} ({s.get('porcentaje_control', 0)}%)"
            elif metrica["id"] == "MET-004": metrica["actual"] = str(s.get('recuento_pendiente', 0))
            elif metrica["id"] == "MET-H01":
                v = mc_limpio.get('economica', mc.get('economica', [0, 0])); metrica["actual"] = f"{v[0]} | {v[1]} mod."
            elif metrica["id"] == "MET-H02":
                v = mc_limpio.get('educacion', mc.get('educacion', [0, 0])); metrica["actual"] = f"{v[0]} | {v[1]} mod."
            elif metrica["id"] == "MET-H03":
                v = mc_limpio.get('justicia', mc.get('justicia', [0, 0])); metrica["actual"] = f"{v[0]} | {v[1]} mod."
            elif metrica["id"] == "MET-H04":
                v = mc_limpio.get('social', mc.get('social', [0, 0])); metrica["actual"] = f"{v[0]} | {v[1]} mod."
            elif metrica["id"] == "MET-H05":
                v = mc_limpio.get('constructor', mc.get('constructor', [0, 0])); metrica["actual"] = f"{v[0]} | {v[1]} mod."
            elif metrica["id"] == "MET-H06":
                v = mc_limpio.get('posts', mc.get('posts', [0, 0])); metrica["actual"] = f"{v[0]} | {v[1]} mod."
            elif metrica["id"] == "MET-IN01": metrica["actual"] = str(s.get('inbox_cantidad', 0))
            elif metrica["id"] == "MET-IN02": metrica["actual"] = f"{s.get('porcentaje_inbox_sipa', 0)}%"
            elif metrica["id"] == "MET-ST01": metrica["actual"] = f"{s.get('peso_total_mb', 1.0)} MB"
            elif metrica["id"] == "MET-ST02": metrica["actual"] = str(s.get('salud_fantasmas', 0))
            elif metrica["id"] == "MET-ST03": metrica["actual"] = f"{s.get('actividad_semanal', 0)} mods."
            elif metrica["id"] == "MET-ST04": metrica["actual"] = f"{porcentaje_gasto_sipa}%"

            if self.service_learn:
                metrica["tendencia_calculada"] = self.service_learn.calcular_flechas_tendencia(
                    metrica["actual"], metrica.get("anterior", metrica["actual"])
                )
            else:
                metrica["tendencia_calculada"] = {"simbolo": "▬", "txt": "est.", "estado": "STABLE"}

        datos_inbox = self.service.obtener_datos_inbox() if self.service else []
        self.model_inbox = GenericModel(datos_inbox, self.cols_prioritarias, tipo_tabla="activos")
        self.px_inbox.setSourceModel(self.model_inbox)
        self.v_inbox.setModel(self.px_inbox)
        
        datos_seg = self.service.sincronizar_ubicaciones_reales() if self.service else []
        self.model_seg = GenericModel(datos_seg, self.cols_prioritarias, tipo_tabla="activos", editable=True, servicio=self.service)
        self.px_seg.setSourceModel(self.model_seg)
        self.v_seg.setModel(self.px_seg)

        self.v_seg.setItemDelegateForColumn(3, ComboDelegate(["Nota", "Acta", "Bitácora", "Tprofesional", "Tformatival", "Posts", "Bloque"], self))
        self.v_seg.setItemDelegateForColumn(4, ComboDelegate(["Pendiente", "Abierto", "Cerrado", "Publicado"], self))

        self.model_metricas = GenericModel(self.cache_metricas, self.cols_metricas, tipo_tabla="metricas", editable=True)
        self.model_metricas.guardar_callback = self._guardar_metricas_a_disco
        self.px_metricas.setSourceModel(self.model_metricas)
        self.v_metricas.setModel(self.px_metricas)
        self.v_metricas.setItemDelegateForColumn(7, ComboDelegate(["✅ VERIFICADO", "❌ PENDIENTE"], self))
        
        for tabla in [self.v_mapa, self.v_inbox, self.v_seg, self.v_metricas]:
            tabla.resizeColumnsToContents()

        # HTML renderizado
        html = f"""
        <div style='font-family: "Segoe UI", sans-serif; font-size: 11px; color: #2c3e50;'>
            <div style='text-align: center; padding: 10px; background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; margin-bottom: 10px;'>
                <span style='font-size: 10px; color: #7f8c8d; letter-spacing: 1px; font-weight: bold;'>CONTROL DEL ECOSISTEMA</span><br>
                <span style='font-size: 26px; font-weight: bold; color: #2980b9;'>{s.get('porcentaje_control', 0)}%</span>
            </div>
            <div style='margin-bottom: 8px;'>
                <b style='color: #2980b9; font-size: 11px;'>📊 GESTIÓN DE ACTIVOS</b><br>
                <table style='width: 100%; margin-top: 2px;'>
                    <tr><td>• Total Detectados:</td><td style='text-align: right;'><b>{s.get('recuento_global', 0)}</b></td></tr>
                    <tr><td>• En Seguimiento:</td><td style='text-align: right;'><b>{s.get('recuento_sipa', 0)}</b> ({s.get('porcentaje_control', 0)}%)</td></tr>
                    <tr><td>• Pendientes:</td><td style='text-align: right; color: #e67e22;'><b>{s.get('recuento_pendiente', 0)}</b></td></tr>
                </table>
            </div>
            <hr style='border: 0; border-top: 1px solid #eee; margin: 6px 0;'>
            <div style='margin-bottom: 8px;'>
                <b style='color: #8e44ad; font-size: 11px;'>🔥 MAPA DE CALOR (Volumen | Esfuerzo 7d)</b><br>
                <table style='width: 100%; margin-top: 2px; font-size: 10px;'>
        """
        for area, val in s.get('mapa_calor', {}).items():
            color_esfuerzo = "#2ecc71" if val[1] > 0 else "#bdc3c7"
            html += f"<tr><td>• {area.capitalize()}:</td><td style='text-align: right;'><b>{val[0]}</b> | <span style='color: {color_esfuerzo};'>{val[1]} mod.</span></td></tr>"

        html += f"""
                </table>
            </div>
            <hr style='border: 0; border-top: 1px solid #eee; margin: 6px 0;'>
            <div style='margin-bottom: 8px;'>
                <b style='color: #c0392b; font-size: 11px;'>⚠️ CARGA INTERNA (INBOX)</b><br>
                <table style='width: 100%; margin-top: 2px;'>
                    <tr><td>• Ficheros en Inbox:</td><td style='text-align: right;'><b>{s.get('inbox_cantidad', 0)}</b></td></tr>
                    <tr><td>• Estrés sobre SIPA:</td><td style='text-align: right; color: #c0392b;'><b>{s.get('porcentaje_inbox_sipa', 0)}%</b></td></tr>
                </table>
            </div>
            <hr style='border: 0; border-top: 1px solid #eee; margin: 6px 0;'>
            <div>
                <b style='color: #27ae60; font-size: 11px;'>🔍 SALUD Y MANTENIMIENTO</b><br>
                <table style='width: 100%; margin-top: 2px;'>
                    <tr><td>• Peso Digital:</td><td style='text-align: right;'><b>{s.get('peso_total_mb', 1.0)} MB</b></td></tr>
                    <tr><td>• Ruido (Fantasmas):</td><td style='text-align: right; color: {"#e67e22" if s.get("salud_fantasmas", 0) > 0 else "#27ae60"};'><b>{s.get('salud_fantasmas', 0)}</b></td></tr>
                    <tr><td>• Actividad (7d):</td><td style='text-align: right;'><b>{s.get('actividad_semanal', 0)} mods.</b></td></tr>
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
        for px in [self.px_inbox, self.px_seg, self.px_metricas, self.px_mapa]:
            px.setFilterKeyColumn(-1)
            px.setFilterFixedString(t)

    def abrir_fichero_default(self, index):
        try:
            if not index.isValid() or index.column() != 2: 
                return

            proxy_model = index.model()
            if isinstance(proxy_model, QSortFilterProxyModel):
                source_idx = proxy_model.mapToSource(index)
                source_model = proxy_model.sourceModel()
            else:
                source_idx = index
                source_model = proxy_model

            row = source_idx.row()
            item_data = source_model._data[row]
            ruta_nota = item_data.get("path_actual")
            
            if ruta_nota and os.path.exists(ruta_nota):
                print(f"🚀 [SIPA SYSTEM] Abriendo activo por defecto: {ruta_nota}")
                if sys.platform == "win32": 
                    os.startfile(ruta_nota)
                else: 
                    subprocess.Popen(["xdg-open", ruta_nota])
            else:
                QMessageBox.warning(self, "Error de Ubicación", f"El archivo físico no reside en esa ruta:\n{ruta_nota}")
        except Exception as e: 
            print(f"Error crítico en evento abrir_fichero_default: {e}")

    def lanzar_ingreso(self):
        if self.tabs.currentIndex() != 2:
            QMessageBox.warning(self, "Acción bloqueada", "El botón INGRESAR solo es operativo dentro de la pestaña 🗺️ MAPA.")
            return

        if not hasattr(self, 'model_mapa') or not self.model_mapa: return
        rutas = list(self.model_mapa.seleccionados)
        if not rutas:
            QMessageBox.information(self, "Selección vacía", "Por favor, marca la casilla 'SEL' de los archivos que deseas ingresar.")
            return
            
        self.btn_ingresar.setText("📥 INGRESANDO...")
        self.btn_ingresar.setEnabled(False)
        QApplication.processEvents()
        
        try:
            if self.service_learn:
                resultado = self.service_learn.ingresar_activos_a_inbox(rutas)
                self.model_mapa.seleccionados.clear()
                self.actualizar_todo()
                
                msg = f"Resumen del proceso de ingreso:\n\n"
                msg += f"• Archivos ingresados con éxito: {resultado['procesados']}\n"
                msg += f"• Errores de lectura/permisos: {resultado['errores']}\n"
                
                if resultado["duplicados_omitidos"]:
                    msg += f"\n⚠️ ALERTA DE DUPLICADOS:\n"
                    for dup in resultado["duplicados_omitidos"]: msg += f"  - {dup}\n"
                    msg += "\nNo se ha modificado ningún archivo existente para preservar la integridad de los datos."
                QMessageBox.information(self, "Auditoría de Ingreso", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo crítico en el proceso de ingreso: {e}")
        finally:
            self.btn_ingresar.setText("📥 INGRESAR")
            self.btn_ingresar.setEnabled(True)

    def lanzar_etiquetado(self):
        if self.tabs.currentIndex() != 3:
            QMessageBox.warning(self, "Acción bloqueada", "El botón ETIQUETAR solo es operativo dentro de la pestaña 📥 INBOX.")
            return

        if not hasattr(self, 'model_inbox') or not self.model_inbox: return
        rutas = list(self.model_inbox.seleccionados)
        if not rutas:
            QMessageBox.information(self, "Selección vacía", "Selecciona los archivos del Inbox que deseas etiquetar o re-etiquetar.")
            return
            
        self.btn_label.setText("⌛ PROCESANDO...")
        self.btn_label.setEnabled(False)
        QApplication.processEvents()
        
        try:
            if self.service:
                self.service.procesar_lote(rutas)
                self.model_inbox.seleccionados.clear()
                self.actualizar_todo()
                QMessageBox.information(self, "Éxito", "Proceso de etiquetado/re-etiquetado completado en Inbox.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar lote en Inbox: {e}")
        finally:
            self.btn_label.setText("🏷️ ETIQUETAR")
            self.btn_label.setEnabled(True)

    def obtener_rutas_seleccionadas_actuales(self):
        idx_pestaña = self.tabs.currentIndex()
        if idx_pestaña == 2 and hasattr(self, 'model_mapa') and self.model_mapa:
            return self.model_mapa, list(self.model_mapa.seleccionados)
        elif idx_pestaña == 3 and hasattr(self, 'model_inbox') and self.model_inbox:
            return self.model_inbox, list(self.model_inbox.seleccionados)
        elif idx_pestaña == 4 and hasattr(self, 'model_seg') and self.model_seg:
            return self.model_seg, list(self.model_seg.seleccionados)
        return None, []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SIPAcurDashboard()
    win.show()
    sys.exit(app.exec())