"""
SIPAweb Builder v1.3
--------------------
Motor de generación estática con auditoría de integridad SHA-256.
Especializado en la gestión de Identidad Digital (Hito 2A).
"""

import markdown
from jinja2 import Environment, FileSystemLoader
import os
import hashlib
import json
import shutil
import unicodedata
import subprocess
from datetime import datetime

class SipaModule:
    """
    CLASE BASE BOLARDO: Gestión de Integridad y Provisión.
    Vigila la constancia de los archivos mediante hashing.
    """
    def __init__(self, page_name, base_path):
        self.page_name = page_name
        self.base_path = base_path
        self.manifest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")
        self.file_path = os.path.join(self.base_path, f"{page_name}.md")
        self.folder_path = os.path.join(self.base_path, page_name)

    def _get_hash(self, data):
        """Genera firma SHA-256."""
        return hashlib.sha256(data).hexdigest()

    def calculate_hashes(self):
        """Calcula hashes para el archivo principal y la carpeta de bloques."""
        f_hash = None
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as f: f_hash = self._get_hash(f.read())
        
        d_hash = None
        if os.path.exists(self.folder_path):
            hashes = []
            for root, _, files in os.walk(self.folder_path):
                for f in sorted(files):
                    if f.endswith(".md"):
                        with open(os.path.join(root, f), "rb") as bf:
                            hashes.append(self._get_hash(bf.read()))
            if hashes: d_hash = self._get_hash("".join(hashes).encode())
        
        return f_hash, d_hash

    def verify_integrity(self):
        """Compara el estado actual con el registro en manifest.json."""
        try:
            if not os.path.exists(self.manifest_path): return False, "NUEVO_ENTORNO"
            with open(self.manifest_path, "r") as f: manifest = json.load(f)
            record = manifest.get(self.page_name, {})
            curr_f, curr_d = self.calculate_hashes()
            if record.get("file_hash") != curr_f: return False, "FILE_CHANGED"
            if record.get("dir_hash") != curr_d: return False, "DIR_CHANGED"
            return True, "OK"
        except: return False, "ERROR"

    def update_manifest(self):
        """PASO CRÍTICO: Actualiza el .json con los nuevos hashes tras el build."""
        manifest = {}
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r") as f: manifest = json.load(f)
        f_h, d_h = self.calculate_hashes()
        manifest[self.page_name] = {"file_hash": f_h, "dir_hash": d_h, "last": datetime.now().isoformat()}
        with open(self.manifest_path, "w") as f: json.dump(manifest, f, indent=4)

class SipaFileIndex(SipaModule):
    """
    CLASE ESPECÍFICA: Creadora de contenido para el Index.
    Mantiene tu lógica de provisión de bloques Bento.
    """
    def provision(self):
        """Si no existen los ficheros, los crea con el estándar SIPA (Recuperado)."""
        # 1. Crear el index.md principal (Tu estructura original)
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            content = (
                "---\n"
                "titulo: Hola, soy Daniel\n"
                "nombre_sitio: Daniel Miñana Montero\n"
                "rol: Propietario\n"
                "subtitulo: Cuándo la tecnología está en tú ADN.\n"
                "hero_bg: img/avatargithub.png\n"
                "experiencia: +20 años\n"
                "estado: Protegido\n"
                "tag: Presentación\n"
                "---\n"
                "# La convergencia entre experiencia e innovación\n\n"
                "Os invito a navegar por este sitio para poder conocerme un poquito mejor, en el no solo vuelco mi trayectoria profesional y formativa, presento mis habilidades, os enseño mi trabajo, y sobre todo recopilo mi conocimiento, tras bastante tiempo intentandolo he conseguido preparar este sistema propio que construye este sitio automáticamente, y presenta quién soy en profundidad.\n"
                "Gracias por visitarme, Daniel\n"
            )
            with open(self.file_path, "w", encoding="utf-8") as f: f.write(content)

        # 2. Crear carpeta de bloques y ejemplo de seguridad (Tu estructura original)
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path, exist_ok=True)
            bloque_path = os.path.join(self.folder_path, "01_seguridad.md")
            bloque_content = (
                "---\n"
                "id: bloque_nombre\n"
                "icono: ph-shield-check\n"
                "titulo: FHS Cybersecurity\n"
                "enlace: '#'\n"
                "orden: 1\n"
                "estado: Auditado\n"
                "tag: Seguridad\n"
                "---\n"
                "# BLOQUE NOMBRE\n\n"
                "Implementación de integridad basada en hashing SHA-256."
            )
            with open(bloque_path, "w", encoding="utf-8") as f: f.write(bloque_content)

