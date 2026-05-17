# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: ssipa_identif.py
# Módulo: Huella Digital & Reputación Forense (Frame Component)
# Versión: 2.0.0.3 | Fecha: 17/05/2026
# ==========================================================

import sys
import os
import requests
import frontmatter
import pandas as pd
import webbrowser
import warnings
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel, QFrame, 
                             QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHBoxLayout, QHeaderView, QLineEdit, 
                             QFormLayout, QComboBox, QGridLayout, QApplication)
from PySide6.QtCore import Qt, QThread, Signal

# --- BLOQUEO DE LOGS INNECESARIOS ---
warnings.filterwarnings("ignore")
logging.getLogger("duckduckgo_search").setLevel(logging.ERROR)

# --- CONFIGURACIÓN DE RUTAS ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Nombre dinámico basado en este script para generar el token (.ssipa_identif.live)
NOMBRE_SCRIPT = os.path.splitext(os.path.basename(__file__))[0]
ARCHIVO_LIVE = os.path.join(CURRENT_DIR, f".{NOMBRE_SCRIPT}.live")

ROOT_SIPA = "/home/toviddfrei/SIPA"
FICHERO_CONFIG = os.path.join(ROOT_SIPA, "data/archive/template_propietario.md")
ARCHIVO_HISTORICO = os.path.join(ROOT_SIPA, "data/archive/historico_rastreo.csv")
ARCHIVO_PATRONES = os.path.join(ROOT_SIPA, "data/archive/patrones_busqueda.json")


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
        total_pasos = len(self.patrones) + 2 
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
        res = []
        nombre = self.config.get('nombre', '')
        dni = self.config.get('dni', '')
        if not nombre: return res

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
                'Fuente': fuente, 'Titulo': f'Análisis: {query}', 'Enlace': url,
                'Fecha_Info': 'LIVE', 'Estado': 'Pendiente', 'Obs': obs
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
        except: pass
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
        except: pass
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
        except: pass
        return res


