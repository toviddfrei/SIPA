# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: scsipacur_learn_file.py
# Módulo: SIPA_Learn_Service (Motor de Auditoría y Radar)
# Versión: 4.1.0 | Fecha: 18/05/2026
# ==========================================================

import os
import json
import getpass
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
        """Realiza un escaneo recursivo total buscando activos .md."""
        mapa_ficheros = []
        rutas_en_seguimiento = self._obtener_rutas_en_seguimiento()
        
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
                        
                        registro = {
                            "id_interno": str(contador_id),
                            "nombre": file,
                            "fecha_detectado": datetime.now().strftime('%d/%m/%Y'),
                            "estado": "Seguimiento" if es_seguido else "Pendiente",
                            "anotacion": " ",
                            "fecha_ingresado": "N/A", 
                            "path_actual": path_completo,
                            "tamaño_kb": str(round(info_disco.st_size / 1024, 2)),
                            "ultima_modificacion": datetime.fromtimestamp(info_disco.st_mtime).strftime('%d/%m/%Y')
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