# ==========================================================
# CITADEL CORE - Sistema de Integridad y Gestión
# Archivo: audit_setup.py
# Versión: 0.2.5 (Referencia unificada)
# Módulo: Core
# Certificación: FHS-Compliant | Norma: ISO/IEC 27001 (Simulada)
# Autor: Daniel Miñana & Gemini
# ---------------------------------------------------------
# Descripción: Audita todos los ficheros, su firma y versión
#              para asegurar la integridad del sistema.
# ==========================================================

# Importaciones necesarias
import os

# Configuración de la auditoría
# Le pasamos a las constantes que utilizaremos para la auditoría los valores
# Definimos los requerimientos y definimos también que ficheros y de que directorios
REQUIRED_SIGNATURE = "CITADEL CORE"
REQUIRED_AUTHOR = "Daniel Miñana"
REQUIRED_VERSION = "0.2.5"
TARGET_EXTENSIONS = ('.py', '.sh', '.html', '.css', '.js')
IGNORE_DIRS = ['venv', '.git', '__pycache__']

def audit_files():
    """
    Audita los ficheros del proyecto para verificar la presencia de
    la firma, autor y versión requerida en la cabecera de cada archivo.
    Utilizamos el módulo os para recorrer los directorios y archivos.
    """
    print(f"{'='*50}")
    print(f"🔍 INICIANDO AUDITORÍA DE FIRMAS - CITADEL v.{REQUIRED_VERSION}")
    print(f"{'='*50}\n")
    
    files_audited = 0
    failures = 0

    for root, dirs, files in os.walk('.'):
        # Ignorar directorios de sistema/entorno
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file.endswith(TARGET_EXTENSIONS):
                files_audited += 1
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Leemos solo la cabecera
                    
                    checks = {
                        "Firma": REQUIRED_SIGNATURE in content,
                        "Autor": REQUIRED_AUTHOR in content,
                        "Versión": REQUIRED_VERSION in content
                    }
                    
                    if all(checks.values()):
                        print(f"[✅] {file_path:<40} | CERTIFICADO")
                    else:
                        failures += 1
                        missing = [k for k, v in checks.items() if not v]
                        print(f"[❌] {file_path:<40} | ERROR: Faltan {missing}")

    print(f"\n{'='*50}")
    print(f"RESUMEN DE AUDITORÍA:")
    print(f"Archivos revisados: {files_audited}")
    print(f"Archivos certificados: {files_audited - failures}")
    print(f"Archivos pendientes: {failures}")
    print(f"{'='*50}")

if __name__ == "__main__":
    audit_files()