class HuellaDigitalFrame(QWidget):
    """Componente SPA acoplable al contenedor QStackedWidget de sipa.py"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self.cargar_config()
        self.datos_actuales = []
        
        # Activar señal de latido inmediatamente al iniciar el Frame
        self.crear_senal_vida()
        self.init_ui()

    def crear_senal_vida(self):
        """Genera la firma temporal en disco para el monitor."""
        try:
            with open(ARCHIVO_LIVE, 'w') as f:
                f.write("RUNNING")
        except Exception as e:
            print(f"Error al escribir señal de vida en Frame: {e}")

    def borrar_senal_vida(self):
        """Remueve la firma temporal en disco."""
        try:
            if os.path.exists(ARCHIVO_LIVE):
                os.remove(ARCHIVO_LIVE)
        except Exception as e:
            print(f"Error al limpiar señal de vida en Frame: {e}")

    def closeEvent(self, event):
        """Intercepta el cierre del componente."""
        self.borrar_senal_vida()
        event.accept()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Header de operaciones interno
        header = QHBoxLayout()
        lbl_title = QLabel("🛡️ REPUTATION & DIGITAL FOOTPRINT MONITORING")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #00FF95;")
        
        self.btn_manual = QPushButton("RUN GLOBAL SCAN")
        self.btn_manual.setObjectName("BtnManage") 
        self.btn_manual.setCursor(Qt.PointingHandCursor)
        self.btn_manual.clicked.connect(self.iniciar_prospeccion)
        
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(self.btn_manual)
        layout.addLayout(header)

        # Panel de Pestañas
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # TAB 1: Tabla de resultados
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Fuente", "Título", "URL", "Estado", "Observaciones", "Fecha"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.tabs.addTab(self.table, "📊 RESULTS")

        # TAB 2: Grid de Motores
        self.tab_motores = QWidget()
        self.layout_mot = QGridLayout(self.tab_motores)
        self.renderizar_motores()
        self.tabs.addTab(self.tab_motores, "⚙️ ENGINES")

        # TAB 3: Configuración de patrones
        self.tab_config = QWidget()
        cfg_lay = QVBoxLayout(self.tab_config)
        cfg_lay.setContentsMargins(15, 15, 15, 15)
        self.inputs_patrones = []
        form = QFormLayout()
        form.setSpacing(8)
        p_guardados = self.cargar_patrones()
        for i in range(10):
            le = QLineEdit()
            if i < len(p_guardados): le.setText(p_guardados[i])
            le.setPlaceholderText(f"Patrón de búsqueda #{i+1}")
            lbl = QLabel(f"PATTERN {i+1:02d}:")
            lbl.setStyleSheet("color: #888888;")
            form.addRow(lbl, le)
            self.inputs_patrones.append(le)
        cfg_lay.addLayout(form)
        cfg_lay.addSpacing(10)
        btn_save = QPushButton("UPDATE SEARCH PATTERNS")
        btn_save.setObjectName("BtnManage")
        btn_save.clicked.connect(self.guardar_patrones)
        cfg_lay.addWidget(btn_save)
        cfg_lay.addStretch()
        self.tabs.addTab(self.tab_config, "🛠 SEARCH CONFIG")

        # TAB 4: Consola dedicada interna
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.tabs.addTab(self.log_output, "⌨️ INTERNAL CONSOLE")

        layout.addWidget(self.tabs)
        
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        layout.addWidget(self.pbar)
        
        self.cargar_datos_tabla()

    def renderizar_motores(self):
        while self.layout_mot.count():
            child = self.layout_mot.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        mots = [("BOE (Oficial)", "#00FF95"), ("BORME (Mercantil)", "#00FF95"), 
                ("DuckDuckGo", "#00FF95"), ("Google Dorking", "#00FF95"), 
                ("Bing Search", "#555"), ("Deep Web Index", "#E63946")]
        for i, (nombre, color) in enumerate(mots):
            card = QFrame()
            card.setObjectName("Card") 
            c_lay = QHBoxLayout(card)
            led = QFrame()
            led.setFixedSize(10, 10)
            led.setStyleSheet(f"background: {color}; border-radius: 5px; border: none;")
            label = QLabel(nombre)
            label.setStyleSheet("font-weight: bold;")
            c_lay.addWidget(led)
            c_lay.addWidget(label)
            c_lay.addStretch()
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
        self.add_log("✅ Patrones dinámicos actualizados con éxito.")

    def add_log(self, message):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{time_str}] {message}")

    def cargar_datos_tabla(self):
        if not os.path.exists(ARCHIVO_HISTORICO): return
        try:
            df = pd.read_csv(ARCHIVO_HISTORICO).fillna('')
            self.datos_actuales = df[df['Estado'] != 'Basura'].to_dict('records')
            self.renderizar_tabla()
        except: pass

    def renderizar_tabla(self):
        try: self.table.itemChanged.disconnect()
        except: pass
        self.table.setRowCount(len(self.datos_actuales))
        for i, row in enumerate(self.datos_actuales):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get('Fuente',''))))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.get('Titulo',''))))
            
            btn = QPushButton("URL")
            btn.setFixedSize(55, 20)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("background-color: #050505; color: #3A86FF; border: 1px solid #3A86FF; font-size: 9px; font-weight: bold;")
            btn.clicked.connect(lambda _, l=row['Enlace']: webbrowser.open(l))
            self.table.setCellWidget(i, 2, btn)
            
            cb = QComboBox()
            cb.addItems(["Pendiente", "Seguimiento", "Basura", "Solicitado Olvido"])
            cb.setCurrentText(row.get('Estado', 'Pendiente'))
            cb.setStyleSheet("QComboBox { background-color: #111111; color: #00FF95; }")
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
        except: pass

    def cambio_manual_obs(self, item):
        if item.column() == 4:
            row_idx = item.row()
            if row_idx < len(self.datos_actuales):
                enlace = self.datos_actuales[row_idx]['Enlace']
                self.actualizar_celda_csv(enlace, 'Obs', item.text())

    def iniciar_prospeccion(self):
        self.btn_manual.setEnabled(False)
        self.tabs.setCurrentIndex(3) 
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
            self.add_log("✅ Trazado forense completado con éxito.")
        except Exception as e:
            self.add_log(f"⚠️ Error al consolidar histórico: {e}")
        finally:
            self.btn_manual.setEnabled(True)
            self.tabs.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    frame = HuellaDigitalFrame()
    frame.show()
    
    codigo_salida = app.exec()
    
    # Limpieza estricta de seguridad al salir del bucle Qt
    try:
        if os.path.exists(ARCHIVO_LIVE):
            os.remove(ARCHIVO_LIVE)
    except:
        pass
        
    sys.exit(codigo_salida)