class SipaFileSobreMi(SipaModule):
    """
    CLASE ESPECÍFICA: Creadora de contenido para Sobre-Mí.
    Réplica exacta de la lógica de matrices del Index.
    """
    def provision(self):
        """Si no existen los ficheros, los crea con el estándar SIPA."""
        # 1. Crear el sobre-mi.md principal (Estructura de Identidad)
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            content = (
                "---\n"
                "titulo: Sobre Mí\n"
                "nombre_sitio: Daniel Miñana Montero\n"
                "rol: Propietario\n"
                "subtitulo: Más de 20 años de evolución IT\n"
                "hero_bg: img/sobre-mi-bg.png\n"
                "estado: Protegido\n"
                "tag: Biografía\n"
                "---\n"
                "# Mi Historia\n\n"
                "## Más allá del código: Constancia, Historia y Resiliencia\n\n"
                "Soy una persona de naturaleza introvertida, lo que me ha llevado a desarrollar una capacidad de observación y análisis muy aguda. Me defino por una palabra: **constancia**. No entiendo la tecnología sin el estudio, ni el éxito sin el camino que conlleva alcanzarlo.\n\n"
                "### Una anécdota que me define\n\n"
                "A principios de los 2000, trabajando para una multinacional inglesa, asumí el reto de desplegar una infraestructura de red completa desde cero. En aquel entonces, mi conocimiento era básico, pero mi instinto autodidacta me llevó a profundizar hasta el punto más alto: la certificación **CCNA de Cisco**.\n"
                "Tras meses de estudio teórico-práctico intenso y excelentes notas, me enfrenté al examen final. Estaba preparado para la tecnología, pero mi inglés básico de aquel entonces me detuvo en la puerta de la certificación oficial. Esa experiencia, lejos de ser un fracaso, cimentó mi personalidad profesional: **soy disciplinado, profesional y mi pasión por aprender no tiene techo**. Lo que no sé hoy, lo estaré dominando mañana.\n\n"
                "### Mi presente en NCR\n\n"
                "Esa misma curiosidad y rigor técnico son los que aplico hoy en **NCR ESPAÑA (NCR VOYIX)**. Como Técnico de Campo (Customer Engineer), gestiono sistemas críticos en los sectores de Retail y Hospitality, donde la resolución de problemas en tiempo real es el estándar.\n\n"
                "Te invito a explorar mis trayectorias formativa y profesional para entender cómo cada paso me ha traído hasta la creación de este proyecto personal.\n\n"
                "**PD:** Revisando documentación antigua, he rescatado mi "
                "[Portfolio 2018 (PDF)](pdf/2018_porfolio.pdf), te invito a echarle un vistazo para conocer mis orígenes.\n"
            )
            
            with open(self.file_path, "w", encoding="utf-8") as f: f.write(content)

        # 2. Crear carpeta sobre-mi/ y el bloque de ejemplo 'trayectoria'
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path, exist_ok=True)
            bloque_path = os.path.join(self.folder_path, "01_trayectoria.md")
            bloque_content = (
                "---\n"
                "id: trayectoria_ejemplo\n"
                "icono: ph-briefcase\n"
                "titulo: Experiencia Principal\n"
                "enlace: '#'\n"
                "orden: 1\n"
                "estado: Auditado\n"
                "tag: Profesional\n"
                "---\n"
                "# TRAYECTORIA\n\n"
                "Usa este bloque como plantilla para tus tablas de experiencia o formación."
            )
            with open(bloque_path, "w", encoding="utf-8") as f: f.write(bloque_content)

