import sys
import os
import requests
import frontmatter
import pandas as pd
import re
import webbrowser
import warnings
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTextEdit, QLabel, QFrame, QProgressBar, QTabWidget,
                             QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, 
                             QHeaderView, QLineEdit, QFormLayout, QComboBox, QGridLayout,
                             QAbstractItemView)
from PySide6.QtCore import Qt, QThread, Signal

# --- BLOQUEO DE LOGS INNECESARIOS ---
warnings.filterwarnings("ignore")
logging.getLogger("duckduckgo_search").setLevel(logging.ERROR)
sys.stderr = open(os.devnull, 'w')

# --- CONFIGURACIÓN DE RUTAS ---
ROOT_SIPA = "/home/toviddfrei/SIPA"
FICHERO_CONFIG = os.path.join(ROOT_SIPA, "data/archive/template_propietario.md")
ARCHIVO_HISTORICO = os.path.join(ROOT_SIPA, "data/archive/historico_rastreo.csv")
ARCHIVO_PATRONES = os.path.join(ROOT_SIPA, "data/archive/patrones_busqueda.json")

class SIPAIdentStyle:
    """Paleta de colores oficial SIPA - Anti-Flicker Edition"""
    MAIN_BG = "#121212"
    CARD_BG = "#0D0D0D"
    ACCENT_BLUE = "#3A86FF"
    ACCENT_GREEN = "#00FF95"
    ACCENT_RED = "#E63946"
    TEXT_PRIMARY = "#E0E0E0"
    TEXT_DIM = "#888888"
    CONSOLE_BG = "#050505"

    SHEET = f"""
    QMainWindow {{ background-color: {MAIN_BG}; }}
    QWidget {{ font-size: 11px; color: {TEXT_PRIMARY}; background-color: transparent; }}
    QTabWidget::panel {{ border: 1px solid #2D2D2D; background-color: {CARD_BG}; top: -1px; border-radius: 4px; }}
    QTabBar::tab {{ background: #1A1A1A; color: {TEXT_DIM}; padding: 10px 20px; border: 1px solid #2D2D2D; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }}
    QTabBar::tab:selected {{ background: {CARD_BG}; color: {ACCENT_GREEN}; border-bottom: 2px solid {ACCENT_GREEN}; font-weight: bold; }}
    QTableWidget {{ background-color: #050505; gridline-color: #222; border: none; selection-background-color: #1A1A1A; }}
    QHeaderView::section {{ background-color: #151515; color: {ACCENT_GREEN}; padding: 8px; border: 1px solid #2D2D2D; font-weight: bold; }}
    QTextEdit, QLineEdit {{ background-color: #020202; color: {ACCENT_GREEN}; font-family: 'Consolas', monospace; border: 1px solid #333; padding: 6px; border-radius: 4px; }}
    QLineEdit:focus {{ border: 1px solid {ACCENT_GREEN}; }}
    QComboBox {{ background-color: #111111; color: {ACCENT_GREEN}; border: 1px solid #333; padding: 4px 10px; }}
    QFrame#MotorCard {{ background-color: #080808; border: 1px solid #222; border-radius: 6px; }}
    QPushButton {{ background-color: #222; color: {TEXT_PRIMARY}; border: none; padding: 8px 15px; border-radius: 4px; font-weight: bold; }}
    QPushButton:hover {{ background-color: {ACCENT_BLUE}; }}
    QPushButton#LaunchBtn {{ background-color: {ACCENT_GREEN}; color: #000; }}
    QPushButton#UrlBtn {{ background-color: #050505; color: {ACCENT_BLUE}; border: 1px solid {ACCENT_BLUE}; font-size: 9px; }}
    QProgressBar {{ background-color: #050505; border: 1px solid #222; height: 4px; text-align: center; border-radius: 2px; }}
    QProgressBar::chunk {{ background-color: {ACCENT_GREEN}; }}
    """

