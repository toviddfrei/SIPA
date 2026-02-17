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
                "nombre_sitio: SIPAweb\n"
                "rol: Trayectoria Profesional\n"
                "subtitulo: Más de 20 años de evolución IT\n"
                "hero_bg: img/sobre-mi-bg.png\n" # Ruta preparada para tu nueva imagen
                "estado: Protegido\n"
                "tag: Biografía\n"
                "---\n"
                "# Mi Historia\n\n"
                "Este es el espacio para tu presentación bibliográfica propia."
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
                "nombre_sitio: SIPAweb\n"
                "rol: Trayectoria Profesional\n"
                "subtitulo: Más de 20 años de evolución IT\n"
                "hero_bg: img/proyectos-bg.png\n" # Ruta preparada para tu nueva imagen
                "estado: Protegido\n"
                "tag: Proyectos\n"
                "---\n"
                "# Mis proyectos\n\n"
                "Este es el espacio para tu presentación proyectos."
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
                "hero_bg: img/Contacto-bg.png\n" # Ruta preparada para tu nueva imagen
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
            ("", "custom.css", os.path.join(self.raiz, "css")),
            ("img", "avatargithub.png", os.path.join(self.raiz, "img")),
            ("img", "sobre-mi-bg.png", os.path.join(self.raiz, "img")),
            ("img", "favicon.ico", os.path.join(self.raiz, "img")), # Nuevo: Favicon
            ("img", "danielminanamontero-logo.png", os.path.join(self.raiz, "img")), # Nuevo: Tu logo azul
            ("pdf", "2018_porfolio.pdf", os.path.join(self.raiz, "pdf"))
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

        print(f"\n--- Construcción Global v1.5 Finalizada ---")

if __name__ == "__main__":
    SipaWebBuilder().build()