class SipaFileProyectos(SipaModule):
    """
    CLASE ESPECÍFICA: Creadora de contenido para Proyectos.
    Réplica exacta de la lógica de matrices del Index.
    """
    def provision(self):
        """Si no existen los ficheros, los crea con el estándar SIPA."""
        # 1. Crear el sobre-mi.md principal (Estructura de Identidad)
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            content = (
                "---\n"
                "titulo: Proyectos\n"
                "nombre_sitio: Daniel Miñana Montero\n"
                "rol: Trayectoria Profesional\n"
                "subtitulo: Más de 20 años de evolución IT\n"
                "hero_bg: img/proyectos-bg.png\n" # Ruta preparada para tu nueva imagen
                "estado: Protegido\n"
                "tag: Proyectos\n"
                "---\n"
                "# Mis proyectos\n\n"
                "Bienvenido a mi rincón de pensar, y no habló en plan paradójico, es así, ante estos documentos, códigos, imágenes, paso gran parte de mi tiempo, disfruto imaginando posibilidades y proponiéndome retos técnicos o nuevos aprendizajes que me podría venir bien, bueno os he presentado mi espacio de proyectos, ahora quiero hacer hincapié en uno fundamentalmente, y en sus ramificaciones, hablamos de SIPA como mi proyecto principal desde hace unos meses y que tras una fase de rediseño y optimización en enero, decidí priorizar el despliegue de SIPAweb como la cara visible de un ecosistema mucho más profundo.\n\n"
                "Ahora sí, mi proyecto SIPA (Sistema de Identificación Personal Autorizada). Si queréis consultar más en profundidad alguno de los proyectos, los bloques a continuación os enlazan a sus páginas específicas; también aprovecho y os animo a dejar cualquier comentario constructivo a través de la página de contacto.\n\n"
                "## Proyecto SIPA, módulo SIPAweb\n\n"
                "Bienvenido a **SIPAweb**, el núcleo digital de mi identidad profesional. Este espacio no es solo una web; es un ecosistema automatizado diseñado para gestionar y proyectar una trayectoria de más de dos décadas en el sector tecnológico. Como característica o una de ellas fundamental, la construcción del sitio web se realiza de forma autónoma desde ficheros markdown que son procesados automáticamente al detectar modificaciones en los ficheros; se renueva su hash y se construye nuevamente el fichero .html.\n\n"
                "### ¿Qué es SIPA?\n\n"
                "El **Sistema de Identificación Personal Autorizada (SIPA)** nace de la necesidad de unificar mi perfil profesional bajo un estándar de integridad y transparencia. Es el motor que destila años de administración de sistemas, redes y soporte técnico hacia el nuevo paradigma de la automatización y la ciberseguridad.\n\n"
                "### ¿Qué es SIPAweb?\n\n"
                "Es la implementación física de esta visión. Un sistema **automático, gratuito y resiliente** que transforma documentos Markdown en una presencia web profesional. Construido bajo la filosofía *Plug & Play*, SIPAweb garantiza que mi perfil esté siempre actualizado, auditado y listo para los retos del futuro digital.\n"
            )
            with open(self.file_path, "w", encoding="utf-8") as f: f.write(content)

        # 2. Crear carpeta proyectos/ y el bloque de ejemplo 'trayectoria'
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path, exist_ok=True)
            bloque_path = os.path.join(self.folder_path, "01_proyectos.md")
            bloque_content = (
                "---\n"
                "id: proyectos_ejemplo\n"
                "icono: ph-briefcase\n"
                "titulo: Proyectos Destacados\n"
                "enlace: '#'\n"
                "orden: 1\n"
                "estado: Auditado\n"
                "tag: Profesional\n"
                "---\n"
                "# PROYECTOS\n\n"
                "Usa este bloque como plantilla para tus tablas proyectos."
            )
            with open(bloque_path, "w", encoding="utf-8") as f: f.write(bloque_content)

