#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco Service - Gestor de Datos de Informes y Documentación
Ubicación: SIPA/core/services/sesipaeco_report.py
Autor: Daniel Miñana Montero
Descripción: Componente lógico encapsulado para la gestión de datos, filtros,
             ordenación y persistencia de la pizarra analítica de informes.
"""

from datetime import datetime

class SESIPAecoReportService:
    def __init__(self, core_maestro):
        """
        Inicializa el servicio de informes acoplado al core unificado de SIPAeco.
        :param core_maestro: Instancia en ejecución de SESIPAecoCore
        """
        self.core = core_maestro
        self.peso_prioridad = {
            "1 - CRÍTICA": 1, "2 - ALTA": 2, "3 - MEDIA": 3, "4 - BAJA": 4
        }

    def obtener_hitos_pizarra(self, proyecto_filtro="TODOS", orden_criterio="Por Prioridad (Crítica -> Baja)"):
        """
        Extrae, resuelve y procesa los hitos instanciados aplicando los criterios
        de filtrado por catálogo y ordenación analítica.
        """
        master_data = self.core._load_json(self.core.cronogramas_path)
        hitos_dict = master_data.get("hitos_instanciados", {})
        catalogos = master_data.get("catalogos", {})
        
        hitos_pizarra = []

        for hito_id, info in hitos_dict.items():
            id_proy = info.get("id_proyecto", "")
            id_crono_tipo = info.get("id_cronograma_tipo", "")
            
            # Resolución transparente desde catálogos maestros
            proyecto_nombre = catalogos.get("proyectos", {}).get(id_proy, {}).get("nombre", "SIN PROYECTO")
            crono_codigo = catalogos.get("cronogramas_tipos", {}).get(id_crono_tipo, {}).get("codigo", "DEFECTO")
            
            estado = info.get("estado", "PLANIFICADO").upper()
            prioridad = info.get("prioridad", "3 - MEDIA").upper()

            hitos_pizarra.append({
                "id": hito_id,
                "nombre": info.get("nombre_accion", "-"),
                "proyecto": proyecto_nombre,
                "crono_codigo": crono_codigo,
                "fecha_inicio": info.get("fecha_inicio", "-"),
                "fecha_fin": info.get("fecha_fin", "-"),
                "horas": info.get("horas_estimadas", 0),
                "estado": estado,
                "prioridad": prioridad,
                "ficheros": info.get("ficheros", []),
                "notas": info.get("notas", "Sin notas registradas.")
            })

        # Aplicación estricta de filtros sobre el catálogo de proyectos
        if proyecto_filtro != "TODOS":
            hitos_pizarra = [h for h in hitos_pizarra if h["proyecto"] == proyecto_filtro]

        # Algoritmos de ordenación de la pizarra
        if "Prioridad" in orden_criterio:
            hitos_pizarra.sort(key=lambda x: (self.peso_prioridad.get(x["prioridad"], 3), x["fecha_fin"]))
        else:
            hitos_pizarra.sort(key=lambda x: (x["estado"], self.peso_prioridad.get(x["prioridad"], 3)))

        return hitos_pizarra

    def actualizar_campo_hito(self, hito_id, campo, nuevo_valor):
        """Persiste modificaciones directas de estado o prioridad en el JSON maestro."""
        master_data = self.core._load_json(self.core.cronogramas_path)
        if hito_id in master_data.get("hitos_instanciados", {}):
            master_data["hitos_instanciados"][hito_id][campo] = nuevo_valor
            self.core._save_json(self.core.cronogramas_path, master_data)
            return True
        return False

    def guardar_ficheros_hito(self, hito_id, lista_ficheros):
        """Persiste los cambios de ficheros .md asociados al hito nuclear."""
        return self.actualizar_campo_hito(hito_id, "ficheros", lista_ficheros)

    def guardar_notas_hito(self, hito_id, texto_notas):
        """Persiste las notas de seguimiento libre del hito."""
        return self.actualizar_campo_hito(hito_id, "notas", texto_notas)