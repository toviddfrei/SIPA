#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco View - Pestaña de Gestión de Informes y Documentación Markdown
Ubicación: SIPA/views/report_view.py
Autor: Daniel Miñana Montero
Descripción: Componente de interfaz de usuario desacoplado en POO que maneja
             la pizarra de tarjetas interactivas de documentación (La Ficha del Detective).
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QScrollArea, QFrame, 
                             QGroupBox, QLineEdit, QTextEdit, QGridLayout)
from PySide6.QtCore import Qt

from core.services.sesipaeco_report import SESIPAecoReportService


class ClickableFrame(QFrame):
    """Contenedor genérico que emite una señal simulada al hacer clic."""
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()
        super().mousePressEvent(event)


class InformesDocsTab(QWidget):
    def __init__(self, core_maestro, parent_window, parent=None):
        super().__init__(parent)
        self.core = core_maestro
        self.parent_window = parent_window  # Referencia para disparar actualizaciones globales
        
        # Instanciar el servicio lógico
        self.service = SESIPAecoReportService(self.core)
        
        self.estilos_estados = {
            "PLANIFICADO": {"bg": "#f1f5f9", "border": "#cbd5e1"},
            "EN_PROCESO":  {"bg": "#fef3c7", "border": "#fcd34d"},
            "COMPLETADO":  {"bg": "#e6ffed", "border": "#acf2bd"},
            "BLOQUEADO":   {"bg": "#fee2e2", "border": "#fecaca"}
        }
        
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(8)
        
        # --- BARRA SUPERIOR DE CONTROL ---
        barra_filtros = QHBoxLayout()
        
        lbl_filtro_proy = QLabel("<b>Filtrar Proyecto:</b>")
        self.combo_filtro_proyecto = QComboBox()
        self.combo_filtro_proyecto.addItem("TODOS")
        self.combo_filtro_proyecto.currentTextChanged.connect(self.renderizar_pizarra_informes)
        
        lbl_orden = QLabel("<b>Orden de Pizarra:</b>")
        self.combo_orden_pizarra = QComboBox()
        self.combo_orden_pizarra.addItems(["Por Prioridad (Crítica -> Baja)", "Por Estado"])
        self.combo_orden_pizarra.currentTextChanged.connect(self.renderizar_pizarra_informes)
        
        self.btn_recargar_pizarra = QPushButton("📋 Actualizar Pizarra")
        self.btn_recargar_pizarra.setStyleSheet("""
            QPushButton { padding: 4px 12px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; font-weight: 500; }
            QPushButton:hover { background-color: #f8fafc; border-color: #94a3b8; }
        """)
        self.btn_recargar_pizarra.clicked.connect(self.renderizar_pizarra_informes)
        
        barra_filtros.addWidget(lbl_filtro_proy)
        barra_filtros.addWidget(self.combo_filtro_proyecto)
        barra_filtros.addSpacing(15)
        barra_filtros.addWidget(lbl_orden)
        barra_filtros.addWidget(self.combo_orden_pizarra)
        barra_filtros.addStretch()
        barra_filtros.addWidget(self.btn_recargar_pizarra)
        
        layout_principal.addLayout(barra_filtros)
        
        # --- ÁREA CENTRAL DE LA PIZARRA (SCROLL) ---
        self.scroll_pizarra = QScrollArea()
        self.scroll_pizarra.setWidgetResizable(True)
        self.scroll_pizarra.setStyleSheet("QScrollArea { border: 1px solid #cbd5e1; border-radius: 6px; background-color: #f8fafc; }")
        
        self.contenedor_pizarra = QWidget()
        self.layout_tarjetas_pizarra = QVBoxLayout(self.contenedor_pizarra)
        self.layout_tarjetas_pizarra.setContentsMargins(10, 10, 10, 10)
        self.layout_tarjetas_pizarra.setSpacing(8)
        self.layout_tarjetas_pizarra.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_pizarra.setWidget(self.contenedor_pizarra)
        layout_principal.addWidget(self.scroll_pizarra)

    def actualizar_combos_catalogos(self):
        """Sincroniza el combo de filtrado con los proyectos reales del catálogo maestro."""
        self.combo_filtro_proyecto.blockSignals(True)
        proyecto_actual = self.combo_filtro_proyecto.currentText()
        
        self.combo_filtro_proyecto.clear()
        self.combo_filtro_proyecto.addItem("TODOS")
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        proyectos = master_data.get("catalogos", {}).get("proyectos", {})
        for p_id, p_info in proyectos.items():
            self.combo_filtro_proyecto.addItem(p_info.get("nombre", "SIN NOMBRE"))
            
        if self.combo_filtro_proyecto.findText(proyecto_actual) != -1:
            self.combo_filtro_proyecto.setCurrentText(proyecto_actual)
            
        self.combo_filtro_proyecto.blockSignals(False)

    def renderizar_pizarra_informes(self):
        """Motor dinámico de renderizado de la Pizarra de Documentación."""
        while self.layout_tarjetas_pizarra.count():
            child = self.layout_tarjetas_pizarra.takeAt(0)
            if child.widget(): 
                child.widget().deleteLater()

        proyecto_activo = self.combo_filtro_proyecto.currentText()
        criterio_orden = self.combo_orden_pizarra.currentText()
        
        hitos_pizarra = self.service.obtener_hitos_pizarra(proyecto_activo, criterio_orden)

        if not hitos_pizarra:
            lbl_vacio = QLabel("No se encontraron hitos para los filtros seleccionados.")
            lbl_vacio.setStyleSheet("color: #64748b; font-style: italic; padding: 10px;")
            self.layout_tarjetas_pizarra.addWidget(lbl_vacio)
            return

        for h in hitos_pizarra:
            tarjeta_completa = QFrame()
            tarjeta_completa.setFrameShape(QFrame.Shape.NoFrame)
            layout_completo = QVBoxLayout(tarjeta_completa)
            layout_completo.setContentsMargins(0, 0, 0, 0)
            layout_completo.setSpacing(0)

            # --- 1. CABECERA ---
            cabecera_tarjeta = ClickableFrame(lambda t_z=tarjeta_completa: self.conmutar_tarjeta_pizarra(t_z))
            estilo = self.estilos_estados.get(h["estado"], {"bg": "#f1f5f9", "border": "#cbd5e1"})
            cabecera_tarjeta.setStyleSheet(f"QFrame {{ background-color: {estilo['bg']}; border: 1px solid {estilo['border']}; border-radius: 6px; }}")
            
            layout_cabecera = QVBoxLayout(cabecera_tarjeta)
            layout_cabecera.setContentsMargins(12, 10, 12, 10)
            layout_cabecera.setSpacing(4)
            
            fila_cabecera = QHBoxLayout()
            lbl_id = QLabel(f"<b>🔒 {h['id']}</b> <font color='#64748b'>[{h['crono_codigo']} ➡️ {h['proyecto']}]</font>")
            lbl_id.setStyleSheet("font-size: 11px; border: none;")
            fila_cabecera.addWidget(lbl_id)
            fila_cabecera.addStretch()
            
            combo_prio = QComboBox()
            combo_prio.addItems(["1 - CRÍTICA", "2 - ALTA", "3 - MEDIA", "4 - BAJA"])
            combo_prio.setCurrentText(h["prioridad"])
            combo_prio.setStyleSheet("""
                QComboBox { font-size: 9px; font-weight: bold; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 3px; padding: 1px 4px; color: #334155; }
                QComboBox::drop-down { border: none; }
            """)
            combo_prio.currentTextChanged.connect(
                lambda val, h_id=h["id"]: self.on_cambio_directo_pizarra(h_id, "prioridad", val)
            )
            fila_cabecera.addWidget(combo_prio)
            
            combo_est = QComboBox()
            combo_est.addItems(["PLANIFICADO", "EN_PROCESO", "COMPLETADO", "BLOQUEADO"])
            combo_est.setCurrentText(h["estado"])
            
            color_txt = "#ffffff"
            color_bg = "#475569" if h["estado"]=="PLANIFICADO" else "#b45309" if h["estado"]=="EN_PROCESO" else "#1a7f37" if h["estado"]=="COMPLETADO" else "#991b1b"
            combo_est.setStyleSheet(f"""
                QComboBox {{ font-size: 9px; font-weight: bold; background-color: {color_bg}; color: {color_txt}; border-radius: 3px; padding: 1px 6px; }}
                QComboBox::drop-down {{ border: none; }}
            """)
            combo_est.currentTextChanged.connect(
                lambda val, h_id=h["id"]: self.on_cambio_directo_pizarra(h_id, "estado", val)
            )
            fila_cabecera.addWidget(combo_est)
            
            lbl_nombre = QLabel(h["nombre"])
            lbl_nombre.setStyleSheet("font-size: 13px; font-weight: 500; color: #0f172a; border: none; padding-top: 2px;")
            lbl_nombre.setWordWrap(True)
            
            fila_pie = QHBoxLayout()
            lbl_fechas = QLabel(f"📅 <b>Inicio:</b> {h['fecha_inicio']}   |   🏁 <b>Límite Objetivo:</b> {h['fecha_fin']}")
            lbl_fechas.setStyleSheet("font-size: 10px; color: #475569; border: none;")
            
            lbl_tiempo = QLabel(f"⏱️ {h['horas']} h estimadas (Clic para desplegar)")
            lbl_tiempo.setStyleSheet("font-size: 10px; font-weight: bold; color: #0f172a; border: none;")
            
            fila_pie.addWidget(lbl_fechas)
            fila_pie.addStretch()
            fila_pie.addWidget(lbl_tiempo)
            
            layout_cabecera.addLayout(fila_cabecera)
            layout_cabecera.addWidget(lbl_nombre)
            layout_cabecera.addLayout(fila_pie)
            
            layout_completo.addWidget(cabecera_tarjeta)

            # --- 2. CONTENEDOR EXPANDIBLE (La Ficha del Detective) ---
            zona_expandible = QFrame()
            zona_expandible.setStyleSheet("""
                QFrame { 
                    background-color: #ffffff; 
                    border: 1px solid #cbd5e1; 
                    border-top: none; 
                    border-bottom-left-radius: 6px; 
                    border-bottom-right-radius: 6px; 
                }
            """)
            zona_expandible.setVisible(False)
            
            layout_expansion = QVBoxLayout(zona_expandible)
            layout_expansion.setContentsMargins(15, 12, 15, 12)
            layout_expansion.setSpacing(10)
            
            panel_detective = QFrame()
            panel_detective.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; } QLabel { border: none; }")
            layout_detective = QGridLayout(panel_detective)
            layout_detective.setContentsMargins(10, 8, 10, 8)
            layout_detective.setSpacing(8)
            
            lbl_det_tiempo = QLabel(f"⏱️ <b>Masa Tiempo:</b> {h['horas']}h vistas | <b>Real:</b> 0h <font color='#16a34a'>(0h desc)</font>")
            lbl_det_tiempo.setStyleSheet("font-size: 11px; color: #334155;")
            
            lbl_det_caja = QLabel("💰 <b>Masa Caja:</b> 0.00 € previstos | <b>Real:</b> 0.00 € <font color='#16a34a'>(0.00 € desviac.)</font>")
            lbl_det_caja.setStyleSheet("font-size: 11px; color: #334155;")
            
            lbl_det_crono = QLabel(f"⏳ <b>Cuenta atrás:</b> Desde {h['fecha_inicio']} hasta {h['fecha_fin']} <font color='#0969da'><b>[Activo]</b></font>")
            lbl_det_crono.setStyleSheet("font-size: 11px; color: #334155;")
            
            layout_detective.addWidget(lbl_det_tiempo, 0, 0)
            layout_detective.addWidget(lbl_det_caja, 0, 1)
            layout_detective.addWidget(lbl_det_crono, 1, 0, 1, 2)
            
            layout_expansion.addWidget(panel_detective)
            
            # BLOQUE A: Gestión de Ficheros (.md)
            bloque_ficheros = QGroupBox("📄 Bloque de Documentación e Informes (.md)")
            bloque_ficheros.setStyleSheet("QGroupBox { font-weight: bold; color: #1e293b; }")
            layout_bl_a = QVBoxLayout(bloque_ficheros)
            layout_bl_a.setContentsMargins(10, 8, 10, 8)
            layout_bl_a.setSpacing(6)
            
            lbl_info_doc = QLabel("<b>Ficheros vinculados a este hito:</b>")
            lbl_info_doc.setStyleSheet("font-size: 11px; color: #475569; border: none;")
            layout_bl_a.addWidget(lbl_info_doc)
            
            lista_ficheros_layout = QVBoxLayout()
            lista_ficheros_layout.setSpacing(4)
            layout_bl_a.addLayout(lista_ficheros_layout)
            
            def eliminar_fichero_vinculo(f_path, hito_ref=h):
                if f_path in hito_ref["ficheros"]:
                    hito_ref["ficheros"].remove(f_path)
                    self.service.guardar_ficheros_hito(hito_ref["id"], hito_ref["ficheros"])
                    self.renderizar_pizarra_informes()
            
            for f in h.get("ficheros", []):
                fil_fich = QHBoxLayout()
                lbl_f = QLabel(f"📎 <code>{f}</code>")
                lbl_f.setStyleSheet("font-size: 11px; border: none;")
                btn_del_f = QPushButton("✕")
                btn_del_f.setFixedSize(16, 16)
                btn_del_f.setStyleSheet("QPushButton { background-color: #fee2e2; color: #991b1b; border: none; border-radius: 2px; font-size: 9px; font-weight: bold; } QPushButton:hover { background-color: #fca5a5; }")
                btn_del_f.clicked.connect(lambda chk=False, path=f: eliminar_fichero_vinculo(path))
                fil_fich.addWidget(lbl_f)
                fil_fich.addWidget(btn_del_f)
                fil_fich.addStretch()
                lista_ficheros_layout.addLayout(fil_fich)
                
            if not h.get("ficheros", []):
                lbl_f_vacio = QLabel("No hay documentos vinculados a este hito nuclear.")
                lbl_f_vacio.setStyleSheet("font-size: 11px; color: #64748b; font-style: italic; border: none;")
                lista_ficheros_layout.addWidget(lbl_f_vacio)
                
            ly_inj_f = QHBoxLayout()
            in_nuevo_f = QLineEdit()
            in_nuevo_f.setPlaceholderText("Nombre del fichero o ruta (ej: hito_seguridad.md)...")
            in_nuevo_f.setStyleSheet("QLineEdit { padding: 3px; font-size: 11px; }")
            btn_inj_f = QPushButton("Vincular Fichero")
            btn_inj_f.setStyleSheet("QPushButton { font-size: 11px; background-color: #f1f5f9; border: 1px solid #cbd5e1; padding: 3px 8px; } QPushButton:hover { background-color: #e2e8f0; }")
            
            def inyectar_fichero_vinculo(input_widget=in_nuevo_f, hito_ref=h):
                path = input_widget.text().strip()
                if path:
                    if path not in hito_ref["ficheros"]:
                        hito_ref["ficheros"].append(path)
                        self.service.guardar_ficheros_hito(hito_ref["id"], hito_ref["ficheros"])
                        self.renderizar_pizarra_informes()
                        
            btn_inj_f.clicked.connect(inyectar_fichero_vinculo)
            ly_inj_f.addWidget(in_nuevo_f)
            ly_inj_f.addWidget(btn_inj_f)
            layout_bl_a.addLayout(ly_inj_f)
            
            layout_expansion.addWidget(bloque_ficheros)
            
            # BLOQUE B: Notas y Seguimiento Libre reactivo al desenfoque (Focus Out)
            bloque_notes = QGroupBox("📝 Notas y Seguimiento")
            bloque_notes.setStyleSheet("QGroupBox { font-weight: bold; color: #1e293b; }")
            layout_bl_b = QVBoxLayout(bloque_notes)
            layout_bl_b.setContentsMargins(10, 8, 10, 8)
            
            txt_notas = QTextEdit()
            txt_notas.setPlainText(h.get("notes", "Sin notas registradas."))
            txt_notas.setStyleSheet("QTextEdit { font-size: 11px; border: 1px solid #cbd5e1; background-color: #ffffff; }")
            
            # Al perder el foco se guarda automáticamente la nota sin interrumpir al usuario
            txt_notas.focusOutEvent = lambda event, h_id=h["id"], widget=txt_notas: [
                self.service.guardar_notas_hito(h_id, widget.toPlainText()),
                QTextEdit.focusOutEvent(widget, event)
            ]
            layout_bl_b.addWidget(txt_notas)
            
            layout_expansion.addWidget(bloque_notes)
            
            layout_completo.addWidget(zona_expandible)
            tarjeta_completa.setProperty("zona_expandible", zona_expandible)
            
            self.layout_tarjetas_pizarra.addWidget(tarjeta_completa)

    def conmutar_tarjeta_pizarra(self, tarjeta_widget):
        zona = tarjeta_widget.property("zona_expandible")
        if zona:
            zona.setVisible(not zona.isVisible())

    def on_cambio_directo_pizarra(self, hito_id, campo, nuevo_valor):
        if self.service.actualizar_campo_hito(hito_id, campo, nuevo_valor):
            self.parent_window.actualizar_todo()