class SipaFileContacto(SipaModule):
    """
    CLASE ESPECÍFICA: Creadora de contenido para Contacto.
    Réplica exacta de la lógica de matrices del Index.
    """
    def provision(self):
        """Si no existen los ficheros, los crea con el estándar SIPA."""
        # 1. Crear el sobre-mi.md principal (Estructura de Identidad)
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            content = (
                "---\n"
                "titulo: Contacto\n"
                "nombre_sitio: SIPAweb\n"
                "rol: Trayectoria Profesional\n"
                "subtitulo: Más de 20 años de evolución IT\n"
                "hero_bg: img/contacto-bg.png\n" # Ruta preparada para tu nueva imagen
                "estado: Protegido\n"
                "tag: Contacto\n"
                "---\n"
                "# Mis Contacto\n\n"
                "Este es el espacio para tu presentación Contacto."
            )
            with open(self.file_path, "w", encoding="utf-8") as f: f.write(content)

        # 2. Crear carpeta Contacto/ y el bloque de ejemplo 'trayectoria'
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path, exist_ok=True)
            bloque_path = os.path.join(self.folder_path, "01_Contacto.md")
            bloque_content = (
                "---\n"
                "id: Contacto_ejemplo\n"
                "icono: ph-briefcase\n"
                "titulo: Contacto Destacados\n"
                "enlace: '#'\n"
                "orden: 1\n"
                "estado: Auditado\n"
                "tag: Profesional\n"
                "---\n"
                "# Contacto\n\n"
                "Usa este bloque como plantilla para tus tablas Contacto."
            )
            with open(bloque_path, "w", encoding="utf-8") as f: f.write(bloque_content)

class SipaFileAyuda(SipaModule):
    """
    CLASE ESPECÍFICA: Creadora de contenido para Ayuda.
    Réplica exacta de la lógica de matrices del Index.
    """
    def provision(self):
        """Si no existen los ficheros, los crea con el estándar SIPA."""
        # 1. Crear el sobre-mi.md principal (Estructura de Identidad)
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            content = (
                "---\n"
                "titulo: Ayuda\n"
                "nombre_sitio: SIPAweb\n"
                "rol: Trayectoria Profesional\n"
                "subtitulo: Más de 20 años de evolución IT\n"
                "hero_bg: img/Ayuda-bg.png\n" # Ruta preparada para tu nueva imagen
                "estado: Protegido\n"
                "tag: Ayuda\n"
                "---\n"
                "# Mis Ayuda\n\n"
                "Este es el espacio para tu presentación Ayuda."
            )
            with open(self.file_path, "w", encoding="utf-8") as f: f.write(content)

        # 2. Crear carpeta Ayuda/ y el bloque de ejemplo 'trayectoria'
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path, exist_ok=True)
            bloque_path = os.path.join(self.folder_path, "01_Ayuda.md")
            bloque_content = (
                "---\n"
                "id: Ayuda_ejemplo\n"
                "icono: ph-briefcase\n"
                "titulo: Ayuda Destacados\n"
                "enlace: '#'\n"
                "orden: 1\n"
                "estado: Auditado\n"
                "tag: Profesional\n"
                "---\n"
                "# Ayuda\n\n"
                "Usa este bloque como plantilla para tus tablas Ayuda."
            )
            with open(bloque_path, "w", encoding="utf-8") as f: f.write(bloque_content)

