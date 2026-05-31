#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco - Módulo de Gestión Relacional de Hitos Nucleares
Ubicación: SIPA/external/SIPAeco/views/hitos_view.py
Autor: Daniel Miñana Montero
Fecha: 2026-05-30
Descripción: Vista POO externalizada para el control operativo de hitos.
             Implementa segmentación entre hitos Básicos (mensuales/vitales)
             y Operativos (cronogramas), cálculo de coste elástico reactivo
             y optimización visual de envoltorio de texto en filas.
             CORRECCIÓN: Coste directo fijo para hitos básicos sin forzar horas.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView, 
                             QLineEdit, QMessageBox, QComboBox, QCheckBox, QGroupBox, 
                             QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime

class HitosTab(QWidget):
    def __init__(self, core, parent_window=None):
        super().__init__(parent_window)
        self.core = core
        self.parent_window = parent_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Formulario de Inyección de Hitos Nucleares
        group_alta = QGroupBox("⚡ Inyección de Hito Nuclear Estratégico (ID Único)")
        ly_alta = QGridLayout(group_alta)
        
        # Selectores de catálogos
        self.combo_add_proyecto = QComboBox()
        self.combo_add_crono = QComboBox()
        
        # Campo de Meta / Acción Principal
        self.in_add_accion = QLineEdit()
        self.in_add_accion.setPlaceholderText("Definición del punto de cruce u objetivo del hito...")
        
        # Clasificación Nuclear: Básico vs Operativo
        self.check_tipo_basico = QCheckBox("Hito Básico (Mensual / Fijo Vital)")
        self.check_tipo_basico.setToolTip("Hitos fijos de vida (alquiler, luz, autónomo...) sin fecha fin obligatoria.")
        
        self.combo_add_prioridad = QComboBox()
        self.combo_add_prioridad.addItems(["1 - CRÍTICA", "2 - ALTA", "3 - MEDIA", "4 - BAJA"])
        self.combo_add_prioridad.setCurrentText("3 - MEDIA")
        
        # Previsiones estancas de datos (Mutables según tipo)
        self.lbl_variable_coste = QLabel("Presupuesto Horas:")
        self.in_add_horas_o_coste = QLineEdit()
        self.in_add_horas_o_coste.setPlaceholderText("Horas estimadas")
        
        self.in_add_ingreso = QLineEdit()
        self.in_add_ingreso.setPlaceholderText("Ingreso previsto (€)")
        
        # Fechas operativas (se desactivarán si es Básico)
        self.in_fecha_inicio = QLineEdit()
        self.in_fecha_inicio.setText(datetime.now().strftime("%Y-%m-%d"))
        self.in_fecha_fin = QLineEdit()
        self.in_fecha_fin.setText(datetime.now().strftime("%Y-%m-%d"))
        
        self.check_tipo_basico.toggled.connect(self.alternar_comportamiento_tipo_hito)
        
        btn_inyectar = QPushButton("➕ Inyectar Hito Estratégico")
        btn_inyectar.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold; padding: 6px 15px;")
        btn_inyectar.clicked.connect(self.ejecutar_alta_hito)
        
        # Distribución en Grid (Fila 0)
        ly_alta.addWidget(QLabel("Proyecto vinculante:"), 0, 0)
        ly_alta.addWidget(self.combo_add_proyecto, 0, 1)
        ly_alta.addWidget(QLabel("Tipo Cronograma:"), 0, 2)
        ly_alta.addWidget(self.combo_add_crono, 0, 3)
        ly_alta.addWidget(QLabel("Meta / Punto Cruce:"), 0, 4)
        ly_alta.addWidget(self.in_add_accion, 0, 5)
        
        # Distribución en Grid (Fila 1)
        ly_alta.addWidget(QLabel("Clasificación:"), 1, 0)
        ly_alta.addWidget(self.check_tipo_basico, 1, 1)
        ly_alta.addWidget(QLabel("F. Inicio (AAAA-MM-DD):"), 1, 2)
        ly_alta.addWidget(self.in_fecha_inicio, 1, 3)
        ly_alta.addWidget(QLabel("F. Fin (AAAA-MM-DD):"), 1, 4)
        ly_alta.addWidget(self.in_fecha_fin, 1, 5)
        
        # Distribución en Grid (Fila 2)
        ly_alta.addWidget(self.lbl_variable_coste, 2, 0)
        ly_alta.addWidget(self.in_add_horas_o_coste, 2, 1)
        ly_alta.addWidget(QLabel("Ingreso Previsto (€):"), 2, 2)
        ly_alta.addWidget(self.in_add_ingreso, 2, 3)
        ly_alta.addWidget(QLabel("Prioridad:"), 2, 4)
        ly_alta.addWidget(self.combo_add_prioridad, 2, 5)
        
        ly_alta.addWidget(btn_inyectar, 3, 5, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(group_alta)
        
        # Matriz de Hitos Nucleares con optimización de columnas y envoltorio de celdas
        self.table_cronogramas = QTableWidget()
        self.table_cronogramas.setColumnCount(11)
        self.table_cronogramas.setHorizontalHeaderLabels([
            "ID Hito Nuclear", "Clase", "Proyecto Relacionado", "Crono Tipo", "Punto de Cruce / Objetivo", 
            "F. Inicio", "F. Fin", "Métrica (H / Fijo)", "Coste Prev.", "Resultado Esperado", "Acciones"
        ])
        
        # OPTIMIZACIÓN VISUAL SOLICITADA
        self.table_cronogramas.setWordWrap(True)
        self.table_cronogramas.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        fuente_compacta = QFont()
        fuente_compacta.setPointSize(9)
        self.table_cronogramas.setFont(fuente_compacta)
        
        self.table_cronogramas.setSortingEnabled(True)
        header = self.table_cronogramas.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.table_cronogramas.cellChanged.connect(self.on_celda_matriz_modificada)
        layout.addWidget(self.table_cronogramas)

    def alternar_comportamiento_tipo_hito(self, es_basico):
        """Muta el formulario dinámicamente según la naturaleza del hito."""
        if es_basico:
            self.in_fecha_fin.setEnabled(False)
            self.in_fecha_fin.setText("MENSUAL (FIJO)")
            self.lbl_variable_coste.setText("Coste Fijo Neto (€):")
            self.in_add_horas_o_coste.setPlaceholderText("Ej. 650.00")
        else:
            self.in_fecha_fin.setEnabled(True)
            self.in_fecha_fin.setText(datetime.now().strftime("%Y-%m-%d"))
            self.lbl_variable_coste.setText("Presupuesto Horas:")
            self.in_add_horas_o_coste.setPlaceholderText("Horas estimadas")

    def renderizar_matriz_cronogramas(self, hitos, catalogos):
        self.table_cronogramas.blockSignals(True)
        self.table_cronogramas.setSortingEnabled(False)
        self.table_cronogramas.setRowCount(0)
        
        self.combo_add_proyecto.clear()
        for p_id, p_info in catalogos.get("proyectos", {}).items():
            self.combo_add_proyecto.addItem(f"{p_info.get('nombre')} ({p_id})", p_id)
            
        self.combo_add_crono.clear()
        for c_id, c_info in catalogos.get("cronogramas_tipos", {}).items():
            self.combo_add_crono.addItem(f"{c_info.get('codigo')} ({c_id})", c_id)
            
        lista_proyectos = sorted(list(catalogos.get("proyectos", {}).keys()))
        lista_cronos = sorted(list(catalogos.get("cronogramas_tipos", {}).keys()))
        
        tasa_hora_banco = 0.0
        if self.parent_window:
            tasa_hora_banco = self.parent_window.calcular_tasa_real_banco_provisional(None)
        
        if tasa_hora_banco <= 0:
            master_data = self.core._load_json(self.core.cronogramas_path)
            tasa_hora_banco = master_data.get("configuracion", {}).get("precio_hora_default", 25.0)

        for row_idx, (hito_id, info) in enumerate(hitos.items()):
            self.table_cronogramas.insertRow(row_idx)
            
            # 0. ID inmutable
            item_id = QTableWidgetItem(hito_id)
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_cronogramas.setItem(row_idx, 0, item_id)
            
            # 1. Clase (BÁSICO / OPERATIVO)
            clase = info.get("tipo_hito", "OPERATIVO")
            item_clase = QTableWidgetItem(clase)
            item_clase.setFlags(item_clase.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if clase == "BÁSICO":
                item_clase.setForeground(Qt.GlobalColor.darkBlue)
            self.table_cronogramas.setItem(row_idx, 1, item_clase)
            
            # 2. Selector de Proyecto
            cb_pry = QComboBox()
            cb_pry.addItems(lista_proyectos)
            cb_pry.setCurrentText(info.get("id_proyecto", ""))
            cb_pry.setProperty("hito_id", hito_id)
            cb_pry.setProperty("campo", "id_proyecto")
            cb_pry.currentTextChanged.connect(self.on_combo_matriz_cambiado)
            self.table_cronogramas.setCellWidget(row_idx, 2, cb_pry)
            
            # 3. Selector de Tipo Cronograma
            cb_crn = QComboBox()
            cb_crn.addItems(lista_cronos)
            cb_crn.setCurrentText(info.get("id_cronograma_tipo", ""))
            cb_crn.setProperty("hito_id", hito_id)
            cb_crn.setProperty("campo", "id_cronograma_tipo")
            cb_crn.currentTextChanged.connect(self.on_combo_matriz_cambiado)
            self.table_cronogramas.setCellWidget(row_idx, 3, cb_crn)
            
            # 4. Meta / Acción Principal (Columna Elástica)
            self.table_cronogramas.setItem(row_idx, 4, QTableWidgetItem(info.get("nombre_accion", "-")))
            
            # 5 y 6. Fechas
            self.table_cronogramas.setItem(row_idx, 5, QTableWidgetItem(info.get("fecha_inicio", "-")))
            self.table_cronogramas.setItem(row_idx, 6, QTableWidgetItem(info.get("fecha_fin", "-")))
            
            # 7. Métrica (Muestra 'fijo' si es básico, u horas si es operativo)
            if clase == "BÁSICO":
                item_metrica = QTableWidgetItem("FIJO NETO")
                item_metrica.setFlags(item_metrica.flags() & ~Qt.ItemFlag.ItemIsEditable)
                coste_calculado = info.get("coste_fijo_directo", 0.0)
            else:
                horas_est = info.get("horas_estimadas", 0.0)
                item_metrica = QTableWidgetItem(str(horas_est))
                coste_calculado = horas_est * tasa_hora_banco
            
            self.table_cronogramas.setItem(row_idx, 7, item_metrica)
            
            # 8. Coste Previsto Realizado (Editable si es Básico, bloqueado si es Operativo)
            item_coste = QTableWidgetItem(f"{coste_calculado:.2f}")
            if clase == "OPERATIVO":
                item_coste.setFlags(item_coste.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_cronogramas.setItem(row_idx, 8, item_coste)
            
            # 9. Resultado Esperado (Ingreso Previsto - Coste Neto)
            ingreso_previsto = info.get("ingreso_previsto_dinero", 0.0)
            resultado_esperado = ingreso_previsto - coste_calculado
            item_res = QTableWidgetItem(f"{resultado_esperado:.2f} €")
            item_res.setFlags(item_res.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if resultado_esperado < 0:
                item_res.setForeground(Qt.GlobalColor.red)
            else:
                item_res.setForeground(Qt.GlobalColor.darkGreen)
            self.table_cronogramas.setItem(row_idx, 9, item_res)
            
            # 10. Baja Atómica
            btn_del = QPushButton("🗑️")
            btn_del.clicked.connect(lambda checked=False, h_id=hito_id: self.ejecutar_baja_hito(h_id))
            self.table_cronogramas.setCellWidget(row_idx, 10, btn_del)
            
        for c in range(self.table_cronogramas.columnCount()):
            if c != 4:
                self.table_cronogramas.resizeColumnToContents(c)
                
        self.table_cronogramas.setSortingEnabled(True)
        self.table_cronogramas.blockSignals(False)

    def on_celda_matriz_modificada(self, row, col):
        item_id = self.table_cronogramas.item(row, 0)
        if not item_id: return
        hito_id = item_id.text()
        
        mapa_columnas = {4: "nombre_accion", 5: "fecha_inicio", 6: "fecha_fin", 7: "horas_estimadas", 8: "coste_fijo_directo"}
        if col not in mapa_columnas: return
        campo = mapa_columnas[col]
        
        item_modificado = self.table_cronogramas.item(row, col)
        if not item_modificado: return
        valor = item_modificado.text().strip()
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        if hito_id in master_data.get("hitos_instanciados", {}):
            clase = master_data["hitos_instanciados"][hito_id].get("tipo_hito", "OPERATIVO")
            
            if campo in ["horas_estimadas", "coste_fijo_directo"]:
                try: valor = float(valor.replace(",", "."))
                except ValueError: valor = 0.0
            
            # Seguridad cruzada: Evitar modificar horas a un hito básico en la celda
            if campo == "horas_estimadas" and clase == "BÁSICO":
                return
                
            master_data["hitos_instanciados"][hito_id][campo] = valor
            
            # Sincronización del legado de presupuesto asignado por compatibilidad de módulos viejos
            if clase == "OPERATIVO" and campo == "horas_estimadas":
                tasa = 25.0
                if self.parent_window:
                    tasa_b = self.parent_window.calcular_tasa_real_banco_provisional(None)
                    if tasa_b > 0: tasa = tasa_b
                master_data["hitos_instanciados"][hito_id]["presupuesto_asignado"] = valor * tasa
            elif clase == "BÁSICO" and campo == "coste_fijo_directo":
                master_data["hitos_instanciados"][hito_id]["presupuesto_asignado"] = valor

            self.core._save_json(self.core.cronogramas_path, master_data)
            if self.parent_window:
                self.parent_window.actualizar_todo()

    def on_combo_matriz_cambiado(self, texto):
        combo = self.sender()
        if not combo: return
        hito_id = combo.property("hito_id")
        campo = combo.property("campo")
        if not hito_id or not campo: return
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        if hito_id in master_data.get("hitos_instanciados", {}):
            master_data["hitos_instanciados"][hito_id][campo] = texto
            self.core._save_json(self.core.cronogramas_path, master_data)
            if self.parent_window:
                self.parent_window.actualizar_todo()

    def ejecutar_alta_hito(self):
        accion = self.in_add_accion.text().strip()
        valor_variable_str = self.in_add_horas_o_coste.text().strip()
        ingreso_str = self.in_add_ingreso.text().strip()
        
        if not accion:
            QMessageBox.warning(self, "Validación", "La meta u objetivo del hito no puede estar vacía.")
            return
            
        try: valor_num = float(valor_variable_str.replace(",", ".")) if valor_variable_str else 0.0
        except ValueError: valor_num = 0.0
        
        try: ingreso = float(ingreso_str.replace(",", ".")) if ingreso_str else 0.0
        except ValueError: ingreso = 0.0
        
        proj_id = self.combo_add_proyecto.currentData()
        crono_id = self.combo_add_crono.currentData()
        es_basico = self.check_tipo_basico.isChecked()
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        hitos = master_data.setdefault("hitos_instanciados", {})
        
        idx = len(hitos) + 1
        nuevo_id = f"HIT-NUCLEAR-2026-{idx:04d}"
        while nuevo_id in hitos:
            idx += 1
            nuevo_id = f"HIT-NUCLEAR-2026-{idx:04d}"
            
        # Construcción híbrida según tipo de hito
        hitos[nuevo_id] = {
            "tipo_hito": "BÁSICO" if es_basico else "OPERATIVO",
            "id_proyecto": proj_id,
            "id_cronograma_tipo": crono_id,
            "id_hito_referencia": nuevo_id,
            "nombre_accion": accion,
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fecha_inicio": self.in_fecha_inicio.text().strip(),
            "fecha_fin": "MENSUAL" if es_basico else self.in_fecha_fin.text().strip(),
            "horas_estimadas": 0.0 if es_basico else valor_num,
            "coste_fijo_directo": valor_num if es_basico else 0.0,
            "ingreso_previsto_dinero": ingreso,
            "estado": "PLANIFICADO",
            "prioridad": self.combo_add_prioridad.currentText(),
            "impactos_recibidos": {"tiempos": [], "finanzas": []}
        }
        
        # Sincronización del campo de compatibilidad heredado
        if es_basico:
            hitos[nuevo_id]["presupuesto_asignado"] = valor_num
        else:
            tasa = master_data.get("configuracion", {}).get("precio_hora_default", 25.0)
            if self.parent_window:
                tasa_b = self.parent_window.calcular_tasa_real_banco_provisional(None)
                if tasa_b > 0: tasa = tasa_b
            hitos[nuevo_id]["presupuesto_asignado"] = valor_num * tasa
        
        self.core._save_json(self.core.cronogramas_path, master_data)
        
        self.in_add_accion.clear()
        self.in_add_horas_o_coste.clear()
        self.in_add_ingreso.clear()
        
        if self.parent_window:
            self.parent_window.actualizar_todo()

    def ejecutar_baja_hito(self, hito_id):
        res = QMessageBox.question(self, "Baja de Hito Nuclear", f"¿Seguro que deseas eliminar irreversiblemente el hito nuclear {hito_id}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            master_data = self.core._load_json(self.core.cronogramas_path)
            if hito_id in master_data.get("hitos_instanciados", {}):
                del master_data["hitos_instanciados"][hito_id]
                self.core._save_json(self.core.cronogramas_path, master_data)
                if self.parent_window:
                    self.parent_window.actualizar_todo()