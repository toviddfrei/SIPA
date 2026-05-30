#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco - Módulo de Gestión de Impactos de Tiempo (Balas Operativas)
Ubicación: SIPA/external/SIPAeco/views/tiempo_view.py
Descripción: Vista POO externalizada para el control y consumo de impactos de tiempo.
             Representa el esfuerzo operativo diario vinculado a los Hitos Nucleares.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

class TiempoTab(QWidget):
    def __init__(self, core, parent_window=None):
        super().__init__(parent_window)
        self.core = core
        self.parent_window = parent_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabla de Impactos Operativos
        self.table_impactos_tiempo = QTableWidget()
        self.table_impactos_tiempo.setColumnCount(6)
        self.table_impactos_tiempo.setHorizontalHeaderLabels([
            "ID Hito Vincular", "Proyecto", "Acción Operativa / Impacto", "Horas Consumidas", "Estado", "Prioridad"
        ])
        
        # Configuración de propiedades de la tabla
        self.table_impactos_tiempo.setSortingEnabled(True)
        header = self.table_impactos_tiempo.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.table_impactos_tiempo)

    def renderizar_impactos_tiempo(self, hitos, catalogos):
        """Fuerza el repintado reactivo de los impactos analizando el almacén JSON."""
        self.table_impactos_tiempo.blockSignals(True)
        self.table_impactos_tiempo.setSortingEnabled(False)
        self.table_impactos_tiempo.setRowCount(0)
        
        proyectos_map = catalogos.get("proyectos", {})
        
        for r, (h_id, info) in enumerate(hitos.items()):
            self.table_impactos_tiempo.insertRow(r)
            
            # Vinculación inmutable al ID Nuclear
            item_id = QTableWidgetItem(h_id)
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_impactos_tiempo.setItem(r, 0, item_id)
            
            # Resolución de nombre del proyecto
            id_pry = info.get("id_proyecto", "")
            nombre_pry = proyectos_map.get(id_pry, {}).get("nombre", id_pry)
            item_pry = QTableWidgetItem(nombre_pry)
            item_pry.setFlags(item_pry.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_impactos_tiempo.setItem(r, 1, item_pry)
            
            # Datos de la acción operativa (bala)
            self.table_impactos_tiempo.setItem(r, 2, QTableWidgetItem(info.get("nombre_accion", "-")))
            self.table_impactos_tiempo.setItem(r, 3, QTableWidgetItem(str(info.get("horas_estimadas", 0.0))))
            self.table_impactos_tiempo.setItem(r, 4, QTableWidgetItem(info.get("estado", "PLANIFICADO")))
            self.table_impactos_tiempo.setItem(r, 5, QTableWidgetItem(info.get("prioridad", "3 - MEDIA")))
            
        self.table_impactos_tiempo.resizeColumnsToContents()
        self.table_impactos_tiempo.setSortingEnabled(True)
        self.table_impactos_tiempo.blockSignals(False)