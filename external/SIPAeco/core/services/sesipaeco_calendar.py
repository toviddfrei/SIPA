#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ubicación: core/services/sesipaeco_calendar.py
Descripción: Motor de cálculo e indexación de bloques semanales y mensuales para el calendario.
             CORRECCIÓN: Soporta múltiples impactos por hito el mismo día enviando ID único de sesión.
             COLD STORAGE: Redirección inteligente a capas frías basada en la fecha consultada.
Autor: Daniel Miñana Montero
Fecha: 2026-05-31
"""

import os
from datetime import datetime, timedelta

class SESIPAecoCalendarService:
    def __init__(self, core_base):
        self.core = core_base

    def obtener_rango_semanal(self, fecha_pivote):
        """Calcula el lunes y domingo de la semana de la fecha de pivote."""
        lunes = fecha_pivote - timedelta(days=fecha_pivote.weekday())
        domingo = lunes + timedelta(days=6)
        return lunes, domingo

    # =====================================================================
    # ⏱️ EXTRACCIÓN DE IMPACTOS DE TIEMPO (RESOLVIENDO DUPLICADOS Y CAPAS)
    # =====================================================================
    def obtener_impactos_tiempo_semana(self, fecha_pivote):
        """
        Filtra y agrupa los IMPACTOS REALES de TIEMPO (sesiones) de la semana activa.
        Resuelve el fallo de duplicados mapeando ID únicos de sesión para la interfaz.
        """
        lunes, domingo = self.obtener_rango_semanal(fecha_pivote)
        semana_data = {i: [] for i in range(7)}
        
        anio_pivote = fecha_pivote.year
        anio_actual = datetime.now().year
        
        # [COLD STORAGE] Redirección transparente según el año que se esté visualizando
        if anio_pivote < anio_actual:
            archive_path = os.path.join(self.core.data_dir, "archive", f"archive_tiempo_{anio_pivote}.json")
            sesiones_reales = self.core._load_json(archive_path).get("sesiones", []) if os.path.exists(archive_path) else []
        else:
            # Capa caliente activa
            sesiones_reales = self.core.obtener_sesiones(incluir_historico=False)
        
        for sesion in sesiones_reales:
            fecha_str = sesion.get("fecha", "")
            try:
                fecha_impacto = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
            except ValueError:
                continue 
            
            # Validar si cae en el rango de la semana solicitada
            if lunes.date() <= fecha_impacto.date() <= domingo.date():
                dia_semana = fecha_impacto.weekday() 
                
                # CORRECCIÓN: Inyectamos 'id_sesion_unico' para que la UI diferencie 
                # dos impactos distintos mapeados sobre un mismo hito en el mismo día.
                impacto_adaptado = {
                    "id_sesion_unico": sesion.get("id_sesion"), 
                    "id_cronograma_tipo": sesion.get("cronograma_id", "DEFECTO"),
                    "id_hito_nuclear": sesion.get("id_hito", "IMPACTO"),
                    "nombre_accion": sesion.get("tarea", "Sesión de Trabajo"),
                    "id_proyecto": "SIPA",
                    "fecha_inicio": sesion.get("hora_inicio"),
                    "fecha_fin": sesion.get("hora_fin"),
                    "horas_estimadas": sesion.get("horas_reales", 0.0),
                    "prioridad": "3 - MEDIA",
                    "repetitivo": False
                }
                semana_data[dia_semana].append(impacto_adaptado)
                
        return semana_data, lunes, domingo

    # =====================================================================
    # 💰 EXTRACCIÓN DE IMPACTOS ECONÓMICOS DESDE LOGS_FINANZAS
    # =====================================================================
    def obtener_finanzas_semana(self, fecha_pivote):
        """
        Escanea el registro bala de finanzas unificando capas anuales 
        para pintar el balance financiero por día en el calendario.
        """
        lunes, domingo = self.obtener_rango_semanal(fecha_pivote)
        semana_finanzas = {i: {"ingresos": 0.0, "gastos": 0.0, "detalles": []} for i in range(7)}
        
        # Determinar qué años cubre esta semana (evita roturas en semanas de fin de año)
        anios_a_revisar = list(set([lunes.year, domingo.year]))
        transacciones_reales = []
        
        for anio in anios_a_revisar:
            if anio < datetime.now().year:
                archive_path = os.path.join(self.core.data_dir, "archive", f"archive_finanzas_{anio}.json")
                if os.path.exists(archive_path):
                    transacciones_reales.extend(self.core._load_json(archive_path).get("transacciones", []))
            else:
                transacciones_reales.extend(self.core.obtener_finanzas(incluir_historico=False))
        
        for tx in transacciones_reales:
            fecha_str = tx.get("fecha", "").strip()
            try:
                fecha_tx = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
            except ValueError:
                try:
                    fecha_tx = datetime.strptime(fecha_str[:10], "%d/%m/%Y")
                except ValueError:
                    continue
            
            if lunes.date() <= fecha_tx.date() <= domingo.date():
                dia_semana = fecha_tx.weekday()
                cantidad = float(tx.get("cantidad", 0.0))
                tipo = tx.get("tipo", "GASTO").upper()
                es_real = tx.get("es_real", True)
                
                if tipo == "INGRESO":
                    semana_finanzas[dia_semana]["ingresos"] += cantidad
                else:
                    semana_finanzas[dia_semana]["gastos"] += cantidad
                
                semana_finanzas[dia_semana]["detalles"].append({
                    "id_transaccion": tx.get("id_transaccion"),
                    "tipo": "REAL" if es_real else "PREVISION",
                    "concepto": f"{'' if es_real else '🔮 '}{tx.get('concepto', 'Movimiento')}",
                    "importe": cantidad if tipo == "INGRESO" else -cantidad
                })

        return semana_finanzas