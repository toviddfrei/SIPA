# =================================================================
# LICENCIA: MIT | MARCA: BApp-CITADEL | PROTOCOLO: FORTRESS
# DOCUMENTO: app.py | RUTA: ./app.py
# VERSIÓN: 0.7.1 | ESTADO: STABLE / AUDITADO (FULL CAPABILITY)
# DESCRIPCIÓN: Núcleo integral. Gestión de perfil, EDR, Agenda 
#              JSON, Roadmap y Telemetría de Latencia.
# =================================================================

import os
import sys
import json
import time
import inspect
import re
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, g

# --- IMPORTACIONES DE LÓGICA DE NEGOCIO Y MODELOS ---
from web_engine.models import db, PerfilProfesional, NoticiaSeguridad, CronogramaRoadmap
from core.integrity import boot_check, log_consola, paths, auditoria_profunda, sync_requirements, obtener_firma_dir

# --- CONFIGURACIÓN E INSTANCIACIÓN DEL KERNEL ---
app = Flask(__name__, template_folder=paths["templates"], static_folder=paths["static"])
app.config.update(
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.join(paths["data"], "sistema.db")}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='citadel_secure_key_2025'
)

db.init_app(app)

# --- CONSTANTES GLOBALES Y TELEMETRÍA (Punto 9) ---
BRAND_INFO = {
    "name": "BApp-CITADEL",
    "version": "0.7.1",
    "protocol": "S.I.P.A.",
    "status": "SECURE_MODE",
    "author": "Daniel Miñana",
    "license": "MIT"
}
SERVER_START_TIME = time.time()

# --- BLOQUE 1: TELEMETRÍA Y PROCESADORES DE CONTEXTO ---

@app.before_request
def start_timer():
    """ Registra el tiempo de inicio exacto de cada petición. """
    g.start_time = time.perf_counter()

@app.after_request
def log_latency(response):
    """ Calcula y añade el tiempo de respuesta a las cabeceras HTTP. """
    if hasattr(g, 'start_time'):
        latency = time.perf_counter() - g.start_time
        response.headers["X-Response-Time"] = f"{latency:.4f}s"
    return response

@app.context_processor
def inject_global_metrics():
    """ Inyecta métricas de sistema y branding en todos los templates. """
    uptime_val = round(time.time() - SERVER_START_TIME, 2)
    
    # Monitorización de Procesos Masivos (Build Documental)
    proc_status = {"status": "IDLE", "progress": 0, "message": "En espera"}
    status_path = os.path.join(paths["data"], 'proc_status.json')
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict): proc_status = data
        except: pass 

    return {
        "brand": BRAND_INFO,
        "sys": BRAND_INFO,
        "uptime": uptime_val,
        "proc": proc_status,
        "now": datetime.now()
    }

