# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: scsipacur_process_file.py
# Módulo: SIPAcur Service (Procesador de Activos)
# Versión: 1.7.0 | Fecha: 17/05/2026
# ----------------------------------------------------------
# FINAL: 23 campos fijos, movimiento físico y limpieza total.
# ==========================================================

import os
import json
import re
import hashlib
import getpass
import shutil
from datetime import datetime

class SIPAcurProcessorService:
    def __init__(self):
        self.user_name = getpass.getuser()
        self.base_path = f"/home/{self.user_name}/SIPA"
        self.path_db = os.path.join(self.base_path, "data/db")
        self.path_inbox = os.path.join(self.base_path, "data/inbox")
        self.path_knowledge = os.path.join(self.base_path, "data/knowledge/procesados")
        self.path_inventario = os.path.join(self.path_db, "sipa_activos.json")
        self.path_logs = os.path.join(self.base_path, "external/SIPAcur/logs")
        self.path_historico = os.path.join(self.path_logs, "historico_process.log")
        
        # LISTA MAESTRA DE LOS 23 CAMPOS (ORDEN SIPA)
        self.columnas_estandar = [
            "id_interno", "pendiente", "revisado", "procesado", "registrado", 
            "nombre_fichero_original", "tipo", "path_actual", "unidad", "estado", 
            "hash", "observaciones", "total_palabras", "palabras", "frase", 
            "path_publicado", "fecha_creación", "fecha_entrada", "fecha_publicación", 
            "tamaño_kB", "extensión", "enlace", "SIPAcur_Sugerencia"
        ]
        
        self.inicializar_servicio()

    def inicializar_servicio(self):
        """Crea la estructura de carpetas necesaria."""
        for p in [self.path_db, self.path_logs, self.path_knowledge, self.path_inbox]:
            os.makedirs(p, exist_ok=True)
        if not os.path.exists(self.path_inventario):
            self.guardar_inventario([])

    def calcular_hash(self, texto):
        return hashlib.sha256(texto.encode('utf-8')).hexdigest()

    def registrar_log_historico(self, mensaje):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self.path_historico, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {mensaje}\n")
        except: pass

    def guardar_inventario(self, data):
        try:
            with open(self.path_inventario, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.registrar_log_historico(f"ERROR CRÍTICO JSON: {e}")

    def obtener_inventario_actual(self):
        if not os.path.exists(self.path_inventario): return []
        try:
            with open(self.path_inventario, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []

    # --- NÚCLEO DE PROCESAMIENTO ---

    def extraer_metadata_completa(self, ruta, id_asig):
        """Extrae los 23 campos asegurando que no falte ninguno en la tabla."""
        # Paso 1: Crear molde de 23 campos vacíos
        metadatos = {col: " " for col in self.columnas_estandar}
        
        # Paso 2: Rellenar básicos por si falla la lectura
        metadatos.update({
            "id_interno": str(id_asig),
            "nombre_fichero_original": os.path.basename(ruta),
            "path_actual": ruta,
            "unidad": "/:",
            "extensión": os.path.splitext(ruta)[1].replace(".", "")
        })

        if not os.path.exists(ruta): return metadatos

        try:
            with open(ruta, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Paso 3: Buscar Frontmatter
            match = re.search(r'^---\s*\n(.*?)\n---\s*', content, re.DOTALL)
            if match:
                lineas = match.group(1).split('\n')
                for linea in lineas:
                    if ':' in linea:
                        k, v = linea.split(':', 1)
                        key = k.strip()
                        if key in metadatos:
                            # Limpieza total de comillas y comas accidentales
                            metadatos[key] = v.strip().strip('"').strip("'").rstrip(',')
            
            # Paso 4: Metadatos físicos si no estaban en el Frontmatter
            if metadatos["tamaño_kB"] == " ":
                metadatos["tamaño_kB"] = str(round(os.path.getsize(ruta) / 1024, 2))
                
        except Exception as e:
            self.registrar_log_historico(f"Error lectura metadata en {ruta}: {e}")
            
        return metadatos

    def obtener_datos_inbox(self):
        """Escanea el Inbox y devuelve los 23 campos por cada archivo."""
        datos = []
        if not os.path.exists(self.path_inbox): return datos
        ficheros = sorted([f for f in os.listdir(self.path_inbox) if f.endswith(".md")])
        for i, f in enumerate(ficheros):
            ruta = os.path.join(self.path_inbox, f)
            datos.append(self.extraer_metadata_completa(ruta, i + 1))
        return datos

    def procesar_lote(self, lista_rutas):
        """Mueve, etiqueta con los 23 campos y registra en el inventario."""
        inventario = self.obtener_inventario_actual()
        fecha_hoy = datetime.now().strftime('%d/%m/%Y')

        for ruta_origen in lista_rutas:
            if not os.path.exists(ruta_origen): continue
            
            nombre_f = os.path.basename(ruta_origen)
            ruta_destino = os.path.join(self.path_knowledge, nombre_f)

            try:
                # 1. Capturar contenido y cuerpo
                with open(ruta_origen, "r", encoding="utf-8") as f:
                    full_text = f.read()

                match = re.search(r'^---\s*\n(.*?)\n---\s*', full_text, re.DOTALL)
                body_content = full_text[match.end():] if match else full_text
                hash_calc = self.calcular_hash(body_content)
                
                # 2. MOVER ARCHIVO FÍSICAMENTE
                shutil.move(ruta_origen, ruta_destino)

                # 3. Determinar ID y buscar si ya existe por Hash
                existente = next((item for item in inventario if item.get('hash') == hash_calc), None)
                nuevo_id = existente['id_interno'] if existente else str(max([int(item.get('id_interno', 0)) for item in inventario] + [0]) + 1)
                
                # 4. CONSTRUIR DICCIONARIO DE 23 CAMPOS (Preservamos los manuales)
                datos_pre_existentes = self.extraer_metadata_completa(ruta_destino, nuevo_id)
                
                valores_nuevos = {
                    "id_interno": nuevo_id,
                    "pendiente": "Si",
                    "revisado": "Si",
                    "procesado": "No",
                    "registrado": "Si",
                    "nombre_fichero_original": nombre_f,
                    "tipo": "Nota",
                    "path_actual": ruta_destino,
                    "unidad": "/:",
                    "estado": "Activo",
                    "hash": hash_calc,
                    "observaciones": "Procesado por SIPAcur",
                    "total_palabras": str(len(body_content.split())),
                    "fecha_creación": fecha_hoy,
                    "fecha_entrada": fecha_hoy,
                    "tamaño_kB": str(round(os.path.getsize(ruta_destino) / 1024, 2)),
                    "extensión": "md",
                    "SIPAcur_Sugerencia": "Ubicación sugerida: procesados"
                }
                
                # Mezclamos: los 23 campos base + los nuevos valores calculados
                datos_pre_existentes.update(valores_nuevos)

                # 5. Escribir Etiqueta final en el archivo .md
                self.escribir_frontmatter_fisico(ruta_destino, datos_pre_existentes)

                # 6. Actualizar el JSON Maestro
                if existente:
                    for i, item in enumerate(inventario):
                        if item.get('hash') == hash_calc: inventario[i] = datos_pre_existentes
                else:
                    inventario.append(datos_pre_existentes)
                
                self.registrar_log_historico(f"ÉXITO: {nombre_f} procesado correctamente.")

            except Exception as e:
                self.registrar_log_historico(f"ERROR procesando {nombre_f}: {e}")

        self.guardar_inventario(inventario)

    def sincronizar_ubicaciones_reales(self):
        """Mantiene la tabla de seguimiento fiel a la realidad del disco."""
        inventario = self.obtener_inventario_actual()
        for item in inventario:
            if os.path.exists(item['path_actual']):
                # Refrescamos los 23 campos desde el archivo físico
                meta_fisica = self.extraer_metadata_completa(item['path_actual'], item['id_interno'])
                item.update(meta_fisica)
        self.guardar_inventario(inventario)
        return inventario

    def escribir_frontmatter_fisico(self, ruta, datos):
        """Escribe las 23 líneas de la etiqueta SIPA en orden estricto y sin comas."""
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'^---\s*\n(.*?)\n---\s*', content, re.DOTALL)
            body = content[match.end():] if match else content
            
            header = ["---"]
            for col in self.columnas_estandar:
                val = datos.get(col, " ")
                # Formato SIPA: Números sin comillas, texto con comillas. Sin comas finales.
                if col in ["id_interno", "hash", "total_palabras", "tamaño_kB"]:
                    header.append(f'{col}: {val}')
                else:
                    header.append(f'{col}: "{val}"')
            header.append("---")
            
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("\n".join(header) + "\n" + body)
        except Exception as e:
            self.registrar_log_historico(f"Error escritura física: {e}")

    def actualizar_item_completo(self, item):
        """Guarda cambios manuales desde la tabla de Seguimiento."""
        inventario = self.obtener_inventario_actual()
        for i, antiguo in enumerate(inventario):
            if antiguo.get('id_interno') == item.get('id_interno'):
                inventario[i] = item
                break
        self.guardar_inventario(inventario)
        
        ruta = item.get('path_actual')
        if ruta and os.path.exists(ruta):
            self.escribir_frontmatter_fisico(ruta, item)