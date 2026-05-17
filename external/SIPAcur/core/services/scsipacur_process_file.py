# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: scsipacur_process_file.py
# Módulo: SIPAcur Service (Procesador de Activos)
# Versión: 1.4.0 | Fecha: 17/05/2026
# ----------------------------------------------------------
# DESCRIPCIÓN: Procesador con Vigilancia Constante.
# Implementa el campo 'observaciones' y sincronización 
# bidireccional entre tabla física y digital.
# ==========================================================

import os
import json
import re
import hashlib
import getpass
from datetime import datetime

class SIPAcurProcessorService:
    def __init__(self):
        self.user_name = getpass.getuser()
        self.base_path = f"/home/{self.user_name}/SIPA"
        self.path_db = os.path.join(self.base_path, "data/db")
        self.path_knowledge = os.path.join(self.base_path, "data/knowledge")
        self.path_template = os.path.join(self.base_path, "core/labels_files/template_frontmatter.md")
        self.path_inventario = os.path.join(self.path_db, "sipa_activos.json")
        self.path_logs = os.path.join(self.base_path, "external/SIPAcur/logs")
        self.path_historico = os.path.join(self.path_logs, "historico_process.log")
        
        self.inicializar_servicio()

    def inicializar_servicio(self):
        os.makedirs(self.path_db, exist_ok=True)
        os.makedirs(self.path_logs, exist_ok=True)
        if not os.path.exists(self.path_inventario):
            with open(self.path_inventario, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)

    def calcular_hash(self, texto):
        return hashlib.sha256(texto.encode('utf-8')).hexdigest()

    def registrar_log_historico(self, mensaje):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self.path_historico, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {mensaje}\n")
        except: pass

    def leer_campos_plantilla(self):
        """Lee el orden exacto de la plantilla maestra corregida."""
        # Orden por defecto si la plantilla no existe
        default_orden = [
            "id_interno", "pendiente", "revisado", "procesado", "registrado", 
            "nombre_fichero_original", "tipo", "path_actual", "unidad", "estado", 
            "hash", "observaciones", "total_palabras", "palabras", "frase", 
            "path_publicado", "fecha_creación", "fecha_entrada", "fecha_publicación", 
            "tamaño_kB", "extensión", "enlace", "SIPAcur_Sugerencia"
        ]
        
        if not os.path.exists(self.path_template):
            return default_orden
        
        campos = []
        try:
            with open(self.path_template, "r", encoding="utf-8") as f:
                content = f.read()
                match = re.search(r'^---\s*\n(.*?)\n---\s*', content, re.DOTALL)
                if match:
                    for line in match.group(1).split('\n'):
                        if ':' in line:
                            campos.append(line.split(':')[0].strip())
            return campos if campos else default_orden
        except:
            return default_orden

    def procesar_lote(self, lista_rutas):
        """Etiquetado basado estrictamente en la Plantilla Maestra SIPA."""
        inventario = self.obtener_inventario_actual()
        orden_plantilla = self.leer_campos_plantilla()
        fecha_hoy = datetime.now().strftime('%d/%m/%Y')

        for ruta in lista_rutas:
            if not os.path.exists(ruta): continue
            nombre_f = os.path.basename(ruta)
            unidad = os.path.splitdrive(ruta)[0] if os.path.splitdrive(ruta)[0] else "/:"
            tipo = os.path.splitext(nombre_f)[1].replace(".", "").lower()
            size_kb = round(os.path.getsize(ruta) / 1024, 2)

            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    full_text = f.read()

                match = re.search(r'^---\s*\n(.*?)\n---\s*', full_text, re.DOTALL)
                body_content = full_text[match.end():] if match else full_text
                hash_calc = self.calcular_hash(body_content)
                total_w = len(body_content.split())

                # Evitar duplicados por Hash
                if any(item.get('hash') == hash_calc for item in inventario):
                    continue

                ids_existentes = [int(item.get('id_interno', 0)) for item in inventario]
                nuevo_id = max(ids_existentes + [0]) + 1

                valores = {
                    "id_interno": str(nuevo_id),
                    "pendiente": "Si",
                    "revisado": "Si",
                    "procesado": "No",
                    "registrado": "Si",
                    "nombre_fichero_original": nombre_f,
                    "tipo": tipo,
                    "path_actual": ruta,
                    "unidad": unidad,
                    "estado": "Activo",
                    "hash": hash_calc,
                    "observaciones": "Fichero procesado por SIPAcur",
                    "total_palabras": str(total_w),
                    "palabras": " ",
                    "frase": " ",
                    "path_publicado": " ",
                    "fecha_creación": fecha_hoy,
                    "fecha_entrada": fecha_hoy,
                    "fecha_publicación": " ",
                    "tamaño_kB": str(size_kb),
                    "extensión": tipo,
                    "enlace": " ",
                    "SIPAcur_Sugerencia": "(Análisis pendiente)"
                }

                # Construcción de la etiqueta física respetando el orden
                cabecera_final = []
                for campo in orden_plantilla:
                    val = valores.get(campo, " ")
                    if campo in ["id_interno", "total_palabras", "hash", "tamaño_kB"]:
                        cabecera_final.append(f'{campo}: {val},')
                    else:
                        cabecera_final.append(f'{campo}: "{val}",')

                with open(ruta, "w", encoding="utf-8") as f:
                    f.write("---\n" + "\n".join(cabecera_final) + "\n---\n" + body_content)

                inventario.append(valores)
                self.registrar_log_historico(f"PROCESADO: {nombre_f} (ID: {nuevo_id})")

            except Exception as e:
                self.registrar_log_historico(f"ERROR: {nombre_f} - {e}")

        self.guardar_inventario(inventario)

    def sincronizar_ubicaciones_reales(self):
        """Vigilancia constante y re-lectura de frontmatter modificado."""
        inventario = self.obtener_inventario_actual()
        disco_actual = {}
        for root, _, files in os.walk(self.path_knowledge):
            for f in files:
                if f.endswith(".md"):
                    disco_actual[f] = os.path.join(root, f)

        nuevo_inventario = []
        hubo_cambios = False

        for item in inventario:
            nombre = item.get('nombre_fichero_original')
            ruta_old = item.get('path_actual')
            ruta_real = ruta_old if os.path.exists(ruta_old) else disco_actual.get(nombre)

            if ruta_real:
                # RE-LECTURA: Verificamos si el usuario cambió datos físicamente
                metadatos_fisicos = self.extraer_datos_físicos(ruta_real)
                for k, v in metadatos_fisicos.items():
                    if item.get(k) != v:
                        item[k] = v
                        hubo_cambios = True
                
                item['path_actual'] = ruta_real
                if item.get('verificado') != "Si":
                    item['verificado'] = "Si"
                    hubo_cambios = True
            else:
                if item.get('verificado') != "No":
                    item['verificado'] = "No"
                    hubo_cambios = True
            
            nuevo_inventario.append(item)

        if hubo_cambios:
            self.guardar_inventario(nuevo_inventario)
        
        return nuevo_inventario

    def extraer_datos_físicos(self, ruta):
        """Lee el frontmatter actual para actualizar el JSON."""
        datos = {}
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'^---\s*\n(.*?)\n---\s*', content, re.DOTALL)
            if match:
                for linea in match.group(1).split('\n'):
                    if ':' in linea:
                        k, v = linea.split(':', 1)
                        # Limpieza de comas y comillas
                        datos[k.strip()] = v.strip().rstrip(',').strip('"').strip("'")
        except: pass
        return datos

    def obtener_inventario_actual(self):
        if not os.path.exists(self.path_inventario): return []
        try:
            with open(self.path_inventario, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []

    def guardar_inventario(self, data):
        with open(self.path_inventario, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)