class SipaFilePost(SipaModule):
    """
    MOTOR EDITORIAL INTEGRADO: Respeta el estándar de rutas de SipaModule.
    Todo el trabajo MD ocurre en templates/static/posts/
    Todo el resultado HTML ocurre en /posts/
    """
    def __init__(self, page_name, base_path, builder):
        super().__init__(page_name, base_path)
        self.builder = builder
        
        # Rutas base
        self.process_folder = os.path.join(self.folder_path, "process")
        self.public_folder = os.path.join(self.folder_path, "public")
        self.output_folder = os.path.join(self.builder.raiz, "posts")
        
        # NUEVO: Subcarpetas específicas en public
        self.laboral_folder = os.path.join(self.public_folder, "laboral")
        self.formativa_folder = os.path.join(self.public_folder, "formativa")

    def provision(self):
        """Crea la estructura física del módulo, incluyendo subcarpetas de trayectoria."""
        carpetas = [
            self.process_folder, 
            self.public_folder, 
            self.output_folder,
            self.laboral_folder,   # <--- Nueva
            self.formativa_folder  # <--- Nueva
        ]
        for carpeta in carpetas:
            os.makedirs(carpeta, exist_ok=True)
            print(f"[*] Verificada carpeta: {carpeta}")
        
        # Semilla de ejemplo (solo si está todo vacío)
        ejemplo_path = os.path.join(self.process_folder, "00-plantilla-post.md")
        if not os.listdir(self.process_folder) and not os.listdir(self.public_folder):
            content = (
                "---\n"
                "titulo: Implementación de Módulos SIPA\n"
                "subtitulo: Guía técnica sobre la arquitectura de datos estáticos\n"
                "estado: proceso\n"
                "fecha_creacion: 2026-02-21\n"
                "fecha_publicacion: pendiente\n"
                "tag: python, arquitectura, web\n"
                "tipo: post\n"
                "autor: Daniel Miñana\n"
                "---\n\n"
                "# Introducción\n"
                "Este es el contenido del post.\n\n"
                "## Desarrollo Técnico\n"
                "Aquí probaremos el despliegue de código:\n"
                "```python\n"
                "print('SIPAweb activo')\n"
                "```\n\n"
                "## Conclusión\n"
                "Finalización del documento."
            )
            with open(ejemplo_path, "w", encoding="utf-8") as f: f.write(content)
            print(f"[*] Semilla creada en: {self.process_folder}")

    def _procesar_md(self, ruta):
        """Extracción limpia de metadatos y cuerpo."""
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            partes = contenido.split('---', 2)
            if len(partes) >= 3:
                meta_raw = partes[1].strip()
                # Diccionario de metadatos: clave: valor
                metadatos = {l.split(":",1)[0].strip(): l.split(":",1)[1].strip().strip('"') 
                            for l in meta_raw.split('\n') if ":" in l}
                return metadatos, partes[2].strip()
            return {}, contenido
        except Exception as e:
            print(f"[X] Error MD: {e}")
            return {}, ""

    def ejecutar_ciclo_editorial(self):
        """Renderizado recursivo de posts y clasificación automática."""
        self.provision() 
        self.coleccion_posts = [] 

        # ESCANEO RECURSIVO: Entra en public/ y en cualquier subcarpeta
        for raiz, carpetas, archivos in os.walk(self.public_folder):
            for filename in archivos:
                if not filename.endswith(".md"):
                    continue

                # A. Identificar si está en una subcarpeta (ej: 'laboral')
                sub_relativa = os.path.relpath(raiz, self.public_folder)
                sub_relativa = "" if sub_relativa == "." else sub_relativa

                ruta_md = os.path.join(raiz, filename)
                meta, texto = self._procesar_md(ruta_md)
                
                # B. Procesar TOC y Anclajes (Slugify con acentos)
                # (Aquí mantenemos tu lógica de '#' y unicodedata que ya validamos)
                lineas = texto.split('\n')
                indice_dinamico = []
                dentro_de_codigo = False 

                for linea in lineas:
                    l_clean = linea.strip()
                    if l_clean.startswith('```'):
                        dentro_de_codigo = not dentro_de_codigo
                        continue 
                    if not dentro_de_codigo and l_clean.startswith('#'):
                        nivel = l_clean.count('#')
                        if nivel <= 6:
                            titulo = l_clean.replace('#', '').strip()
                            # Normalización para IDs
                            import unicodedata, re
                            anchor = titulo.lower()
                            anchor = unicodedata.normalize('NFKD', anchor).encode('ascii', 'ignore').decode('ascii')
                            anchor = re.sub(r'[^\w\s-]', '', anchor)
                            anchor = re.sub(r'[\s]+', '-', anchor).strip('-')
                            
                            indice_dinamico.append({'nivel': nivel, 'titulo': titulo, 'anchor': anchor})

                # C. Renderizado HTML del cuerpo
                cuerpo_html = markdown.markdown(texto, extensions=['extra', 'codehilite', 'toc'])
                # Tu reemplazo para el acordeón de código
                cuerpo_html = cuerpo_html.replace(
                    '<div class="codehilite">', 
                    '<details class="code-accordion"><summary>Ver Bloque de Código</summary><div class="codehilite">'
                ).replace('</pre></div>', '</pre></div></details>')

                # D. Gestión de Salida y Profundidad
                out_name = filename.replace(".md", ".html")
                # URL relativa para el índice (ej: laboral/mi_puesto.html)
                url_final = os.path.join(sub_relativa, out_name).replace("\\", "/")
                
                # Calculamos profundidad: si está en subcarpeta, base_path es ../../
                profundidad = len(sub_relativa.split(os.sep)) if sub_relativa else 0
                prefix = "../" * (profundidad + 1)

                # E. Acumular para los índices (usamos fecha_inicio si es laboral/formativa)
                fecha_item = meta.get("fecha_creacion", meta.get("fecha_inicio", "2026-01-01"))

                # ... dentro del bucle de archivos ...
                tipo_limpio = meta.get("tipo", "post").strip().lower() # Limpieza de seguridad
                
                self.coleccion_posts.append({
                    "url": url_final,
                    "titulo": meta.get("titulo", "Sin título"),
                    "subtitulo": meta.get("subtitulo", ""),
                    "fecha": fecha_item,
                    "tipo": tipo_limpio,
                    "tag": meta.get("tag", "")
                })

                # F. Guardar archivo físico
                ruta_dest_carpeta = os.path.join(self.output_folder, sub_relativa)
                os.makedirs(ruta_dest_carpeta, exist_ok=True)
                
                contexto = {
                    "contenido": cuerpo_html,
                    "base_path": prefix,
                    "toc": indice_dinamico,
                    **meta
                }

                try:
                    template = self.builder.env.get_template('post.html')
                    html_final = template.render(**contexto)
                    with open(os.path.join(ruta_dest_carpeta, out_name), "w", encoding="utf-8") as f:
                        f.write(html_final)
                    print(f"[!] ÉXITO Editorial: {url_final}")
                except Exception as e:
                    print(f"[X] Error en {filename}: {e}")

        # G. Generar índices al finalizar el bucle
        if self.coleccion_posts:
            self.generar_indices_multifase()

    def generar_indices_multifase(self):
        """Genera el índice general y los específicos de Trayectoria."""
    
        # --- FUNCIÓN INTERNA DE CONVERSIÓN ---
        def helper_fecha(item):
            fecha_str = item.get('fecha', '01/01/1900')
            try:
                # Convertimos el texto dd/mm/aaaa en un objeto fecha real
                return datetime.strptime(fecha_str, "%d/%m/%Y")
            except Exception:
                # Si algo falla, lo manda al final del listado
                return datetime(1900, 1, 1)

        # 1. ORDENACIÓN REAL (Usando el helper)
        # Ahora sí, 2026 irá arriba de 1988 aunque sea texto.
        self.coleccion_posts.sort(key=helper_fecha, reverse=True)

        # A. ÍNDICE GLOBAL
        self._escribir_archivo_indice(
            items=self.coleccion_posts, 
            nombre_archivo="list_posts.html", 
            titulo="Índice de Actividad"
        )

        # B. TRAYECTORIA LABORAL
        laborales = [p for p in self.coleccion_posts if p.get('tipo') == 'laboral']
        if laborales:
            self._escribir_archivo_indice(laborales, "trayectoria_laboral.html", "Trayectoria Profesional")

        # C. TRAYECTORIA FORMATIVA
        formativos = [p for p in self.coleccion_posts if p.get('tipo') == 'formativa']
        if formativos:
            self._escribir_archivo_indice(formativos, "trayectoria_formativa.html", "Trayectoria Formativa")

    def _escribir_archivo_indice(self, items, nombre_archivo, titulo):
        """Helper privado para renderizar la plantilla time.html con seguridad."""
        contexto = {
            "items": items,
            "titulo_pagina": titulo,
            "base_path": "../"  # Los índices viven en /posts/, necesitan un salto atrás
        }

        try:
            template = self.builder.env.get_template('time.html')
            html_final = template.render(**contexto)
            ruta_salida = os.path.join(self.output_folder, nombre_archivo)
            
            with open(ruta_salida, "w", encoding="utf-8") as f:
                f.write(html_final)
            print(f"[!] ÉXITO: Generado {nombre_archivo} con {len(items)} registros.")
        except Exception as e:
            print(f"[X] Error al generar el índice {nombre_archivo}: {e}")

