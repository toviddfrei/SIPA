# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: scsipacur_learn_file.py
# Módulo: SIPA_Learn_Service (Motor de Auditoría y Radar)
# Versión: 4.2.0 | Fecha: 20/05/2026
# ==========================================================

import os
import json
import getpass
import re
import shutil
from datetime import datetime, timedelta

class SIPA_Learn_Service:
    def __init__(self):
        # Configuración de estado y tiempos
        self.status = "RUNNING"
        self.start_time = datetime.now()
        
        # Rutas dinámicas basadas en el sistema
        self.user_name = getpass.getuser()
        self.user_home = f"/home/{self.user_name}"
        self.path_sipa = os.path.join(self.user_home, "SIPA")
        
        # Rutas de persistencia de datos
        self.path_mapa = os.path.join(self.path_sipa, "external/SIPAcur/data/sipa_map_files.json")
        self.path_activos = os.path.join(self.path_sipa, "data/db/sipa_activos.json")
        self.path_historial = os.path.join(self.path_sipa, "external/SIPAcur/data/sipa_metrics_history.json")
        
        # Asegurar existencia de directorios de datos
        os.makedirs(os.path.dirname(self.path_mapa), exist_ok=True)

    def get_ai_status(self):
        """Retorna el estado de salud y tiempo de actividad del motor IA."""
        uptime = str(datetime.now() - self.start_time).split('.')[0]
        return {
            "status": self.status,
            "uptime": uptime,
            "engine": "Gemini-SIPA-Core"
        }

    def _obtener_rutas_en_seguimiento(self):
        """Carga las rutas de archivos que ya están integrados en la base de datos SIPA."""
        if not os.path.exists(self.path_activos):
            return set()
        try:
            with open(self.path_activos, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {item.get("path_actual") for item in data if "path_actual" in item}
        except Exception:
            return set()

    def escanear_entorno(self):
        """Realiza un escaneo recursivo total buscando activos .md preservando metadatos históricos."""
        mapa_ficheros = []
        rutas_en_seguimiento = self._obtener_rutas_en_seguimiento()
        
        # --- NUEVO: Cargar el mapa anterior para recuperar fechas históricas ---
        # --- NUEVO: Cargar el mapa anterior para recuperar fechas históricas y observaciones ---
        datos_historicos_mapa = {}
        if os.path.exists(self.path_mapa):
            try:
                with open(self.path_mapa, "r", encoding="utf-8") as f:
                    viejos_datos = json.load(f)
                    # Mapeamos path_actual -> (fecha_entrada, observaciones)
                    datos_historicos_mapa = {
                        item["path_actual"]: {
                            "fecha": item.get("fecha_entrada", "N/A"),
                            "observaciones": item.get("observaciones", " ")
                        }
                        for item in viejos_datos if "path_actual" in item
                    }
            except: pass
        # ------------------------------------------------------------------------------

        # Filtros de exclusión para optimizar el escaneo
        directorios_ignorar = {'.git', '.cache', 'node_modules', 'SIPAcur', 'venv', 'snap', 'anaconda3'}
        
        contador_id = 1
        for root, dirs, files in os.walk(self.user_home):
            dirs[:] = [d for d in dirs if d not in directorios_ignorar and not d.startswith('.')]
            
            for file in files:
                if file.endswith(".md"):
                    path_completo = os.path.join(root, file)
                    try:
                        info_disco = os.stat(path_completo)
                        es_seguido = path_completo in rutas_en_seguimiento
                        
                        # --- UNIFICACIÓN INTEGRAL DE FECHAS Y OBSERVACIONES EN EL MOTOR MAPA ---
                        # 1. Recuperamos los datos históricos (fecha y observaciones) de nuestro nuevo diccionario estructurado
                        historial_archivo = datos_historicos_mapa.get(path_completo, {})
                        fecha_entrada_real = historial_archivo.get("fecha", "N/A")
                        observacion_guardada = historial_archivo.get("observaciones", " ") # <-- Rescatamos tu anotación manual
                        
                        # 2. Si el archivo está en seguimiento real del sistema, obligamos a unificar
                        if es_seguido:
                            # Si en el histórico del mapa no existía, le asignamos la fecha de hoy para el log visual
                            if fecha_entrada_real == "N/A":
                                fecha_entrada_real = datetime.now().strftime('%d/%m/%Y')
                        
                        registro = {
                            "id_interno": str(contador_id),
                            "nombre": file,
                            "fecha_detectado": datetime.now().strftime('%d/%m/%Y'),
                            "estado": "Seguimiento" if es_seguido else "Pendiente",
                            "observaciones": observacion_guardada, # <--- ¡AHORA ESTÁ BLINDADA Y PROTEGIDA!
                            "fecha_entrada": fecha_entrada_real, # <--- CLAVE UNIFICADA PARA TU TABLA MAPA
                            "path_actual": path_completo,
                            "tamaño_kb": str(round(info_disco.st_size / 1024, 2)),
                            "extensión": ".md"
                        }
                        mapa_ficheros.append(registro)
                        contador_id += 1
                    except (PermissionError, OSError):
                        continue
        
        with open(self.path_mapa, "w", encoding="utf-8") as f:
            json.dump(mapa_ficheros, f, indent=4, ensure_ascii=False)
            
        return mapa_ficheros

    def calcular_auditoria_ecosistema(self, mapa_actual):
        """Calcula métricas de productividad, salud, distribución completa y mapa de calor."""
        total_activos = len(mapa_actual)
        if total_activos == 0:
            return {}

        # Contadores base
        conteo_sipa = 0
        conteo_inbox = 0
        peso_acumulado_kb = 0
        activos_fantasmas = 0
        limite_actividad = datetime.now() - timedelta(days=7)
        activos_recientes = 0
        
        # Métrica A: Distribución completa (La que teníamos antes)
        distribucion_interna = {}
        
        # Métrica B: Mapa de Calor Áreas Core [Volumen, Esfuerzo]
        areas_core_keys = ["economica", "educacion", "justicia", "social", "constructor", "posts"]
        mapa_calor = {area: [0, 0] for area in areas_core_keys}

        for activo in mapa_actual:
            ruta = activo["path_actual"]
            ruta_lower = ruta.lower()
            peso_kb = float(activo["tamaño_kb"])
            peso_acumulado_kb += peso_kb
            
            # Salud Documental
            if peso_kb < 0.1:
                activos_fantasmas += 1
            
            # Actividad Semanal
            f_mod = datetime.strptime(activo["ultima_modificacion"], '%d/%m/%Y')
            es_reciente = f_mod > limite_actividad
            if es_reciente:
                activos_recientes += 1

            # Ubicación SIPA
            if self.path_sipa.lower() in ruta_lower:
                conteo_sipa += 1
                if "/data/inbox" in ruta_lower:
                    conteo_inbox += 1
                
                # Desglose de arquitectura completo (Métrica A)
                sub = os.path.relpath(ruta, self.path_sipa).split(os.sep)[0]
                distribucion_interna[sub] = distribucion_interna.get(sub, 0) + 1
                
                # Mapa de Calor Áreas Core (Métrica B)
                for area in areas_core_keys:
                    if f"/{area}/" in ruta_lower:
                        mapa_calor[area][0] += 1 # Volumen
                        if es_reciente:
                            mapa_calor[area][1] += 1 # Esfuerzo

        stats = {
            "recuento_global": total_activos,
            "recuento_sipa": conteo_sipa,
            "recuento_pendiente": total_activos - conteo_sipa,
            "inbox_cantidad": conteo_inbox,
            "porcentaje_control": round((conteo_sipa / total_activos) * 100, 2),
            "porcentaje_inbox_global": round((conteo_inbox / total_activos) * 100, 2),
            "porcentaje_inbox_sipa": round((conteo_inbox / conteo_sipa * 100), 2) if conteo_sipa > 0 else 0,
            "peso_total_mb": round(peso_acumulado_kb / 1024, 2),
            "salud_fantasmas": activos_fantasmas,
            "actividad_semanal": activos_recientes,
            "distribucion": distribucion_interna,
            "mapa_calor": mapa_calor
        }
        
        self.sincronizar_historico_evolucion(stats)
        return stats

    def sincronizar_historico_evolucion(self, stats):
        """Registra el progreso en el tiempo para análisis de tendencias (4 veces al día)."""
        historial = []
        if os.path.exists(self.path_historial):
            try:
                with open(self.path_historial, "r", encoding="utf-8") as f:
                    historial = json.load(f)
            except: pass

        ahora = datetime.now()
        # Modificación para forzar guardado inicial si está vacío, o respetar la ventana de 6h
        if historial:
            ultima_fecha = datetime.strptime(historial[-1]["ts"], '%Y-%m-%d %H:%M')
            if ahora - ultima_fecha < timedelta(hours=6):
                return

        historial.append({
            "ts": ahora.strftime('%Y-%m-%d %H:%M'),
            "control": stats["porcentaje_control"],
            "inbox": stats["inbox_cantidad"],
            "global": stats["recuento_global"]
        })
        
        with open(self.path_historial, "w", encoding="utf-8") as f:
            json.dump(historial[-500:], f, indent=4, ensure_ascii=False)

    def calcular_flechas_tendencia(self, actual_str, anterior_str):
        """Analiza cadenas complejas de métricas y devuelve un diccionario de tendencia con el 'azuquitar' formativo."""
        def limpiar_a_flotante(cadena):
            if not cadena or cadena == "N/A": return 0.0
            # Extrae el primer número válido entero o decimal (ej: "30.58%" -> 30.58, "158 | 1 mod." -> 158.0)
            match = re.search(r"[-+]?\d*\.\d+|\d+", str(cadena))
            return float(match.group()) if match else 0.0

        act_val = limpiar_a_flotante(actual_str)
        ant_val = limpiar_a_flotante(anterior_str)

        diferencia = act_val - ant_val
        es_porcentaje = "%" in str(actual_str) or "%" in str(anterior_str)
        es_mb = "MB" in str(actual_str) or "MB" in str(anterior_str)
        es_modulo = "|" in str(actual_str)

        if diferencia > 0:
            simbolo = "▲"
            estado = "UP"
            signo = "+"
        elif diferencia < 0:
            simbolo = "▼"
            estado = "DOWN"
            signo = ""
        else:
            return {"simbolo": "▬", "txt": "est.", "estado": "STABLE"}

        # Dar formato azuquitar con la etiqueta temporal simulada en base al último periodo
        if es_porcentaje:
            txt_diff = f"{signo}{round(diferencia, 2)}%"
        elif es_mb:
            txt_diff = f"{signo}{round(diferencia, 2)} MB"
        elif es_modulo:
            txt_diff = f"{signo}{int(diferencia)} mod"
        else:
            txt_diff = f"{signo}{int(diferencia)}"

        return {"simbolo": simbolo, "txt": f"{txt_diff} (24h)", "estado": estado}

    def ingresar_activos_a_inbox(self, lista_rutas):
        """Mueve físicamente al Inbox, actualiza estado, path y fecha de ingreso en el Mapa."""
        import shutil
        ruta_inbox_destino = os.path.join(self.path_sipa, "data/inbox")
        os.makedirs(ruta_inbox_destino, exist_ok=True)
        
        fecha_hoy = datetime.now().strftime('%d/%m/%Y')
        
        # Cargar el JSON del mapa para actualizar los estados en caliente
        datos_mapa = []
        if os.path.exists(self.path_mapa):
            try:
                with open(self.path_mapa, "r", encoding="utf-8") as f:
                    datos_mapa = json.load(f)
            except: pass

        # Cargar rutas en seguimiento para evitar duplicados catastróficos
        rutas_sipa_activas = self._obtener_rutas_en_seguimiento()
        ficheros_en_inbox = set(os.listdir(ruta_inbox_destino)) if os.path.exists(ruta_inbox_destino) else set()
        
        reporte = {"procesados": 0, "errores": 0, "duplicados_omitidos": []}
        
        for ruta_origen in lista_rutas:
            if not os.path.exists(ruta_origen):
                reporte["errores"] += 1
                continue
                
            nombre_fichero = os.path.basename(ruta_origen)
            
            # Control de Duplicados
            if nombre_fichero in ficheros_en_inbox:
                reporte["duplicados_omitidos"].append(f"{nombre_fichero} (Ya está en Inbox)")
                continue
            if ruta_origen in rutas_sipa_activas:
                reporte["duplicados_omitidos"].append(f"{nombre_fichero} (Ya está en Seguimiento)")
                continue

            destino_final = os.path.join(ruta_inbox_destino, nombre_fichero)
            
            try:
                # 1. Movimiento físico en el disco de Linux
                shutil.move(ruta_origen, destino_final)
                reporte["procesados"] += 1
                
                # 2. Actualizar el registro dentro del JSON del MAPA en caliente
                for item in datos_mapa:
                    if item.get("path_actual") == ruta_origen:
                        item["estado"] = "Seguimiento"         # Cambia el estado
                        item["path_actual"] = destino_final    # Actualiza el Path al Inbox
                        
                        # Asignación exacta según los nombres de tus columnas:
                        item["fecha_ingresado"] = fecha_hoy    # Para que se pinte en la tabla MAPA 🗺️
                        item["fecha_entrada"] = fecha_hoy      # Para la trazabilidad interna
                        break
                        
            except (PermissionError, OSError) as e:
                print(f"❌ Error en movimiento: {e}")
                reporte["errores"] += 1
        
        # Guardar los estados actualizados en el JSON del mapa
        if reporte["procesados"] > 0:
            try:
                with open(self.path_mapa, "w", encoding="utf-8") as f:
                    json.dump(datos_mapa, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error guardando actualización de mapa: {e}")
                
        return reporte

    def editar_mapa_observaciones(self, path_archivo, nueva_observacion):
        """Gestiona las observaciones creadas en los registros persistentes en sipa-activos.json"""
        
        # COMPROBAMOS EXISTENCIA DE FICHERO
        try:
            if not os.path.exists(self.path_mapa):
                return False
        except Exception as e:
            print(f"❌ Error al verificar el archivo del MAPA: {e}")
            return False

        # ABRIMOS FICHERO EN MODO LECTURA
        try:
            with open(self.path_mapa, "r", encoding="utf-8") as f:
                datos_mapa = json.load(f)
        except Exception as e:
            print(f"❌ Error al leer el contenido del MAPA: {e}")
            return False
        # RECORREMOS CON UN BUCLE BUSCANDO EL REGISTRO CORRECTO
        for item in datos_mapa:
            if item.get("path_actual") == path_archivo:
                item["observaciones"] = nueva_observacion
                break
        # ABRIMOS EL FICHERO EN MODO ESCRITURA Y LO CERRAMOS
        try:
            with open(self.path_mapa, "w", encoding="utf-8") as f:
                json.dump(datos_mapa, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error al escribir el archivo del mapa: {e}")
            return False