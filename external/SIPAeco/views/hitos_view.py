#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco - Módulo de Gestión Relacional de Hitos Nucleares
Ubicación: SIPA/external/SIPAeco/views/hitos_view.py
Descripción: Vista POO externalizada para el control operativo de hitos.
             Implementa IDs nucleares únicos para evitar sobreescrituras y
             establece las bases para la relación 1:N con impactos de tiempo.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView, 
                             QLineEdit, QMessageBox, QComboBox, QCheckBox, QGroupBox, 
                             QGridLayout)
from PySide6.QtCore import Qt
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
        
        self.combo_add_proyecto = QComboBox()
        self.combo_add_crono = QComboBox()
        self.in_add_accion = QLineEdit()
        self.in_add_accion.setPlaceholderText("Definición del punto de cruce u objetivo del hito...")
        
        self.combo_add_prioridad = QComboBox()
        self.combo_add_prioridad.addItems(["1 - CRÍTICA", "2 - ALTA", "3 - MEDIA", "4 - BAJA"])
        self.combo_add_prioridad.setCurrentText("3 - MEDIA")
        
        self.in_add_horas = QLineEdit()
        self.in_add_horas.setPlaceholderText("Horas estimadas iniciales")
        
        self.check_add_repetitivo = QCheckBox("Hito de Ciclo Repetitivo")
        self.combo_add_frecuencia = QComboBox()
        self.combo_add_frecuencia.addItems(["DIARIA", "SEMANAL", "MENSUAL"])
        self.combo_add_frecuencia.setEnabled(False)
        self.check_add_repetitivo.toggled.connect(self.combo_add_frecuencia.setEnabled)
        
        btn_inyectar = QPushButton("➕ Inyectar Hito Estratégico")
        btn_inyectar.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold; padding: 5px 15px;")
        btn_inyectar.clicked.connect(self.ejecutar_alta_hito)
        
        ly_alta.addWidget(QLabel("Proyecto vinculante:"), 0, 0)
        ly_alta.addWidget(self.combo_add_proyecto, 0, 1)
        ly_alta.addWidget(QLabel("Tipo Cronograma:"), 0, 2)
        ly_alta.addWidget(self.combo_add_crono, 0, 3)
        ly_alta.addWidget(QLabel("Meta / Punto Cruce:"), 0, 4)
        ly_alta.addWidget(self.in_add_accion, 0, 5)
        
        ly_alta.addWidget(QLabel("Prioridad Operativa:"), 1, 0)
        ly_alta.addWidget(self.combo_add_prioridad, 1, 1)
        ly_alta.addWidget(QLabel("Presupuesto Horas:"), 1, 2)
        ly_alta.addWidget(self.in_add_horas, 1, 3)
        ly_alta.addWidget(self.check_add_repetitivo, 1, 4)
        ly_alta.addWidget(self.combo_add_frecuencia, 1, 5)
        
        ly_alta.addWidget(btn_inyectar, 2, 5, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(group_alta)
        
        # Matriz de Hitos Nucleares
        self.table_cronogramas = QTableWidget()
        self.table_cronogramas.setColumnCount(10)
        self.table_cronogramas.setHorizontalHeaderLabels([
            "ID Hito Nuclear", "Proyecto Relacionado", "Crono Tipo", "Punto de Cruce / Objetivo", 
            "F. Inicio", "F. Fin", "Horas Acumuladas", "Estado", "Prioridad", "Controles"
        ])
        
        self.table_cronogramas.setSortingEnabled(True)
        header = self.table_cronogramas.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        self.table_cronogramas.cellChanged.connect(self.on_celda_matriz_modificada)
        layout.addWidget(self.table_cronogramas)

    def renderizar_matriz_cronogramas(self, hitos, catalogos):
        self.table_cronogramas.blockSignals(True)
        self.table_cronogramas.setSortingEnabled(False)
        self.table_cronogramas.setRowCount(0)
        
        # Cargar selectores dinámicos del formulario de inyección
        self.combo_add_proyecto.clear()
        for p_id, p_info in catalogos.get("proyectos", {}).items():
            self.combo_add_proyecto.addItem(f"{p_info.get('nombre')} ({p_id})", p_id)
            
        self.combo_add_crono.clear()
        for c_id, c_info in catalogos.get("cronogramas_tipos", {}).items():
            self.combo_add_crono.addItem(f"{c_info.get('codigo')} ({c_id})", c_id)
            
        lista_proyectos = sorted(list(catalogos.get("proyectos", {}).keys()))
        lista_cronos = sorted(list(catalogos.get("cronogramas_tipos", {}).keys()))
        lista_estados = ["PLANIFICADO", "EN_PROCESO", "COMPLETADO", "PROROGADO", "CANCELADO"]
        lista_prioridades = ["1 - CRÍTICA", "2 - ALTA", "3 - MEDIA", "4 - BAJA"]
        
        for row_idx, (hito_id, info) in enumerate(hitos.items()):
            self.table_cronogramas.insertRow(row_idx)
            
            # ID inmutable absoluto
            item_id = QTableWidgetItem(hito_id)
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_cronogramas.setItem(row_idx, 0, item_id)
            
            # Selector de Proyecto
            cb_pry = QComboBox()
            cb_pry.addItems(lista_proyectos)
            cb_pry.setCurrentText(info.get("id_proyecto", ""))
            cb_pry.setProperty("hito_id", hito_id)
            cb_pry.setProperty("campo", "id_proyecto")
            cb_pry.currentTextChanged.connect(self.on_combo_matriz_cambiado)
            self.table_cronogramas.setCellWidget(row_idx, 1, cb_pry)
            
            # Selector de Tipo Cronograma
            cb_crn = QComboBox()
            cb_crn.addItems(lista_cronos)
            cb_crn.setCurrentText(info.get("id_cronograma_tipo", ""))
            cb_crn.setProperty("hito_id", hito_id)
            cb_crn.setProperty("campo", "id_cronograma_tipo")
            cb_crn.currentTextChanged.connect(self.on_combo_matriz_cambiado)
            self.table_cronogramas.setCellWidget(row_idx, 2, cb_crn)
            
            # Campos directos de texto
            self.table_cronogramas.setItem(row_idx, 3, QTableWidgetItem(info.get("nombre_accion", "-")))
            self.table_cronogramas.setItem(row_idx, 4, QTableWidgetItem(info.get("fecha_inicio", "-")))
            self.table_cronogramas.setItem(row_idx, 5, QTableWidgetItem(info.get("fecha_fin", "-")))
            self.table_cronogramas.setItem(row_idx, 6, QTableWidgetItem(str(info.get("horas_estimadas", 0.0))))
            
            # Selector de Estado
            cb_est = QComboBox()
            cb_est.addItems(lista_estados)
            cb_est.setCurrentText(info.get("estado", "PLANIFICADO"))
            cb_est.setProperty("hito_id", hito_id)
            cb_est.setProperty("campo", "estado")
            cb_est.currentTextChanged.connect(self.on_combo_matriz_cambiado)
            self.table_cronogramas.setCellWidget(row_idx, 7, cb_est)
            
            # Selector de Prioridad
            cb_pri = QComboBox()
            cb_pri.addItems(lista_prioridades)
            cb_pri.setCurrentText(info.get("prioridad", "3 - MEDIA"))
            cb_pri.setProperty("hito_id", hito_id)
            cb_pri.setProperty("campo", "prioridad")
            cb_pri.currentTextChanged.connect(self.on_combo_matriz_cambiado)
            self.table_cronogramas.setCellWidget(row_idx, 8, cb_pri)
            
            # Botón de Eliminación Segura
            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar hito nuclear estratégico")
            btn_del.clicked.connect(lambda checked=False, h_id=hito_id: self.ejecutar_baja_hito(h_id))
            self.table_cronogramas.setCellWidget(row_idx, 9, btn_del)
            
        self.table_cronogramas.resizeColumnsToContents()
        self.table_cronogramas.setSortingEnabled(True)
        self.table_cronogramas.blockSignals(False)

    def on_celda_matriz_modificada(self, row, col):
        item_id = self.table_cronogramas.item(row, 0)
        if not item_id: return
        hito_id = item_id.text()
        
        mapa_columnas = {3: "nombre_accion", 4: "fecha_inicio", 5: "fecha_fin", 6: "horas_estimadas"}
        if col not in mapa_columnas: return
        campo = mapa_columnas[col]
        
        item_modificado = self.table_cronogramas.item(row, col)
        if not item_modificado: return
        valor = item_modificado.text().strip()
        
        if campo == "horas_estimadas":
            try: valor = float(valor.replace(",", "."))
            except ValueError: valor = 0.0
            
        master_data = self.core._load_json(self.core.cronogramas_path)
        if hito_id in master_data.get("hitos_instanciados", {}):
            master_data["hitos_instanciados"][hito_id][campo] = valor
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
        horas_str = self.in_add_horas.text().strip()
        if not accion:
            QMessageBox.warning(self, "Validación", "El objetivo/meta del hito nuclear no puede estar vacío.")
            return
            
        try: horas = float(horas_str.replace(",", ".")) if horas_str else 1.0
        except ValueError: horas = 1.0
        
        proj_id = self.combo_add_proyecto.currentData()
        crono_id = self.combo_add_crono.currentData()
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        hitos = master_data.setdefault("hitos_instanciados", {})
        
        idx = len(hitos) + 1
        nuevo_id = f"HIT-NUCLEAR-2026-{idx:04d}"
        while nuevo_id in hitos:
            idx += 1
            nuevo_id = f"HIT-NUCLEAR-2026-{idx:04d}"
            
        hitos[nuevo_id] = {
            "id_proyecto": proj_id,
            "id_cronograma_tipo": crono_id,
            "id_hito_referencia": nuevo_id,
            "nombre_accion": accion,
            "fecha_inicio": datetime.now().strftime("%Y-%m-%d"),
            "fecha_fin": datetime.now().strftime("%Y-%m-%d"),
            "horas_estimadas": horas,
            "presupuesto_asignado": horas * 25.0,
            "estado": "PLANIFICADO",
            "prioridad": self.combo_add_prioridad.currentText(),
            "repetitivo": self.check_add_repetitivo.isChecked(),
            "frecuencia": self.combo_add_frecuencia.currentText() if self.check_add_repetitivo.isChecked() else None,
            "dias_ciclo": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"] if self.check_add_repetitivo.isChecked() else []
        }
        
        self.core._save_json(self.core.cronogramas_path, master_data)
        self.in_add_accion.clear()
        self.in_add_horas.clear()
        if self.parent_window:
            self.parent_window.actualizar_todo()

    def ejecutar_baja_hito(self, hito_id):
        res = QMessageBox.question(self, "Baja de Hito", f"¿Seguro que deseas eliminar el hito nuclear estratégico {hito_id}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            master_data = self.core._load_json(self.core.cronogramas_path)
            if hito_id in master_data.get("hitos_instanciados", {}):
                del master_data["hitos_instanciados"][hito_id]
                self.core._save_json(self.core.cronogramas_path, master_data)
                if self.parent_window:
                    self.parent_window.actualizar_todo()