class ProspeccionWorker(QThread):
    update_log = Signal(str)
    progress = Signal(int)
    finished_data = Signal(list)

    def __init__(self, config, patrones):
        super().__init__()
        self.config = config
        self.patrones = [p for p in patrones if p.strip()]

    def run(self):
        hallazgos = []
        total_pasos = len(self.patrones) + 2 # +1 BOE +1 Dorks
        paso_actual = 0

        try:
            # 1. MOTOR DORKS (Google Inteligencia)
            self.update_log.emit(f"🚀 Generando Dorks Forenses para {self.config.get('nombre', 'Usuario')}...")
            hallazgos.extend(self.motor_google_dorks())
            paso_actual += 1
            self.progress.emit(int((paso_actual / total_pasos) * 100))

            # 2. MOTOR BOE INICIAL (DNI)
            self.update_log.emit(f"⚖️ Iniciando Trazado BOE para: {self.config.get('dni', 'N/A')}")
            hallazgos.extend(self.motor_boe(self.config.get('dni', '')))
            paso_actual += 1
            self.progress.emit(int((paso_actual / total_pasos) * 100))

            # 3. MOTORES DINÁMICOS (Patrones)
            for p in self.patrones:
                self.update_log.emit(f"🔍 Escaneando patrón dinámico: '{p}'...")
                hallazgos.extend(self.motor_boe(p))
                hallazgos.extend(self.motor_borme(p))
                hallazgos.extend(self.motor_duckduckgo(p))
                paso_actual += 1
                self.progress.emit(int((paso_actual / total_pasos) * 100))

            self.finished_data.emit(hallazgos)
        except Exception as e:
            self.update_log.emit(f"⚠️ ERROR CRÍTICO EN WORKER: {str(e)}")

    def motor_google_dorks(self):
        """Genera enlaces de búsqueda avanzada (Dorks) basados en el perfil"""
        res = []
        nombre = self.config.get('nombre', '')
        dni = self.config.get('dni', '')
        if not nombre: return res

        # Definición de Dorks Forenses
        dorks = [
            ("DORK | Global", f'"{nombre}"', "Rastreo de menciones exactas en toda la web."),
            ("DORK | Documentos", f'"{nombre}" filetype:pdf OR filetype:doc OR filetype:xlsx', "Búsqueda de archivos expuestos (PDF/Excel)."),
            ("DORK | Redes", f'site:linkedin.com OR site:facebook.com OR site:instagram.com "{nombre}"', "Menciones en perfiles sociales."),
            ("DORK | Gobierno", f'site:gob.es OR site:juntaandalucia.es "{nombre}"', "Menciones en dominios gubernamentales."),
            ("DORK | DNI-Leaks", f'"{dni}"', "Verificación de exposición de número de identidad.")
        ]

        for fuente, query, obs in dorks:
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            res.append({
                'Fuente': fuente,
                'Titulo': f'Análisis: {query}',
                'Enlace': url,
                'Fecha_Info': 'LIVE',
                'Estado': 'Pendiente',
                'Obs': obs
            })
        return res

    def motor_boe(self, t):
        res = []
        if not t: return res
        try:
            r = requests.get("https://www.boe.es/buscar/boe.php", params={'campo[0]':'TIT','dato[0]':t}, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for item in soup.find_all('li', class_='resultado'):
                link = item.find('a')
                if link:
                    res.append({
                        'Fuente': 'BOE', 'Titulo': link.get_text().strip(),
                        'Enlace': "https://www.boe.es" + link.get('href'),
                        'Fecha_Info': 'Oficial', 'Estado': 'Pendiente', 'Obs': ''
                    })
        except Exception as e: self.update_log.emit(f"❌ Error BOE: {str(e)}")
        return res

    def motor_borme(self, t):
        res = []
        if not t: return res
        try:
            r = requests.get("https://www.boe.es/buscar/borme.php", params={'campo[0]':'TIT','dato[0]':t}, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for item in soup.find_all('li', class_='resultado'):
                link = item.find('a')
                if link:
                    res.append({
                        'Fuente': 'BORME', 'Titulo': link.get_text().strip(),
                        'Enlace': "https://www.boe.es" + link.get('href'),
                        'Fecha_Info': 'Mercantil', 'Estado': 'Pendiente', 'Obs': ''
                    })
        except Exception as e: self.update_log.emit(f"❌ Error BORME: {str(e)}")
        return res

    def motor_duckduckgo(self, t):
        res = []
        if not t: return res
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(f'"{t}"', max_results=5):
                    res.append({
                        'Fuente': 'Web', 'Titulo': r['title'], 'Enlace': r['href'],
                        'Fecha_Info': datetime.now().strftime("%d/%m/%Y"), 'Estado': 'Pendiente', 'Obs': ''
                    })
        except Exception as e: self.update_log.emit(f"❌ Error DDG: {str(e)}")
        return res

class SIPAIdentifWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIPA | Intel Intelligence Manager")
        self.resize(1200, 850)
        self.setStyleSheet(SIPAIdentStyle.SHEET)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.config = self.cargar_config()
        self.datos_actuales = []
        
        central = QWidget()
        central.setObjectName("CentralWidget")
        central.setStyleSheet(f"#CentralWidget {{ background-color: {SIPAIdentStyle.MAIN_BG}; }}")
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        lbl_title = QLabel("🛡️ REPUTATION MONITORING SERVICE")
        lbl_title.setStyleSheet(f"color: {SIPAIdentStyle.ACCENT_GREEN}; font-weight: bold; font-size: 16px;")
        self.btn_manual = QPushButton("RUN GLOBAL SCAN")
        self.btn_manual.setObjectName("LaunchBtn")
        self.btn_manual.setCursor(Qt.PointingHandCursor)
        self.btn_manual.clicked.connect(self.iniciar_prospeccion)
        header.addWidget(lbl_title); header.addStretch(); header.addWidget(self.btn_manual)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Fuente", "Título", "URL", "Estado", "Observaciones", "Fecha"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.tabs.addTab(self.table, "📊 RESULTS")

        self.tab_motores = QWidget()
        self.tab_motores.setAttribute(Qt.WA_StyledBackground, True)
        self.tab_motores.setStyleSheet(f"background-color: {SIPAIdentStyle.CARD_BG};")
        self.layout_mot = QGridLayout(self.tab_motores)
        self.renderizar_motores()
        self.tabs.addTab(self.tab_motores, "⚙️ ENGINES")

        self.tab_config = QWidget()
        self.tab_config.setAttribute(Qt.WA_StyledBackground, True)
        self.tab_config.setStyleSheet(f"background-color: {SIPAIdentStyle.CARD_BG};")
        cfg_lay = QVBoxLayout(self.tab_config)
        cfg_lay.setContentsMargins(30, 30, 30, 30)
        self.inputs_patrones = []
        form = QFormLayout()
        form.setSpacing(12)
        p_guardados = self.cargar_patrones()
        for i in range(10):
            le = QLineEdit()
            if i < len(p_guardados): le.setText(p_guardados[i])
            le.setPlaceholderText(f"Patrón de búsqueda #{i+1}")
            lbl = QLabel(f"PATTERN {i+1:02d}:")
            lbl.setStyleSheet("color: #666;")
            form.addRow(lbl, le)
            self.inputs_patrones.append(le)
        cfg_lay.addLayout(form)
        cfg_lay.addSpacing(20)
        btn_save = QPushButton("UPDATE SEARCH PATTERNS")
        btn_save.clicked.connect(self.guardar_patrones)
        cfg_lay.addWidget(btn_save); cfg_lay.addStretch()
        self.tabs.addTab(self.tab_config, "🛠 SEARCH CONFIG")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #050505; border: none;")
        self.tabs.addTab(self.log_output, "⌨️ CONSOLE")

        layout.addWidget(self.tabs)
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)
        self.cargar_datos_tabla()

    def renderizar_motores(self):
        while self.layout_mot.count():
            child = self.layout_mot.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        mots = [("BOE (Oficial)", SIPAIdentStyle.ACCENT_GREEN), ("BORME (Mercantil)", SIPAIdentStyle.ACCENT_GREEN), 
                ("DuckDuckGo", SIPAIdentStyle.ACCENT_GREEN), ("Google Dorking", SIPAIdentStyle.ACCENT_GREEN), 
                ("Bing Search", "#555"), ("Deep Web Index", SIPAIdentStyle.ACCENT_RED)]
        for i, (nombre, color) in enumerate(mots):
            card = QFrame(); card.setObjectName("MotorCard")
            c_lay = QHBoxLayout(card)
            led = QFrame(); led.setFixedSize(10, 10); led.setStyleSheet(f"background: {color}; border-radius: 5px; border: none;")
            label = QLabel(nombre); label.setStyleSheet("font-weight: bold; color: #E0E0E0;")
            c_lay.addWidget(led); c_lay.addWidget(label); c_lay.addStretch()
            self.layout_mot.addWidget(card, i // 2, i % 2)

    def cargar_config(self):
        if not os.path.exists(FICHERO_CONFIG): return {}
        try:
            with open(FICHERO_CONFIG, 'r', encoding='utf-8') as f:
                p = frontmatter.load(f)
            return {'dni': p.get('dni',''), 'nombre': p.get('nombre','')}
        except: return {}

    def cargar_patrones(self):
        if os.path.exists(ARCHIVO_PATRONES):
            try:
                with open(ARCHIVO_PATRONES, 'r') as f: return json.load(f)
            except: pass
        return []

    def guardar_patrones(self):
        pats = [le.text() for le in self.inputs_patrones]
        with open(ARCHIVO_PATRONES, 'w') as f: json.dump(pats, f)
        self.add_log("✅ Patrones actualizados.")

    def add_log(self, message):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{time_str}] {message}")

    def cargar_datos_tabla(self):
        if not os.path.exists(ARCHIVO_HISTORICO): return
        try:
            df = pd.read_csv(ARCHIVO_HISTORICO).fillna('')
            self.datos_actuales = df[df['Estado'] != 'Basura'].to_dict('records')
            self.renderizar_tabla()
        except Exception as e: self.add_log(f"⚠️ Error cargando CSV: {e}")

    def renderizar_tabla(self):
        try: self.table.itemChanged.disconnect()
        except: pass
        self.table.setRowCount(len(self.datos_actuales))
        for i, row in enumerate(self.datos_actuales):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get('Fuente',''))))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.get('Titulo',''))))
            btn = QPushButton("OPEN URL"); btn.setObjectName("UrlBtn"); btn.setFixedSize(65, 22)
            btn.clicked.connect(lambda _, l=row['Enlace']: webbrowser.open(l))
            self.table.setCellWidget(i, 2, btn)
            cb = QComboBox()
            cb.addItems(["Pendiente", "Seguimiento", "Basura", "Solicitado Olvido"])
            cb.setCurrentText(row.get('Estado', 'Pendiente'))
            cb.currentTextChanged.connect(lambda txt, r=row['Enlace']: self.actualizar_celda_csv(r, 'Estado', txt))
            self.table.setCellWidget(i, 3, cb)
            self.table.setItem(i, 4, QTableWidgetItem(str(row.get('Obs', ''))))
            self.table.setItem(i, 5, QTableWidgetItem(str(row.get('Fecha_Info', ''))))
        self.table.itemChanged.connect(self.cambio_manual_obs)

    def actualizar_celda_csv(self, enlace, col, valor):
        if not os.path.exists(ARCHIVO_HISTORICO): return
        try:
            df = pd.read_csv(ARCHIVO_HISTORICO).fillna('')
            df.loc[df['Enlace'] == enlace, col] = valor
            df.to_csv(ARCHIVO_HISTORICO, index=False, encoding='utf-8')
            if valor == "Basura": self.cargar_datos_tabla()
        except Exception as e: self.add_log(f"⚠️ Error al guardar: {e}")

    def cambio_manual_obs(self, item):
        if item.column() == 4:
            row_idx = item.row()
            if row_idx < len(self.datos_actuales):
                enlace = self.datos_actuales[row_idx]['Enlace']
                self.actualizar_celda_csv(enlace, 'Obs', item.text())

    def iniciar_prospeccion(self):
        self.btn_manual.setEnabled(False); self.tabs.setCurrentIndex(3)
        pats = [le.text() for le in self.inputs_patrones if le.text().strip()]
        self.worker = ProspeccionWorker(self.config, pats)
        self.worker.update_log.connect(self.add_log)
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.finished_data.connect(self.finalizar)
        self.worker.start()

    def finalizar(self, nuevos_dict):
        try:
            df_new = pd.DataFrame(nuevos_dict)
            if os.path.exists(ARCHIVO_HISTORICO):
                df_old = pd.read_csv(ARCHIVO_HISTORICO).fillna('')
                existentes = df_old['Enlace'].values
                para_añadir = df_new[~df_new['Enlace'].isin(existentes)]
                df_final = pd.concat([df_old, para_añadir], ignore_index=True)
            else:
                df_final = df_new
            df_final.to_csv(ARCHIVO_HISTORICO, index=False, encoding='utf-8')
            self.cargar_datos_tabla()
            self.add_log("✅ Trazado forense completado.")
        except Exception as e: self.add_log(f"⚠️ Error: {e}")
        finally:
            self.btn_manual.setEnabled(True); self.tabs.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SIPAIdentifWindow()
    w.show()
    sys.exit(app.exec())