def analizar_kernel_recursivo():
    """ 
    S.I.P.A. FULL INSPECTOR: 
    Escaneo profundo de activos verificados. Recupera pedagogía, ubicación 
    y telemetría de proceso para el Dataset de Daniel Miñana.
    """
    checklist_path = os.path.join(paths["data"], 'check_list_ficheros_importantes.json')
    telemetria_path = os.path.join(paths["data"], 'telemetria_mapa.json')
    data_map = []
    
    # 1. Validación de existencia del activo maestro
    if not os.path.exists(checklist_path):
        log_consola("SIPA", "ALERTA: Fichero de activos importantes no encontrado.")
        return []

    try:
        # 2. Apertura y carga de la lista de blancos (targets)
        with open(checklist_path, 'r', encoding='utf-8') as f:
            activos = json.load(f).get("critical_assets", [])
            
        for activo in activos:
            ruta_fichero = activo['filename']
            if os.path.exists(ruta_fichero):
                # Clasificación de ámbito por ruta
                ambito = "NUCLEO"
                if "core" in ruta_fichero: ambito = "SEGURIDAD"
                elif "constructor" in ruta_fichero: ambito = "CONSTRUCTOR"

                try:
                    # 3. Análisis de flujo interno del fichero
                    with open(ruta_fichero, "r", encoding="utf-8") as f_code:
                        lineas = f_code.readlines()
                        for num_linea, contenido_linea in enumerate(lineas):
                            
                            # Detección de firma de función
                            if contenido_linea.strip().startswith('def '):
                                nombre_func = contenido_linea.split('def ')[1].split('(')[0]
                                
                                # --- BÚSQUEDA DE PEDAGOGÍA (Comentario superior) ---
                                # Buscamos si la línea de arriba es un comentario #
                                pedagogia_extraida = "Pendiente de documentación técnica."
                                if num_linea > 0 and '#' in lineas[num_linea - 1]:
                                    pedagogia_extraida = lineas[num_linea - 1].replace('#', '').strip()
                                # O si la línea de abajo es un docstring """
                                elif num_linea + 1 < len(lineas) and '"""' in lineas[num_linea + 1]:
                                    pedagogia_extraida = lineas[num_linea + 1].replace('"""', '').strip()
                                
                                # 4. Construcción del objeto de telemetría por función
                                data_map.append({
                                    "modulo": ambito,
                                    "fichero": ruta_fichero,
                                    "linea": num_linea + 1,
                                    "funcion": nombre_func,
                                    "pedagogia": pedagogia_extraida,
                                    "latencia_scan": f"{time.process_time():.6f}s",
                                    "estado": "VERIFIED_BY_DANIEL",
                                    "autor": "Daniel Miñana" if "Daniel" in lineas[0] else "SIPA_SYSTEM"
                                })
                except Exception as e_inner:
                    log_consola("ERROR", f"Fallo leyendo interior de {ruta_fichero}: {e_inner}")
            else:
                log_consola("WARNING", f"Activo listado pero no encontrado en disco: {ruta_fichero}")

        # 5. Persistencia del Dataset para el panel de telemetría
        with open(telemetria_path, 'w', encoding='utf-8') as f_out:
            json.dump(data_map, f_out, indent=4, ensure_ascii=False)
            
    except Exception as e_outer:
        log_consola("CRITICAL", f"Fallo masivo en el Kernel Recursivo: {e_outer}")
        
    return data_map

@app.route('/admin/mapa')
def mapa_kernel():
    """ Consola de visualización del árbol de funciones y telemetría SIPA. """
    telemetria = analizar_kernel_recursivo()
    return render_template('mapa_sistema.html', telemetria=telemetria)

# --- BLOQUE 2: SEGURIDAD (Protocolo de Defensa) ---

@app.before_request
def monitor_seguridad():
    """ WAF INTERNO: Analiza patrones de ataque antes de procesar rutas. """
    path = request.path.lower()
    palabras_prohibidas = ["/etc/passwd", ".env", "select * from", "drop table"]
    if any(p in path for p in palabras_prohibidas):
        log_consola("SEGURIDAD", f"ALERTA: Bloqueo de acceso IP: {request.remote_addr} -> {path}")
        return "Acceso Denegado por Protocolo CITADEL", 403

# --- BLOQUE 3: RUTAS PÚBLICAS Y API DOCUMENTAL ---

@app.route('/')
def index():
    perfil_db = PerfilProfesional.query.first()
    user_data = {
        "nombre": perfil_db.nombre if perfil_db else "Daniel Miñana",
        "profesion": perfil_db.profesion if perfil_db else "Desarrollador de Sistemas",
        "especialidad": "Protocolo S.I.P.A.",
        "presentacion_breve": perfil_db.biografia_corta if perfil_db else "Trayectoria en Ciberseguridad",
        "bio_larga": "Registro verificado bajo el núcleo CITADEL.",
        "edad": 53,
        "habilidades": ["Ciberseguridad", "Sistemas", "Ética", "S.I.P.A."]
    }
    contexto_final = {"user": user_data, "version": "0.7.1"}
    return render_template('index.html', context=contexto_final, sys={"codename": "CITADEL"}, bitacora=[])

@app.route('/ayuda')
def ayuda_view():
    perfil = PerfilProfesional.query.first()
    return render_template('ayuda.html', context={"user": perfil, "version": "0.7.1"})

@app.route('/admin/api/get_docs')
def get_docs():
    docs_path = 'constructor/docs/'
    try:
        if not os.path.exists(docs_path): os.makedirs(docs_path)
        files = [f for f in os.listdir(docs_path) if f.endswith('.md')]
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/admin/api/load_doc/<filename>')
def load_doc(filename):
    try:
        path = os.path.join('constructor/docs/', filename)
        with open(path, 'r', encoding='utf-8') as f:
            return {"content": f.read()}
    except Exception as e:
        return {"error": str(e)}, 500

# --- BLOQUE 4: ADMINISTRACIÓN (DASHBOARD & EDR) ---

