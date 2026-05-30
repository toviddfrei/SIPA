#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QFrame, QMessageBox, QComboBox, QFileDialog, QHeaderView, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# Servicio especializado
from core.services.sesipaeco_caja import SESIPAecoCajaService

class FinanzasTab(QWidget):
    def __init__(self, core_base, parent=None):
        super().__init__(parent)
        self.core = core_base
        
        # Cachés relacionales locales
        self.hitos_locales_cache = {}
        self.catalogos_locales_cache = {}
        
        # Lista en memoria de registros pre-filtrados para la paginación activa
        self.registros_filtrados_cache = []
        
        # Instanciamos el servicio financiero
        self.servicio_caja = SESIPAecoCajaService(self.core)
        
        # Inicializar UI
        self.init_ui()

    def init_ui(self):
        """Construye la interfaz simplificada, ultra-ligera y con paginación avanzada."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(10)
        
        # --- 1. SCORECARDS METRICAS (CALCULO DE PERSPECTIVA DE 6 MESES) ---
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
        
        # --- 2. PANEL DE PASARELA BANCARIA (.TXT) Y AUDITORÍA ---
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
        
        # --- 3. FORMULARIO DE INPUT DE NUEVO REGISTRO (CON VALORES COMPUESTOS) ---
        frame_form = QFrame()
        frame_form.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; }")
        form_layout = QHBoxLayout(frame_form)
        form_layout.setContentsMargins(8, 8, 8, 8)
        
        self.combo_f_crono = QComboBox()
        self.combo_f_crono.setFixedWidth(140)
        self.combo_f_crono.currentTextChanged.connect(self.on_crono_changed)
        
        self.combo_f_hito = QComboBox()
        self.combo_f_hito.setFixedWidth(160)
        
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
        
        btn_disparar = QPushButton("🚀 Fichar Caja")
        btn_disparar.setStyleSheet("background-color: #0969da; color: white; font-weight: bold; padding: 4px 12px; border-radius: 4px;")
        btn_disparar.clicked.connect(self.procesar_bala_local)
        
        form_layout.addWidget(QLabel("<b>Crono:</b>"))
        form_layout.addWidget(self.combo_f_crono)
        form_layout.addWidget(QLabel("<b>Hito:</b>"))
        form_layout.addWidget(self.combo_f_hito)
        form_layout.addWidget(self.combo_f_naturaleza)
        form_layout.addWidget(self.combo_f_estado)
        form_layout.addWidget(self.in_f_concepto)
        form_layout.addWidget(self.in_f_cantidad)
        form_layout.addWidget(btn_disparar)
        layout_principal.addWidget(frame_form)
        
        # --- 4. BARRA DE CABECERA DE TABLA CON ABANICO DE PAGINACIÓN ---
        ly_cabecera_tabla = QHBoxLayout()
        self.lbl_titulo_tabla = QLabel("<b>📋 Flujo de Trabajo Activo (Desde 31/03/2026)</b>")
        self.lbl_titulo_tabla.setStyleSheet("color: #0f172a; font-size: 13px;")
        
        ly_cabecera_tabla.addWidget(self.lbl_titulo_tabla, stretch=1)
        
        # Paginador elástico solicitado para el abanico anterior/posterior
        ly_cabecera_tabla.addWidget(QLabel("<b>Ver filas:</b>"))
        self.combo_paginacion = QComboBox()
        self.combo_paginacion.addItems(["25", "50", "100", "Todos posterior"])
        self.combo_paginacion.setCurrentText("100")  # Valor por defecto seguro y rápido
        self.combo_paginacion.currentTextChanged.connect(self.renderizar_pagina_actual)
        ly_cabecera_tabla.addWidget(self.combo_paginacion)
        
        layout_principal.addLayout(ly_cabecera_tabla)
        
        # --- 5. MATRIZ FINANCIERA (ESTILO BÁSICO, MÁXIMO RENDIMIENTO) ---
        self.table_finanzas = QTableWidget()
        self.table_finanzas.setColumnCount(9)
        self.table_finanzas.setHorizontalHeaderLabels([
            "ID Hito Asignado", "Fecha / Cuenta", "Concepto / Acción (Extracto Banco)", "Previsto In", "Previsto Out", "Real In", "Real Out", "Desviación", "Acción"
        ])
        self.table_finanzas.setSortingEnabled(False) 
        self.table_finanzas.setWordWrap(True) # Ajuste a lo ancho activo
        
        header = self.table_finanzas.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout_principal.addWidget(self.table_finanzas)

    def poblar_combos_filtrado(self, catalogos):
        self.combo_f_crono.blockSignals(True)
        self.combo_f_crono.clear()
        cronos_tipos = catalogos.get("cronogramas_tipos", {})
        if cronos_tipos:
            for c_id, c_info in cronos_tipos.items():
                self.combo_f_crono.addItem(f"{c_info.get('codigo', c_id)} ({c_id})", c_id)
        else:
            self.combo_f_crono.addItem("SIPAeco Global", "SIPA")
        self.combo_f_crono.blockSignals(False)
        self.on_crono_changed()

    def on_crono_changed(self):
        self.combo_f_hito.clear()
        idx = self.combo_f_crono.currentIndex()
        if idx < 0: return
        crono_id_target = self.combo_f_crono.itemData(idx)
        hitos_filtrados = []
        for hito_id, info in self.hitos_locales_cache.items():
            if info.get("id_cronograma") == crono_id_target or info.get("cronograma_id") == crono_id_target:
                hitos_filtrados.append(hito_id)
        if hitos_filtrados:
            self.combo_f_hito.addItems(sorted(hitos_filtrados))
        else:
            self.combo_f_hito.addItem("[Sin hitos]", "")

    def solicitar_importacion_txt(self, tipo_cuenta):
        ruta_sugerida = self.servicio_caja.ruta_online if tipo_cuenta == "ONLINE" else self.servicio_caja.ruta_ahorro
        file_path, _ = QFileDialog.getOpenFileName(self, f"Importar Extracto - {tipo_cuenta}", ruta_sugerida, "Archivos (*.txt)")
        if not file_path: return
        try:
            resultado = self.servicio_caja.procesar_txt_extracto(file_path, tipo_cuenta)
            QMessageBox.information(self, "Sincronizado", f"Añadidos: {resultado['nuevos']} | Omitidos por Duplicidad: {resultado['duplicados']}")
            if hasattr(self.window(), 'actualizar_todo'): self.window().actualizar_todo()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def recargar_balances_interfaz(self):
        master_data = self.core._load_json(self.core.cronogramas_path)
        balances = master_data.get("finanzas_globales", {}).get("balances_apertura", {"ONLINE": 0.0, "AHORRO": 0.0})
        self.lbl_status_banco.setText(f"<b>Apertura de Cuentas:</b> Online: <font color='#0969da'>{balances.get('ONLINE', 0.0):.2f}€</font> | Ahorro: <font color='#1a7f37'>{balances.get('AHORRO', 0.0):.2f}€</font>")

    def procesar_bala_local(self):
        hito_target = self.combo_f_hito.currentText()
        concepto = self.in_f_concepto.text().strip()
        cantidad_raw = self.in_f_cantidad.text().strip()
        if not hito_target or hito_target.startswith("[") or not concepto or not cantidad_raw: return
        try:
            importe = float(cantidad_raw.replace(",", "."))
        except ValueError: return
        if "GASTO" in self.combo_f_naturaleza.currentText() and importe > 0: importe = -importe

        master_data = self.core._load_json(self.core.cronogramas_path)
        historico = master_data.setdefault("finanzas_globales", {}).setdefault("historico_bancario", [])
        historico.append({
            "hash_id": f"MANUAL-{uuid.uuid4().hex[:8].upper()}",
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "concepto": concepto,
            "importe": importe,
            "cuenta": "MANUAL",
            "id_hito": hito_target,
            "fecha_importacion": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.core._save_json(self.core.cronogramas_path, master_data)
        self.in_f_concepto.clear()
        self.in_f_cantidad.clear()
        if hasattr(self.window(), 'actualizar_todo'): self.window().actualizar_todo()

    # =====================================================================
    # REFRESH DATA (PRE-FILTRADO EXCLUSIVO DE DATOS EN MEMORIA)
    # =====================================================================
    def refresh_data(self, hitos_dict, catalogos):
        """Carga y calcula los acumulados, aislando los datos calientes en la caché interna."""
        self.hitos_locales_cache = hitos_dict
        self.catalogos_locales_cache = catalogos
        
        if self.combo_f_crono.count() <= 1:
            self.poblar_combos_filtrado(catalogos)
            
        master_data = self.core._load_json(self.core.cronogramas_path)
        historico_bancario = master_data.get("finanzas_globales", {}).get("historico_bancario", [])
        
        hoy = datetime.now()
        limite_60_dias = hoy - timedelta(days=60)
        limite_6_meses = hoy - timedelta(days=180)
        
        tot_prev_in, tot_prev_out = 0.0, 0.0
        tot_real_in, tot_real_out = 0.0, 0.0
        
        self.registros_filtrados_cache = []
        
        # 1. Inyectar Previsiones automáticas desde la raíz de los hitos del JSON
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
                    "fecha": info.get("fecha_inicio", hoy.strftime("%d/%m/%Y")),
                    "concepto": f"🔄 Previsión automática: {info.get('nombre_accion', 'Gasto Hito')}",
                    "importe": p_in if p_in > 0 else -p_out,
                    "cuenta": "SISTEMA",
                    "id_hito": hito_id,
                    "_fecha_dt": datetime.max # Forzar previsiones arriba de la lista siempre
                })

        # 2. Filtrado con parseo DD/MM/AAAA real del extracto bancario
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
                
            # TIJERETAZO BIMENSUAL (Desde finales de marzo en adelante)
            if fecha_tx >= limite_60_dias:
                tx_copia = tx.copy()
                tx_copia["_fecha_dt"] = fecha_tx
                self.registros_filtrados_cache.append(tx_copia)

        # Ordenar: Previsiones fijas arriba, banco abajo por fecha descendente
        self.registros_filtrados_cache.sort(key=lambda x: (0 if x.get("cuenta") == "SISTEMA" else 1, x.get("_fecha_dt", datetime.min)), reverse=False)

        # Pintar KPIs globales macro de la cabecera
        neto_p = tot_prev_in - tot_prev_out
        neto_r = tot_real_in - tot_real_out
        desv = neto_r - neto_p
        self.lbl_kpi_previsto.setText(f"{neto_p:.2f} €")
        self.lbl_kpi_real.setText(f"{neto_r:.2f} €")
        self.lbl_kpi_desviacion.setText(f"{desv:+.2f} €")
        self.card_desviacion.setStyleSheet("QFrame { background-color: #e6ffed; border: 2px solid #2da44e; border-radius: 6px; }" if desv >= 0 else "QFrame { background-color: #fee2e2; border: 2px solid #ef4444; border-radius: 6px; }")
        self.lbl_kpi_desviacion.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a7f37;" if desv >= 0 else "font-size: 18px; font-weight: bold; color: #991b1b;")
        
        # Renderizar el subconjunto según el combo de abanico activo
        self.renderizar_pagina_actual()

    # =====================================================================
    # MOTOR DE RENDERIZADO BASICO CON ALINEACION VERTICAL SUPERIOR (TOP)
    # =====================================================================
    def renderizar_pagina_actual(self):
        """Pinta de forma fluida y ultra-ligera limitando las filas y forzando alineación arriba."""
        self.table_finanzas.setSortingEnabled(False)
        self.table_finanzas.setRowCount(0)
        
        # Determinar límite del abanico del paginador elástico
        seleccion_combo = self.combo_paginacion.currentText()
        if seleccion_combo == "Todos posterior":
            limite_filas = len(self.registros_filtrados_cache)
        else:
            limite_filas = int(seleccion_combo)
            
        lista_hitos_combo = [" [ SIN ASIGNAR ] "] + sorted(list(self.hitos_locales_cache.keys()))
        subconjunto_registros = self.registros_filtrados_cache[:limite_filas]
        
        for local_row_idx, tx in enumerate(subconjunto_registros):
            self.table_finanzas.insertRow(local_row_idx)
            
            hash_id = tx.get("hash_id", "")
            cuenta_tx = tx.get("cuenta", "ONLINE")
            concepto_tx = tx.get("concepto", "-")
            hito_assigned = tx.get("id_hito", "")
            importe = float(tx.get("importe", 0.0))
            
            p_in, p_out = (importe, 0.0) if (cuenta_tx == "SISTEMA" and importe > 0) else (0.0, abs(importe) if cuenta_tx == "SISTEMA" else 0.0)
            r_in, r_out = (importe, 0.0) if (cuenta_tx != "SISTEMA" and importe > 0) else (0.0, abs(importe) if cuenta_tx != "SISTEMA" else 0.0)
            
            if cuenta_tx != "SISTEMA" and hito_assigned in self.hitos_locales_cache:
                f_node = self.hitos_locales_cache[hito_assigned].get("finanzas", {}) if isinstance(self.hitos_locales_cache[hito_assigned], dict) else {}
                p_in = float(f_node.get("ingresos_previstos", 0.0))
                p_out = float(f_node.get("gastos_previstos", self.hitos_locales_cache[hito_assigned].get("presupuesto_asignado", 0.0)))

            # --- ID HITO CELL ---
            combo_celda = QComboBox()
            combo_celda.addItems(lista_hitos_combo)
            combo_celda.setCurrentText(hito_assigned if hito_assigned in self.hitos_locales_cache else " [ SIN ASIGNAR ] ")
            combo_celda.setProperty("tx_hash_id", hash_id)
            
            if cuenta_tx == "SISTEMA":
                combo_celda.setEnabled(False)
            else:
                combo_celda.blockSignals(True)
                combo_celda.currentTextChanged.connect(self.on_celda_hito_cambiado)
                combo_celda.blockSignals(False)
                
            self.table_finanzas.setCellWidget(local_row_idx, 0, combo_celda)
            
            # --- CELL ITEMS CON ALINEACION STRICT TOP (EVITA FILAS DESCOMUNALES) ---
            origen_visual = f"⚙️ {tx.get('fecha')} [PREV]" if cuenta_tx == "SISTEMA" else (f"✍️ {tx.get('fecha')} [MAN]" if cuenta_tx == "MANUAL" else f"📅 {tx.get('fecha')} [{cuenta_tx}]")
            item_origen = QTableWidgetItem(origen_visual)
            item_origen.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.table_finanzas.setItem(local_row_idx, 1, item_origen)
            
            item_concepto = QTableWidgetItem(concepto_tx)
            item_concepto.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.table_finanzas.setItem(local_row_idx, 2, item_concepto)
            
            # Columnas numéricas
            v_p_in = QTableWidgetItem(f"{p_in:.2f} €" if p_in > 0 else "-")
            v_p_in.setTextAlignment(Qt.AlignRight | Qt.AlignTop)
            self.table_finanzas.setItem(local_row_idx, 3, v_p_in)
            
            v_p_out = QTableWidgetItem(f"{p_out:.2f} €" if p_out > 0 else "-")
            v_p_out.setTextAlignment(Qt.AlignRight | Qt.AlignTop)
            self.table_finanzas.setItem(local_row_idx, 4, v_p_out)
            
            v_r_in = QTableWidgetItem(f"{r_in:.2f} €" if r_in > 0 else "-")
            v_r_in.setTextAlignment(Qt.AlignRight | Qt.AlignTop)
            self.table_finanzas.setItem(local_row_idx, 5, v_r_in)
            
            v_r_out = QTableWidgetItem(f"{r_out:.2f} €" if r_out > 0 else "-")
            v_r_out.setTextAlignment(Qt.AlignRight | Qt.AlignTop)
            self.table_finanzas.setItem(local_row_idx, 6, v_r_out)
            
            # Desviación
            neto_linea = (r_in - r_out) - (p_in - p_out) if cuenta_tx != "SISTEMA" else 0.0
            item_desv = QTableWidgetItem(f"{neto_linea:+.2f} €" if cuenta_tx != "SISTEMA" else "-")
            item_desv.setTextAlignment(Qt.AlignRight | Qt.AlignTop)
            if cuenta_tx != "SISTEMA":
                item_desv.setForeground(QColor("#1a7f37") if neto_linea >= 0 else QColor("#991b1b"))
            self.table_finanzas.setItem(local_row_idx, 7, item_desv)
            
            # Botón Desvincular
            btn_limbo = QPushButton("🎯 Desvincular")
            btn_limbo.setStyleSheet("font-size: 10px; padding: 2px;")
            if cuenta_tx == "SISTEMA": 
                btn_limbo.setEnabled(False)
            else: 
                btn_limbo.clicked.connect(lambda checked=False, h_id=hash_id: self.desvincular_registro_banco(h_id))
            self.table_finanzas.setCellWidget(local_row_idx, 8, btn_limbo)

        self.table_finanzas.resizeRowsToContents()
        self.table_finanzas.setSortingEnabled(True)
        self.recargar_balances_interfaz()

    def on_celda_hito_cambiado(self, nuevo_hito_texto):
        combo = self.sender()
        if not combo or not combo.property("tx_hash_id"): return
        id_hito_final = "" if "SIN ASIGNAR" in nuevo_hito_texto else nuevo_hito_texto
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        for tx in master_data.get("finanzas_globales", {}).get("historico_bancario", []):
            if tx.get("hash_id") == combo.property("tx_hash_id"):
                tx["id_hito"] = id_hito_final
                break
        self.core._save_json(self.core.cronogramas_path, master_data)
        if hasattr(self.window(), 'actualizar_todo'): self.window().actualizar_todo()

    def desvincular_registro_banco(self, hash_id):
        master_data = self.core._load_json(self.core.cronogramas_path)
        for tx in master_data.get("finanzas_globales", {}).get("historico_bancario", []):
            if tx.get("hash_id") == hash_id:
                tx["id_hito"] = ""
                break
        self.core._save_json(self.core.cronogramas_path, master_data)
        if hasattr(self.window(), 'actualizar_todo'): self.window().actualizar_todo()

    # =====================================================================
    # VENTANA DE AUDITORÍA HISTÓRICA CON ENTRADA DE FILTRO SÚPER RÁPIDA
    # =====================================================================
    def abrir_ventana_auditoria(self):
        """Consola de asignación en frío con buscador optimizado de texto estático."""
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Auditoría Histórica Fría - Buscador Dinámico")
        dialogo.resize(1100, 650)
        
        ly_dialogo = QVBoxLayout(dialogo)
        
        ly_buscador = QHBoxLayout()
        ly_buscador.addWidget(QLabel("<b>🔍 Filtrar Historial:</b>"))
        in_buscar = QLineEdit()
        in_buscar.setPlaceholderText("Escribe concepto, comercio, importe...")
        ly_buscador.addWidget(in_buscar)
        ly_dialogo.addLayout(ly_buscador)
        
        tabla_auditoria = QTableWidget()
        tabla_auditoria.setColumnCount(4)
        tabla_auditoria.setHorizontalHeaderLabels(["Hito Vinculado", "Fecha / Cuenta", "Concepto de Extracto", "Importe"])
        tabla_auditoria.setWordWrap(True)
        tabla_auditoria.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tabla_auditoria.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        ly_dialogo.addWidget(tabla_auditoria)
        
        master_data = self.core._load_json(self.core.cronogramas_path)
        historico = master_data.get("finanzas_globales", {}).get("historico_bancario", [])
        lista_hitos = [" [ SIN ASIGNAR ] "] + sorted(list(self.hitos_locales_cache.keys()))
        
        tabla_auditoria.setRowCount(len(historico))
        referencias_filas = []
        
        for row, tx in enumerate(historico):
            hash_id = tx.get("hash_id", "")
            hito_asig = tx.get("id_hito", "")
            concepto_clean = tx.get("concepto", "-")
            importe_clean = float(tx.get("importe", 0.0))
            
            c_combo = QComboBox()
            c_combo.addItems(lista_hitos)
            c_combo.setCurrentText(hito_asig if hito_asig in self.hitos_locales_cache else " [ SIN ASIGNAR ] ")
            c_combo.setProperty("hash_id", hash_id)
            
            def al_cambiar_historico(txt, h_id=hash_id):
                final_hito = "" if "SIN ASIGNAR" in txt else txt
                m_data = self.core._load_json(self.core.cronogramas_path)
                for t in m_data.get("finanzas_globales", {}).get("historico_bancario", []):
                    if t.get("hash_id") == h_id:
                        t["id_hito"] = final_hito
                        break
                self.core._save_json(self.core.cronogramas_path, m_data)
            
            c_combo.currentTextChanged.connect(al_cambiar_historico)
            tabla_auditoria.setCellWidget(row, 0, c_combo)
            
            txt_origen = f"{tx.get('fecha')} [{tx.get('cuenta')}]"
            
            # Items estáticos alineados estricto arriba para velocidad
            i_origen = QTableWidgetItem(txt_origen)
            i_origen.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            tabla_auditoria.setItem(row, 1, i_origen)
            
            i_concepto = QTableWidgetItem(concepto_clean)
            i_concepto.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            tabla_auditoria.setItem(row, 2, i_concepto)
            
            item_imp = QTableWidgetItem(f"{importe_clean:.2f} €")
            item_imp.setTextAlignment(Qt.AlignRight | Qt.AlignTop)
            item_imp.setForeground(QColor("#1a7f37") if importe_clean >= 0 else QColor("#991b1b"))
            tabla_auditoria.setItem(row, 3, item_imp)
            
            referencias_filas.append({
                "row_idx": row,
                "texto_busqueda": f"{concepto_clean} {txt_origen} {importe_clean}".lower()
            })
            
        tabla_auditoria.resizeRowsToContents()
        
        def filtrar_tabla_historica(texto_nuevo):
            query = texto_nuevo.lower().strip()
            tabla_auditoria.setUpdatesEnabled(False)
            for ref in referencias_filas:
                if not query or query in ref["texto_busqueda"]:
                    tabla_auditoria.setRowHidden(ref["row_idx"], False)
                else:
                    tabla_auditoria.setRowHidden(ref["row_idx"], True)
            tabla_auditoria.setUpdatesEnabled(True)

        in_buscar.textChanged.connect(filtrar_tabla_historica)
        
        btn_cerrar = QPushButton("💾 Sincronizar Cambios de Auditoría")
        btn_cerrar.setStyleSheet("background-color: #0969da; color: white; font-weight: bold; padding: 6px;")
        btn_cerrar.clicked.connect(dialogo.accept)
        ly_dialogo.addWidget(btn_cerrar)
        
        if dialogo.exec() == QDialog.Accepted:
            if hasattr(self.window(), 'actualizar_todo'):
                self.window().actualizar_todo()