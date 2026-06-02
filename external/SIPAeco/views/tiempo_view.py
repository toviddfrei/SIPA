#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco - Módulo de Inyección y Gestión de Impactos de Tiempo (Balas Operativas)
Ubicación: SIPA/external/SIPAeco/views/tiempo_view.py
Autor: Daniel Miñana Montero & Gemini
Fecha: 2026-06-02
Descripción: Vista POO que actúa como INPUT dinámico y registro histórico de impactos.
             MEJORA: Selección de tipo de coste (Real vs Default) e imputación financiera.
             AÑADIDO: Infraestructura de adjuntar y crear ficheros vinculados a la FDU.
             INTEGRACIÓN ORÁCULO: Lista dinámica vinculada a sipa_activos.json.
             🔌 TRUNKING: Alimentación PoE heredada por el Switch de infraestructura.
"""

import os
import sys
import subprocess
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView, 
                             QLineEdit, QMessageBox, QComboBox, QGroupBox, 
                             QGridLayout, QTextEdit, QFileDialog, QListWidget, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# =====================================================================
# 🎛️ CONEXIÓN TRONCAL DIRECTA (Conmutada de forma transparente por el Switch)
# =====================================================================
# Corrección del enlace físico a la biblioteca central de utilidades
from external.utils.sipa_utils import sincronizar_contexto_hito_labels

class TiempoTab(QWidget):
    def __init__(self, core, parent_window=None):
        super().__init__(parent_window)
        self.core = core
        self.parent_window = parent_window
        self.hitos_cache = {}  
        self.id_impacto_seleccionado = None  # Almacena la bala activa en foco
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # =====================================================================
        # ⚡ FORMULARIO DE INPUT: INYECCIÓN DE IMPACTOS DE TIEMPO
        # =====================================================================
        group_input = QGroupBox("⏱️ Inyección de Impacto Temporal / Agenda Predictiva")
        ly_input = QGridLayout(group_input)
        
        # Desplegables y selectores estratégicos
        self.combo_vincular_hito = QComboBox()
        
        self.lbl_auto_proyecto = QLabel("<b>Proyecto:</b> -")
        self.lbl_auto_proyecto.setStyleSheet("color: #0969da; background: #f0f7ff; padding: 4px; border-radius: 4px;")
        self.lbl_auto_crono = QLabel("<b>Crono Tipo:</b> -")
        self.lbl_auto_crono.setStyleSheet("color: #0969da; background: #f0f7ff; padding: 4px; border-radius: 4px;")
        
        # Conexión reactiva utilizando el gestor de la biblioteca compartida utils
        self.combo_vincular_hito.currentTextChanged.connect(
            lambda txt: sincronizar_contexto_hito_labels(txt, self.hitos_cache, self.lbl_auto_proyecto, self.lbl_auto_crono)
        )
        
        self.in_fecha_impacto = QLineEdit()
        self.in_fecha_impacto.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        self.in_tiempo_aplicado = QLineEdit()
        self.in_tiempo_aplicado.setPlaceholderText("Horas (Ej: 2.5)")
        
        self.combo_estado_impacto = QComboBox()
        self.combo_estado_impacto.addItems(["PLANIFICADO", "EN PROCESO", "COMPLETADO", "SUSPENDIDO", "CANCELADO"])
        
        # --- REFERENCIA DE TARIFA (PRECIO HORA A APLICAR) ---
        self.combo_tipo_tarifa = QComboBox()
        self.combo_tipo_tarifa.addItems(["REAL (BANCO)", "DEFAULT (RESPALDO)"])
        self.combo_tipo_tarifa.setToolTip("Elige si este impacto se calcula a precio real de banco o con la tarifa de respaldo.")
        
        # Detalle de la acción (Calibre del impacto)
        self.txt_detalle_impacto = QTextEdit()
        self.txt_detalle_impacto.setPlaceholderText("Detalle de la acción realizada o a realizar (Bitácora, Notas, Acta...)")
        self.txt_detalle_impacto.setMaximumHeight(60)
        
        # --- GESTIÓN DOCUMENTAL DE IMPACTOS (PANEL INTERACTIVO) ---
        ly_docs_master = QVBoxLayout()
        
        ly_botones_docs = QHBoxLayout()
        self.btn_crear_plantilla = QPushButton("📄 Crear Fichero (Plantilla)")
        self.btn_crear_plantilla.setStyleSheet("background-color: #0969da; color: white; font-weight: bold;")
        self.configurar_menu_plantillas() # Generar el menú desplegable de opciones
        
        self.btn_adjuntar_fichero = QPushButton("📎 Adjuntar Fichero")
        self.btn_adjuntar_fichero.setStyleSheet("background-color: #6e7681; color: white; font-weight: bold;")
        self.btn_adjuntar_fichero.clicked.connect(self.ejecutar_vinculacion_archivo)
        
        ly_botones_docs.addWidget(self.btn_crear_plantilla)
        ly_botones_docs.addWidget(self.btn_adjuntar_fichero)
        
        # Lista visual de los archivos de la Bala seleccionada
        self.lbl_info_lista = QLabel("<b>Ficheros Vinculados (Doble clic para editar/abrir):</b>")
        self.lbl_info_lista.setStyleSheet("font-size: 11px; color: #57606a;")
        self.list_ficheros_fdu = QListWidget()
        self.list_ficheros_fdu.setMaximumHeight(80)
        self.list_ficheros_fdu.itemDoubleClicked.connect(self.on_fichero_doble_clic)

        # Permitir menú contextual personalizado (Clic derecho)
        self.list_ficheros_fdu.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_ficheros_fdu.customContextMenuRequested.connect(self.mostrar_menu_contextual_ficheros)
        
        ly_docs_master.addLayout(ly_botones_docs)
        ly_docs_master.addWidget(self.lbl_info_lista)
        ly_docs_master.addWidget(self.list_ficheros_fdu)
        
        btn_inyectar_impacto = QPushButton("💥 Impactar Tiempo")
        btn_inyectar_impacto.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold; padding: 6px 15px;")
        btn_inyectar_impacto.clicked.connect(self.ejecutar_alta_impacto)
        
        # Distribución en Grid (Fila 0)
        ly_input.addWidget(QLabel("Hito Nucleo Vinculante:"), 0, 0)
        ly_input.addWidget(self.combo_vincular_hito, 0, 1)
        ly_input.addWidget(self.lbl_auto_proyecto, 0, 2)
        ly_input.addWidget(self.lbl_auto_crono, 0, 3)
        
        # Distribución en Grid (Fila 1)
        ly_input.addWidget(QLabel("Fecha (AAAA-MM-DD HH:MM):"), 1, 0)
        ly_input.addWidget(self.in_fecha_impacto, 1, 1)
        ly_input.addWidget(QLabel("Tiempo (Horas):"), 1, 2)
        ly_input.addWidget(self.in_tiempo_aplicado, 1, 3)
        
        # Distribución en Grid (Fila 2)
        ly_input.addWidget(QLabel("Estado Impacto:"), 2, 0)
        ly_input.addWidget(self.combo_estado_impacto, 2, 1)
        ly_input.addWidget(QLabel("Estrategia Coste/Tarifa:"), 2, 2)
        ly_input.addWidget(self.combo_tipo_tarifa, 2, 3)
        
        # Fila 3: Documentación y Archivos de Trabajo
        ly_input.addWidget(QLabel("Documentación / FDU:"), 3, 0)
        ly_input.addLayout(ly_docs_master, 3, 1, 1, 3)
        
        # Fila 4: Detalles extensos
        ly_input.addWidget(QLabel("Detalle / Bitácora:"), 4, 0)
        ly_input.addWidget(self.txt_detalle_impacto, 4, 1, 1, 3)
        
        # Botón de disparo
        ly_input.addWidget(btn_inyectar_impacto, 5, 3, Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(group_input)
        
        # =====================================================================
        # 📊 HISTÓRICO LINEAL: REGISTRO BALA DE IMPACTOS REALIZADOS / AGENDADOS
        # =====================================================================
        group_tabla = QGroupBox("📋 Registro Bala Lineal de Impactos de Tiempo")
        ly_tabla = QVBoxLayout(group_tabla)
        
        self.table_impactos_tiempo = QTableWidget()
        self.table_impactos_tiempo.setColumnCount(10)
        self.table_impactos_tiempo.setHorizontalHeaderLabels([
            "ID Bala", "Fecha Impacto", "Hito Vinculado", "Proyecto", \
            "Detalle de la Acción Operativa", "Horas", "Tarifa Aplicada", "Coste Imputado", "Estado", "Acciones"
        ])
        
        self.table_impactos_tiempo.setWordWrap(True)
        self.table_impactos_tiempo.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        fuente_compacta = QFont()
        fuente_compacta.setPointSize(9)
        self.table_impactos_tiempo.setFont(fuente_compacta)
        
        self.table_impactos_tiempo.setSortingEnabled(True)
        self.table_impactos_tiempo.itemSelectionChanged.connect(self.on_fila_tabla_seleccionada)
        
        header = self.table_impactos_tiempo.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) 
        
        self.table_impactos_tiempo.cellChanged.connect(self.on_celda_impacto_modificada)
        
        ly_tabla.addWidget(self.table_impactos_tiempo)
        layout.addWidget(group_tabla)

    def configurar_menu_plantillas(self):
        """Genera el árbol desplegable estándar en el botón Crear."""
        menu = QMenu(self)
        plantillas = [
            ("Nota estándar", "nota"),
            ("Acta de Reunión", "acta"),
            ("Bitácora de Trabajo", "bitacora"),
            ("Trayectoria Profesional", "trayectoria_profesional"),
            ("Trayectoria Formativa", "trayectoria_formativa"),
            ("Post / Publicación", "post"),
            ("Bloque de Contenido", "bloque")
        ]
        for nombre, codigo in plantillas:
            accion = menu.addAction(nombre)
            accion.triggered.connect(lambda checked=False, c=codigo: self.ejecutar_creacion_plantilla(c))
        self.btn_crear_plantilla.setMenu(menu)

    def on_fila_tabla_seleccionada(self):
        """Detecta qué Bala está seleccionada y vuelca sus archivos en la lista interactiva."""
        items = self.table_impactos_tiempo.selectedItems()
        if not items:
            return
        
        fila = items[0].row()
        id_bala = self.table_impactos_tiempo.item(fila, 0).text()
        self.id_impacto_seleccionado = id_bala
        self.lbl_info_lista.setText(f"<b>Ficheros Vinculados a {id_bala}:</b>")
        
        # Buscar la sesión en caliente para pintar sus adjuntos
        self.list_ficheros_fdu.clear()
        sesiones = self.core.obtener_sesiones()
        for s in sesiones:
            if s.get("id_sesion") == id_bala:
                for fichero in s.get("ficheros_adjuntos", []):
                    self.list_ficheros_fdu.addItem(fichero)
                break

    def renderizar_impactos_tiempo(self, hitos, catalogos):
        """Rellena el histórico incorporando las lógicas de coste elástico."""
        self.table_impactos_tiempo.blockSignals(True)
        self.table_impactos_tiempo.setSortingEnabled(False)
        self.table_impactos_tiempo.setRowCount(0)
        self.list_ficheros_fdu.clear()
        self.id_impacto_seleccionado = None
        self.lbl_info_lista.setText("<b>Ficheros Vinculados (Selecciona una fila abajo):</b>")
        
        self.hitos_cache = hitos
        self.combo_vincular_hito.blockSignals(True)
        self.combo_vincular_hito.clear()
        
        lista_hitos_ordenados = sorted(list(hitos.keys()))
        for h_id in lista_hitos_ordenados:
            nombre_breve = hitos[h_id].get("nombre_accion", "")[:30]
            self.combo_vincular_hito.addItem(f"{h_id} ({nombre_breve}...)", h_id)
        self.combo_vincular_hito.blockSignals(False)
            
        # Sincronización inicial tras carga en frío
        sincronizar_contexto_hito_labels(self.combo_vincular_hito.currentText(), self.hitos_cache, self.lbl_auto_proyecto, self.lbl_auto_crono)

        sesiones = self.core.obtener_sesiones()
        proyectos_map = catalogos.get("proyectos", {})
        
        for row_idx, sesion in enumerate(sesiones):
            self.table_impactos_tiempo.insertRow(row_idx)
            
            id_bala = sesion.get("id_sesion", "-")
            id_hito = sesion.get("id_hito", "-").upper()
            info_h = hitos.get(id_hito, {})
            
            id_pry = info_h.get("id_proyecto", "")
            nombre_pry = proyectos_map.get(id_pry, {}).get("nombre", id_pry)
            
            # 0. ID Bala, 1. Fecha, 2. Hito, 3. Proyecto
            self.table_impactos_tiempo.setItem(row_idx, 0, self._crear_item_inmutable(id_bala))
            self.table_impactos_tiempo.setItem(row_idx, 1, QTableWidgetItem(sesion.get("hora_inicio", sesion.get("fecha", ""))))
            self.table_impactos_tiempo.setItem(row_idx, 2, self._crear_item_inmutable(id_hito))
            self.table_impactos_tiempo.setItem(row_idx, 3, self._crear_item_inmutable(nombre_pry))
            
            # 4. Detalle de la acción
            self.table_impactos_tiempo.setItem(row_idx, 4, QTableWidgetItem(sesion.get("tarea", "-")))
            
            # 5. Horas consumidas
            self.table_impactos_tiempo.setItem(row_idx, 5, QTableWidgetItem(str(sesion.get("horas_reales", 0.0))))
            
            # 6. Tarifa Aplicada por Hora
            tipo_t = sesion.get("tipo_tarifa_seleccionada", "REAL")
            tarifa = float(sesion.get("tarifa_aplicada", 25.0))
            item_tarifa = QTableWidgetItem(f"{tarifa:.2f} €/h ({tipo_t})")
            item_tarifa.setFlags(item_tarifa.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_tarifa.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_impactos_tiempo.setItem(row_idx, 6, item_tarifa)
            
            # 7. Coste total imputado (Horas * Tarifa)
            coste_total = float(sesion.get("coste_imputado_recurso", 0.0))
            item_coste = QTableWidgetItem(f"{coste_total:.2f} €")
            item_coste.setFlags(item_coste.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_coste.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_impactos_tiempo.setItem(row_idx, 7, item_coste)
            
            # 8. Estado del impacto
            self.table_impactos_tiempo.setItem(row_idx, 8, QTableWidgetItem(sesion.get("estado_impacto", "COMPLETADO")))
            
            # 9. Acciones (Baja / Indicador Ficheros)
            ly_btns = QWidget()
            lt = QHBoxLayout(ly_btns)
            lt.setContentsMargins(2, 2, 2, 2)
            lt.setSpacing(4)
            
            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar impacto temporal")
            btn_del.clicked.connect(lambda checked=False, s_id=id_bala: self.ejecutar_baja_impacto(s_id))
            
            if sesion.get("ficheros_adjuntos"):
                lbl_adjunto = QLabel("📎")
                lbl_adjunto.setToolTip(f"Contiene {len(sesion['ficheros_adjuntos'])} archivo(s). Selecciónala para verlos.")
                lt.addWidget(lbl_adjunto)

            lt.addWidget(btn_del)
            self.table_impactos_tiempo.setCellWidget(row_idx, 9, ly_btns)

        for c in range(self.table_impactos_tiempo.columnCount()):
            if c != 4: self.table_impactos_tiempo.resizeColumnToContents(c)
                
        self.table_impactos_tiempo.setSortingEnabled(True)
        self.table_impactos_tiempo.blockSignals(False)

    def _crear_item_inmutable(self, texto):
        item = QTableWidgetItem(texto)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def ejecutar_alta_impacto(self):
        """Lee el input del formulario, aplica el tipo de tasa elegido e impacta en el Core."""
        hito_texto = self.combo_vincular_hito.currentText()
        if not hito_texto:
            QMessageBox.warning(self, "Validación", "Debes seleccionar un hito nuclear vinculante.")
            return
            
        id_hito = hito_texto.split(" ")[0]
        info_h = self.hitos_cache.get(id_hito, {})
        crono_id = info_h.get("id_cronograma_tipo", "PLAN_MAESTRO")
        
        fecha_str = self.in_fecha_impacto.text().strip()
        tiempo_str = self.in_tiempo_aplicado.text().strip()
        detalle = self.txt_detalle_impacto.toPlainText().strip()
        estado = self.combo_estado_impacto.currentText()
        estrategia_tarifa = self.combo_tipo_tarifa.currentText()
        
        if not detalle:
            QMessageBox.warning(self, "Validación", "El detalle o acción del impacto no puede estar vacío.")
            return
            
        try: horas = float(tiempo_str.replace(",", ".")) if tiempo_str else 0.0
        except ValueError: horas = 0.0
        
        hora_fin_str = fecha_str
        try:
            dt_i = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
            import datetime as dt_mod
            dt_f = dt_i + dt_mod.timedelta(hours=horas)
            hora_fin_str = dt_f.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            QMessageBox.warning(self, "Validación", "Formato de fecha incorrecto (AAAA-MM-DD HH:MM)")
            return

        tasa_aplicar = 25.0
        master_data = self.core._load_json(self.core.cronogramas_path)
        
        if "DEFAULT" in estrategia_tarifa:
            tasa_aplicar = float(master_data.get("configuracion", {}).get("precio_hora_default", 25.0))
            tipo_log = "DEFAULT"
        else:
            if self.parent_window:
                tasa_aplicar = self.parent_window.calcular_tasa_real_banco_provisional(master_data)
            if tasa_aplicar <= 0:
                tasa_aplicar = float(master_data.get("configuracion", {}).get("precio_hora_default", 25.0))
            tipo_log = "REAL"

        success, msg = self.core.registrar_sesion(crono_id, id_hito, fecha_str, hora_fin_str, detalle, tasa_aplicar)
        
        if success:
            data_logs = self.core._load_json(self.core.time_log_path)
            if data_logs.get("sesiones"):
                data_logs["sesiones"][-1]["estado_impacto"] = estado
                data_logs["sesiones"][-1]["tipo_tarifa_seleccionada"] = tipo_log
                data_logs["sesiones"][-1]["ficheros_adjuntos"] = []
                
                if hasattr(self, 'archivo_temporal_adjunto'):
                    data_logs["sesiones"][-1]["ficheros_adjuntos"].append(self.archivo_temporal_adjunto)
                    delattr(self, 'archivo_temporal_adjunto')
                    
                self.core._save_json(self.core.time_log_path, data_logs)
            
            self.txt_detalle_impacto.clear()
            self.in_tiempo_aplicado.clear()
            self.in_fecha_impacto.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
            
            if self.parent_window:
                self.parent_window.actualizar_todo()
        else:
            QMessageBox.critical(self, "Error Core", msg)

    def on_celda_impacto_modificada(self, row, col):
        item_id = self.table_impactos_tiempo.item(row, 0)
        if not item_id: return
        id_bala = item_id.text()
        
        mapa_columnas = {1: "hora_inicio", 4: "tarea", 5: "horas_reales", 8: "estado_impacto"}
        if col not in mapa_columnas: return
        campo = mapa_columnas[col]
        
        valor = self.table_impactos_tiempo.item(row, col).text().strip()
        data_logs = self.core._load_json(self.core.time_log_path)
        
        for sesion in data_logs.get("sesiones", []):
            if sesion.get("id_sesion") == id_bala:
                if campo == "horas_reales":
                    try: 
                        valor = float(valor.replace(",", "."))
                        sesion["coste_imputado_recurso"] = round(valor * float(sesion.get("tarifa_aplicada", 25.0)), 2)
                    except ValueError: valor = 0.0
                sesion[campo] = valor
                break
                
        self.core._save_json(self.core.time_log_path, data_logs)
        if self.parent_window:
            self.parent_window.actualizar_todo()

    def ejecutar_baja_impacto(self, id_bala):
        res = QMessageBox.question(self, "Baja de Impacto", f"¿Deseas eliminar la bala de impacto {id_bala}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            data_logs = self.core._load_json(self.core.time_log_path)
            data_logs["sesiones"] = [s for s in data_logs.get("sesiones", []) if s.get("id_sesion") != id_bala]
            self.core._save_json(self.core.time_log_path, data_logs)
            if self.parent_window:
                self.parent_window.actualizar_todo()

    def ejecutar_creacion_plantilla(self, tipo_plantilla):
        """Disparador para generar actas o bitácoras profesionales en inbox."""
        if self.id_impacto_seleccionado:
            id_impacto = self.id_impacto_seleccionado
            fila = self.table_impactos_tiempo.currentRow()
            titulo_impacto = self.table_impactos_tiempo.item(fila, 4).text()
        else:
            hito_texto = self.combo_vincular_hito.currentText()
            if not hito_texto:
                QMessageBox.warning(self, "Atención", "Selecciona una Bala de la tabla o un Hito del formulario para vincular el documento.")
                return
            id_impacto = f"BALA_TEMP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            titulo_impacto = self.txt_detalle_impacto.toPlainText().strip() or "Documento Sin Titulo"

        nombre_archivo = self.core.crear_documento_desde_plantilla(id_impacto, tipo_plantilla, titulo_impacto)
        
        if self.id_impacto_seleccionado:
            self.on_fila_tabla_seleccionada()
        else:
            self.archivo_temporal_adjunto = nombre_archivo
            self.list_ficheros_fdu.clear()
            self.list_ficheros_fdu.addItem(nombre_archivo)
            
        self.abrir_fichero_para_edicion_so(nombre_archivo)

    def ejecutar_vinculacion_archivo(self):
        """Abre el explorador nativo forzando el inicio en SIPA/data."""
        base_sipa = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        directorio_trabajo = os.path.join(base_sipa, "data")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "FDU - Vincular Recurso Único a Impacto", 
            directorio_trabajo, 
            "Todos los archivos (*.*);;Markdown (*.md);;PDF (*.pdf)"
        )
        
        if file_path:
            if self.id_impacto_seleccionado:
                exito, nombre_final = self.core.adjuntar_fichero_existente(self.id_impacto_seleccionado, file_path)
                if exito:
                    self.on_fila_tabla_seleccionada()
                else:
                    QMessageBox.critical(self, "Error", nombre_final)
            else:
                import shutil
                inbox_dir = os.path.join(directorio_trabajo, "inbox")
                if not os.path.exists(inbox_dir): os.makedirs(inbox_dir)
                nombre_final = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
                shutil.copy2(file_path, os.path.join(inbox_dir, nombre_final))
                
                self.archivo_temporal_adjunto = nombre_final
                self.list_ficheros_fdu.clear()
                self.list_ficheros_fdu.addItem(nombre_final)
                QMessageBox.information(self, "FDU Vinculada", f"Archivo copiado al inbox listo para impactar: {nombre_final}")

    def on_fichero_doble_clic(self, item):
        nombre_archivo = item.text()
        self.abrir_fichero_para_edicion_so(nombre_archivo)

    def abrir_fichero_para_edicion_so(self, nombre_archivo):
        ruta_lista, resultado = self.core.preparar_fichero_para_edicion(nombre_archivo)
        if not ruta_lista:
            QMessageBox.critical(self, "Error de Ubicación", resultado)
            return

        try:
            if os.name == 'nt':  
                os.startfile(ruta_lista)
            else:  
                subprocess.Popen(['xdg-open', ruta_lista])
        except Exception as e:
            QMessageBox.critical(self, "Error OS", f"No se pudo invocar el editor del sistema: {e}")
    
    def mostrar_menu_contextual_ficheros(self, posicion):
        item = self.list_ficheros_fdu.itemAt(posicion)
        if not item: return

        nombre_archivo = item.text()
        menu = QMenu(self)
        accion_desvincular = menu.addAction("❌ Desvincular de la Bala")
        accion_seleccionada = menu.exec(self.list_ficheros_fdu.mapToGlobal(posicion))
        
        if accion_seleccionada == accion_desvincular:
            self.ejecutar_desvinculacion_fichero(nombre_archivo)

    def ejecutar_desvinculacion_fichero(self, nombre_archivo):
        if not self.id_impacto_seleccionado:
            if hasattr(self, 'archivo_temporal_adjunto') and self.archivo_temporal_adjunto == nombre_archivo:
                delattr(self, 'archivo_temporal_adjunto')
                self.list_ficheros_fdu.clear()
                QMessageBox.information(self, "FDU Saneada", "Archivo temporal removido del formulario.")
            return

        res = QMessageBox.question(
            self, 
            "Desvincular Archivo", 
            f"¿Estás seguro de que deseas quitar '{nombre_archivo}' de la Bala {self.id_impacto_seleccionado}?\n\n(Nota: El archivo físico no se borrará de data/inbox/ o knowledge/)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if res == QMessageBox.StandardButton.Yes:
            exito, msg = self.core.desvincular_archivo_de_impacto(self.id_impacto_seleccionado, nombre_archivo)
            if exito:
                self.on_fila_tabla_seleccionada()
                if self.parent_window:
                    self.parent_window.actualizar_todo()
            else:
                QMessageBox.critical(self, "Error", msg)