#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco GUI - Sistema de Control Operativo y Cronogramas Existenciales
Ubicación: SIPA/external/SIPAeco/sipaeco.py
Autor: Daniel Miñana Montero
Fecha: 2026-05-30
Versión: 2.4.0
Descripción: Culminación de la refactorización POO del ecosistema.
             Externalización de la pestaña de Impactos de Tiempo hacia módulo dedicado.
             Orquestación unificada de vistas modulares y preservación absoluta de
             lógicas de búsqueda en tiempo real, migración nuclear y pizarras de control.
"""

import sys
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QHeaderView, QApplication, QLineEdit, 
                             QFrame, QMessageBox, QComboBox, QGroupBox, QLayout)
from PySide6.QtCore import Qt, QPoint

# Servicio unificado core de SIPA
from core.services.sesipaeco_core import SESIPAecoCore

# Importación de la suite completa de submódulos refactorizados a POO
from views.calendar_view import CalendarioSemanaTab
from views.report_view import InformesDocsTab
from views.hitos_view import HitosTab
from views.tiempo_view import TiempoTab
from views.finanzas_view import FinanzasTab

class ClickableFrame(QFrame):
    """Contenedor genérico que emite una señal simulada al hacer clic."""
    def __init__(self, callback, *args, **kwargs):
        super().__init__(args, **kwargs)
        self.callback = callback
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()
        super().mousePressEvent(event)


class DraggableHitoBlock(QFrame):
    """Bloque de hito interactivo que permite arrastre vertical libre en la vista diaria."""
    def __init__(self, hito_id, hito_nombre, bg_color, text_color, parent=None):
        super().__init__(parent)
        self.hito_id = hito_id
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {text_color};
                border-radius: 4px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        
        lbl_id = QLabel(f"<b>🔒 {hito_id}</b>")
        lbl_id.setStyleSheet(f"color: {text_color}; border: none; font-size: 10px;")
        lbl_nom = QLabel(hito_nombre)
        lbl_nom.setStyleSheet("color: #0f172a; border: none; font-size: 9px;")
        
        layout.addWidget(lbl_id)
        layout.addWidget(lbl_nom)
        
        self.drag_start_position = QPoint()
        self.widget_start_y = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
            self.widget_start_y = self.geometry().y()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta_y = event.globalPosition().toPoint().y() - self.drag_start_position.y()
            nueva_y = self.widget_start_y + delta_y
            
            nueva_y = max(0, min(nueva_y, 24 * 40 - self.height()))
            ajuste_hora = round(nueva_y / 40) * 40
            self.move(self.geometry().x(), ajuste_hora)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)


class SIPAecoWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SIPAeco — Consola de Control de Hitos e Impactos")
        self.setMinimumSize(1024, 720) 
        self.resize(1280, 800)

        self.core = SESIPAecoCore()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        
        self.fecha_pivote = datetime.now()
        self.dias_map_es = {
            0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 
            4: "Viernes", 5: "Sábado", 6: "Domingo"
        }
        
        self.asegurar_y_migrar_estructura_nuclear()
        self.init_header()
        
        # Contenedor de Pestañas Principal
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(False)
        self.tabs.currentChanged.connect(self.ejecutar_filtrado_global)
        self.main_layout.addWidget(self.tabs)
        
        # Inicialización del ecosistema de pestañas modulares POO (Orden Estricto Consolidado)
        self.init_tab_calendario_poo()      # Pestaña 1 (Index 0)
        self.init_tab_informes_docs()       # Pestaña 2 (Index 1)
        self.init_tab_planificacion_poo()   # Pestaña 3 (Index 2)
        self.init_tab_tiempo_poo()          # Pestaña 4 (Index 3) - ¡Nueva bala externalizada!
        self.init_tab_finanzas_poo()        # Pestaña 5 (Index 4)
        self.init_tab_config_catalogos()    # Pestaña 6 (Index 5)
        
        self.tabs.setCurrentIndex(0)
        
        self.actualizar_todo()
        self.cargar_datos_catalogos()

    def asegurar_y_migrar_estructura_nuclear(self):
        master_data = self.core._load_json(self.core.cronogramas_path)
        if "catalogos" in master_data and "hitos_instanciados" in master_data:
            return

        print("⚠️ Detectado formato antiguo. Iniciando migración nuclear segura de registros...")
        nuevo_json = {
            "catalogos": {"proyectos": {}, "cronogramas_tipos": {}, "hitos_reutilizables": {}},
            "hitos_instanciados": {}
        }
        
        mapa_proyectos, mapa_cronos, mapa_hitos_ref = {}, {}, {}
        contador_proy, contador_crn, contador_ref, contador_nuclear = 1, 1, 1, 1
        
        cronogramas_viejos = master_data.get("cronogramas", {})
        for crono_id_viejo, info_crono in cronogramas_viejos.items():
            if crono_id_viejo not in mapa_cronos:
                id_crn = f"CRN-{contador_crn:03d}"
                nuevo_json["catalogos"]["cronogramas_tipos"][id_crn] = {
                    "codigo": crono_id_viejo.upper(),
                    "descripcion": info_crono.get("descripcion", f"Cronograma {crono_id_viejo}")
                }
                mapa_cronos[crono_id_viejo] = id_crn
                contador_crn += 1
            
            id_cronograma_maestro = mapa_cronos[crono_id_viejo]
            for hito_viejo in info_crono.get("hitos", []):
                nombre_completo = hito_viejo.get("nombre", "Hito sin nombre")
                proyecto_nombre = hito_viejo.get("proyecto", "SIPAeco")
                
                if proyecto_nombre not in mapa_proyectos:
                    id_pry = f"PRY-{contador_proy:03d}"
                    nuevo_json["catalogos"]["proyectos"][id_pry] = {
                        "nombre": proyecto_nombre,
                        "descripcion": f"Proyecto {proyecto_nombre}"
                    }
                    mapa_proyectos[proyecto_nombre] = id_pry
                    contador_proy += 1
                
                id_proyecto_maestro = mapa_proyectos[proyecto_nombre]
                if nombre_completo not in mapa_hitos_ref:
                    id_ref = f"HIT-REF-{contador_ref:04d}"
                    nuevo_json["catalogos"]["hitos_reutilizables"][id_ref] = {"nombre": nombre_completo}
                    mapa_hitos_ref[nombre_completo] = id_ref
                    contador_ref += 1
                
                id_referencia_maestro = mapa_hitos_ref[nombre_completo]
                id_nuclear = hito_viejo.get("id", f"HIT-NUCLEAR-2026-{contador_nuclear:04d}").upper()
                horas = hito_viejo.get("horas_estimadas", hito_viejo.get("presupuesto_tiempo_estimado_horas", 0.0))
                fecha_fin = hito_viejo.get("fecha_fin", hito_viejo.get("fecha_limite_objetivo", ""))
                
                nuevo_json["hitos_instanciados"][id_nuclear] = {
                    "id_proyecto": id_proyecto_maestro,
                    "id_cronograma_tipo": id_cronograma_maestro,
                    "id_hito_referencia": id_referencia_maestro,
                    "nombre_accion": nombre_completo,
                    "fecha_inicio": hito_viejo.get("fecha_inicio", ""),
                    "fecha_fin": fecha_fin,
                    "horas_estimadas": float(horas),
                    "presupuesto_asignado": hito_viejo.get("presupuesto_asignado", float(horas) * 25.0),
                    "estado": hito_viejo.get("estado", "PLANIFICADO").upper(),
                    "prioridad": hito_viejo.get("prioridad", "3 - MEDIA").upper(),
                    "repetitivo": hito_viejo.get("repetitivo", False),
                    "frecuencia": hito_viejo.get("frecuencia", None),
                    "dias_ciclo": hito_viejo.get("dias_ciclo", [])
                }
                contador_nuclear += 1

        self.core._save_json(self.core.cronogramas_path, nuevo_json)
        print(f"✅ Migración estructural completada con éxito. {contador_nuclear - 1} registros blindados.")

    def init_header(self):
        header = QHBoxLayout()
        title_label = QLabel(f"<b>SIPAeco v2.4.0</b> | Terminal de Gestión de <b>{self.core.propietario}</b>")
        title_label.setStyleSheet("font-size: 14px;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar texto en tabla activa...")
        self.search_input.setFixedWidth(320)
        self.search_input.setStyleSheet("""
            QLineEdit { padding: 4px 8px; border: 1px solid #cbd5e1; border-radius: 4px; background-color: #ffffff; }
            QLineEdit:focus { border: 1px solid #0969da; }
        """)
        self.search_input.textChanged.connect(self.ejecutar_filtrado_global)
        
        self.btn_refresh = QPushButton("🔄 Sincronizar Datos General")
        self.btn_refresh.clicked.connect(self.actualizar_todo)
        
        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(self.search_input)
        header.addWidget(self.btn_refresh)
        self.main_layout.addLayout(header)

    def init_tab_calendario_poo(self):
        self.tab_calendario = CalendarioSemanaTab(self.core, self)
        self.tabs.addTab(self.tab_calendario, "📅 Calendario y Disponibilidad")

    def init_tab_informes_docs(self):
        self.tab_informes = InformesDocsTab(self.core, self)
        self.tabs.addTab(self.tab_informes, "📋 Informes y Documentación")

    def combo_filter_proyecto_text(self):
        if hasattr(self, 'combo_filtro_proyecto'):
            return self.combo_filtro_proyecto.currentText()
        return "TODOS"

    def init_tab_planificacion_poo(self):
        self.tab_planificacion = HitosTab(self.core, self)
        self.tabs.addTab(self.tab_planificacion, "📋 Matriz de Hitos")

    # =====================================================================
    # PESTAÑA 4: IMPACTOS DE TIEMPO (POO EXTERNALIZADO)
    # =====================================================================
    def init_tab_tiempo_poo(self):
        """Instancia el módulo de control de impactos extraído a tiempo_view.py"""
        self.tab_tiempo = TiempoTab(self.core, self)
        self.tabs.addTab(self.tab_tiempo, "⏱️ Impactos de Tiempo")

    def init_tab_finanzas_poo(self):
        self.tab_finanzas = FinanzasTab(self.core, self)
        self.tabs.addTab(self.tab_finanzas, "💰 Flujo de Caja")

    def init_tab_config_catalogos(self):
        self.tab_catalogos = QWidget()
        layout = QHBoxLayout(self.tab_catalogos)
        layout.setContentsMargins(10, 10, 10, 10)
        
        box_pry = QGroupBox("📁 Catálogo Maestro de Proyectos Activos")
        ly_pry = QVBoxLayout(box_pry)
        self.table_cat_proyectos = QTableWidget()
        self.table_cat_proyectos.setColumnCount(2)
        self.table_cat_proyectos.setHorizontalHeaderLabels(["ID Proyecto", "Nombre de Proyecto"])
        self.configurar_propiedades_tabla(self.table_cat_proyectos)
        self.table_cat_proyectos.cellChanged.connect(self.on_celda_catalogo_proyecto_cambiada)
        ly_pry.addWidget(self.table_cat_proyectos)
        layout.addWidget(box_pry, stretch=1)
        
        box_crn = QGroupBox("⚙️ Clasificación de Cronogramas Tipos")
        ly_crn = QVBoxLayout(box_crn)
        self.table_cat_cronos = QTableWidget()
        self.table_cat_cronos.setColumnCount(2)
        self.table_cat_cronos.setHorizontalHeaderLabels(["ID Crono Tipo", "Código Clasificador"])
        self.configurar_propiedades_tabla(self.table_cat_cronos)
        self.table_cat_cronos.cellChanged.connect(self.on_celda_catalogo_crono_cambiada)
        ly_crn.addWidget(self.table_cat_cronos)
        layout.addWidget(box_crn, stretch=1)
        
        self.tabs.addTab(self.tab_catalogos, "⚙️ Catálogos y Configuración")

    def cargar_datos_catalogos(self):
        master_data = self.core._load_json(self.core.cronogramas_path)
        catalogos = master_data.get("catalogos", {})
        self.renderizar_catalogos_maestros(catalogos)

    def renderizar_catalogos_maestros(self, catalogos):
        self.table_cat_proyectos.blockSignals(True)
        self.table_cat_proyectos.setRowCount(0)
        for r, (p_id, p_info) in enumerate(catalogos.get("proyectos", {}).items()):
            self.table_cat_proyectos.insertRow(r)
            it_id = QTableWidgetItem(p_id)
            it_id.setFlags(it_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_cat_proyectos.setItem(r, 0, it_id)
            self.table_cat_proyectos.setItem(r, 1, QTableWidgetItem(p_info.get("nombre", "")))
        self.table_cat_proyectos.blockSignals(False)
        
        self.table_cat_cronos.blockSignals(True)
        self.table_cat_cronos.setRowCount(0)
        for r, (c_id, c_info) in enumerate(catalogos.get("cronogramas_tipos", {}).items()):
            self.table_cat_cronos.insertRow(r)
            it_id = QTableWidgetItem(c_id)
            it_id.setFlags(it_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_cat_cronos.setItem(r, 0, it_id)
            self.table_cat_cronos.setItem(r, 1, QTableWidgetItem(c_info.get("codigo", "")))
        self.table_cat_cronos.blockSignals(False)

    def on_celda_catalogo_proyecto_cambiada(self, row, col):
        if col != 1: return
        item_id = self.table_cat_proyectos.item(row, 0)
        item_nombre = self.table_cat_proyectos.item(row, 1)
        if not item_id or not item_nombre: return
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        master_data["catalogos"]["proyectos"][item_id.text()]["nombre"] = item_nombre.text().strip()
        self.core._save_json(self.core.cronogramas_path, master_data)
        self.actualizar_todo()

    def on_celda_catalogo_crono_cambiada(self, row, col):
        if col != 1: return
        item_id = self.table_cat_cronos.item(row, 0)
        item_codigo = self.table_cat_cronos.item(row, 1)
        if not item_id or not item_codigo: return
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        master_data["catalogos"]["cronogramas_tipos"][item_id.text()]["codigo"] = item_codigo.text().strip().upper()
        self.core._save_json(self.core.cronogramas_path, master_data)
        self.actualizar_todo()

    def actualizar_todo(self):
        """Sincroniza y fuerza la renderización reactiva de todas las interfaces."""
        master_data = self.core._load_json(self.core.cronogramas_path)
        hitos = master_data.get("hitos_instanciados", {})
        catalogos = master_data.get("catalogos", {})

        # Sincronizar matriz de hitos externalizada
        if hasattr(self, 'tab_planificacion') and hasattr(self.tab_planificacion, 'renderizar_matriz_cronogramas'):
            self.tab_planificacion.renderizar_matriz_cronogramas(hitos, catalogos)

        # Sincronizar submódulo de impactos de tiempo (Bala 1) externalizado
        if hasattr(self, 'tab_tiempo') and hasattr(self.tab_tiempo, 'renderizar_impactos_tiempo'):
            self.tab_tiempo.renderizar_impactos_tiempo(hitos, catalogos)

        # Sincronizar submódulo financiero (Bala 2)
        if hasattr(self, 'tab_finanzas'):
            if hasattr(self.tab_finanzas, 'renderizar_flujo_caja'):
                self.tab_finanzas.renderizar_flujo_caja(hitos)
            elif hasattr(self.tab_finanzas, 'actualizar_datos'):
                self.tab_finanzas.actualizar_datos(hitos)

        # Sincronizar submódulo de calendario
        if hasattr(self, 'tab_calendario') and hasattr(self.tab_calendario, 'renderizar_calendario_semanal'):
            self.tab_calendario.renderizar_calendario_semanal()

        # Sincronizar submódulo de Informes y Documentación (.md)
        if hasattr(self, 'tab_informes'):
            self.tab_informes.actualizar_combos_catalogos()
            self.tab_informes.renderizar_pizarra_informes()

        if hasattr(self, 'table_cat_proyectos') and hasattr(self, 'table_cat_cronos'):
            self.renderizar_catalogos_maestros(catalogos)

    def ejecutar_filtrado_global(self):
        texto = self.search_input.text().lower().strip()
        idx_pestana = self.tabs.currentIndex()
        
        # Filtro en la pestaña Hitos (Index 2)
        if idx_pestana == 2 and hasattr(self, 'tab_planificacion'):
            tabla = self.tab_planificacion.table_cronogramas
            for r in range(tabla.rowCount()):
                coincide = False
                for c in range(tabla.columnCount()):
                    widget = tabla.cellWidget(r, c)
                    txt_celda = widget.currentText() if isinstance(widget, QComboBox) else (tabla.item(r, c).text() if tabla.item(r, c) else "")
                    if texto in txt_celda.lower():
                        coincide = True
                        break
                tabla.setRowHidden(r, not coincide)
                
        # Filtro en la pestaña Impactos de Tiempo (Index 3)
        elif idx_pestana == 3 and hasattr(self, 'tab_tiempo'):
            tabla = self.tab_tiempo.table_impactos_tiempo
            for r in range(tabla.rowCount()):
                coincide = False
                for c in range(tabla.columnCount()):
                    item = tabla.item(r, c)
                    txt_celda = item.text() if item else ""
                    if texto in txt_celda.lower():
                        coincide = True
                        break
                tabla.setRowHidden(r, not coincide)

    def configurar_propiedades_tabla(self, tabla: QTableWidget):
        tabla.setSortingEnabled(True)
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SIPAecoWindow()
    window.show()
    sys.exit(app.exec())