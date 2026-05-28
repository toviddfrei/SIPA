#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco GUI - Sistema de Control Operativo y Cronogramas Existenciales
Ubicación: SIPA/external/SIPAeco/sipaeco.py
Autor: Daniel Miñana Montero
Fecha: 2026-05-28
Versión: 1.99.4
Descripción: Reordenación de pestañas para establecer el Calendario dinámico e interactivo
             como la página principal (índice 0). Preparación del contenedor para el
             siguiente bloque de gestión de informes y documentación.
"""

import sys
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QHeaderView, QApplication, QLineEdit, 
                             QFrame, QMessageBox, QComboBox, QCheckBox, QGroupBox,
                             QButtonGroup, QStackedWidget, QGridLayout, QScrollArea)
from PySide6.QtCore import Qt, QDateTime, QPoint
from PySide6.QtGui import QColor

# Servicio unificado core de SIPA
from core.services.sesipaeco_core import SESIPAecoCore


class ClickableFrame(QFrame):
    """Contenedor genérico que emite una señal simulada al hacer clic."""
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            
            # Restricciones lógicas de movimiento dentro de la pista horaria
            nueva_y = max(0, min(nueva_y, 24 * 40 - self.height()))
            
            # Efecto visual imán a tramos de hora
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
        self.resize(1450, 850)
        
        self.core = SESIPAecoCore()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Fecha de pivote operativa para el calendario
        self.fecha_pivote = datetime.now()
        
        # Mapeo de traducción de días de la semana de Python a Castellano
        self.dias_map_es = {
            0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 
            4: "Viernes", 5: "Sábado", 6: "Domingo"
        }
        
        self.init_header()
        
        # Contenedor de Pestañas Principal
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(False)
        self.tabs.currentChanged.connect(self.ejecutar_filtrado_global)
        self.main_layout.addWidget(self.tabs)
        
        # Inicialización de las zonas operativas en el NUEVO ORDEN PACTADO
        self.init_tab_calendario()           # Pestaña 1: Página Principal (Index 0)
        self.init_tab_informes_docs()        # Pestaña 2: Gestión de Informes y Markdown (Index 1)
        self.init_tab_planificacion()        # Pestaña 3: Planificación de Hitos (Index 2)
        self.init_tab_tiempo()               # Pestaña 4: Impactos de Tiempo (Bala 1) (Index 3)
        self.init_tab_finanzas()             # Pestaña 5: Flujo de Caja (Bala 2) (Index 4)
        
        # Asegurar foco inicial en la pestaña estrella
        self.tabs.setCurrentIndex(0)
        
        # Carga y sincronización inicial de las estructuras
        self.actualizar_todo()

    def init_header(self):
        header = QHBoxLayout()
        title_label = QLabel(f"<b>SIPAeco v1.99.4</b> | Terminal de Gestión de <b>{self.core.propietario}</b>")
        title_label.setStyleSheet("font-size: 14px;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar texto en tabla actual...")
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

    # =====================================================================
    # PESTAÑA 1: CALENDARIO DINÁMICO (PÁGINA PRINCIPAL)
    # =====================================================================
    def init_tab_calendario(self):
        self.tab_calendario = QWidget()
        layout_principal_cal = QHBoxLayout(self.tab_calendario)
        layout_principal_cal.setContentsMargins(5, 5, 5, 5)
        
        container_izquierdo = QWidget()
        layout_izq = QVBoxLayout(container_izquierdo)
        layout_izq.setContentsMargins(0, 0, 0, 0)
        
        barra_vistas = QHBoxLayout()
        
        self.btn_time_prev = QPushButton("◀ Anterior")
        self.btn_time_today = QPushButton("📅 Hoy")
        self.btn_time_next = QPushButton("Siguiente ▶")
        
        for btn_nav in [self.btn_time_prev, self.btn_time_today, self.btn_time_next]:
            btn_nav.setStyleSheet("""
                QPushButton { padding: 4px 10px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; font-weight: 500; }
                QPushButton:hover { background-color: #f8fafc; border-color: #94a3b8; }
            """)
            
        self.btn_time_prev.clicked.connect(lambda: self.paginar_tiempo(-1))
        self.btn_time_today.clicked.connect(lambda: self.paginar_tiempo(0))
        self.btn_time_next.clicked.connect(lambda: self.paginar_tiempo(1))
        
        self.lbl_rango_actual = QLabel("<b>Mayo 2026</b>")
        self.lbl_rango_actual.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f172a; margin-left: 10px; margin-right: 10px;")
        
        self.btn_vista_mes = QPushButton("Mes")
        self.btn_vista_sem = QPushButton("Semana")
        self.btn_vista_dia = QPushButton("Día")
        
        for btn in [self.btn_vista_mes, self.btn_vista_sem, self.btn_vista_dia]:
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { padding: 4px 14px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; }
                QPushButton:checked { font-weight: bold; background-color: #0969da; color: white; border-color: #054ece; }
            """)
            
        self.btn_vista_mes.setChecked(True)
        
        self.group_vistas = QButtonGroup(self)
        self.group_vistas.addButton(self.btn_vista_mes)
        self.group_vistas.addButton(self.btn_vista_sem)
        self.group_vistas.addButton(self.btn_vista_dia)
        self.group_vistas.buttonClicked.connect(self.conmutar_vista_interfaz)
        
        barra_vistas.addWidget(self.btn_time_prev)
        barra_vistas.addWidget(self.btn_time_today)
        barra_vistas.addWidget(self.btn_time_next)
        barra_vistas.addWidget(self.lbl_rango_actual)
        barra_vistas.addStretch()
        barra_vistas.addWidget(self.btn_vista_mes)
        barra_vistas.addWidget(self.btn_vista_sem)
        barra_vistas.addWidget(self.btn_vista_dia)
        layout_izq.addLayout(barra_vistas)
        
        self.stack_vistas_cal = QStackedWidget()
        
        self.widget_mes = QWidget()
        self.grid_mes_layout = QGridLayout(self.widget_mes)
        self.grid_mes_layout.setSpacing(2)
        self.grid_mes_layout.setContentsMargins(0, 5, 0, 0)
        self.stack_vistas_cal.addWidget(self.widget_mes)
        
        self.widget_semana = QWidget()
        self.layout_semana_columnas = QHBoxLayout(self.widget_semana)
        self.layout_semana_columnas.setSpacing(4)
        self.layout_semana_columnas.setContentsMargins(0, 5, 0, 0)
        self.stack_vistas_cal.addWidget(self.widget_semana)
        
        self.scroll_dia = QScrollArea()
        self.scroll_dia.setWidgetResizable(True)
        self.stack_vistas_cal.addWidget(self.scroll_dia)
        
        layout_izq.addWidget(self.stack_vistas_cal)
        layout_principal_cal.addWidget(container_izquierdo, stretch=3)
        
        self.sidebar_metricas = QFrame()
        self.sidebar_metricas.setFrameShape(QFrame.Shape.StyledPanel)
        self.sidebar_metricas.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }")
        layout_side = QVBoxLayout(self.sidebar_metricas)
        
        layout_side.addWidget(QLabel("<b>📊 BALANCES EXISTENCIALES</b>"))
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("color: #e2e8f0;")
        layout_side.addWidget(linea)
        
        layout_side.addWidget(QLabel("Frecuencia Base Analizada:"))
        self.lbl_val_base_bruta = QLabel("44,640 minutos / mensual")
        self.lbl_val_base_bruta.setStyleSheet("font-weight: bold; color: #0f172a; font-size: 11px; margin-bottom: 8px;")
        layout_side.addWidget(self.lbl_val_base_bruta)
        
        layout_side.addWidget(QLabel("🔒 Minutos Comprometidos (Vendidos):"))
        self.lbl_val_canibalizados = QLabel("0 minutos")
        self.lbl_val_canibalizados.setStyleSheet("font-weight: bold; color: #cf222e; font-size: 11px; margin-bottom: 8px;")
        layout_side.addWidget(self.lbl_val_canibalizados)
        
        layout_side.addWidget(QLabel("🛌 Reserva Fisiológica Blindada:"))
        self.lbl_val_fisiologico = QLabel("480 minutos (8.00 h)")
        self.lbl_val_fisiologico.setStyleSheet("font-weight: bold; color: #d97706; font-size: 11px; margin-bottom: 8px;")
        layout_side.addWidget(self.lbl_val_fisiologico)
        
        layout_side.addWidget(QLabel("🚀 Tiempo Líquido SIPA Real Disponible:"))
        self.lbl_val_liquido = QLabel("960 minutos")
        self.lbl_val_liquido.setStyleSheet("font-weight: bold; color: #2da44e; font-size: 13px;")
        layout_side.addWidget(self.lbl_val_liquido)
        
        layout_side.addStretch()
        lbl_nota_cal = QLabel("⚠️ Vista interactiva vinculada a motor SIPA.")
        lbl_nota_cal.setStyleSheet("font-size: 9px; color: #57606a; font-style: italic;")
        layout_side.addWidget(lbl_nota_cal)
        
        layout_principal_cal.addWidget(self.sidebar_metricas, stretch=1)
        self.tabs.addTab(self.tab_calendario, "📅 Calendario y Disponibilidad")

    # =====================================================================
    # PESTAÑA 2: GESTIÓN DE INFORMES Y DOCUMENTOS (PRÓXIMO PASO CRÍTICO)
    # =====================================================================
    def init_tab_informes_docs(self):
        """Contenedor preparado para la gestión de READMEs, Roadmaps y Reportes de color por Estado."""
        self.tab_informes = QWidget()
        layout = QVBoxLayout(self.tab_informes)
        
        # Placeholder elegante temporal para mantener la integridad de la UI antes del desarrollo del bloque
        frame_placeholder = QFrame()
        frame_placeholder.setFrameShape(QFrame.Shape.StyledPanel)
        frame_placeholder.setStyleSheet("background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 6px;")
        layout_pl = QVBoxLayout(frame_placeholder)
        layout_pl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_icono = QLabel("📋")
        lbl_icono.setStyleSheet("font-size: 48px;")
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_aviso = QLabel("<b>Módulo de Informes, Roadmaps y Documentación Markdown</b>")
        lbl_aviso.setStyleSheet("font-size: 14px; color: #0f172a;")
        lbl_aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_detalle = QLabel("Próxima parada técnica tras la paradiña para café. Aquí se inyectará el control de estados por colores.")
        lbl_detalle.setStyleSheet("font-size: 11px; color: #64748b; font-style: italic;")
        lbl_detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_pl.addWidget(lbl_icono)
        layout_pl.addWidget(lbl_aviso)
        layout_pl.addWidget(lbl_detalle)
        
        layout.addWidget(frame_placeholder)
        self.tabs.addTab(self.tab_informes, "📋 Informes y Documentación")

    # =====================================================================
    # PESTAÑA 3: PLANIFICACIÓN DE HITOS
    # =====================================================================
    def init_tab_planificacion(self):
        self.tab_plan = QWidget()
        layout = QVBoxLayout(self.tab_plan)
        
        frame_nec = QFrame()
        frame_nec.setFrameShape(QFrame.Shape.StyledPanel)
        layout_form = QVBoxLayout(frame_nec)
        
        layout_form.addWidget(QLabel("<b>📋 INPUT DE NECESIDADES (Cronogramas / Hitos de Trabajo)</b>"))
        
        row1 = QHBoxLayout()
        self.in_nec_crono = QLineEdit()
        self.in_nec_crono.setPlaceholderText("ID Cronograma (ej: PLAN_MAESTRO, SOCIAL)")
        self.in_nec_hito = QLineEdit()
        self.in_nec_hito.setPlaceholderText("ID Hito Único (ej: DESARROLLO_V1, SALUD_REVISION)")
        row1.addWidget(self.in_nec_crono)
        row1.addWidget(self.in_nec_hito)
        
        row2 = QHBoxLayout()
        self.in_nec_nombre = QLineEdit()
        self.in_nec_nombre.setPlaceholderText("Nombre descriptivo o meta del Hito")
        self.in_nec_proyecto = QLineEdit()
        self.in_nec_proyecto.setPlaceholderText("Proyecto Asociado (ej: SIPA, BOLARDO)")
        row2.addWidget(self.in_nec_nombre)
        row2.addWidget(self.in_nec_proyecto)
        
        row3 = QHBoxLayout()
        self.in_nec_inicio = QLineEdit()
        self.in_nec_inicio.setPlaceholderText("F. Inicio (AAAA-MM-DD)")
        self.in_nec_inicio.setText(self.fecha_pivote.strftime("%Y-%m-%d"))
        self.in_nec_fin = QLineEdit()
        self.in_nec_fin.setPlaceholderText("F. Límite / Fin (AAAA-MM-DD)")
        row3.addWidget(self.in_nec_inicio)
        row3.addWidget(self.in_nec_fin)
        
        row4 = QHBoxLayout()
        self.in_nec_horas = QLineEdit()
        self.in_nec_horas.setPlaceholderText("Horas Estimadas por sesión")
        self.check_repetitivo = QCheckBox("¿Es un hito repetitivo o cíclico?")
        self.check_repetitivo.stateChanged.connect(self.toggle_panel_repeticion)
        row4.addWidget(self.in_nec_horas)
        row4.addWidget(self.check_repetitivo)
        
        self.group_repeticion = QGroupBox("⚙️ Configuración de Recurrencia y Flexibilidad")
        self.group_repeticion.setVisible(False)
        layout_rep = QVBoxLayout(self.group_repeticion)
        
        row_rep_config = QHBoxLayout()
        row_rep_config.addWidget(QLabel("Frecuencia:"))
        self.combo_frecuencia = QComboBox()
        self.combo_frecuencia.addItems(["DIARIA", "SEMANAL"])
        row_rep_config.addWidget(self.combo_frecuencia)
        row_rep_config.addStretch()
        
        row_dias = QHBoxLayout()
        self.chk_lun = QCheckBox("Lunes")
        self.chk_mar = QCheckBox("Martes")
        self.chk_mie = QCheckBox("Miércoles")
        self.chk_jue = QCheckBox("Jueves")
        self.chk_vie = QCheckBox("Viernes")
        self.chk_sab = QCheckBox("Sábado")
        self.chk_dom = QCheckBox("Domingo")
        
        for chk in [self.chk_lun, self.chk_mar, self.chk_mie, self.chk_jue, self.chk_vie]:
            chk.setChecked(True)
            
        row_dias.addWidget(self.chk_lun)
        row_dias.addWidget(self.chk_mar)
        row_dias.addWidget(self.chk_mie)
        row_dias.addWidget(self.chk_jue)
        row_dias.addWidget(self.chk_vie)
        row_dias.addWidget(self.chk_sab)
        row_dias.addWidget(self.chk_dom)
        
        layout_rep.addLayout(row_rep_config)
        layout_rep.addLayout(row_dias)
        
        btn_crear = QPushButton("➕ Consolidar Plan / Hito")
        btn_crear.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold; padding: 6px;")
        btn_crear.clicked.connect(self.procesar_creacion_hito)
        
        layout_form.addLayout(row1)
        layout_form.addLayout(row2)
        layout_form.addLayout(row3)
        layout_form.addLayout(row4)
        layout_form.addWidget(self.group_repeticion)
        layout_form.addWidget(btn_crear)
        layout.addWidget(frame_nec)
        
        self.table_hitos = QTableWidget()
        self.table_hitos.setColumnCount(8)
        self.table_hitos.setHorizontalHeaderLabels([
            "Cronograma", "ID Hito", "Nombre", "Proyecto", "F. Inicio", "F. Fin", "H. Estimadas Total", "Coste Estimado y Acciones"
        ])
        self.configurar_propiedades_tabla(self.table_hitos)
        self.table_hitos.cellChanged.connect(self.on_celda_hito_cambiada)
        
        layout.addWidget(self.table_hitos)
        self.tabs.addTab(self.tab_plan, "🔧 Configuración de Hitos")

    def toggle_panel_repeticion(self, state):
        self.group_repeticion.setVisible(state == Qt.CheckState.Checked.value)

    # =====================================================================
    # PESTAÑA 4: DIARIO DE IMPACTOS DE TIEMPO (BALA 1)
    # =====================================================================
    def init_tab_tiempo(self):
        self.tab_tiempo = QWidget()
        layout = QVBoxLayout(self.tab_tiempo)
        
        frame_b_t = QFrame()
        frame_b_t.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QHBoxLayout(frame_b_t)
        
        self.combo_t_crono = QComboBox()
        self.combo_t_crono.currentTextChanged.connect(self.filtrar_hitos_tiempo_combo)
        self.combo_t_hito = QComboBox()
        
        self.in_t_inicio = QLineEdit()
        self.in_t_inicio.setText("2026-05-28 09:00")
        self.in_t_fin = QLineEdit()
        self.in_t_fin.setText("2026-05-28 17:00")
        
        self.in_t_tarea = QLineEdit()
        self.in_t_tarea.setPlaceholderText("Bitácora de tarea...")
        
        btn_disparar = QPushButton("🚀 Fichar Tiempo")
        btn_disparar.setStyleSheet("background-color: #0969da; color: white; font-weight: bold;")
        btn_disparar.clicked.connect(self.procesar_bala_tiempo)
        
        form_layout.addWidget(QLabel("Crono:"))
        form_layout.addWidget(self.combo_t_crono)
        form_layout.addWidget(QLabel("Hito:"))
        form_layout.addWidget(self.combo_t_hito)
        form_layout.addWidget(QLabel("Inicio:"))
        form_layout.addWidget(self.in_t_inicio)
        form_layout.addWidget(QLabel("Fin:"))
        form_layout.addWidget(self.in_t_fin)
        form_layout.addWidget(self.in_t_tarea)
        form_layout.addWidget(btn_disparar)
        layout.addWidget(frame_b_t)
        
        self.table_tiempo = QTableWidget()
        self.table_tiempo.setColumnCount(7)
        self.table_tiempo.setHorizontalHeaderLabels([
            "ID Bala", "Fecha Impacto", "Cronograma", "ID Hito", "Horas Reales", "Coste Imputado", "Bitácora de Tarea"
        ])
        self.configurar_propiedades_tabla(self.table_tiempo)
        layout.addWidget(self.table_tiempo)
        
        self.tabs.addTab(self.tab_tiempo, "⏱️ Impactos de Tiempo")

    # =====================================================================
    # PESTAÑA 5: FLUJO DE CAJA (BALA 2)
    # =====================================================================
    def init_tab_finanzas(self):
        self.tab_finanzas = QWidget()
        layout = QVBoxLayout(self.tab_finanzas)
        
        frame_b_f = QFrame()
        frame_b_f.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QHBoxLayout(frame_b_f)
        
        self.combo_f_crono = QComboBox()
        self.combo_f_crono.currentTextChanged.connect(self.filtrar_hitos_finanzas_combo)
        self.combo_f_hito = QComboBox()
        
        self.combo_f_naturaleza = QComboBox()
        self.combo_f_naturaleza.addItems(["GASTO", "INGRESO"])
        self.combo_f_estado = QComboBox()
        self.combo_f_estado.addItems(["REAL (BALA)", "PREVISIÓN"])
        
        self.in_f_concepto = QLineEdit()
        self.in_f_concepto.setPlaceholderText("Concepto/Factura...")
        self.in_f_cantidad = QLineEdit()
        self.in_f_cantidad.setPlaceholderText("Importe (€)")
        
        btn_disparar = QPushButton("🚀 Fichar Caja")
        btn_disparar.setStyleSheet("background-color: #0969da; color: white; font-weight: bold;")
        btn_disparar.clicked.connect(self.procesar_bala_finanzas)
        
        form_layout.addWidget(QLabel("Crono:"))
        form_layout.addWidget(self.combo_f_crono)
        form_layout.addWidget(QLabel("Hito:"))
        form_layout.addWidget(self.combo_f_hito)
        form_layout.addWidget(self.combo_f_naturaleza)
        form_layout.addWidget(self.combo_f_estado)
        form_layout.addWidget(self.in_f_concepto)
        form_layout.addWidget(self.in_f_cantidad)
        form_layout.addWidget(btn_disparar)
        layout.addWidget(frame_b_f)
        
        self.table_finanzas = QTableWidget()
        self.table_finanzas.setColumnCount(8)
        self.table_finanzas.setHorizontalHeaderLabels([
            "ID Movimiento", "Fecha", "Hito Vinc.", "Tipo", "Estado", "Concepto", "Previsión/Plan (€)", "Ejecutado Real (€)"
        ])
        self.configurar_propiedades_tabla(self.table_finanzas)
        layout.addWidget(self.table_finanzas)
        
        self.tabs.addTab(self.tab_finanzas, "💰 Flujo de Caja")

    # =====================================================================
    # FILTRADO Y MOTOR DE BÚSQUEDA
    # =====================================================================
    def ejecutar_filtrado_global(self):
        texto_buscado = self.search_input.text().strip().lower()
        idx_pestaña_activa = self.tabs.currentIndex()
        
        tabla_activa = None
        # Mapeo ajustado a los nuevos índices de pestañas
        if idx_pestaña_activa == 2:
            tabla_activa = self.table_hitos
        elif idx_pestaña_activa == 3:
            tabla_activa = self.table_tiempo
        elif idx_pestaña_activa == 4:
            tabla_activa = self.table_finanzas
            
        if tabla_activa is None:
            return
            
        for row in range(tabla_activa.rowCount()):
            coincide = False
            for col in range(tabla_activa.columnCount()):
                item = tabla_activa.item(row, col)
                if item and item.text() and texto_buscado in item.text().lower():
                    coincide = True
                    break
            tabla_activa.setRowHidden(row, not coincide)

    def paginar_tiempo(self, direccion):
        if direccion == 0:
            self.fecha_pivote = datetime.now()
        else:
            if self.btn_vista_mes.isChecked():
                año = self.fecha_pivote.year
                mes = self.fecha_pivote.month + direccion
                if mes > 12:
                    mes = 1
                    año += 1
                elif mes < 1:
                    mes = 12
                    año -= 1
                self.fecha_pivote = datetime(año, mes, min(self.fecha_pivote.day, 28))
            elif self.btn_vista_sem.isChecked():
                self.fecha_pivote += timedelta(days=7 * direccion)
            else:
                self.fecha_pivote += timedelta(days=direccion)
                
        self.renderizar_motores_calendario()

    def conmutar_vista_interfaz(self, button):
        texto = button.text()
        if texto == "Mes":
            self.stack_vistas_cal.setCurrentIndex(0)
            self.lbl_val_base_bruta.setText("44,640 minutos / mensual")
        elif texto == "Semana":
            self.stack_vistas_cal.setCurrentIndex(1)
            self.lbl_val_base_bruta.setText("10,080 minutos / semanal")
        else:
            self.stack_vistas_cal.setCurrentIndex(2)
            self.lbl_val_base_bruta.setText("1,440 minutos / diario")
        self.renderizar_motores_calendario()

    def saltar_a_vista_semana_desde_fecha(self, fecha_destino):
        self.fecha_pivote = fecha_destino
        self.btn_vista_sem.setChecked(True)
        self.stack_vistas_cal.setCurrentIndex(1)
        self.renderizar_motores_calendario()

    def saltar_a_vista_dia_desde_fecha(self, fecha_destino):
        self.fecha_pivote = fecha_destino
        self.btn_vista_dia.setChecked(True)
        self.stack_vistas_cal.setCurrentIndex(2)
        self.renderizar_motores_calendario()

    # =====================================================================
    # NÚCLEO DE RENDERIZADO INTERACTIVO (CON FILTRO CÍCLICO CORREGIDO)
    # =====================================================================
    def hito_aplica_para_fecha(self, hito, fecha_eval):
        """Valida si un hito debe renderizarse en una fecha dada según rango y días permitidos."""
        if not (hito["inicio"].date() <= fecha_eval.date() <= hito["fin"].date()):
            return False
            
        if hito.get("repetitivo", False):
            dias_permitidos = hito.get("dias_ciclo", [])
            if dias_permitidos:
                dia_semana_str = self.dias_map_es.get(fecha_eval.weekday())
                if dia_semana_str not in dias_permitidos:
                    return False
        return True

    def renderizar_motores_calendario(self):
        master_data = self.core._load_json(self.core.cronogramas_path)
        cronogramas = master_data.get("cronogramas", {})
        
        color_map = {
            "PLAN_MAESTRO": "#e0f2fe", "SOCIAL": "#fef3c7", "SALUD": "#fee2e2", "DEFECTO": "#f1f5f9"
        }
        text_color_map = {
            "PLAN_MAESTRO": "#0369a1", "SOCIAL": "#b45309", "SALUD": "#991b1b", "DEFECTO": "#475569"
        }

        hitos_planos = []
        minutos_compromiso_rango = 0
        
        for crono_id, info in cronogramas.items():
            for hito in info.get("hitos", []):
                hitos_planos.append({
                    "crono": crono_id, 
                    "id": hito.get("id"), 
                    "nombre": hito.get("nombre"), 
                    "proyecto": hito.get("proyecto"),
                    "inicio": datetime.strptime(hito.get("fecha_inicio"), "%Y-%m-%d") if hito.get("fecha_inicio") else self.fecha_pivote,
                    "fin": datetime.strptime(hito.get("fecha_fin"), "%Y-%m-%d") if hito.get("fecha_fin") else self.fecha_pivote,
                    "horas": float(hito.get("horas_estimadas", 0)),
                    "repetitivo": hito.get("repetitivo", False),
                    "dias_ciclo": hito.get("dias_ciclo", [])
                })
                minutos_compromiso_rango += int(float(hito.get("horas_estimadas", 0)) * 60)

        # -----------------------------------------------------------------
        # MOTOR 1: VISTA MES
        # -----------------------------------------------------------------
        if self.btn_vista_mes.isChecked():
            self.lbl_rango_actual.setText(f"<b>Mes: {self.fecha_pivote.strftime('%B %Y').capitalize()}</b>")
            while self.grid_mes_layout.count():
                child = self.grid_mes_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
            
            cabeceras = ["Sem", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            for col_idx, texto_dia in enumerate(cabeceras):
                lbl_cabeza = QLabel(f"<b>{texto_dia}</b>")
                lbl_cabeza.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_cabeza.setStyleSheet("background-color: #e2e8f0; padding: 4px; border-radius: 2px; font-size: 10px;")
                self.grid_mes_layout.addWidget(lbl_cabeza, 0, col_idx)

            primer_dia_mes = datetime(self.fecha_pivote.year, self.fecha_pivote.month, 1)
            dia_semana_inicio = primer_dia_mes.weekday()
            fecha_iteracion = primer_dia_mes - timedelta(days=dia_semana_inicio)
            
            for fila in range(1, 7):
                f_sem = datetime(fecha_iteracion.year, fecha_iteracion.month, fecha_iteracion.day)
                num_semana = f_sem.isocalendar()[1]
                
                frame_sem = ClickableFrame(callback=lambda f=f_sem: self.saltar_a_vista_semana_desde_fecha(f))
                frame_sem.setFrameShape(QFrame.Shape.StyledPanel)
                frame_sem.setStyleSheet("QFrame { background-color: #f1f5f9; border-radius: 3px; } QFrame:hover { background-color: #e2e8f0; }")
                layout_f_sem = QVBoxLayout(frame_sem)
                layout_f_sem.setContentsMargins(2, 2, 2, 2)
                lbl_num_sem = QLabel(f"W{num_semana}")
                lbl_num_sem.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_num_sem.setStyleSheet("color: #0969da; font-weight: bold; font-size: 9px; border:none;")
                layout_f_sem.addWidget(lbl_num_sem)
                self.grid_mes_layout.addWidget(frame_sem, fila, 0)
                
                for col in range(1, 8):
                    f_dia = datetime(fecha_iteracion.year, fecha_iteracion.month, fecha_iteracion.day)
                    celda_widget = ClickableFrame(callback=lambda f=f_dia: self.saltar_a_vista_dia_desde_fecha(f))
                    celda_widget.setFrameShape(QFrame.Shape.StyledPanel)
                    
                    bg_celda = "#ffffff" if fecha_iteracion.month == self.fecha_pivote.month else "#f8fafc"
                    borde_celda = "1px solid #e2e8f0"
                    if fecha_iteracion.date() == datetime.now().date():
                        borde_celda = "2px solid #2da44e"
                    elif fecha_iteracion.date() == self.fecha_pivote.date():
                        borde_celda = "2px solid #0969da"
                        
                    celda_widget.setStyleSheet(f"QFrame {{ background-color: {bg_celda}; border: {borde_celda}; border-radius: 4px; }} QFrame:hover {{ border: 1px solid #0969da; }}")
                    layout_celda = QVBoxLayout(celda_widget)
                    layout_celda.setContentsMargins(3, 3, 3, 3)
                    layout_celda.setSpacing(2)
                    
                    lbl_num_dia = QLabel(str(fecha_iteracion.day))
                    lbl_num_dia.setStyleSheet("font-size: 9px; font-weight: bold; color: #475569; border: none;")
                    layout_celda.addWidget(lbl_num_dia)
                    
                    for h in hitos_planos:
                        if self.hito_aplica_para_fecha(h, fecha_iteracion):
                            lbl_bloque = QLabel(f"{h['id']}")
                            c_bg = color_map.get(h["crono"], color_map["DEFECTO"])
                            c_tx = text_color_map.get(h["crono"], text_color_map["DEFECTO"])
                            lbl_bloque.setStyleSheet(f"font-size: 8px; background-color: {c_bg}; color: {c_tx}; padding: 1px 3px; border-radius: 2px; border: none;")
                            layout_celda.addWidget(lbl_bloque)
                            
                    layout_celda.addStretch()
                    self.grid_mes_layout.addWidget(celda_widget, fila, col)
                    fecha_iteracion += timedelta(days=1)

        # -----------------------------------------------------------------
        # MOTOR 2: VISTA SEMANA
        # -----------------------------------------------------------------
        elif self.btn_vista_sem.isChecked():
            lunes_semana = self.fecha_pivote - timedelta(days=self.fecha_pivote.weekday())
            domingo_semana = lunes_semana + timedelta(days=6)
            self.lbl_rango_actual.setText(f"<b>Semana: {lunes_semana.strftime('%d %b')} – {domingo_semana.strftime('%d %b %Y')}</b>")
            
            while self.layout_semana_columnas.count():
                child = self.layout_semana_columnas.takeAt(0)
                if child.widget(): child.widget().deleteLater()
                
            dias_nombre = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            for i in range(7):
                dia_actual = lunes_semana + timedelta(days=i)
                f_dia = datetime(dia_actual.year, dia_actual.month, dia_actual.day)
                
                columna_frame = ClickableFrame(callback=lambda f=f_dia: self.saltar_a_vista_dia_desde_fecha(f))
                columna_frame.setFrameShape(QFrame.Shape.StyledPanel)
                bg_col = "#ffffff" if dia_actual.date() != self.fecha_pivote.date() else "#f0f7ff"
                columna_frame.setStyleSheet(f"QFrame {{ background-color: {bg_col}; border: 1px solid #cbd5e1; border-radius: 6px; }} QFrame:hover {{ border: 1px solid #0969da; }}")
                
                layout_col = QVBoxLayout(columna_frame)
                layout_col.setContentsMargins(5, 5, 5, 5)
                layout_col.setSpacing(4)
                
                lbl_tit_col = QLabel(f"<b>{dias_nombre[i]}</b><br><font color='#64748b'>{dia_actual.strftime('%d %b')}</font>")
                lbl_tit_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_tit_col.setStyleSheet("font-size: 11px; border:none; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;")
                layout_col.addWidget(lbl_tit_col)
                
                for h in hitos_planos:
                    if self.hito_aplica_para_fecha(h, dia_actual):
                        card = QFrame()
                        c_bg = color_map.get(h["crono"], color_map["DEFECTO"])
                        c_tx = text_color_map.get(h["crono"], text_color_map["DEFECTO"])
                        card.setStyleSheet(f"QFrame {{ background-color: {c_bg}; border: 1px solid {c_tx}; border-radius: 4px; }}")
                        
                        layout_card = QVBoxLayout(card)
                        layout_card.setContentsMargins(4, 4, 4, 4)
                        
                        lbl_c1 = QLabel(f"<b>{h['id']}</b>")
                        lbl_c1.setStyleSheet(f"font-size: 10px; color: {c_tx}; border:none;")
                        lbl_c2 = QLabel(h["nombre"])
                        lbl_c2.setStyleSheet("font-size: 9px; color: #334155; border:none;")
                        lbl_c2.setWordWrap(True)
                        
                        layout_card.addWidget(lbl_c1)
                        layout_card.addWidget(lbl_c2)
                        layout_col.addWidget(card)
                        
                layout_col.addStretch()
                self.layout_semana_columnas.addWidget(columna_frame)

        # -----------------------------------------------------------------
        # MOTOR 3: VISTA DIARIA
        # -----------------------------------------------------------------
        else:
            self.lbl_rango_actual.setText(f"<b>Día: {self.fecha_pivote.strftime('%d de %B, %Y')}</b>")
            
            canvas_dia = QWidget()
            canvas_dia.setMinimumHeight(960)
            canvas_dia.setStyleSheet("background-color: #ffffff;")
            
            for hora in range(24):
                lbl_eje = QLabel(f"<b>{hora:02d}:00</b>", canvas_dia)
                lbl_eje.setGeometry(10, hora * 40, 55, 20)
                lbl_eje.setStyleSheet("font-size: 11px; color: #64748b; border: none;")
                
                linea_div = QFrame(canvas_dia)
                linea_div.setGeometry(70, hora * 40 + 10, 1000, 1)
                linea_div.setStyleSheet("background-color: #f1f5f9;")

            offset_x = 80
            for h in hitos_planos:
                if self.hito_aplica_para_fecha(h, self.fecha_pivote):
                    c_bg = color_map.get(h["crono"], color_map["DEFECTO"])
                    c_tx = text_color_map.get(h["crono"], text_color_map["DEFECTO"])
                    
                    hora_defecto = 9 if h["crono"] == "PLAN_MAESTRO" else 17
                    
                    bloque_movil = DraggableHitoBlock(h["id"], h["nombre"], c_bg, c_tx, parent=canvas_dia)
                    altura_bloque = max(40, int(h["horas"] * 40))
                    bloque_movil.setGeometry(offset_x, hora_defecto * 40, 320, altura_bloque)
                    bloque_movil.show()
                    
                    offset_x += 340

            self.scroll_dia.setWidget(canvas_dia)

        self.actualizar_calculos_sidebar_existencial(minutos_compromiso_rango)

    def actualizar_calculos_sidebar_existencial(self, minutos_compromiso_rango):
        fisiologico_dia = 480 
        if self.btn_vista_dia.isChecked():
            comprometido_dia = 480 
            liquido_dia = 1440 - comprometido_dia - fisiologico_dia
            self.lbl_val_canibalizados.setText(f"{comprometido_dia} minutos ({(comprometido_dia/60):.2f} h)")
            self.lbl_val_fisiologico.setText(f"{fisiologico_dia} minutes (8.00 h)")
            self.lbl_val_liquido.setText(f"{liquido_dia} minutos ({(liquido_dia/60):.2f} h)")
        elif self.btn_vista_sem.isChecked():
            comprometido_sem = min(minutos_compromiso_rango, 2400)
            fisiologico_sem = fisiologico_dia * 7
            liquido_sem = 10080 - comprometido_sem - fisiologico_sem
            self.lbl_val_canibalizados.setText(f"{comprometido_sem} minutos ({(comprometido_sem/60):.2f} h)")
            self.lbl_val_fisiologico.setText(f"{fisiologico_sem} minutos (56.00 h)")
            self.lbl_val_liquido.setText(f"{liquido_sem} minutos ({(liquido_sem/60):.2f} h)")
        else:
            comprometido_mes = minutos_compromiso_rango
            fisiologico_mes = fisiologico_dia * 31
            liquido_mes = 44640 - comprometido_mes - fisiologico_mes
            self.lbl_val_canibalizados.setText(f"{comprometido_mes} minutos ({(comprometido_mes/60):.2f} h)")
            self.lbl_val_fisiologico.setText(f"{fisiologico_mes} minutos (248.00 h)")
            self.lbl_val_liquido.setText(f"{liquido_mes} minutos ({(liquido_mes/60):.2f} h)")

    # =========================================================================
    # PERSISTENCIA Y EVENTOS OPERATIVOS
    # =========================================================================
    def actualizar_todo(self):
        self.table_hitos.cellChanged.disconnect()
        self.table_hitos.setSortingEnabled(False)
        self.table_tiempo.setSortingEnabled(False)
        self.table_finanzas.setSortingEnabled(False)
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        cronogramas = master_data.get("cronogramas", {})
        
        filas_hitos = []
        for crono_id, info in cronogramas.items():
            for hito in info.get("hitos", []):
                es_rep = hito.get("repetitivo", False)
                decoracion_nombre = hito.get("nombre", "-")
                if es_rep:
                    dias_s = hito.get("dias_ciclo", [])
                    resumen_dias = "Lun-Vie" if len(dias_s) == 5 and "Sábado" not in dias_s and "Domingo" not in dias_s else ",".join([d[:3] for d in dias_s])
                    decoracion_nombre = f"🔄 [{resumen_dias}] {decoracion_nombre}"
                    
                filas_hitos.append({
                    "crono": crono_id, "id": hito.get("id", "-"), "nombre": decoracion_nombre, "proyecto": hito.get("proyecto", "-"),
                    "inicio": hito.get("fecha_inicio", "-"), "fin": hito.get("fecha_fin", "-"),
                    "horas": str(hito.get("horas_estimadas", "0")), "dinero": str(hito.get("presupuesto_asignado", hito.get("coste_estimado", "0")))
                })
                
        self.table_hitos.setRowCount(len(filas_hitos))
        for r, h in enumerate(filas_hitos):
            item_crono = QTableWidgetItem(h["crono"])
            item_hito = QTableWidgetItem(h["id"])
            item_crono.setData(Qt.ItemDataRole.UserRole, h["crono"])
            item_hito.setData(Qt.ItemDataRole.UserRole, h["id"])
            
            self.table_hitos.setItem(r, 0, item_crono)
            self.table_hitos.setItem(r, 1, item_hito)
            self.table_hitos.setItem(r, 2, QTableWidgetItem(h["nombre"]))
            self.table_hitos.setItem(r, 3, QTableWidgetItem(h["proyecto"]))
            self.table_hitos.setItem(r, 4, QTableWidgetItem(h["inicio"]))
            self.table_hitos.setItem(r, 5, QTableWidgetItem(h["fin"]))
            self.table_hitos.setItem(r, 6, QTableWidgetItem(h["horas"]))
            
            container_widget = QWidget()
            container_widget.setStyleSheet("background-color: transparent;")
            cell_layout = QHBoxLayout(container_widget)
            cell_layout.setContentsMargins(5, 2, 5, 2)
            
            lbl_coste = QLabel(f"-{h['dinero']} €")
            lbl_coste.setStyleSheet("color: #cf222e; font-weight: bold;")
            
            btn_eliminar = QPushButton("🗑️")
            btn_eliminar.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: #f1f5f9; }")
            btn_eliminar.clicked.connect(lambda checked=False, c=h["crono"], hi=h["id"]: self.eliminar_hito_registro(c, hi))
            
            cell_layout.addWidget(lbl_coste)
            cell_layout.addStretch()
            cell_layout.addWidget(btn_eliminar)
            
            dummy_item = QTableWidgetItem("")
            self.table_hitos.setItem(r, 7, dummy_item)
            self.table_hitos.setCellWidget(r, 7, container_widget)

        # Tabla Tiempo
        sesiones = self.core.obtener_sesiones()
        self.table_tiempo.setRowCount(len(sesiones))
        for r, s in enumerate(sesiones):
            self.table_tiempo.setItem(r, 0, QTableWidgetItem(str(s.get("id_sesion", "-"))))
            self.table_tiempo.setItem(r, 1, QTableWidgetItem(str(s.get("fecha", "-"))))
            self.table_tiempo.setItem(r, 2, QTableWidgetItem(str(s.get("cronograma_id", "-"))))
            self.table_tiempo.setItem(r, 3, QTableWidgetItem(str(s.get("id_hito", "-"))))
            self.table_tiempo.setItem(r, 4, QTableWidgetItem(f"{s.get('horas_reales', '0')} h"))
            self.table_tiempo.setItem(r, 5, QTableWidgetItem(f"{s.get('coste_imputado_recurso', '0')} €"))
            self.table_tiempo.setItem(r, 6, QTableWidgetItem(str(s.get("tarea", "-"))))

        # Tabla Flujo de Caja
        transacciones = self.core.obtener_finanzas()
        self.table_finanzas.setRowCount(len(transacciones))
        for r, t in enumerate(transacciones):
            self.table_finanzas.setItem(r, 0, QTableWidgetItem(str(t.get("id_transaccion", "-"))))
            self.table_finanzas.setItem(r, 1, QTableWidgetItem(str(t.get("fecha", "-"))))
            self.table_finanzas.setItem(r, 2, QTableWidgetItem(str(t.get("id_hito", "-"))))
            
            tipo = t.get("tipo", "GASTO")
            self.table_finanzas.setItem(r, 3, QTableWidgetItem(tipo))
            estado = t.get("estado", "REAL (BALA)")
            self.table_finanzas.setItem(r, 4, QTableWidgetItem(estado))
            self.table_finanzas.setItem(r, 5, QTableWidgetItem(str(t.get("concepto", "-"))))
            
            cantidad = float(t.get("cantidad", 0))
            item_prev = QTableWidgetItem("-")
            item_real = QTableWidgetItem("-")
            color_txt = QColor("#cf222e") if tipo == "GASTO" else QColor("#2da44e")
            
            if estado == "PREVISIÓN":
                item_prev.setText(f"{cantidad} €")
                item_prev.setForeground(color_txt)
            else:
                item_real.setText(f"{cantidad} €")
                item_real.setForeground(color_txt)
                
            self.table_finanzas.setItem(r, 6, item_prev)
            self.table_finanzas.setItem(r, 7, item_real)

        self.autoajustar_columnas(self.table_hitos)
        self.autoajustar_columnas(self.table_tiempo)
        self.autoajustar_columnas(self.table_finanzas)

        self.table_hitos.setSortingEnabled(True)
        self.table_tiempo.setSortingEnabled(True)
        self.table_finanzas.setSortingEnabled(True)
        self.table_hitos.cellChanged.connect(self.on_celda_hito_cambiada)

        lista_cronos = list(cronogramas.keys())
        for combo in [self.combo_t_crono, self.combo_f_crono]:
            curr = combo.currentText()
            combo.clear()
            combo.addItems(lista_cronos)
            if curr in lista_cronos: combo.setCurrentText(curr)

        self.ejecutar_filtrado_global()
        self.renderizar_motores_calendario()

    def filtrar_hitos_tiempo_combo(self, crono_key):
        if not crono_key: return
        self.combo_t_hito.clear()
        master_data = self.core._load_json(self.core.cronogramas_path)
        hitos = master_data.get("cronogramas", {}).get(crono_key, {}).get("hitos", [])
        for h in hitos: self.combo_t_hito.addItem(h["id"])

    def filtrar_hitos_finanzas_combo(self, crono_key):
        if not crono_key: return
        self.combo_f_hito.clear()
        master_data = self.core._load_json(self.core.cronogramas_path)
        hitos = master_data.get("cronogramas", {}).get(crono_key, {}).get("hitos", [])
        for h in hitos: self.combo_f_hito.addItem(h["id"])

    def on_celda_hito_cambiada(self, row, col):
        item_modificado = self.table_hitos.item(row, col)
        if not item_modificado: return
        nuevo_valor = item_modificado.text().strip()

        item_crono_origen = self.table_hitos.item(row, 0)
        item_hito_origen = self.table_hitos.item(row, 1)
        if not item_crono_origen or not item_hito_origen: return
        
        crono_orig_id = item_crono_origen.data(Qt.ItemDataRole.UserRole)
        hito_orig_id = item_hito_origen.data(Qt.ItemDataRole.UserRole)

        master_data = self.core._load_json(self.core.cronogramas_path)
        hitos_lista = master_data.get("cronogramas", {}).get(crono_orig_id, {}).get("hitos", [])
        target_hito = next((h for h in hitos_lista if h.get("id") == hito_orig_id), None)
        if not target_hito: return

        if col == 0:
            nuevo_crono = nuevo_valor.upper()
            if nuevo_crono and nuevo_crono != crono_orig_id:
                if nuevo_crono not in master_data["cronogramas"]:
                    master_data["cronogramas"][nuevo_crono] = {"descripcion": f"Cronograma {nuevo_crono}", "hitos": []}
                hitos_lista.remove(target_hito)
                master_data["cronogramas"][nuevo_crono]["hitos"].append(target_hito)
        elif col == 1: target_hito["id"] = nuevo_valor.upper()
        elif col == 2: 
            if "🔄 [" in nuevo_valor:
                nuevo_valor = nuevo_valor.split("] ", 1)[-1]
            target_hito["nombre"] = nuevo_valor
        elif col == 3: target_hito["proyecto"] = nuevo_valor
        elif col == 4: target_hito["fecha_inicio"] = nuevo_valor
        elif col == 5: target_hito["fecha_fin"] = nuevo_valor
        elif col == 6:
            try: 
                nuevas_horas = float(nuevo_valor.replace(",", "."))
                target_hito["horas_estimadas"] = nuevas_horas
                target_hito["presupuesto_asignado"] = nuevas_horas * 25.0
                if "coste_estimado" in target_hito:
                    target_hito["coste_estimado"] = nuevas_horas * 25.0
            except ValueError: 
                pass

        self.core._save_json(self.core.cronogramas_path, master_data)
        self.actualizar_todo()

    def eliminar_hito_registro(self, crono_id, hito_id):
        confirmacion = QMessageBox.question(
            self, "Confirmar Eliminación", f"¿Deseas eliminar '{hito_id}'?\nEsta acción es irreversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmacion == QMessageBox.StandardButton.Yes:
            master_data = self.core._load_json(self.core.cronogramas_path)
            if crono_id in master_data.get("cronogramas", {}):
                hitos_lista = master_data["cronogramas"][crono_id].get("hitos", [])
                master_data["cronogramas"][crono_id]["hitos"] = [h for h in hitos_lista if h.get("id") != hito_id]
                self.core._save_json(self.core.cronogramas_path, master_data)
                self.actualizar_todo()

    def procesar_creacion_hito(self):
        crono = self.in_nec_crono.text().strip().upper()
        id_hito = self.in_nec_hito.text().strip().upper()
        nombre = self.in_nec_nombre.text().strip()
        proyecto = self.in_nec_proyecto.text().strip()
        inicio = self.in_nec_inicio.text().strip()
        fin = self.in_nec_fin.text().strip()
        horas_raw = self.in_nec_horas.text().strip() or "0"

        if not (crono and id_hito and nombre and inicio and fin): return
        try: horas_base = float(horas_raw.replace(",", "."))
        except ValueError: return

        dias_seleccionados = []
        if self.check_repetitivo.isChecked():
            mapeo_checkboxes = {
                self.chk_lun: "Lunes", self.chk_mar: "Martes", self.chk_mie: "Miércoles",
                self.chk_jue: "Jueves", self.chk_vie: "Viernes", self.chk_sab: "Sábado",
                self.chk_dom: "Domingo"
            }
            for cb, nombre_dia in mapeo_checkboxes.items():
                if cb.isChecked():
                    dias_seleccionados.append(nombre_dia)

        self.core.crear_subcronograma(crono, f"Cronograma {crono}")
        master_data = self.core._load_json(self.core.cronogramas_path)
        master_data["cronogramas"][crono]["hitos"].append({
            "id": id_hito, 
            "nombre": nombre, 
            "proyecto": proyecto, 
            "fecha_inicio": inicio, 
            "fecha_fin": fin,
            "horas_estimadas": horas_base, 
            "presupuesto_asignado": horas_base * 25.0, 
            "repetitivo": self.check_repetitivo.isChecked(),
            "frecuencia": self.combo_frecuencia.currentText() if self.check_repetitivo.isChecked() else None,
            "dias_ciclo": dias_seleccionados
        })
        self.core._save_json(self.core.cronogramas_path, master_data)
        self.actualizar_todo()

    def procesar_bala_tiempo(self):
        crono = self.combo_t_crono.currentText()
        hito = self.combo_t_hito.currentText()
        if not (crono and hito and self.in_t_tarea.text().strip()): return
        exito, msg = self.core.registrar_sesion(crono, hito, self.in_t_inicio.text(), self.in_t_fin.text(), self.in_t_tarea.text())
        if exito: self.actualizar_todo()

    def procesar_bala_finanzas(self):
        crono = self.combo_f_crono.currentText()
        hito = self.combo_f_hito.currentText()
        if not (crono and hito and self.in_f_concepto.text().strip()): return
        master_fin = self.core._load_json(self.core.finanzas_path)
        master_fin.setdefault("transacciones", []).append({
            "id_transaccion": len(master_fin.get("transacciones", [])) + 1,
            "fecha": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm"), "cronograma_id": crono, "id_hito": hito,
            "tipo": self.combo_f_naturaleza.currentText(), "estado": self.combo_f_estado.currentText(),
            "concepto": self.in_f_concepto.text().strip(), "cantidad": float(self.in_f_cantidad.text() or 0)
        })
        self.core._save_json(self.core.finanzas_path, master_fin)
        self.actualizar_todo()

    def configurar_propiedades_tabla(self, tabla: QTableWidget):
        tabla.setSortingEnabled(True)
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

    def autoajustar_columnas(self, tabla: QTableWidget):
        tabla.resizeColumnsToContents()
        for col in range(tabla.columnCount() - 1):
            width = tabla.columnWidth(col)
            tabla.setColumnWidth(col, width + 14)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SIPAecoWindow()
    window.show()
    sys.exit(app.exec())