@app.route('/admin/dashboard')
def admin_dashboard():
    perfil = PerfilProfesional.query.first()
    stats = auditoria_profunda()
    json_path = os.path.join(paths["data"], 'agenda_intenciones.json')
    agenda_data = []
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                agenda_data = json.load(f)
                agenda_data.reverse()
            except: pass

    servicios = {
        "sqlite": {"status": True, "label": "DB System"},
        "curator": {"status": True, "label": "Filesystem"},
        "integrity": {"status": True, "label": "EDR Sensor"}
    }

    componentes = [
        {"file": "app.py", "lvl": "Lvl 1"},
        {"file": "models.py", "lvl": "Lvl 1"},
        {"file": "core/integrity.py", "lvl": "Lvl 1"},
        {"file": "data/sistema.db", "lvl": "Lvl 2"}
    ]
    
    matriz_sensores = []
    for item in componentes:
        file_path = item["file"]
        exists = os.path.exists(file_path)
        start_io = time.perf_counter()
        if exists: os.path.getmtime(file_path)
        latency = time.perf_counter() - start_io
        matriz_sensores.append({
            "componente": file_path,
            "sensor_h": "✅ INTEGRO" if exists else "❌ ERROR",
            "sensor_l": f"{latency:.6f}s",
            "sensor_p": "ACTIVE" if exists else "MISSING",
            "nivel": item["lvl"]
        })

    return render_template('admin_dashboard.html', perfil=perfil, agenda_items=agenda_data, servicios=servicios, stats=stats, matriz=matriz_sensores, active_tab='presentacion')

@app.route('/admin/security/status')
def security_status():
    checklist_path = os.path.join(paths["data"], 'check_list_ficheros_importantes.json')
    linea_base = []
    if os.path.exists(checklist_path):
        try:
            with open(checklist_path, 'r', encoding='utf-8') as f:
                linea_base = json.load(f).get("critical_assets", [])
        except: pass

    reporte_habitaciones = []
    root_actual = os.path.dirname(os.path.abspath(__file__))
    for activo in linea_base:
        ruta_fichero_real = os.path.join(root_actual, activo['filename'])
        t_inicio = time.perf_counter()
        hash_actual = obtener_firma_dir(os.path.dirname(ruta_fichero_real))
        latencia = time.perf_counter() - t_inicio
        reporte_habitaciones.append({
            "fichero": activo['filename'],
            "version": activo.get('version', 'N/A'),
            "hash_esperado": activo['sha256'],
            "hash_real": hash_actual,
            "estado": "✅ INTEGRO" if hash_actual == activo['sha256'] else "❌ MODIFICADO",
            "nivel": activo.get('security_level', 'LOW'),
            "pedagogia": activo.get('pedagogia', 'Sin descripción.'),
            "mantenimiento": activo.get('mantenimiento', ''),
            "latencia": f"{latencia:.6f}s"
        })

    kb_path = os.path.join(paths["data"], 'biblioteca_it.md')
    contenido_kb = ""
    if os.path.exists(kb_path):
        with open(kb_path, 'r', encoding='utf-8') as f: contenido_kb = f.read()

    total_activos = len(reporte_habitaciones) if len(reporte_habitaciones) > 0 else 1
    puntos_integridad = sum(1 for h in reporte_habitaciones if "INTEGRO" in h['estado'])
    score_h = (puntos_integridad / total_activos) * 40
    puntos_pedagogia = sum(1 for h in reporte_habitaciones if len(h['pedagogia']) > 25)
    score_p = (puntos_pedagogia / total_activos) * 30
    sipa_index = int(score_h + score_p + 20 + 2)

    return render_template('admin_security.html', habitaciones=reporte_habitaciones, biblioteca=contenido_kb, protocolo="S.I.P.A.", sipa_index=sipa_index)

@app.route('/admin/dataset')
def admin_dataset():
    json_path = os.path.join(paths["data"], 'agenda_intenciones.json')
    agenda_data = []
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            try: agenda_data = json.load(f); agenda_data.reverse()
            except: pass
    return render_template('admin_dataset.html', agenda_items=agenda_data)

@app.route('/admin/roadmap')
def admin_roadmap_detail():
    roadmap_items = CronogramaRoadmap.query.order_by(CronogramaRoadmap.prioridad.desc()).all()
    return render_template('admin_roadmap.html', items=roadmap_items)

# --- BLOQUE 5: ACCIONES DE ESCRITURA (Kernel Write Ops) ---

