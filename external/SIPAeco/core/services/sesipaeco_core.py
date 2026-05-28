#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco Core Services - Motor de Gestión Económica y Cronogramas Elásticos
Ubicación: SIPA/external/SIPAeco/core/services/sesipaeco_core.py
Autor: Daniel Miñana Montero
Fecha: 2026-05-27
Descripción: Unifica la persistencia de cronogramas/hitos con el histórico lineal 
             de impactos (Registro Bala) de tiempo y finanzas.
"""

import os
import json
from datetime import datetime

class SESIPAecoCore:
    def __init__(self, base_path=None, propietario="Daniel"):
        # Si no se define ruta, asume la carpeta relativa al archivo (SIPA/external/SIPAeco)
        if base_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        self.propietario = propietario
        self.data_dir = os.path.join(base_path, "data")
        
        # Archivos de persistencia de datos (El Histórico Lineal y la Estructura Base)
        self.cronogramas_path = os.path.join(self.data_dir, "cronogramas_master.json")
        self.time_log_path = os.path.join(self.data_dir, "logs_tiempo.json")
        self.cash_log_path = os.path.join(self.data_dir, "logs_finanzas.json")
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Inicialización blindada de los almacenes de datos
        self._init_cronogramas_file()
        self._init_json_file(self.time_log_path, {"sesiones": []})
        self._init_json_file(self.cash_log_path, {"transacciones": []})

    def _init_json_file(self, path, default_content):
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, indent=4, ensure_ascii=False)

    def _init_cronogramas_file(self):
        """Inicializa el archivo de cronogramas con la flexibilidad temporal requerida."""
        if not os.path.exists(self.cronogramas_path):
            estructura_base = {
                "propietario": self.propietario,
                "configuracion": {
                    "minutos_diarios_totales": 1440
                },
                "cronogramas": {
                    "PLAN_MAESTRO": {
                        "id": "CRONO_PLAN_MAESTRO",
                        "nombre": "Plan General",
                        "descripcion": "Línea temporal maestra y colchón operativo libre",
                        "estado": "ACTIVO",
                        "hitos": []
                    }
                }
            }
            self._save_json(self.cronogramas_path, estructura_base)

    def _load_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Robustez: si se corrompe en caliente, devolvemos estructura limpia para no tumbar la UI
            if "logs_tiempo" in path: return {"sesiones": []}
            if "logs_finanzas" in path: return {"transacciones": []}
            return {}

    def _save_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # =========================================================================
    # 📦 GESTIÓN DE CRONOGRAMAS E HITOS (EL CONTRATO/NECESIDADES)
    # =========================================================================

    def crear_subcronograma(self, id_crono, nombre, descripcion=""):
        """Permite dar de alta nuevas áreas (Social, Trabajo, Salud...) en caliente."""
        data = self._load_json(self.cronogramas_path)
        id_upper = id_crono.upper()
        
        if id_upper in data.get("cronogramas", {}):
            return False, f"El cronograma '{id_upper}' ya existe."
        
        data["cronogramas"][id_upper] = {
            "id": f"CRONO_{id_upper}",
            "nombre": nombre,
            "descripcion": descripcion,
            "estado": "ACTIVO",
            "hitos": []
        }
        self._save_json(self.cronogramas_path, data)
        return True, f"Cronograma '{nombre}' creado con éxito."

    def crear_hito(self, cronograma_id, id_hito, nombre, proyecto, fecha_inicio, fecha_limite, horas_est=0.0, dinero_est=0.0):
        """Crea una necesidad/hito en un cronograma. Permite fechas pasadas o futuras."""
        data = self._load_json(self.cronogramas_path)
        crono_key = cronograma_id.upper()
        
        if crono_key not in data.get("cronogramas", {}):
            return False, f"No existe el cronograma contenedor: {crono_key}"
        
        for hito in data["cronogramas"][crono_key]["hitos"]:
            if hito["id"] == id_hito:
                return False, f"El hito con ID '{id_hito}' ya existe."

        nuevo_hito = {
            "id": id_hito,
            "nombre": nombre,
            "proyecto_asociado": proyecto.upper(),
            "fecha_inicio": fecha_inicio, 
            "fecha_limite_objetivo": fecha_limite,
            "presupuesto_tiempo_estimado_horas": float(horas_est),
            "presupuesto_dinero_estimado": float(dinero_est),
            "estado": "PLANIFICADO",
            "checklist_acciones": []
        }

        data["cronogramas"][crono_key]["hitos"].append(nuevo_hito)
        self._save_json(self.cronogramas_path, data)
        return True, f"Hito '{nombre}' registrado con éxito."

    def agregar_accion_en_caliente(self, cronograma_id, id_hito, id_accion, descripcion):
        """Añade una micro-acción al checklist de un hito en pleno foco operativo."""
        data = self._load_json(self.cronogramas_path)
        crono_key = cronograma_id.upper()

        if crono_key not in data.get("cronogramas", {}): return False, "Cronograma no encontrado."

        for hito in data["cronogramas"][crono_key]["hitos"]:
            if hito["id"] == id_hito:
                for acc in hito["checklist_acciones"]:
                    if acc["id_accion"] == id_accion: return False, "La acción ya existe."
                
                hito["checklist_acciones"].append({
                    "id_accion": id_accion,
                    "descripcion": descripcion,
                    "estado": "PENDIENTE",
                    "fecha_cierre": None
                })
                self._save_json(self.cronogramas_path, data)
                return True, f"Acción '{id_accion}' integrada en caliente."
        return False, "Hito no encontrado."

    # =========================================================================
    # ⚡ REGISTRO BALA (EL IMPACTO LINEAL OPERATIVO)
    # =========================================================================

    def registrar_sesion(self, cronograma_id, id_hito, hora_inicio, hora_fin, tarea, tarifa_hora=25.0):
        """Impacta una bala de TIEMPO vinculada directamente a un hito ejecutor."""
        fmt = "%Y-%m-%d %H:%M"
        
        try:
            dt_inicio = datetime.strptime(hora_inicio, fmt)
            dt_fin = datetime.strptime(hora_fin, fmt)
        except ValueError:
            return False, "Formato de fecha inválido (AAAA-MM-DD HH:MM)"

        if dt_fin <= dt_inicio:
            return False, "La hora de fin debe ser posterior a la de inicio."

        horas = (dt_fin - dt_inicio).total_seconds() / 3600.0
        coste = horas * tarifa_hora

        nueva_sesion = {
            "id_sesion": f"BALA_T_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "cronograma_id": cronograma_id.upper(),
            "id_hito": id_hito,
            "fecha": dt_inicio.strftime("%Y-%m-%d"),
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "horas_reales": round(horas, 2),
            "tarea": tarea,
            "tarifa_aplicada": tarifa_hora,
            "coste_imputado_recurso": round(coste, 2),
            "liquidada": False
        }

        data = self._load_json(self.time_log_path)
        data["sesiones"].append(nueva_sesion)
        self._save_json(self.time_log_path, data)
        return True, "Impacto de tiempo registrado en el histórico lineal."

    def registrar_movimiento(self, cronograma_id, id_hito, tipo, concepto, cantidad, es_real=True):
        """Impacta una bala FINANCIERA (Ingreso/Gasto) vinculada a un hito."""
        if tipo.upper() not in ["INGRESO", "GASTO"]:
            return False, "El tipo debe ser INGRESO o GASTO."

        nuevo_movimiento = {
            "id_transaccion": f"BALA_F_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "cronograma_id": cronograma_id.upper(),
            "id_hito": id_hito,
            "tipo": tipo.upper(),
            "concepto": concepto,
            "cantidad": round(float(cantidad), 2),
            "es_real": bool(es_real)
        }

        data = self._load_json(self.cash_log_path)
        data["transacciones"].append(nuevo_movimiento)
        self._save_json(self.cash_log_path, data)
        return True, "Impacto financiero registrado en el histórico lineal."

    # =========================================================================
    # 📊 MOTOR DE SEGUIMIENTO (AUDITORÍA DE SALUD Y DESVIACIONES)
    # =========================================================================

    def obtener_sesiones(self):
        return self._load_json(self.time_log_path)["sesiones"]

    def obtener_finanzas(self):
        return self._load_json(self.cash_log_path)["transacciones"]

    def obtener_salud_hito(self, cronograma_id, id_hito):
        """Cruza los datos del hito planificado con sus impactos lineales reales."""
        master_data = self._load_json(self.cronogramas_path)
        crono_key = cronograma_id.upper()
        
        # Buscar el hito de referencia
        cronograma = master_data.get("cronogramas", {}).get(crono_key, {})
        hito = next((h for h in cronograma.get("hitos", []) if h["id"] == id_hito), None)
        
        if not hito:
            return {"status": "error", "message": f"Hito '{id_hito}' no encontrado en {crono_key}."}
            
        # Cargar los históricos de impactos (Las Balas)
        finanzas = self._load_json(self.cash_log_path).get("transacciones", [])
        tiempos = self._load_json(self.time_log_path).get("sesiones", [])
        
        # Calcular acumulados específicos de este hito
        gastos_reales = sum(t["cantidad"] for t in finanzas if t["id_hito"] == id_hito and t["tipo"] == "GASTO" and t["es_real"])
        ingresos_reales = sum(t["cantidad"] for t in finanzas if t["id_hito"] == id_hito and t["tipo"] == "INGRESO" and t["es_real"])
        horas_reales = sum(s["horas_reales"] for s in tiempos if s["id_hito"] == id_hito)
        
        horas_estimadas = hito["presupuesto_tiempo_estimado_horas"]
        dinero_estimado = hito["presupuesto_dinero_estimado"]
        
        return {
            "cronograma": crono_key,
            "hito_id": id_hito,
            "nombre": hito["nombre"],
            "proyecto": hito["proyecto_asociado"],
            "estado_actual": hito["estado"],
            "tiempo": {
                "estimado_horas": horas_estimadas,
                "real_horas": round(horas_reales, 2),
                "desviacion_horas": round(horas_reales - horas_estimadas, 2)
            },
            "finanzas": {
                "presupuesto_estimado": dinero_estimado,
                "gastos_reales": round(gastos_reales, 2),
                "ingresos_reales": round(ingresos_reales, 2),
                "desviacion_gasto": round(gastos_reales - dinero_estimado, 2)
            },
            "progreso_checklist": {
                "totales": len(hito["checklist_acciones"]),
                "completadas": len([a for a in hito["checklist_acciones"] if a["estado"] == "COMPLETADO"])
            }
        }