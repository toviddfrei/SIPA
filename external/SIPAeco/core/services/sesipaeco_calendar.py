#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ubicación: core/services/sesipaeco_calendar.py
Descripción: Motor de cálculo e indexación de bloques semanales para el calendario.
"""

from datetime import datetime, timedelta

class SESIPAecoCalendarService:
    def __init__(self, core_base):
        self.core = core_base

    def obtener_rango_semanal(self, fecha_pivote):
        """Calcula el lunes y domingo de la semana de la fecha de pivote."""
        # weekday() devuelve 0 para Lunes, 6 para Domingo
        lunes = fecha_pivote - timedelta(days=fecha_pivote.weekday())
        domingo = lunes + timedelta(days=6)
        return lunes, domingo

    def obtener_hitos_semana(self, hitos_dict, fecha_pivote):
        """Filtra y agrupa los hitos que caen dentro de la semana activa."""
        lunes, domingo = self.obtener_rango_semanal(fecha_pivote)
        
        # Estructura limpia para los 7 días de la semana
        semana_data = {i: [] for i in range(7)}
        
        for hito_id, info in hitos_dict.items():
            # Intentar parsear la fecha de fin o inicio del hito
            fecha_str = info.get("fecha_fin", info.get("fecha_inicio", ""))
            try:
                fecha_hito = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
            except ValueError:
                try:
                    fecha_hito = datetime.strptime(fecha_str[:10], "%d/%m/%Y")
                except ValueError:
                    continue # Si la fecha está corrupta, saltamos de forma segura
            
            # Si el hito cae en el rango de esta semana, lo asignamos a su día
            if lunes.date() <= fecha_hito.date() <= domingo.date():
                dia_semana = fecha_hito.weekday() # 0 = Lunes, 6 = Domingo
                hito_copia = info.copy()
                hito_copia["id_hito_nuclear"] = hito_id
                semana_data[dia_semana].append(hito_copia)
                
        return semana_data, lunes, domingo