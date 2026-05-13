import os
import requests
import frontmatter
import pandas as pd
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# --- CONFIGURACIÓN DE RUTAS ---
FICHERO_CONFIG = "/home/toviddfrei/SIPA/data/archive/template_propietario.md"
ARCHIVO_HISTORICO = "/home/toviddfrei/SIPA/data/archive/historico_rastreo.csv"

# ==========================================
# OBJETIVO 1: CAPTURA DE DATOS DESDE .MD
# ==========================================
def cargar_variables_trabajo():
    if not os.path.exists(FICHERO_CONFIG):
        print(f"❌ Error: No se encuentra {FICHERO_CONFIG}")
        return None

    with open(FICHERO_CONFIG, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    config = {
        'nombre': post.get('nombre', ''),
        'apellido_1': post.get('apellido_1', ''),
        'apellido_2': post.get('apellido_2', ''),
        'frase': f"{post.get('nombre')} {post.get('apellido_1')} {post.get('apellido_2')}"
    }
    return config

# ==========================================
# OBJETIVO 2: MOTOR BOE (OFICIAL)
# ==========================================
def motor_boe(nombre, a1, a2):
    print("🔎 Consultando BOE...")
    frase_query = f"{nombre} {a1} {a2}"
    resultados = []
    
    url_base = "https://www.boe.es/buscar/boe.php"
    params = {
        'campo[0]': 'TIT', 'dato[0]': frase_query, 'operador[0]': 'and',
        'campo[1]': 'TEXT', 'dato[1]': frase_query, 'operador[1]': 'or',
        'tipo_busqueda': 'todo'
    }

    try:
        r = requests.get(url_base, params=params, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.find_all('li', class_='resultado')
            
            for item in items:
                link = item.find('a')
                if link:
                    # Extraer fecha mediante regex DD/MM/AAAA
                    fecha_match = re.search(r'\d{2}/\d{2}/\d{4}', item.get_text())
                    fecha_pub = fecha_match.group() if fecha_match else "---"
                    
                    resultados.append({
                        'Fuente': 'BOE',
                        'Posicion': 0, # Prioridad oficial
                        'Titulo': link.get_text().strip(),
                        'Enlace': "https://www.boe.es" + link.get('href'),
                        'Fecha_Info': fecha_pub
                    })
    except Exception as e:
        print(f"⚠️ Error BOE: {e}")
    return resultados

# ==========================================
# OBJETIVO 2.1: MOTOR DUCKDUCKGO (COMERCIAL)
# ==========================================
def motor_duckduckgo(frase):
    print("🔎 Consultando DuckDuckGo...")
    resultados = []
    try:
        with DDGS() as ddgs:
            # Buscamos la frase exacta entre comillas
            busqueda = ddgs.text(f'"{frase}"', region='es-es', max_results=10)
            for i, r in enumerate(busqueda):
                resultados.append({
                    'Fuente': 'DuckDuckGo',
                    'Posicion': i + 1,
                    'Titulo': r['title'],
                    'Enlace': r['href'],
                    'Fecha_Info': datetime.now().strftime("%d/%m/%Y")
                })
    except Exception as e:
        print(f"⚠️ Error DuckDuckGo: {e}")
    return resultados

# ==========================================
# GESTIÓN DE ALMACENAMIENTO Y TIEMPO
# ==========================================
def guardar_y_consolidar(nuevos_datos):
    if not nuevos_datos:
        print("Empty: No se han encontrado resultados.")
        return

    df_nuevo = pd.DataFrame(nuevos_datos)
    df_nuevo['Fecha_Ejecucion'] = datetime.now().strftime("%Y-%m-%d")

    # Si ya existe el archivo, lo cargamos para comparar/añadir
    if os.path.exists(ARCHIVO_HISTORICO):
        df_nuevo.to_csv(ARCHIVO_HISTORICO, mode='a', index=False, header=False, encoding='utf-8')
    else:
        df_nuevo.to_csv(ARCHIVO_HISTORICO, index=False, encoding='utf-8')
    
    print(f"✅ Datos guardados en {ARCHIVO_HISTORICO}")

def verificar_7_dias():
    if not os.path.exists(ARCHIVO_HISTORICO):
        return True # Primera vez
    
    df = pd.read_csv(ARCHIVO_HISTORICO)
    df['Fecha_Ejecucion'] = pd.to_datetime(df['Fecha_Ejecucion'])
    ultima_fecha = df['Fecha_Ejecucion'].max()
    
    dias_pasados = (datetime.now() - ultima_fecha).days
    if dias_pasados >= 7:
        return True
    else:
        print(f"⏳ Faltan {7 - dias_pasados} días para la siguiente actualización.")
        return False

# ==========================================
# FLUJO PRINCIPAL DEL LAUNCHER
# ==========================================
def ejecutar_launcher():
    print("--- INICIANDO LAUNCHER DE RASTREO ---")
    
    # 1. Cargar datos del .md
    config = cargar_variables_trabajo()
    if not config: return

    # 2. Verificar si toca actualizar (7 días)
    if verificar_7_dias():
        hallazgos = []
        
        # Ejecutar motores
        hallazgos.extend(motor_boe(config['nombre'], config['apellido_1'], config['apellido_2']))
        hallazgos.extend(motor_duckduckgo(config['frase']))
        
        # 3. Guardar resultados
        guardar_y_consolidar(hallazgos)
    
    print("--- PROCESO FINALIZADO ---")

if __name__ == "__main__":
    ejecutar_launcher()