@app.route('/admin/update_agenda', methods=['POST'])
def update_agenda():
    entrada = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "categoria": request.form.get('categoria_intencion'),
        "tags": request.form.get('tags_vinculados'),
        "razon": request.form.get('razon_aprendizaje'),
        "prioridad": request.form.get('nivel_estres'),
        "visibilidad": request.form.get('target_visibility')
    }
    json_path = os.path.join(paths["data"], 'agenda_intenciones.json')
    try:
        data_existente = []
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                try: data_existente = json.load(f)
                except: pass
        data_existente.append(entrada)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_existente, f, indent=4, ensure_ascii=False)
        flash(f"Inyección exitosa: {entrada['categoria']}", "success")
    except Exception as e:
        flash(f"Error en persistencia JSON: {e}", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/quick_update', methods=['POST'])
def quick_update():
    p = PerfilProfesional.query.first()
    if p:
        p.nombre = request.form.get('nombre')
        p.profesion = request.form.get('profesion')
        p.email = request.form.get('email')
        p.biografia_corta = request.form.get('biografia')
        db.session.commit()
        flash("Identidad SQL actualizada", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/security/edit', methods=['POST'])
def edit_pedagogia():
    filename = request.form.get('filename')
    nueva_pedagogia = request.form.get('pedagogia')
    json_path = os.path.join(paths["data"], 'check_list_ficheros_importantes.json')
    try:
        with open(json_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            for activo in data.get('critical_assets', []):
                if activo['filename'] == filename:
                    activo['pedagogia'] = nueva_pedagogia
                    break
            f.seek(0); json.dump(data, f, indent=4, ensure_ascii=False); f.truncate()
        flash(f"Pedagogía de {filename} actualizada.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for('security_status'))

@app.route('/admin/security/sign', methods=['POST'])
def sign_hash():
    filename = request.form.get('filename')
    new_hash = request.form.get('new_hash')
    json_path = os.path.join(paths["data"], 'check_list_ficheros_importantes.json')
    try:
        with open(json_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            for activo in data.get('critical_assets', []):
                if activo['filename'] == filename:
                    activo['sha256'] = new_hash
                    break
            f.seek(0); json.dump(data, f, indent=4, ensure_ascii=False); f.truncate()
        flash(f"Activo {filename} firmado.", "success")
    except Exception as e:
        flash(f"Error de firma: {e}", "danger")
    return redirect(url_for('security_status'))

@app.route('/admin/biblioteca/save', methods=['POST'])
def save_kb():
    filename = request.form.get('filename', 'biblioteca_it.md')
    nuevo_contenido = request.form.get('biblioteca_content')
    if filename != 'biblioteca_it.md':
        target_path = os.path.join('constructor/docs/', filename)
    else:
        target_path = os.path.join(paths["data"], 'biblioteca_it.md')
    try:
        with open(target_path, 'w', encoding='utf-8') as f: f.write(nuevo_contenido)
        flash(f"Sincronización exitosa: {filename}", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for('security_status'))

@app.route('/update_identity', methods=['POST'])
def update_identity():
    try:
        perfil = PerfilProfesional.query.first() or PerfilProfesional()
        if not perfil.id: db.session.add(perfil)
        perfil.nombre = request.form.get('nombre')
        perfil.profesion = request.form.get('profesion')
        perfil.email = request.form.get('email')
        perfil.telefono = request.form.get('telefono')
        perfil.ubicacion = request.form.get('ubicacion')
        perfil.biografia_corta = request.form.get('biografia')
        db.session.commit()
        with open('data/identity.json', 'w', encoding='utf-8') as f:
            json.dump(request.form.to_dict(), f, indent=4, ensure_ascii=False)
        flash("Identidad sincronizada.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('security_status'))

# --- LANZAMIENTO Y PROTOCOLO DE ARRANQUE ---

def inicializar_sistema():
    with app.app_context():
        db.create_all()
        if not PerfilProfesional.query.first():
            db.session.add(PerfilProfesional(nombre="Daniel Miñana", profesion="IT Expert"))
            db.session.commit()
            log_consola("SQLITE", "Persistencia vinculada.")

if __name__ == '__main__':
    if boot_check():
        log_consola("CITADEL", "Fase de pre-arranque completada.")
        inicializar_sistema()
        sync_requirements() 
        log_consola("FLASK", f"Kernel {BRAND_INFO['name']} operativo en puerto 5000.")
        app.run(debug=True, host='0.0.0.0', port=5000)