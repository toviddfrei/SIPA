#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco GUI - Gestión de Caja, Pasarela Bancaria y Previsiones Elásticas
Ubicación: SIPA/external/SIPAeco/views/finanzas_view.py
Autor: Daniel Miñana Montero & Gemini
Descripción: Módulo de interfaz para finanzas con entrada de datos blindada,
             replicando exactamente el motor de lectura y eventos de tiempo_view.py.
             🔌 TRUNKING: Alimentación PoE heredada por el Switch de infraestructura.
"""

import os
import uuid
import subprocess
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QFrame, QMessageBox, QComboBox, QFileDialog, QHeaderView, QDialog, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

# Corrección de la pasarela física al servicio de caja local de la extensión
from external.SIPAeco.core.services.sesipaeco_caja import SESIPAecoCajaService

# =====================================================================
# 🎛️ CONEXIÓN TRONCAL DIRECTA (Conmutada de forma transparente por el Switch)
# =====================================================================
# Corrección definitiva del enlace a la biblioteca central de utilidades
from external.utils.sipa_utils import sincronizar_contexto_hito_labels

class FinanzasTab(QWidget):
    def __init__(self, core, parent_window=None):
        super().__init__(parent_window)
        self.core = core
        self.parent_window = parent_window
        
        # Cachés relacionales idénticas al motor de impactos de tiempo
        self.hitos_cache = {}
        self.registros_filtrados_cache = []
        self.ficheros_temporales_formulario = []
        
        self.servicio_caja = SESIPAecoCajaService(self.core)
        self.init_ui()

    def init_ui(self):
        """Construye la interfaz con el patrón de entrada infalible de hitos."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(10)
        
        # =====================================================================
        # 1. FORMULARIO DE ENTRADA (Estilo Impactos de Tiempo - Entrada Directa)
        # =====================================================================
        frame_form = QFrame()
        frame_form.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; }")
        form_layout = QHBoxLayout(frame_form)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)
        
        # Combo de Hitos: Configuración reactiva delegada a sipa_utils
        self.combo_vincular_hito = QComboBox()
        self.combo_vincular_hito.setFixedWidth(280)
        
        # Etiquetas informativas dinámicas integradas en la cabecera
        self.lbl_auto_proyecto = QLabel("<b>Proyecto:</b> -")
        self.lbl_auto_proyecto.setStyleSheet("color: #0969da; background: #f0f7ff; padding: 4px; border-radius: 4px;")
        self.lbl_auto_crono = QLabel("<b>Crono Tipo:</b> -")
        self.lbl_auto_crono.setStyleSheet("color: #0969da; background: #f0f7ff; padding: 4px; border-radius: 4px;")
        
        self.combo_vincular_hito.currentTextChanged.connect(
            lambda txt: sincronizar_contexto_hito_labels(txt, self.hitos_cache, self.lbl_auto_proyecto, self.lbl_auto_crono)
        )
        
        self.combo_f_naturaleza = QComboBox()
        self.combo_f_naturaleza.addItems(["GASTO 🔽", "INGRESO 🔼"])
        self.combo_f_naturaleza.setFixedWidth(110)
        
        self.combo_f_estado = QComboBox()
        self.combo_f_estado.addItems(["REAL (BALA)", "PREVISIÓN PLAN"])
        self.combo_f_estado.setFixedWidth(130)
        
        self.in_f_concepto = QLineEdit()
        self.in_f_concepto.setPlaceholderText("Concepto manual...")
        
        self.in_f_cantidad = QLineEdit()
        self.in_f_cantidad.setPlaceholderText("Importe (€)")
        self.in_f_cantidad.setFixedWidth(90)
        
        self.btn_adjuntar_form = QPushButton("📎 Justificante (0)")
        self.btn_adjuntar_form.clicked.connect(self.adjuntar_fichero_temporal_formulario)
        
        btn_disparar = QPushButton("🚀 Fichar Caja")
        btn_disparar.setStyleSheet("background-color: #0969da; color: white; font-weight: bold; padding: 4px 12px; border-radius: 4px;")
        btn_disparar.clicked.connect(self.procesar_bala_local)
        
        # Ensamblado lineal idéntico en cabecera superior
        form_layout.addWidget(QLabel("<b>Hito Núcleo Vinculante:</b>"))
        form_layout.addWidget(self.combo_vincular_hito)
        form_layout.addWidget(self.lbl_auto_proyecto)
        form_layout.addWidget(self.lbl_auto_crono)
        form_layout.addWidget(self.combo_f_naturaleza)
        form_layout.addWidget(self.combo_f_estado)
        form_layout.addWidget(self.in_f_concepto)
        form_layout.addWidget(self.in_f_cantidad)
        form_layout.addWidget(self.btn_adjuntar_form)
        form_layout.addWidget(btn_disparar)
        layout_principal.addWidget(frame_form)
        
        # =====================================================================
        # 2. SCORECARDS MÉTRICAS (Justo debajo de los inputs)
        # =====================================================================
        panel_kpi = QHBoxLayout()
        
        self.card_previsto = QFrame()
        self.card_previsto.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; }")
        ly_prev = QVBoxLayout(self.card_previsto)
        ly_prev.addWidget(QLabel("<font color='#475569'>💰 Rendimiento Previsto Neto (6M)</font>"))
        self.lbl_kpi_previsto = QLabel("0.00 €")
        self.lbl_kpi_previsto.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a;")
        ly_prev.addWidget(self.lbl_kpi_previsto)
        
        self.card_real = QFrame()
        self.card_real.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; }")
        ly_real = QVBoxLayout(self.card_real)
        ly_real.addWidget(QLabel("<font color='#475569'>🚀 Caja Real Ejecutada Neta (6M)</font>"))
        self.lbl_kpi_real = QLabel("0.00 €")
        self.lbl_kpi_real.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a;")
        ly_real.addWidget(self.lbl_kpi_real)
        
        self.card_desviacion = QFrame()
        self.card_desviacion.setStyleSheet("QFrame { background-color: #ffffff; border: 2px solid #e2e8f0; border-radius: 6px; }")
        ly_desv = QVBoxLayout(self.card_desviacion)
        ly_desv.addWidget(QLabel("<b>📊 Desviación Total Absoluta</b>"))
        self.lbl_kpi_desviacion = QLabel("0.00 €")
        self.lbl_kpi_desviacion.setStyleSheet("font-size: 18px; font-weight: bold; color: #0969da;")
        ly_desv.addWidget(self.lbl_kpi_desviacion)
        
        panel_kpi.addWidget(self.card_previsto, stretch=1)
        panel_kpi.addWidget(self.card_real, stretch=1)
        panel_kpi.addWidget(self.card_desviacion, stretch=1)
        layout_principal.addLayout(panel_kpi)
        
        # =====================================================================
        # 3. PANEL DE PASARELA BANCARIA (.TXT)
        # =====================================================================
        frame_banco = QFrame()
        frame_banco.setStyleSheet("QFrame { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; }")
        ly_banco = QHBoxLayout(frame_banco)
        ly_banco.setContentsMargins(8, 8, 8, 8)
        
        self.lbl_status_banco = QLabel("<b>Apertura de Cuentas:</b> Online: -- € | Ahorro: -- €")
        
        btn_importar_online = QPushButton("📥 Importar TXT Online")
        btn_importar_online.clicked.connect(lambda: self.solicitar_importacion_txt("ONLINE"))
        
        btn_importar_ahorro = QPushButton("🐷 Importar TXT Ahorro")
        btn_importar_ahorro.clicked.connect(lambda: self.solicitar_importacion_txt("AHORRO"))
        
        btn_auditoria = QPushButton("🔍 Ventana de Auditoría Histórica")
        btn_auditoria.setStyleSheet("background-color: #1f2937; color: white; font-weight: bold; padding: 4px 10px;")
        btn_auditoria.clicked.connect(self.abrir_ventana_auditoria)
        
        ly_banco.addWidget(self.lbl_status_banco, stretch=1)
        ly_banco.addWidget(btn_importar_online)
        ly_banco.addWidget(btn_importar_ahorro)
        ly_banco.addWidget(btn_auditoria)
        layout_principal.addWidget(frame_banco)
        
        # =====================================================================
        # 4. BARRA DE FILTRADO Y REGISTROS
        # =====================================================================
        ly_cabecera = QHBoxLayout()
        self.lbl_titulo_tabla = QLabel("<b>📋 Flujo de Trabajo Activo (Últimos 60 días)</b>")
        self.lbl_titulo_tabla.setStyleSheet("color: #0f172a; font-size: 13px;")
        ly_cabecera.addWidget(self.lbl_titulo_tabla, stretch=1)
        ly_cabecera.addWidget(QLabel("<b>Ver filas:</b>"))
        
        self.combo_paginacion = QComboBox()
        self.combo_paginacion.addItems(["25", "50", "100", "Todos posterior"])
        self.combo_paginacion.setCurrentText("100")  
        self.combo_paginacion.currentTextChanged.connect(self.renderizar_pagina_actual)
        ly_cabecera.addWidget(self.combo_paginacion)
        layout_principal.addLayout(ly_cabecera)
        
        # =====================================================================
        # 5. MATRIZ FINANCIERA PRINCIPAL (PARTE INFERIOR)
        # =====================================================================
        self.table_finanzas = QTableWidget()
        self.table_finanzas.setColumnCount(10)
        self.table_finanzas.setHorizontalHeaderLabels([
            "ID Hito Asignado", "Fecha / Cuenta", "Concepto / Acción (Extracto Banco)", 
            "Previsto In", "Previsto Out", "Real In", "Real Out", "Desviación", "Ficheros", "Acción"
        ])
        self.table_finanzas.setSortingEnabled(False) 
        self.table_finanzas.setWordWrap(True) 
        
        fuente_compacta = QFont()
        fuente_compacta.setPointSize(9)
        self.table_finanzas.setFont(fuente_compacta)
        
        header = self.table_finanzas.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout_principal.addWidget(self.table_finanzas)

    def refresh_data(self, hitos_dict, catalogos):
        """Llamado por el Core. Inyecta datos en frío de manera idéntica a tiempo_view.py"""
        self.hitos_cache = hitos_dict
        
        # Sincronización limpia del combo sin disparos en bucle
        self.combo_vincular_hito.blockSignals(True)
        self.combo_vincular_hito.clear()
        
        lista_hitos_ordenados = sorted(list(hitos_dict.keys()))
        for h_id in lista_hitos_ordenados:
            nombre_breve = hitos_dict[h_id].get("nombre_accion", "")[:30]
            self.combo_vincular_hito.addItem(f"{h_id} ({nombre_breve}...)", h_id)
        self.combo_vincular_hito.blockSignals(False)
            
        # Forzar el refresco inicial reactivo en la carga del panel de control financiero
        sincronizar_contexto_hito_labels(self.combo_vincular_hito.currentText(), self.hitos_cache, self.lbl_auto_proyecto, self.lbl_auto_crono)

        # Carga del repositorio maestro JSON de Finanzas
        master_data = self.core._load_json(self.core.cronogramas_path)
        fin_globales = master_data.get("finanzas_globales", {})
        historico_bancario = fin_globales.get("historico_bancario", [])
        previsiones_manuales = fin_globales.get("previsiones_futuras", [])
        
        hoy = datetime.now()
        limite_60_dias = hoy - timedelta(days=60)
        limite_6_meses = hoy - timedelta(days=180)
        
        tot_prev_in, tot_prev_out = 0.0, 0.0
        tot_real_in, tot_real_out = 0.0, 0.0
        
        self.registros_filtrados_cache = []
        
        # 1. Previsiones de Hitos Automáticos
        for hito_id, info in hitos_dict.items():
            fin_node = info.get("finanzas", {}) if isinstance(info, dict) else {}
            if not fin_node: continue
            
            p_in = float(fin_node.get("ingresos_previstos", 0.0))
            p_out = float(fin_node.get("gastos_previstos", info.get("presupuesto_asignado", 0.0)))
            tot_prev_in += p_in
            tot_prev_out += p_out
            
            if p_in > 0 or p_out > 0:
                self.registros_filtrados_cache.append({
                    "hash_id": f"PREV-AUTO-{hito_id}",
                    "fecha": info.get("fecha_inicio", hoy.strftime("%Y-%m-%d")),
                    "concepto": f"🔄 Previsión automática: {info.get('nombre_accion', 'Gasto Hito')}",
                    "importe": p_in if p_in > 0 else -p_out,
                    "cuenta": "SISTEMA",
                    "id_hito": hito_id,
                    "_fecha_dt": datetime.max,
                    "ficheros_adjuntos": []
                })

        # 2. Previsiones Manuales de Planificación
        for prev in previsiones_manuales:
            imp = prev.get("importe", 0.0)
            if imp > 0: tot_prev_in += imp
            else: tot_prev_out += abs(imp)
            
            try:
                f_dt = datetime.strptime(prev.get("fecha_impacto", ""), "%Y-%m-%d")
                f_visual = f_dt.strftime("%d/%m/%Y")
            except ValueError:
                f_visual = hoy.strftime("%d/%m/%Y")
                f_dt = hoy

            self.registros_filtrados_cache.append({
                "hash_id": prev.get("hash_id"),
                "fecha": f_visual,
                "concepto": f"🔮 [Plan] {prev.get('concepto')}",
                "importe": imp,
                "cuenta": "SISTEMA",
                "id_hito": prev.get("id_hito_vinculado"),
                "_fecha_dt": f_dt,
                "ficheros_adjuntos": []
            })

        # 3. Historial Real de Bancos
        for tx in historico_bancario:
            fecha_str = tx.get("fecha", "").strip()
            importe = float(tx.get("importe", 0.0))
            
            try:
                fecha_tx = datetime.strptime(fecha_str[:10], "%d/%m/%Y")
            except ValueError:
                try:
                    fecha_tx = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                except ValueError:
                    fecha_tx = hoy - timedelta(days=365)
            
            if fecha_tx >= limite_6_meses:
                if importe > 0: tot_real_in += importe
                else: tot_real_out += abs(importe)
                
            if fecha_tx >= limite_60_dias:
                tx_copia = tx.copy()
                tx_copia["_fecha_dt"] = fecha_tx
                self.registros_filtrados_cache.append(tx_copia)

        self.registros_filtrados_cache.sort(key=lambda x: (0 if x.get("cuenta") == "SISTEMA" else 1, x.get("_fecha_dt", datetime.min)))

        # Repintar KPI Scorecards superiores
        neto_p = tot_prev_in - tot_prev_out
        neto_r = tot_real_in - tot_real_out
        desv = neto_r - neto_p
        self.lbl_kpi_previsto.setText(f"{neto_p:.2f} €")
        self.lbl_kpi_real.setText(f"{neto_r:.2f} €")
        self.lbl_kpi_desviacion.setText(f"{desv:+.2f} €")
        
        self.card_desviacion.setStyleSheet("QFrame { background-color: #e6ffed; border: 2px solid #2da44e; border-radius: 6px; }" if desv >= 0 else "QFrame { background-color: #fee2e2; border: 2px solid #ef4444; border-radius: 6px; }")
        self.lbl_kpi_desviacion.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a7f37;" if desv >= 0 else "font-size: 18px; font-weight: bold; color: #991b1b;")
        
        self.renderizar_pagina_actual()

    def renderizar_pagina_actual(self):
        """Pinta la matriz financiera de forma limpia."""
        self.table_finanzas.setSortingEnabled(False)
        self.table_finanzas.setRowCount(0)
        
        seleccion_combo = self.combo_paginacion.currentText()
        limite_filas = len(self.registros_filtrados_cache) if seleccion_combo == "Todos posterior" else int(seleccion_combo)
            
        lista_hitos_combo = [" [ SIN ASIGNAR ] "] + sorted(list(self.hitos_cache.keys()))
        subconjunto_registros = self.registros_filtrados_cache[:limite_filas]
        
        for local_row_idx, tx in enumerate(subconjunto_registros):
            self.table_finanzas.insertRow(local_row_idx)
            
            hash_id = tx.get("hash_id", "")
            cuenta_tx = tx.get("cuenta", "ONLINE")
            concepto_tx = tx.get("concepto", "-")
            hito_assigned = tx.get("id_hito", "")
            importe = float(tx.get("importe", 0.0))
            adjuntos = tx.get("ficheros_adjuntos", [])
            
            p_in, p_out = (importe, 0.0) if (cuenta_tx == "SISTEMA" and importe > 0) else (0.0, abs(importe) if cuenta_tx == "SISTEMA" else 0.0)
            r_in, r_out = (importe, 0.0) if (cuenta_tx != "SISTEMA" and importe > 0) else (0.0, abs(importe) if cuenta_tx != "SISTEMA" else 0.0)
            
            if cuenta_tx != "SISTEMA" and hito_assigned in self.hitos_cache:
                f_node = self.hitos_cache[hito_assigned].get("finanzas", {}) if isinstance(self.hitos_cache[hito_assigned], dict) else {}
                p_in = float(f_node.get("ingresos_previstos", 0.0))
                p_out = float(f_node.get("gastos_previstos", self.hitos_cache[hito_assigned].get("presupuesto_asignado", 0.0)))

            combo_celda = QComboBox()
            combo_celda.addItems(lista_hitos_combo)
            combo_celda.setCurrentText(hito_assigned if hito_assigned in self.hitos_cache else " [ SIN ASIGNAR ] ")
            combo_celda.setProperty("tx_hash_id", hash_id)
            
            if cuenta_tx == "SISTEMA":
                combo_celda.setEnabled(False)
            else:
                combo_celda.blockSignals(True)
                combo_celda.currentTextChanged.connect(self.on_celda_hito_cambiado)
                combo_celda.blockSignals(False)
            self.table_finanzas.setCellWidget(local_row_idx, 0, combo_celda)
            
            origen_visual = f"⚙️ {tx.get('fecha')} [PREV]" if cuenta_tx == "SISTEMA" else (f"✍️ {tx.get('fecha')} [MAN]" if cuenta_tx == "MANUAL" else f"📅 {tx.get('fecha')} [{cuenta_tx}]")
            item_origen = QTableWidgetItem(origen_visual)
            item_origen.setFlags(item_origen.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_finanzas.setItem(local_row_idx, 1, item_origen)
            
            item_concepto = QTableWidgetItem(concepto_tx)
            item_concepto.setFlags(item_concepto.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_finanzas.setItem(local_row_idx, 2, item_concepto)
            
            v_p_in = QTableWidgetItem(f"{p_in:.2f} €" if p_in > 0 else "-")
            v_p_in.setFlags(v_p_in.flags() & ~Qt.ItemFlag.ItemIsEditable)
            v_p_in.setTextAlignment(Qt.AlignRight | Qt.AlignVertical)
            self.table_finanzas.setItem(local_row_idx, 3, v_p_in)
            
            v_p_out = QTableWidgetItem(f"{p_out:.2f} €" if p_out > 0 else "-")
            v_p_out.setFlags(v_p_out.flags() & ~Qt.ItemFlag.ItemIsEditable)
            v_p_out.setTextAlignment(Qt.AlignRight | Qt.AlignVertical)
            self.table_finanzas.setItem(local_row_idx, 4, v_p_out)
            
            v_r_in = QTableWidgetItem(f"{r_in:.2f} €" if r_in > 0 else "-")
            v_r_in.setFlags(v_r_in.flags() & ~Qt.ItemFlag.ItemIsEditable)
            v_r_in.setTextAlignment(Qt.AlignRight | Qt.AlignVertical)
            self.table_finanzas.setItem(local_row_idx, 5, v_r_in)
            
            v_r_out = QTableWidgetItem(f"{r_out:.2f} €" if r_out > 0 else "-")
            v_r_out.setFlags(v_r_out.flags() & ~Qt.ItemFlag.ItemIsEditable)
            v_r_out.setTextAlignment(Qt.AlignRight | Qt.AlignVertical)
            self.table_finanzas.setItem(local_row_idx, 6, v_r_out)
            
            neto_linea = (r_in - r_out) - (p_in - p_out) if cuenta_tx != "SISTEMA" else 0.0
            item_desv = QTableWidgetItem(f"{neto_linea:+.2f} €" if cuenta_tx != "SISTEMA" else "-")
            item_desv.setFlags(item_desv.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_desv.setTextAlignment(Qt.AlignRight | Qt.AlignVertical)
            if cuenta_tx != "SISTEMA":
                item_desv.setForeground(QColor("#1a7f37") if neto_linea >= 0 else QColor("#991b1b"))
            self.table_finanzas.setItem(local_row_idx, 7, item_desv)
            
            txt_fdu = f"📎 ({len(adjuntos)})" if adjuntos else "➕ Adjuntar"
            item_fdu = QTableWidgetItem(txt_fdu)
            item_fdu.setFlags(item_fdu.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_fdu.setTextAlignment(Qt.AlignCenter | Qt.AlignVertical)
            if adjuntos:
                item_fdu.setForeground(QColor("#0969da"))
            self.table_finanzas.setItem(local_row_idx, 8, item_fdu)
            
            btn_limbo = QPushButton("🎯 Desvincular")
            btn_limbo.setStyleSheet("font-size: 10px; padding: 2px;")
            if cuenta_tx == "SISTEMA": 
                btn_limbo.setEnabled(False)
            else: 
                btn_limbo.clicked.connect(lambda checked=False, h_id=hash_id: self.desvincular_registro_banco(h_id))
            self.table_finanzas.setCellWidget(local_row_idx, 9, btn_limbo)

        self.table_finanzas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        try: self.table_finanzas.customContextMenuRequested.disconnect()
        except Exception: pass
        self.table_finanzas.customContextMenuRequested.connect(self.mostrar_menu_contextual_tabla_principal)

        for c in range(self.table_finanzas.columnCount()):
            if c != 2: self.table_finanzas.resizeColumnToContents(c)
        self.table_finanzas.setSortingEnabled(True)
        self.recargar_balances_interfaz()

    def adjuntar_fichero_temporal_formulario(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Justificante o Factura", "", "Todos (*.md *.pdf *.png *.jpg)")
        if not file_path: return
        id_temporal_form = "FINANZAS-PRE-REGISTRO"
        exito, resultado = self.core.adjuntar_fichero_existente(id_temporal_form, file_path)
        if exito:
            self.ficheros_temporales_formulario.append(resultado)
            self.btn_adjuntar_form.setText(f"📎 Justificante ({len(self.ficheros_temporales_formulario)})")
            self.btn_adjuntar_form.setStyleSheet("background-color: #e6ffed; color: #1a7f37; font-weight: bold;")
        else:
            QMessageBox.critical(self, "Error FDU", resultado)

    def solicitar_importacion_txt(self, tipo_cuenta):
        ruta_sugerida = self.servicio_caja.ruta_online if tipo_cuenta == "ONLINE" else self.servicio_caja.ruta_ahorro
        file_path, _ = QFileDialog.getOpenFileName(self, f"Importar Extracto - {tipo_cuenta}", ruta_sugerida, "Archivos (*.txt)")
        if not file_path: return
        try:
            resultado = self.servicio_caja.procesar_txt_extracto(file_path, tipo_cuenta)
            nuevos = resultado.get('nuevos', 0)
            duplicados = resultado.get('duplicados', 0)
            QMessageBox.information(self, "Pasarela Bancaria Sincronizada", f"📊 Extracto ({tipo_cuenta}):\n\n🔹 Nuevos: {nuevos}\n🛡️ Duplicados omitidos: {duplicados}")
            if self.parent_window: self.parent_window.actualizar_todo()
        except Exception as e:
            QMessageBox.critical(self, "Error de Importación", str(e))

    def recargar_balances_interfaz(self):
        master_data = self.core._load_json(self.core.cronogramas_path)
        balances = master_data.get("finanzas_globales", {}).get("balances_apertura", {"ONLINE": 0.0, "AHORRO": 0.0})
        self.lbl_status_banco.setText(f"<b>Apertura de Cuentas:</b> Online: <font color='#0969da'>{balances.get('ONLINE', 0.0):.2f}€</font> | Ahorro: <font color='#1a7f37'>{balances.get('AHORRO', 0.0):.2f}€</font>")

    def procesar_bala_local(self):
        """Aplica la misma extracción de ID de hito mediante split que tiempo_view.py"""
        hito_texto = self.combo_vincular_hito.currentText()
        concepto = self.in_f_concepto.text().strip()
        cantidad_raw = self.in_f_cantidad.text().strip()
        
        if not hito_texto or not concepto or not cantidad_raw: 
            QMessageBox.warning(self, "Campos Incompletos", "Por favor, selecciona un hito operativo, rellena concepto e importe.")
            return
            
        id_hito = hito_texto.split(" ")[0]
        try:
            importe = float(cantidad_raw.replace(",", "."))
        except ValueError: 
            QMessageBox.warning(self, "Formato Incorrecto", "El importe debe ser un número válido.")
            return
        
        if "GASTO" in self.combo_f_naturaleza.currentText() and importe > 0: 
            importe = -importe

        if "PREVISIÓN" in self.combo_f_estado.currentText():
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            info_h = self.hitos_cache.get(id_hito, {})
            crono_id = info_h.get("id_cronograma_tipo", "SIPA")
            tipo_h = "BASICO" if crono_id == "SIPA" else "OPERATIVO"
            self.servicio_caja.inyectar_prevision_economica(id_hito, tipo_h, concepto, importe, fecha_hoy)
        else:
            master_data = self.core._load_json(self.core.cronogramas_path)
            historico = master_data.setdefault("finanzas_globales", {}).setdefault("historico_bancario", [])
            historico.append({
                "hash_id": f"MANUAL-{uuid.uuid4().hex[:8].upper()}",
                "fecha": datetime.now().strftime("%d/%m/%Y"),
                "concepto": concepto,
                "importe": importe,
                "cuenta": "MANUAL",
                "id_hito": id_hito,
                "fecha_importacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ficheros_adjuntos": list(self.ficheros_temporales_formulario)
            })
            self.core._save_json(self.core.cronogramas_path, master_data)
            
        self.in_f_concepto.clear()
        self.in_f_cantidad.clear()
        self.ficheros_temporales_formulario = []
        self.btn_adjuntar_form.setText("📎 Justificante (0)")
        self.btn_adjuntar_form.setStyleSheet("")
        
        if self.parent_window: self.parent_window.actualizar_todo()

    def mostrar_menu_contextual_tabla_principal(self, posicion):
        item = self.table_finanzas.itemAt(posicion)
        if not item: return
        row = item.row()
        seleccion_combo = self.combo_paginacion.currentText()
        limite_filas = len(self.registros_filtrados_cache) if seleccion_combo == "Todos posterior" else int(seleccion_combo)
        subconjunto = self.registros_filtrados_cache[:limite_filas]
        if row >= len(subconjunto): return
        tx = subconjunto[row]
        if tx.get("cuenta") == "SISTEMA": return
        
        hash_id = tx.get("hash_id")
        adjuntos = tx.get("ficheros_adjuntos", [])
        
        menu = QMenu(self)
        accion_adjuntar = menu.addAction("📎 Adjuntar Justificante / Factura")
        menu_abrir = menu.addMenu("📂 Abrir Fichero Adjunto") if adjuntos else None
        if menu_abrir:
            for arch in adjuntos: menu_abrir.addAction(arch)
        menu_borrar = menu.addMenu("❌ Desvincular Fichero") if adjuntos else None
        if menu_borrar:
            for arch in adjuntos: menu_borrar.addAction(arch)

        accion_seleccionada = menu.exec(self.table_finanzas.mapToGlobal(posicion))
        if not accion_seleccionada: return

        if accion_seleccionada == accion_adjuntar:
            self.ejecutar_adjuntado_fdu_directo(hash_id)
        elif menu_abrir and accion_seleccionada in menu_abrir.actions():
            self.abrir_fichero_fdu_so(accion_seleccionada.text())
        elif menu_borrar and accion_seleccionada in menu_borrar.actions():
            self.eliminar_referencia_fdu_registro(hash_id, accion_seleccionada.text())

    def ejecutar_adjuntado_fdu_directo(self, hash_id):
        file_path, _ = QFileDialog.getOpenFileName(self, "Asociar Fichero", "", "Formatos (*.md *.pdf *.png *.jpg)")
        if not file_path: return
        exito, resultado = self.core.adjuntar_fichero_existente(hash_id, file_path)
        if exito:
            master_data = self.core._load_json(self.core.cronogramas_path)
            for tx in master_data.get("finanzas_globales", {}).get("historico_bancario", []):
                if tx.get("hash_id") == hash_id:
                    adjuntos = tx.setdefault("ficheros_adjuntos", [])
                    if resultado not in adjuntos: adjuntos.append(resultado)
                    break
            self.core._save_json(self.core.cronogramas_path, master_data)
            if self.parent_window: self.parent_window.actualizar_todo()

    def abrir_fichero_fdu_so(self, nombre_archivo):
        ruta_lista, resultado = self.core.preparar_fichero_para_edicion(nombre_archivo)
        if not ruta_lista: return
        if os.name == 'nt': os.startfile(ruta_lista)
        else: subprocess.Popen(['xdg-open', ruta_lista])

    def eliminar_referencia_fdu_registro(self, hash_id, nombre_archivo):
        if QMessageBox.question(self, "Quitar Fichero", f"¿Quitar '{nombre_archivo}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            master_data = self.core._load_json(self.core.cronogramas_path)
            for tx in master_data.get("finanzas_globales", {}).get("historico_bancario", []):
                if tx.get("hash_id") == hash_id:
                    if nombre_archivo in tx.get("ficheros_adjuntos", []): tx["ficheros_adjuntos"].remove(nombre_archivo)
                    break
            self.core._save_json(self.core.cronogramas_path, master_data)
            if self.parent_window: self.parent_window.actualizar_todo()

    def on_celda_hito_cambiado(self, nuevo_hito_texto):
        combo = self.sender()
        if not combo or not combo.property("tx_hash_id"): return
        id_hito_final = "" if "SIN ASIGNAR" in nuevo_hito_texto else nuevo_hito_texto.split(" ")[0]
        master_data = self.core._load_json(self.core.cronogramas_path)
        for tx in master_data.get("finanzas_globales", {}).get("historico_bancario", []):
            if tx.get("hash_id") == combo.property("tx_hash_id"):
                tx["id_hito"] = id_hito_final
                break
        self.core._save_json(self.core.cronogramas_path, master_data)
        if self.parent_window: self.parent_window.actualizar_todo()

    def desvincular_registro_banco(self, hash_id):
        master_data = self.core._load_json(self.core.cronogramas_path)
        for tx in master_data.get("finanzas_globales", {}).get("historico_bancario", []):
            if tx.get("hash_id") == hash_id:
                tx["id_hito"] = ""
                break
        self.core._save_json(self.core.cronogramas_path, master_data)
        if self.parent_window: self.parent_window.actualizar_todo()

    # =====================================================================
    # 🔍 CONSOLA DE AUDITORÍA HISTÓRICA FRÍA CON BUSCADOR OPTIMIZADO
    # =====================================================================
    def abrir_ventana_auditoria(self):
        """Consola de asignación con buscador optimizado."""
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Auditoría Histórica Fría")
        dialogo.resize(1150, 650)
        ly_dialogo = QVBoxLayout(dialogo)
        
        ly_buscador = QHBoxLayout()
        ly_buscador.addWidget(QLabel("<b>🔍 Filtrar Historial:</b>"))
        in_buscar = QLineEdit()
        ly_buscador.addWidget(in_buscar)
        ly_dialogo.addLayout(ly_buscador)
        
        tabla_auditoria = QTableWidget()
        tabla_auditoria.setColumnCount(5)
        tabla_auditoria.setHorizontalHeaderLabels(["Hito Vinculado", "Fecha / Cuenta", "Concepto de Extracto", "Importe", "Ficheros"])
        tabla_auditoria.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tabla_auditoria.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        ly_dialogo.addWidget(tabla_auditoria)
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        historico = master_data.get("finanzas_globales", {}).get("historico_bancario", [])
        lista_hitos = [" [ SIN ASIGNAR ] "] + [f"{h_id} ({self.hitos_cache[h_id].get('nombre_accion', '')[:20]}...)" for h_id in sorted(list(self.hitos_cache.keys()))]
        
        tabla_auditoria.setRowCount(len(historico))
        referencias_filas = []
        
        for row, tx in enumerate(historico):
            hash_id = tx.get("hash_id", "")
            hito_asig = tx.get("id_hito", "")
            concepto_clean = tx.get("concepto", "-")
            importe_clean = float(tx.get("importe", 0.0))
            
            c_combo = QComboBox()
            c_combo.addItems(lista_hitos)
            
            texto_inicial = " [ SIN ASIGNAR ] "
            if hito_asig in self.hitos_cache:
                texto_inicial = f"{hito_asig} ({self.hitos_cache[hito_asig].get('nombre_accion', '')[:20]}...)"
            c_combo.setCurrentText(texto_inicial)
            
            def al_cambiar_historico(txt, h_id=hash_id):
                final_hito = "" if "SIN ASIGNAR" in txt else txt.split(" ")[0]
                m_data = self.core._load_json(self.core.cronogramas_path)
                for t in m_data.get("finanzas_globales", {}).get("historico_bancario", []):
                    if t.get("hash_id") == h_id: t["id_hito"] = final_hito; break
                self.core._save_json(self.core.cronogramas_path, m_data)
            
            c_combo.currentTextChanged.connect(al_cambiar_historico)
            tabla_auditoria.setCellWidget(row, 0, c_combo)
            
            txt_origen = f"{tx.get('fecha')} [{tx.get('cuenta')}]"
            tabla_auditoria.setItem(row, 1, QTableWidgetItem(txt_origen))
            tabla_auditoria.setItem(row, 2, QTableWidgetItem(concepto_clean))
            
            item_imp = QTableWidgetItem(f"{importe_clean:.2f} €")
            item_imp.setForeground(QColor("#1a7f37") if importe_clean >= 0 else QColor("#991b1b"))
            tabla_auditoria.setItem(row, 3, item_imp)
            
            referencias_filas.append({"row_idx": row, "hash_id": hash_id, "texto_busqueda": f"{concepto_clean} {txt_origen}".lower()})
            
        in_buscar.textChanged.connect(lambda t: [tabla_auditoria.setRowHidden(r["row_idx"], not (not t.strip() or t.lower() in r["texto_busqueda"])) for r in referencias_filas])
        
        btn_cerrar = QPushButton("💾 Sincronizar Cambios de Auditoría")
        btn_cerrar.clicked.connect(dialogo.accept)
        ly_dialogo.addWidget(btn_cerrar)
        
        if dialogo.exec() == QDialog.Accepted and self.parent_window:
            self.parent_window.actualizar_todo()