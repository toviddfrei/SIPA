#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco GUI - Vista del Calendario Dinámico, Cíclico y Relacional (POO)
Ubicación: SIPA/external/SIPAeco/views/calendar_view.py
Autor: Daniel Miñana Montero
Descripción: Módulo de interfaz desacoplado que gestiona los tres motores de visualización.
             CORRECCIONES: 
             - Reducción de fuentes en títulos del sidebar para evitar desbordamientos.
             - Motor de balances existenciales 100% dinámico y vinculado al rango visible.
"""

import calendar
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QButtonGroup, QStackedWidget, 
                             QGridLayout, QScrollArea)
from PySide6.QtCore import Qt


class ClickableFrame(QFrame):
    """Contenedor genérico que emite una señal simulada al hacer clic."""
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()
        super().mousePressEvent(event)


class CalendarioSemanaTab(QWidget):
    def __init__(self, core_base, parent_window=None):
        super().__init__(parent_window)
        self.core = core_base
        self.parent_window = parent_window
        
        # Fecha de pivote operativa local
        self.fecha_pivote = datetime.now()
        
        # Mapeo de traducción cronológica estricta
        self.dias_map_es = {
            0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 
            4: "Viernes", 5: "Sábado", 6: "Domingo"
        }
        
        # Pesos de prioridad para ordenación existencial estricta
        self.peso_prioridad = {
            "1 - CRÍTICA": 1,
            "2 - ALTA": 2,
            "3 - MEDIA": 3,
            "4 - BAJA": 4
        }
        
        self.init_ui()
        
        # Forzar renderizado inmediato en Vista Mes al inicializar
        self.renderizar_motores_calendario()

    def init_ui(self):
        layout_principal_cal = QHBoxLayout(self)
        layout_principal_cal.setContentsMargins(5, 5, 5, 5)
        
        container_izquierdo = QWidget()
        layout_izq = QVBoxLayout(container_izquierdo)
        layout_izq.setContentsMargins(0, 0, 0, 0)
        
        # --- BARRA DE NAVEGACIÓN Y VISTAS ---
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
        
        self.lbl_rango_actual = QLabel("<b>Cargando Período...</b>")
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
        
        # --- CONTENEDOR APILADO (STACK) DE MOTORES ---
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
        
        # --- SIDEBAR DE CALCULOS EXISTENCIALES ---
        self.sidebar_metricas = QFrame()
        self.sidebar_metricas.setFrameShape(QFrame.Shape.StyledPanel)
        self.sidebar_metricas.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }")
        self.sidebar_metricas.setFixedWidth(230)
        
        layout_side = QVBoxLayout(self.sidebar_metricas)
        layout_side.setSpacing(6)
        
        lbl_tit_panel = QLabel("<b>📊 BALANCES EN PANTALLA</b>")
        lbl_tit_panel.setStyleSheet("font-size: 11px; color: #0f172a;")
        layout_side.addWidget(lbl_tit_panel)
        
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("color: #e2e8f0;")
        layout_side.addWidget(linea)
        
        # CORRECCIÓN DE ESTILOS: Títulos más pequeños (font-size: 10px) para evitar desbordamiento horizontal
        lbl_t1 = QLabel("Frecuencia Base Analizada:")
        lbl_t1.setStyleSheet("font-size: 10px; color: #475569; font-weight: 500;")
        self.lbl_val_base_bruta = QLabel("0 minutos")
        self.lbl_val_base_bruta.setStyleSheet("font-weight: bold; color: #0f172a; font-size: 11px; margin-bottom: 4px;")
        layout_side.addWidget(lbl_t1)
        layout_side.addWidget(self.lbl_val_base_bruta)
        
        lbl_t2 = QLabel("🔒 Minutos Comprometidos:")
        lbl_t2.setStyleSheet("font-size: 10px; color: #475569; font-weight: 500;")
        self.lbl_val_canibalizados = QLabel("0 minutos")
        self.lbl_val_canibalizados.setStyleSheet("font-weight: bold; color: #cf222e; font-size: 11px; margin-bottom: 4px;")
        layout_side.addWidget(lbl_t2)
        layout_side.addWidget(self.lbl_val_canibalizados)
        
        lbl_t3 = QLabel("🛌 Reserva Fisiológica Blindada:")
        lbl_t3.setStyleSheet("font-size: 10px; color: #475569; font-weight: 500;")
        self.lbl_val_fisiologico = QLabel("0 minutos")
        self.lbl_val_fisiologico.setStyleSheet("font-weight: bold; color: #d97706; font-size: 11px; margin-bottom: 4px;")
        layout_side.addWidget(lbl_t3)
        layout_side.addWidget(self.lbl_val_fisiologico)
        
        lbl_t4 = QLabel("🚀 Tiempo Líquido SIPA Visible:")
        lbl_t4.setStyleSheet("font-size: 10px; color: #475569; font-weight: 500;")
        self.lbl_val_liquido = QLabel("0 minutos")
        self.lbl_val_liquido.setStyleSheet("font-weight: bold; color: #2da44e; font-size: 12px;")
        layout_side.addWidget(lbl_t4)
        layout_side.addWidget(self.lbl_val_liquido)
        
        layout_side.addStretch()
        lbl_nota_cal = QLabel("⚠️ Resumen calculado sobre el rango visible.")
        lbl_nota_cal.setStyleSheet("font-size: 9px; color: #57606a; font-style: italic;")
        layout_side.addWidget(lbl_nota_cal)
        
        layout_principal_cal.addWidget(self.sidebar_metricas, stretch=1)

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
        elif texto == "Semana":
            self.stack_vistas_cal.setCurrentIndex(1)
        else:
            self.stack_vistas_cal.setCurrentIndex(2)
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

    def hito_aplica_para_fecha(self, hito, fecha_eval):
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
        hitos_instanciados = master_data.get("hitos_instanciados", {})
        
        color_map = {
            "PLAN_MAESTRO": "#e0f2fe", "SOCIAL": "#fef3c7", "SALUD": "#fee2e2", "DEFECTO": "#f1f5f9"
        }
        text_color_map = {
            "PLAN_MAESTRO": "#0369a1", "SOCIAL": "#b45309", "SALUD": "#991b1b", "DEFECTO": "#475569"
        }

        hitos_planos = []
        
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
                    "prioridad": hito.get("prioridad", "3 - MEDIA"),
                    "repetitivo": hito.get("repetitivo", False),
                    "dias_ciclo": hito.get("dias_ciclo", [])
                })
                
        for h_id, info in hitos_instanciados.items():
            crono_vinc = info.get("id_cronograma", "DEFECTO")
            f_ini_str = info.get("fecha_inicio", datetime.now().strftime("%Y-%m-%d"))
            f_fin_str = info.get("fecha_fin", datetime.now().strftime("%Y-%m-%d"))
            try:
                dt_ini = datetime.strptime(f_ini_str[:10], "%Y-%m-%d")
                dt_fin = datetime.strptime(f_fin_str[:10], "%Y-%m-%d")
            except ValueError:
                dt_ini = self.fecha_pivote
                dt_fin = self.fecha_pivote

            hitos_planos.append({
                "crono": crono_vinc,
                "id": h_id,
                "nombre": info.get("nombre_accion", "Acción"),
                "proyecto": info.get("id_proyecto", "SIPA"),
                "inicio": dt_ini,
                "fin": dt_fin,
                "horas": float(info.get("horas_estimadas", 0.0)),
                "prioridad": info.get("prioridad", "3 - MEDIA"),
                "repetitivo": info.get("repetitivo", False),
                "dias_ciclo": info.get("dias_ciclo", [])
            })

        # Inicialización de rango contextual para el cálculo existencial dinámico
        fecha_inicio_vista = self.fecha_pivote
        fecha_fin_vista = self.fecha_pivote

        # -----------------------------------------------------------------
        # MOTOR 1: VISTA MES
        # -----------------------------------------------------------------
        if self.btn_vista_mes.isChecked():
            self.lbl_rango_actual.setText(f"<b>Mes: {self.fecha_pivote.strftime('%B %Y').capitalize()}</b>")
            
            # Definir límites del mes real visible para el conteo de balances
            fecha_inicio_vista = datetime(self.fecha_pivote.year, self.fecha_pivote.month, 1)
            dias_del_mes = calendar.monthrange(self.fecha_pivote.year, self.fecha_pivote.month)[1]
            fecha_fin_vista = datetime(self.fecha_pivote.year, self.fecha_pivote.month, dias_del_mes)

            while self.grid_mes_layout.count():
                child = self.grid_mes_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
            
            cabeceras = ["Sem", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            for col_idx, texto_dia in enumerate(cabeceras):
                lbl_cabeza = QLabel(f"<b>{texto_dia}</b>")
                lbl_cabeza.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_cabeza.setStyleSheet("background-color: #e2e8f0; padding: 4px; border-radius: 2px; font-size: 10px;")
                self.grid_mes_layout.addWidget(lbl_cabeza, 0, col_idx)

            dia_semana_inicio = fecha_inicio_vista.weekday()
            fecha_iteracion = fecha_inicio_vista - timedelta(days=dia_semana_inicio)
            
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
                    celda_widget.setSizePolicy(self.sizePolicy().Policy.Ignored, self.sizePolicy().Policy.Expanding)
                    
                    layout_celda = QVBoxLayout(celda_widget)
                    layout_celda.setContentsMargins(3, 3, 3, 3)
                    layout_celda.setSpacing(2)
                    
                    lbl_num_dia = QLabel(str(fecha_iteracion.day))
                    lbl_num_dia.setStyleSheet("font-size: 9px; font-weight: bold; color: #475569; border: none;")
                    layout_celda.addWidget(lbl_num_dia)
                    
                    count_hitos = 0
                    for h in hitos_planos:
                        if self.hito_aplica_para_fecha(h, fecha_iteracion):
                            count_hitos += 1
                            if count_hitos <= 3:
                                lbl_bloque = QLabel(f"{h['id']}")
                                c_bg = color_map.get(h["crono"], color_map["DEFECTO"])
                                c_tx = text_color_map.get(h["crono"], text_color_map["DEFECTO"])
                                lbl_bloque.setStyleSheet(f"font-size: 8px; background-color: {c_bg}; color: {c_tx}; padding: 1px 2px; border-radius: 2px; border: none;")
                                layout_celda.addWidget(lbl_bloque)
                            elif count_hitos == 4:
                                lbl_mas = QLabel("+ más...")
                                lbl_mas.setStyleSheet("font-size: 7px; color: #64748b; border: none;")
                                layout_celda.addWidget(lbl_mas)
                                
                    layout_celda.addStretch()
                    self.grid_mes_layout.addWidget(celda_widget, fila, col)
                    fecha_iteracion += timedelta(days=1)

        # -----------------------------------------------------------------
        # MOTOR 2: VISTA SEMANA
        # -----------------------------------------------------------------
        elif self.btn_vista_sem.isChecked():
            fecha_inicio_vista = self.fecha_pivote - timedelta(days=self.fecha_pivote.weekday())
            fecha_fin_vista = fecha_inicio_vista + timedelta(days=6)
            self.lbl_rango_actual.setText(f"<b>Semana: {fecha_inicio_vista.strftime('%d %b')} – {fecha_fin_vista.strftime('%d %b %Y')}</b>")
            
            while self.layout_semana_columnas.count():
                child = self.layout_semana_columnas.takeAt(0)
                if child.widget(): child.widget().deleteLater()
                
            dias_nombre = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            for i in range(7):
                dia_actual = fecha_inicio_vista + timedelta(days=i)
                f_dia = datetime(dia_actual.year, dia_actual.month, dia_actual.day)
                
                columna_frame = ClickableFrame(callback=lambda f=f_dia: self.saltar_a_vista_dia_desde_fecha(f))
                columna_frame.setFrameShape(QFrame.Shape.StyledPanel)
                bg_col = "#ffffff" if dia_actual.date() != self.fecha_pivote.date() else "#f0f7ff"
                columna_frame.setStyleSheet(f"QFrame {{ background-color: {bg_col}; border: 1px solid #cbd5e1; border-radius: 6px; }} QFrame:hover {{ border: 1px solid #0969da; }}")
                
                columna_frame.setSizePolicy(self.sizePolicy().Policy.Ignored, self.sizePolicy().Policy.Expanding)
                
                layout_col = QVBoxLayout(columna_frame)
                layout_col.setContentsMargins(4, 5, 4, 5)
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
                        layout_card.setSpacing(2)
                        
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
            fecha_inicio_vista = self.fecha_pivote
            fecha_fin_vista = self.fecha_pivote
            
            canvas_dia = QWidget()
            layout_muro_diario = QVBoxLayout(canvas_dia)
            layout_muro_diario.setContentsMargins(15, 15, 15, 15)
            layout_muro_diario.setSpacing(10)
            
            hitos_del_dia = [h for h in hitos_planos if self.hito_aplica_para_fecha(h, self.fecha_pivote)]
            hitos_del_dia.sort(key=lambda x: self.peso_prioridad.get(x["prioridad"], 3))
            
            if not hitos_del_dia:
                lbl_vacio = QLabel("🍀 No hay hitos estratégicos asignados para este día. ¡Tiempo líquido SIPA absoluto!")
                lbl_vacio.setStyleSheet("font-size: 12px; color: #64748b; font-style: italic; padding: 20px;")
                lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout_muro_diario.addWidget(lbl_vacio)
            else:
                for h in hitos_del_dia:
                    tarjeta_fila = QFrame()
                    c_bg = color_map.get(h["crono"], color_map["DEFECTO"])
                    c_tx = text_color_map.get(h["crono"], text_color_map["DEFECTO"])
                    
                    borde_color = "#cf222e" if "CRÍTICA" in h["prioridad"] else ("#d97706" if "ALTA" in h["prioridad"] else c_tx)
                    
                    tarjeta_fila.setStyleSheet(f"""
                        QFrame {{
                            background-color: {c_bg};
                            border: 1px solid #cbd5e1;
                            border-left: 5px solid {borde_color};
                            border-radius: 4px;
                        }}
                    """)
                    
                    ly_tarjeta = QHBoxLayout(tarjeta_fila)
                    ly_tarjeta.setContentsMargins(12, 10, 12, 10)
                    
                    vbox_id = QVBoxLayout()
                    lbl_id = QLabel(f"<b>🔒 {h['id']}</b>")
                    lbl_id.setStyleSheet(f"font-size: 12px; color: {c_tx}; border: none;")
                    lbl_pry = QLabel(f"📁 {h['proyecto']}")
                    lbl_pry.setStyleSheet("font-size: 10px; color: #64748b; border: none;")
                    vbox_id.addWidget(lbl_id)
                    vbox_id.addWidget(lbl_pry)
                    ly_tarjeta.addLayout(vbox_id, stretch=1)
                    
                    lbl_nom = QLabel(h["nombre"])
                    lbl_nom.setStyleSheet("font-size: 11px; color: #0f172a; font-weight: 500; border: none;")
                    lbl_nom.setWordWrap(True)
                    ly_tarjeta.addWidget(lbl_nom, stretch=3)
                    
                    vbox_meta = QVBoxLayout()
                    vbox_meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    lbl_prio = QLabel(f"⚡ {h['prioridad']}")
                    color_txt_prio = "#cf222e" if "CRÍTICA" in h["prioridad"] else "#0f172a"
                    lbl_prio.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {color_txt_prio}; border: none;")
                    
                    lbl_hrs = QLabel(f"⏳ {h['horas']} horas")
                    lbl_hrs.setStyleSheet("font-size: 11px; color: #334155; font-weight: bold; border: none;")
                    
                    vbox_meta.addWidget(lbl_prio)
                    vbox_meta.addWidget(lbl_hrs)
                    ly_tarjeta.addLayout(vbox_meta, stretch=1)
                    
                    layout_muro_diario.addWidget(tarjeta_fila)
            
            layout_muro_diario.addStretch()
            self.scroll_dia.setWidget(canvas_dia)

        # --- MOTOR DE CÁLCULO CONTEXTUAL INTEGRADO ---
        self.calcular_existencial_contextual(fecha_inicio_vista, fecha_fin_vista, hitos_planos)

    def calcular_existencial_contextual(self, inicio, fin, hitos_planos):
        """Calcula los minutos consumidos recorriendo día a día el intervalo visible actual."""
        minutos_comprometidos = 0
        dias_intervalo = (fin.date() - inicio.date()).days + 1
        
        # Iterar día a día en el marco temporal exacto renderizado en pantalla
        for d in range(dias_intervalo):
            dia_evaluar = inicio + timedelta(days=d)
            for h in hitos_planos:
                if self.hito_aplica_para_fecha(h, dia_evaluar):
                    # Distribución lineal simplificada de las horas estimadas del hito en su marco temporal
                    duracion_hito_dias = (h["fin"].date() - h["inicio"].date()).days + 1
                    duracion_hito_dias = max(1, duracion_hito_dias)
                    
                    # Carga de impacto de tiempo proporcional imputado a este día específico
                    horas_proporcionales_dia = h["horas"] / duracion_hito_dias
                    minutos_comprometidos += int(horas_proporcionales_dia * 60)

        # Definición de la frecuencia bruta e inmunidad fisiológica en función de los días visibles
        minutos_brutos_periodo = dias_intervalo * 1440
        reserva_fisiologica_periodo = dias_intervalo * 480  # 8 horas de sueño blindado diario
        
        # El tiempo líquido real restante responde a las leyes de exclusión del sistema SIPA
        tiempo_liquido_periodo = minutos_brutos_periodo - minutos_comprometidos - reserva_fisiologica_periodo
        
        # Formatear cadenas para inyección visual en el Sidebar
        if self.btn_vista_dia.isChecked():
            texto_base = f"{minutos_brutos_periodo:,} min / diario"
        elif self.btn_vista_sem.isChecked():
            texto_base = f"{minutos_brutos_periodo:,} min / semanal"
        else:
            texto_base = f"{minutos_brutos_periodo:,} min / mensual ({inicio.strftime('%b')})"
            
        self.lbl_val_base_bruta.setText(texto_base.replace(",", "."))
        self.lbl_val_canibalizados.setText(f"{minutos_comprometidos:,} min ({(minutos_comprometidos/60):.2f} h)".replace(",", "."))
        self.lbl_val_fisiologico.setText(f"{reserva_fisiologica_periodo:,} min ({(reserva_fisiologica_periodo/60):.2f} h)".replace(",", "."))
        self.lbl_val_liquido.setText(f"{tiempo_liquido_periodo:,} min ({(tiempo_liquido_periodo/60):.2f} h)".replace(",", "."))

    def update_tab_data(self):
        """Punto de entrada de sincronización estándar invocado por el orquestador principal."""
        self.renderizar_motores_calendario()