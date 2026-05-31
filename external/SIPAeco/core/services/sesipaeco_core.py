#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIPAeco Core Services - Motor de Gestión Económica y Cronogramas Elásticos
Ubicación: SIPA/external/SIPAeco/core/services/sesipaeco_core.py
Autor: Daniel Miñana Montero
Fecha: 2026-05-31
Descripción: Unifica la persistencia de cronogramas/hitos con el histórico lineal 
             de impactos (Registro Bala) de tiempo y finanzas.
             AUTOCURACIÓN AVANZADA: Protocolo de cuarentena unificada.
             COLD STORAGE INTEGRADO: Particionado de logs antiguos para optimizar RAM.
"""

import os
import json
import zipfile
import shutil
from datetime import datetime

class ColdStorageEngine:
    def __init__(self, core_base):
        self.core = core_base
        # Umbral operativo: registros anteriores al año en curso (2026)
        self.anio_actual = datetime.now().year
        
        # Carpeta de archivo histórica dedicada
        self.archive_dir = os.path.join(self.core.data_dir, "archive")
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)

    def ejecutar_archivado_saneado(self):
        """Filtra los históricos lineales, mueve lo consolidado a frío y sanea el activo."""
        try:
            self._archivar_finanzas()
            self._archivar_tiempo()
        except Exception as e:
            print(f"[COLD STORAGE ERROR] No se pudo completar el ciclo de optimización: {e}")

    def _archivar_finanzas(self):
        if not os.path.exists(self.core.cash_log_path):
            return
        
        data_activa = self.core._load_json(self.core.cash_log_path)
        transacciones = data_activa.get("transacciones", [])
        
        calientes = []
        frios_por_anio = {}
        
        for tx in transacciones:
            fecha_str = tx.get("fecha", "").strip()
            es_real = tx.get("es_real", True)
            
            try:
                fecha_dt = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
            except ValueError:
                try:
                    fecha_dt = datetime.strptime(fecha_str[:10], "%d/%m/%Y")
                except ValueError:
                    calientes.append(tx)
                    continue
            
            # Condición de frío: Asientos reales liquidados de años anteriores
            if fecha_dt.year < self.anio_actual and es_real:
                frios_por_anio.setdefault(fecha_dt.year, []).append(tx)
            else:
                calientes.append(tx)
                
        if not frios_por_anio:
            return
            
        for anio, registros in frios_por_anio.items():
            archivo_frio_path = os.path.join(self.archive_dir, f"archive_finanzas_{anio}.json")
            data_fria = {"transacciones": []}
            if os.path.exists(archivo_frio_path):
                try:
                    with open(archivo_frio_path, "r", encoding="utf-8") as f:
                        data_fria = json.load(f)
                except json.JSONDecodeError:
                    pass
            
            data_fria["transacciones"].extend(registros)
            with open(archivo_frio_path, "w", encoding="utf-8") as f:
                json.dump(data_fria, f, indent=4, ensure_ascii=False)
                
        data_activa["transacciones"] = calientes
        self.core._save_json(self.core.cash_log_path, data_activa)

    def _archivar_tiempo(self):
        if not os.path.exists(self.core.time_log_path):
            return
            
        data_activa = self.core._load_json(self.core.time_log_path)
        sesiones = data_activa.get("sesiones", [])
        
        calientes = []
        frios_por_anio = {}
        
        for sesion in sesiones:
            fecha_str = sesion.get("fecha", "").strip()
            estado = sesion.get("estado_impacto", "").upper()
            liquidada = sesion.get("liquidada", False)
            
            try:
                fecha_dt = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
            except ValueError:
                calientes.append(sesion)
                continue
                
            # Condición de frío: Sesiones cerradas o liquidadas de años pasados
            if fecha_dt.year < self.anio_actual and (estado == "COMPLETADO" or liquidada):
                frios_por_anio.setdefault(fecha_dt.year, []).append(sesion)
            else:
                calientes.append(sesion)
                
        if not frios_por_anio:
            return
            
        for anio, registros in frios_por_anio.items():
            archivo_frio_path = os.path.join(self.archive_dir, f"archive_tiempo_{anio}.json")
            data_fria = {"sesiones": []}
            if os.path.exists(archivo_frio_path):
                try:
                    with open(archivo_frio_path, "r", encoding="utf-8") as f:
                        data_fria = json.load(f)
                except json.JSONDecodeError:
                    pass
                    
            data_fria["sesiones"].extend(registros)
            with open(archivo_frio_path, "w", encoding="utf-8") as f:
                json.dump(data_fria, f, indent=4, ensure_ascii=False)
                
        data_activa["sesiones"] = calientes
        self.core._save_json(self.core.time_log_path, data_activa)


class SESIPAecoCore:
    def __init__(self, base_path=None, propietario="Daniel"):
        if base_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        self.propietario = propietario
        self.data_dir = os.path.join(base_path, "data")
        
        self.cronogramas_path = os.path.join(self.data_dir, "cronogramas_master.json")
        self.time_log_path = os.path.join(self.data_dir, "logs_tiempo.json")
        self.cash_log_path = os.path.join(self.data_dir, "logs_finanzas.json")
        
        self.alerta_corrupcion = False
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self._verificar_integridad_sistema()
        
        # Instanciar y ejecutar el Cold Storage tras la verificación de integridad
        self.storage_engine = ColdStorageEngine(self)
        self.storage_engine.ejecutar_archivado_saneado()

    def _verificar_integridad_sistema(self):
        """Asegura la coherencia absoluta. Si falta el maestro, se ejecuta el protocolo de cuarentena."""
        maestro_existe = os.path.exists(self.cronogramas_path)
        
        if maestro_existe:
            try:
                with open(self.cronogramas_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError:
                maestro_existe = False 
        
        if not maestro_existe:
            if os.path.exists(self.time_log_path) or os.path.exists(self.cash_log_path):
                self._ejecutar_protocolo_cuarentena()
                self.alerta_corrupcion = True

        self._init_cronogramas_file()
        self._init_json_file(self.time_log_path, {"sesiones": []})
        self._init_json_file(self.cash_log_path, {"transacciones": []})

    def _ejecutar_protocolo_cuarentena(self):
        """Empaqueta los archivos actuales en un archivo ZIP de respaldo y limpia el directorio activo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_zip_name = f"BACKUP_CORRUPTO_{timestamp}.zip"
        backup_zip_path = os.path.join(self.data_dir, backup_zip_name)
        
        try:
            with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in [self.cronogramas_path, self.time_log_path, self.cash_log_path]:
                    if os.path.exists(file_path):
                        zipf.write(file_path, os.path.basename(file_path))
                        
            for file_path in [self.cronogramas_path, self.time_log_path, self.cash_log_path]:
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Error crítico durante la ejecución de la cuarentena: {e}")

    def _init_json_file(self, path, default_content):
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, indent=4, ensure_ascii=False)

    def _init_cronogramas_file(self):
        """Inicializa el almacén de datos bajo la arquitectura de Catálogos v2.6."""
        if not os.path.exists(self.cronogramas_path):
            estructura_base = {
                "propietario": self.propietario,
                "configuracion": {
                    "precio_hora_default": 25.0,
                    "minutos_diarios_totales": 1440
                },
                "catalogos": {
                    "proyectos": {
                        "PRY-001": {"nombre": "SIPA", "descripcion": "Ecosistema de gestión"}
                    },
                    "cronogramas_tipos": {
                        "CRN-001": {"codigo": "SIPA", "descripcion": "Línea temporal maestra"}
                    },
                    "hitos_reutilizables": {}
                },
                "hitos_instanciados": {}
            }
            self._save_json(self.cronogramas_path, estructura_base)

    def _load_json(self, path):
        """Carga un archivo JSON garantizando que devuelva una estructura válida."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            if "logs_tiempo" in path: return {"sesiones": []}
            if "logs_finanzas" in path: return {"transacciones": []}
            if "cronogramas_master" in path:
                self._init_cronogramas_file()
                with open(path, 'r', encoding='utf-8') as f: return json.load(f)
            return {}

    def _save_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    # =========================================================================
    # 📦 GESTIÓN DE CRONOGRAMAS E HITOS (VINCULACIÓN MAESTRA)
    # =========================================================================

    def crear_subcronograma(self, id_crono, codigo, descripcion=""):
        data = self._load_json(self.cronogramas_path)
        cronos = data.setdefault("catalogos", {}).setdefault("cronogramas_tipos", {})
        
        id_upper = id_crono.upper()
        if id_upper in cronos:
            return False, f"El clasificador '{id_upper}' ya existe."
        
        cronos[id_upper] = {
            "codigo": codigo.upper(),
            "descripcion": descripcion
        }
        self._save_json(self.cronogramas_path, data)
        return True, f"Clasificador de cronograma '{codigo}' registrado."

    def crear_hito(self, cronograma_tipo_id, id_hito, nombre_accion, proyecto_id, fecha_inicio, fecha_fin, horas_est=0.0, dinero_est=0.0, es_basico=False):
        data = self._load_json(self.cronogramas_path)
        hitos = data.setdefault("hitos_instanciados", {})
        
        id_upper = id_hito.upper()
        if id_upper in hitos:
            return False, f"El hito con ID '{id_upper}' ya existe."

        hitos[id_upper] = {
            "tipo_hito": "BÁSICO" if es_basico else "OPERATIVO",
            "id_proyecto": proyecto_id.upper(),
            "id_cronograma_tipo": cronograma_tipo_id.upper(),
            "id_hito_referencia": id_upper,
            "nombre_accion": nombre_accion,
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fecha_inicio": fecha_inicio,
            "fecha_fin": "MENSUAL" if es_basico else fecha_fin,
            "horas_estimadas": 0.0 if es_basico else float(horas_est),
            "coste_fijo_directo": float(horas_est) if es_basico else 0.0,
            "ingreso_previsto_dinero": float(dinero_est),
            "presupuesto_asignado": float(dinero_est) if es_basico else (float(horas_est) * data.get("configuracion", {}).get("precio_hora_default", 25.0)),
            "estado": "PLANIFICADO",
            "prioridad": "3 - MEDIA",
            "checklist_acciones": []
        }

        self._save_json(self.cronogramas_path, data)
        return True, f"Hito nuclear '{id_upper}' instanciado."

    def agregar_accion_en_caliente(self, id_hito, id_accion, descripcion):
        data = self._load_json(self.cronogramas_path)
        hitos = data.get("hitos_instanciados", {})
        
        id_h_upper = id_hito.upper()
        if id_h_upper not in hitos: 
            return False, "Hito estratégico no encontrado."

        hito = hitos[id_h_upper]
        checklist = hito.setdefault("checklist_acciones", [])
        
        for acc in checklist:
            if acc["id_accion"] == id_accion: 
                return False, "La acción ya existe en el checklist."
        
        checklist.append({
            "id_accion": id_accion,
            "descripcion": descripcion,
            "estado": "PENDIENTE",
            "fecha_cierre": None
        })
        
        self._save_json(self.cronogramas_path, data)
        return True, f"Acción '{id_accion}' integrada al hito {id_h_upper}."

    # =========================================================================
    # ⚡ REGISTRO BALA (HISTÓRICO LINEAL INTEGRADO)
    # =========================================================================

    def registrar_sesion(self, cronograma_id, id_hito, hora_inicio, hora_fin, tarea, tarifa_hora=25.0):
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
            "id_hito": id_hito.upper(),
            "fecha": dt_inicio.strftime("%Y-%m-%d"),
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "horas_reales": round(horas, 2),
            "tarea": tarea,
            "tarifa_aplicada": tarifa_hora,
            "coste_imputado_recurso": round(coste, 2),
            "liquidada": False,
            "estado_impacto": "EN PROCESO" # Inicializado por defecto en proceso
        }

        data = self._load_json(self.time_log_path)
        data["sesiones"].append(nueva_sesion)
        self._save_json(self.time_log_path, data)
        return True, "Impacto de tiempo registrado en el histórico lineal."

    def registrar_movimiento(self, cronograma_id, id_hito, tipo, concepto, cantidad, es_real=True):
        if tipo.upper() not in ["INGRESO", "GASTO"]:
            return False, "El tipo debe ser INGRESO o GASTO."

        nuevo_movimiento = {
            "id_transaccion": f"BALA_F_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "cronograma_id": cronograma_id.upper(),
            "id_hito": id_hito.upper(),
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
    # 📊 MOTOR DE SEGUIMIENTO (AUDITORÍA CRUZADA CON EXTRACCIÓN CAPAS)
    # =========================================================================

    def obtener_sesiones(self, incluir_historico=False):
        """Devuelve las sesiones de la capa caliente y, opcionalmente, de la fría."""
        sesiones = self._load_json(self.time_log_path).get("sesiones", [])
        if not incluir_historico:
            return sesiones
            
        # Añadir barrido por los históricos fríos de la carpeta archive
        archive_dir = os.path.join(self.data_dir, "archive")
        if os.path.exists(archive_dir):
            for archivo in os.listdir(archive_dir):
                if archivo.startswith("archive_tiempo_") and archivo.endswith(".json"):
                    path_completo = os.path.join(archive_dir, archivo)
                    try:
                        with open(path_completo, "r", encoding="utf-8") as f:
                            sesiones.extend(json.load(f).get("sesiones", []))
                    except (json.JSONDecodeError, IOError):
                        pass
        return sesiones

    def obtener_finanzas(self, incluir_historico=False):
        """Devuelve los movimientos de la capa caliente y, opcionalmente, de la fría."""
        transacciones = self._load_json(self.cash_log_path).get("transacciones", [])
        if not incluir_historico:
            return transacciones
            
        archive_dir = os.path.join(self.data_dir, "archive")
        if os.path.exists(archive_dir):
            for archivo in os.listdir(archive_dir):
                if archivo.startswith("archive_finanzas_") and archivo.endswith(".json"):
                    path_completo = os.path.join(archive_dir, archivo)
                    try:
                        with open(path_completo, "r", encoding="utf-8") as f:
                            transacciones.extend(json.load(f).get("transacciones", []))
                    except (json.JSONDecodeError, IOError):
                        pass
        return transacciones

    def obtener_salud_hito(self, id_hito):
        """Cruza de forma exacta la definición de un hito con sus impactos totales (ambas capas)."""
        master_data = self._load_json(self.cronogramas_path)
        hitos = master_data.get("hitos_instanciados", {})
        
        id_upper = id_hito.upper()
        if id_upper not in hitos:
            return {"status": "error", "message": f"Hito '{id_upper}' no encontrado en el sistema."}
            
        hito = hitos[id_upper]
        
        # Auditoría profunda recurriendo a la combinación completa de capas
        finanzas = self.obtener_finanzas(incluir_historico=True)
        tiempos = self.obtener_sesiones(incluir_historico=True)
        
        gastos_reales = sum(t["cantidad"] for t in finanzas if t["id_hito"] == id_upper and t["tipo"] == "GASTO" and t["es_real"])
        ingresos_reales = sum(t["cantidad"] for t in finanzas if t["id_hito"] == id_upper and t["tipo"] == "INGRESO" and t["es_real"])
        horas_reales = sum(s["horas_reales"] for s in tiempos if s["id_hito"] == id_upper)
        
        es_basico = hito.get("tipo_hito") == "BÁSICO"
        horas_estimadas = hito.get("horas_estimadas", 0.0)
        coste_previsto = hito.get("coste_fijo_directo", 0.0) if es_basico else (horas_estimadas * master_data.get("configuracion", {}).get("precio_hora_default", 25.0))
        
        return {
            "hito_id": id_upper,
            "tipo_hito": hito.get("tipo_hito", "OPERATIVO"),
            "nombre": hito.get("nombre_accion", "-"),
            "proyecto": hito.get("id_proyecto", "-"),
            "cronograma_tipo": hito.get("id_cronograma_tipo", "-"),
            "estado_actual": hito.get("estado", "PLANIFICADO"),
            "tiempo": {
                "estimado_horas": horas_estimadas,
                "real_horas": round(horas_reales, 2),
                "desviacion_horas": round(horas_reales - horas_estimadas, 2)
            },
            "finanzas": {
                "coste_previsto": coste_previsto,
                "gastos_reales": round(gastos_reales, 2),
                "ingresos_reales": round(ingresos_reales, 2),
                "resultado_neto_real": round(ingresos_reales - gastos_reales, 2)
            },
            "progreso_checklist": {
                "totales": len(hito.get("checklist_acciones", [])),
                "completadas": len([a for a in hito.get("checklist_acciones", []) if a["estado"] == "COMPLETADO"])
            }
        }
    # =========================================================================
    # 📑 MOTOR VIGILANTE DE ARCHIVOS (ORÁCULO ENLACE FUD)
    # =========================================================================

    def buscar_fichero_impacto_por_oraculo(self, nombre_archivo):
        """
        Consulta sipa_activos.json generado por SIPACur para obtener
        la ruta real e instantánea del archivo Markdown sin escanear el disco.
        Maneja estructuras JSON tanto de lista directa como de diccionario raíz.
        """
        base_sipa = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        activos_path = os.path.join(base_sipa, "data", "db", "sipa_activos.json")
        
        if not os.path.exists(activos_path):
            # Fallback 1: Si no se encuentra el oráculo, miramos directo en el inbox
            inbox_path = os.path.join(base_sipa, "data", "inbox", nombre_archivo)
            if os.path.exists(inbox_path):
                return inbox_path
            return None

        try:
            with open(activos_path, "r", encoding="utf-8") as f:
                activos_data = json.load(f)
        except Exception as e:
            print(f"[ORÁCULO ERROR] No se pudo leer sipa_activos.json: {e}")
            return None
        
        # --- SOLUCIÓN ELÁSTICA AL ATTRIBUTEERROR ---
        # Si el JSON es una lista directa [...], la usamos. Si es un diccionario, extraemos la clave "activos".
        lista_activos = activos_data if isinstance(activos_data, list) else activos_data.get("activos", [])
        
        # Escaneo en el catálogo indexado por SIPACur
        for activo in lista_activos:
            if isinstance(activo, dict):
                if activo.get("nombre") == nombre_archivo or activo.get("archivo") == nombre_archivo:
                    return activo.get("ruta_absoluta") or activo.get("ruta")

        # Fallback 2: Si es muy nuevo y SIPACur no ha hecho la ronda todavía
        inbox_path = os.path.join(base_sipa, "data", "inbox", nombre_archivo)
        if os.path.exists(inbox_path):
            return inbox_path

        return None

    def preparar_fichero_para_edicion(self, nombre_archivo):
        """
        Extrae el archivo al inbox si estaba consolidado en knowledge y remueve el frontmatter
        para evitar conflictos en la re-indexación de SIPACur.
        """
        # 1. Consultar la ubicación real en el oráculo (sipa_activos.json)
        ruta_actual = self.buscar_fichero_impacto_por_oraculo(nombre_archivo)
        
        # Obtener el directorio raíz del ecosistema SIPA subiendo 4 niveles
        base_sipa = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        inbox_dir = os.path.join(base_sipa, "data", "inbox")
        ruta_inbox = os.path.join(inbox_dir, nombre_archivo)

        # Si el oráculo no sabe nada de él, hacemos un fallback directo al inbox por si es muy nuevo
        if not ruta_actual or not os.path.exists(ruta_actual):
            if os.path.exists(ruta_inbox):
                ruta_actual = ruta_inbox
            else:
                return None, f"El archivo '{nombre_archivo}' no existe en inbox ni está indexado en el ecosistema."

        # 2. Si el archivo está consolidado en 'knowledge', ejecutar el rescate al 'inbox'
        if "knowledge" in ruta_actual and ruta_actual != ruta_inbox:
            if not os.path.exists(inbox_dir):
                os.makedirs(inbox_dir)
            
            try:
                # Movemos el archivo de vuelta a la casilla de salida (inbox)
                shutil.move(ruta_actual, ruta_inbox)
                ruta_actual = ruta_inbox
                print(f"[RESCATE] Archivo {nombre_archivo} traído de vuelta al inbox de trabajo.")
            except Exception as e:
                return None, f"Error al mover el archivo al inbox: {e}"

            # 3. Saneamiento del bloque Frontmatter (--- ... ---) para evitar bucles con SIPACur
            try:
                with open(ruta_actual, "r", encoding="utf-8") as f:
                    lineas = f.readlines()
                
                if lineas and lineas[0].strip() == "---":
                    cierre_idx = -1
                    for i in range(1, len(lineas)):
                        if lineas[i].strip() == "---":
                            cierre_idx = i
                            break
                    if cierre_idx != -1:
                        # Conservamos solo el contenido limpio quitando las etiquetas antiguas
                        lineas_limpias = lineas[cierre_idx + 1:]
                        with open(ruta_actual, "w", encoding="utf-8") as f:
                            f.writelines(lineas_limpias)
                        print(f"[SANEAMIENTO] Frontmatter limpiado con éxito en {nombre_archivo}.")
            except Exception as e:
                print(f"[CLEAN FRONTMATTER ERROR] No se pudo limpiar el encabezado: {e}")

        # Retornamos la ruta final lista para que el sistema operativo la abra
        return ruta_actual, "OK"

    def crear_documento_desde_plantilla(self, id_impacto, tipo_plantilla, titulo_impacto):
        """Genera un archivo .md estructurado en el inbox basado en plantillas limpias."""
        base_sipa = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        inbox_dir = os.path.join(base_sipa, "data", "inbox")
        if not os.path.exists(inbox_dir):
            os.makedirs(inbox_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import re
        slug = titulo_impacto.lower().replace(" ", "_")
        slug = re.sub(r'[^a-zA-Z0-9_]', '', slug)[:30]
        nombre_archivo = f"{timestamp}_{id_impacto}_{slug}.md"
        ruta_destino = os.path.join(inbox_dir, nombre_archivo)

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        contenido = f"# {titulo_impacto.upper()}\n\n"
        contenido += f"**Fecha de Registro:** {fecha_hoy}\n"
        contenido += f"**Impacto Vinculado:** {id_impacto}\n"
        contenido += f"**Categoría de Plantilla:** {tipo_plantilla.upper()}\n"
        contenido += "\n---\n\n## 📝 DESARROLLO / NOTAS OPERATIVAS\n\n- "

        with open(ruta_destino, "w", encoding="utf-8") as f:
            f.write(contenido)

        self.vincular_archivo_a_impacto(id_impacto, nombre_archivo)
        return nombre_archivo

    def adjuntar_fichero_existente(self, id_impacto, ruta_origen):
        """Copia un archivo externo del usuario exclusivamente a la carpeta SIPA/data/inbox."""
        if not os.path.exists(ruta_origen):
            return False, "El archivo de origen no existe."

        base_sipa = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        inbox_dir = os.path.join(base_sipa, "data", "inbox")
        if not os.path.exists(inbox_dir):
            os.makedirs(inbox_dir)

        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(ruta_origen)}"
        ruta_destino = os.path.join(inbox_dir, nombre_archivo)
        
        shutil.copy2(ruta_origen, ruta_destino)
        self.vincular_archivo_a_impacto(id_impacto, nombre_archivo)
        return True, nombre_archivo

    def vincular_archivo_a_impacto(self, id_impacto, nombre_archivo):
        """Inyecta el archivo en el array 'ficheros_adjuntos' de la bala correspondiente."""
        path = self.time_log_path if "BALA_T_" in id_impacto else self.cash_log_path
        clave = "sesiones" if "BALA_T_" in id_impacto else "transacciones"
        id_clave = "id_sesion" if "BALA_T_" in id_impacto else "id_transaccion"

        data = self._load_json(path)
        for elemento in data.get(clave, []):
            if elemento.get(id_clave) == id_impacto:
                adjuntos = elemento.setdefault("ficheros_adjuntos", [])
                if nombre_archivo not in adjuntos:
                    adjuntos.append(nombre_archivo)
                break
        self._save_json(path, data)

    def desvincular_archivo_de_impacto(self, id_impacto, nombre_archivo):
            """
            Remueve la referencia de un archivo del array 'ficheros_adjuntos' 
            de una Bala específica (Tiempo o Finanzas).
            """
            path = self.time_log_path if "BALA_T_" in id_impacto else self.cash_log_path
            clave = "sesiones" if "BALA_T_" in id_impacto else "transacciones"
            id_clave = "id_sesion" if "BALA_T_" in id_impacto else "id_transaccion"

            data = self._load_json(path)
            modificado = False
            
            for elemento in data.get(clave, []):
                if elemento.get(id_clave) == id_impacto:
                    adjuntos = elemento.get("ficheros_adjuntos", [])
                    if nombre_archivo in adjuntos:
                        adjuntos.remove(nombre_archivo)
                        modificado = True
                    break
                    
            if modificado:
                self._save_json(path, data)
                return True, "Archivo desvinculado con éxito."
            return False, "No se encontró el archivo asociado a esta Bala."
    