class SipaWebBuilder:
    """
    ORQUESTADOR: Provisión de activos core, lectura de MD y renderizado.
    Acciones que realiza:
    - Audita, llama a provision() y verifiy_integrity()
    - Extrae, lee los .md y los convierte en meta_main y bloques_data
    - Inyecta todo en el template.render()
    """
    def __init__(self, usuario="Daniel"):
        self.raiz = os.path.dirname(os.path.abspath(__file__))
        self.static = os.path.join(self.raiz, "templates", "static")
        self.templates = os.path.join(self.raiz, "templates")
        self.data_public = os.path.join(self.raiz, "data", "public")   # Listos para publicar
        
        # Sincronización de activos (base.html y custom.css)
        self.asegurar_activos_core()
        
        self.env = Environment(loader=FileSystemLoader(self.templates))
        self.index_manager = SipaFileIndex("index", self.static)
        self.sobre_mi_manager = SipaFileSobreMi("sobre-mi", self.static)
        self.proyectos_manager = SipaFileProyectos("proyectos", self.static)
        self.contacto_manager = SipaFileContacto("contacto", self.static)
        self.ayuda_manager = SipaFileAyuda("ayuda", self.static)

    def asegurar_activos_core(self):
        """
        Sincroniza activos desde core/assets a sus destinos de producción.
        Detecta subcarpetas en el origen para evitar errores de 'File Not Found'.
        """
        # Mapeo: (Subruta_Origen, Nombre_Fichero, Carpeta_Destino)
        activos = [
            ("", "base.html", self.templates),
            ("", "post.html", self.templates),
            ("", "time.html", self.templates),
            ("", "custom.css", os.path.join(self.raiz, "css")),
            ("mkdocs/docs", "index.md", os.path.join(self.raiz, "docs")),
            ("mkdocs/docs", "referencia.md", os.path.join(self.raiz, "docs")),
            ("mkdocs", "mkdocs.yml", self.raiz), # El config suele ir en la raíz del proyecto
            ("img", "avatargithub.png", os.path.join(self.raiz, "img")),
            ("img", "sobre-mi-bg.png", os.path.join(self.raiz, "img")),
            ("img", "favicon.ico", os.path.join(self.raiz, "img")), # Nuevo: Favicon
            ("img", "danielminanamontero-logo.png", os.path.join(self.raiz, "img")), # Nuevo: Tu logo azul
            ("img", "proyectos-bg.png", os.path.join(self.raiz, "img")),
            ("img", "contacto-bg.png", os.path.join(self.raiz, "img")),
            ("img", "ayuda-bg.png", os.path.join(self.raiz, "img")),
            ("pdf", "2018_porfolio.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "certificado_profesionalidad.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "certificado_servef_00.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "certificado_servef_01.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "certificado_ciberseguridad_google.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-automatizar-tareas.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-conectar-y-proteger-redes.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-gestionar-los-riegos.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-fundamentos-ciberseguridad.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-herramientas-linux-sql.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-recursos-amenazas-vulnerabilidades.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-deteccion-respuesta.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-preparase-para-empleos.pdf", os.path.join(self.raiz, "pdf")),
            ("pdf", "ciber-google-busqueda-empleo-ia.pdf", os.path.join(self.raiz, "pdf"))
        ]
        
        for subfolder, nombre, destino_folder in activos:
            # Construimos la ruta de origen entrando en la subcarpeta si existe
            origen = os.path.join(self.raiz, "core", "assets", subfolder, nombre)
            destino = os.path.join(destino_folder, nombre)
            
            if os.path.exists(origen):
                os.makedirs(destino_folder, exist_ok=True)
                shutil.copy2(origen, destino)
                # print(f"[*] Sincronizado: {nombre} -> {destino_folder}")
            else:
                print(f"[X] ERROR: No se encuentra el origen real: {origen}")

    def leer_markdown_nativo(self, ruta_relativa):
        """Lector de Markdown con separación de Frontmatter (Tu método funcional)."""
        ruta_completa = os.path.join(self.static, ruta_relativa)
        try:
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                contenido = f.read()
            partes = contenido.split('---', 2)
            if len(partes) >= 3:
                meta_raw = partes[1].strip()
                metadatos = {l.split(":",1)[0].strip(): l.split(":",1)[1].strip().strip('"') 
                            for l in meta_raw.split('\n') if ":" in l}
                return metadatos, partes[2].strip()
            return {}, contenido
        except: return {}, ""

    def ejecutar_mkdocs(self):
        """
        Lanza la construcción de la documentación técnica mediante MkDocs.
        Asegura que el directorio de salida exista y el comando se ejecute.
        """
        import subprocess
        print(f"\n[*] Iniciando construcción de Documentación Técnica (MkDocs)...")
        
        # 1. Definimos la ruta de salida (dentro de tu raíz para que GitHub Pages lo vea)
        # Puedes llamarlo 'docs_tecnicos' para no confundir con tu carpeta de origen 'docs'
        output_docs = os.path.join(self.raiz, "docs")
        
        try:
            # Ejecutamos: mkdocs build --clean -d [ruta_destino]
            # --clean asegura que no queden restos de builds anteriores
            resultado = subprocess.run(
                ["mkdocs", "build", "--clean", "-d", output_docs],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"[!] MkDocs: Documentación actualizada en {output_docs}")
            
        except subprocess.CalledProcessError as e:
            print(f"[X] ERROR al ejecutar MkDocs: {e.stderr}")
        except FileNotFoundError:
            print(f"[X] ERROR: MkDocs no está instalado o no se encuentra en el PATH.")

    def build(self):
        """Ciclo de construcción v1.5: Generación Multitarea (Primary Pages)."""
        print(f"--- SIPAweb Builder v1.5 | Despliegue Global ---")

        # 1. Definición del Mapa del Sitio (Páginas Primarias)
        misiones = [
            {"mgr": self.index_manager,    "out": "index.html",    "md": "index.md"},
            {"mgr": self.sobre_mi_manager, "out": "sobre-mi.html", "md": "sobre-mi.md"},
            {"mgr": self.proyectos_manager,"out": "proyectos.html","md": "proyectos.md"},
            {"mgr": self.contacto_manager, "out": "contacto.html", "md": "contacto.md"},
            {"mgr": self.ayuda_manager,    "out": "ayuda.html",    "md": "ayuda.md"}
        ]

        for mision in misiones:
            mgr = mision["mgr"]
            print(f"\n[*] Construyendo: {mision['out']}")

            # A. Provisión y Auditoría (Bolardo SHA-256)
            mgr.provision()
            mgr.verify_integrity()
            
            # B. Recolección Dinámica de Bloques (de 0 a N bloques)
            bloques_data = []
            if os.path.exists(mgr.folder_path):
                for f in sorted(os.listdir(mgr.folder_path)):
                    if f.endswith(".md"):
                        meta_b, texto_b = self.leer_markdown_nativo(os.path.join(mgr.page_name, f))
                        if meta_b:
                            bloques_data.append({**meta_b, "contenido": markdown.markdown(texto_b)})

            # C. Renderizado con Identidad Variable
            meta_main, cuerpo_md = self.leer_markdown_nativo(mision["md"])
            html_main = markdown.markdown(cuerpo_md, extensions=['extra', 'admonition'])

            try:
                template = self.env.get_template('base.html')
                html_final = template.render(
                    **meta_main, 
                    contenido=html_main, 
                    bloques=bloques_data
                )
                
                with open(os.path.join(self.raiz, mision["out"]), "w", encoding="utf-8") as f:
                    f.write(html_final)
                
                mgr.update_manifest()
                print(f"[!] ÉXITO: {mision['out']} publicado.")

            except Exception as e:
                print(f"[X] ERROR en {mision['out']}: {e}")

        # NUEVO: Encapsulación total
        post_mgr = SipaFilePost("posts", self.static, self)
        post_mgr.ejecutar_ciclo_editorial()

        # MISIÓN KERNEL: Documentación Técnica (MkDocs)
        # Se ejecuta al final para asegurar que el código (sipaweb.py) 
        # esté listo para ser leído por mkdocstrings.
        self.disparar_mision_mkdocs()

        print(f"\n--- Construcción Global v1.5 Finalizada ---")

    def disparar_mision_mkdocs(self):
                """Disparador controlado del motor MkDocs."""
                print(f"\n[*] Iniciando Misión Kernel: MkDocs")
                
                # Verificamos que el archivo de configuración exista antes de disparar
                config_path = os.path.join(self.raiz, "mkdocs.yml")
                if not os.path.exists(config_path):
                    print(f"[X] ABORTADO: No se encuentra mkdocs.yml en la raíz.")
                    return

                try:
                    # Ejecución silenciosa capturando errores
                    subprocess.run(
                        ["mkdocs", "build", "--clean"], 
                        check=True, 
                        capture_output=True, 
                        text=True
                    )
                    print(f"[!] KERNEL: Documentación técnica sincronizada.")
                except Exception as e:
                    print(f"[X] ERROR en Misión MkDocs: {e}")

if __name__ == "__main__":
    SipaWebBuilder().build()