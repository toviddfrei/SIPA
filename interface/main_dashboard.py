# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: main_dashboard.py
# Módulo: SIPAbap / SIPAdel (Interfaz de Control)
# Versión: 0.2.5 | Fecha: 06/01/2026
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
from datetime import datetime

# Anclaje de rutas del sistema
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import APP_TITLE, BG_COLOR_PRIMARY, SIPA_LEVEL_1, SIPA_LEVEL_2
from core.persistence_old import PersistenceManager
# NUEVA IMPORTACIÓN PARA EL CRONOGRAMA VITAL
from components.sipa_timeline import SipaTimeline

class MainDashboard:
    def __init__(self, logs_inicio=None):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.knowledge_dir = os.path.join(self.root_dir, "data", "knowledge")
        
        self.window = tk.Tk()
        self.window.title(f"{APP_TITLE} - Panel de Control v0.2.5")
        self.window.geometry("1150x850")
        self.window.configure(bg="#1e1e1e")
        
        self.db = PersistenceManager()
        if not self.db.connect():
            messagebox.showerror("ERROR CRÍTICO", "No se pudo inicializar sistema.db.")
        self.logs_recibidos = logs_inicio if logs_inicio else []

        self._build_header()
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self._init_tab_telemetria()
        self._init_tab_auditoria_db()
        self._init_tab_sipadoc()
        self._init_tab_roadmap()
        # INICIALIZACIÓN DE LA NUEVA PESTAÑA ESPECTACULAR
        self._init_tab_vital()

    def _build_header(self):
        header = tk.Frame(self.window, bg=BG_COLOR_PRIMARY, height=60)
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(header, text="SIPA ENGINE: SISTEMA ESTRATÉGICO DE PERSISTENCIA", 
                 fg="white", bg=BG_COLOR_PRIMARY, font=("Consolas", 14, "bold")).pack(pady=15)

    def _init_tab_vital(self):
        """Inicializa la pestaña del Cronograma Vital de Daniel Miñana."""
        self.tab_vital = SipaTimeline(self.notebook, self.db)
        self.notebook.add(self.tab_vital, text=" CRONOGRAMA VITAL ")

    # --- MÉTODOS DE EDICIÓN (SIN CAMBIOS PARA MANTENER ESTABILIDAD) ---
    def abrir_editor(self, event=None, source="sipadoc"):
        try:
            if source == "roadmap":
                selected = self.tabla_road.selection()
                if not selected: return
                val = self.tabla_road.item(selected)['values']
                filename = val[5] 
                db_id = val[0]
                if not filename or filename == "None":
                    safe_task = "".join([c for c in str(val[4]) if c.isalnum() or c==' ']).replace(" ", "_")
                    filename = f"{val[1]}_{safe_task}.md"
            else:
                selected = self.tabla_docs.selection()
                if not selected: return
                filename = self.tabla_docs.item(selected)['values'][0]
                db_id = 0

            fpath = os.path.join(self.knowledge_dir, filename)
            if not os.path.exists(fpath):
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(f"# DOCUMENTO: {filename}\nGenerado el: {datetime.now()}\n" + "="*30 + "\n")
            self._lanzar_ventana_editor(fpath, filename, db_id)
        except Exception as e:
            messagebox.showerror("Error de Edición", f"No se pudo abrir el artefacto: {e}")

    def _lanzar_ventana_editor(self, path, name, db_id):
        win = tk.Toplevel(self.window)
        win.title(f"Editor SIPA: {name}")
        win.geometry("900x700")
        txt = tk.Text(win, font=("Consolas", 11), undo=True, padx=15, pady=15)
        txt.pack(fill=tk.BOTH, expand=True)
        with open(path, 'r', encoding='utf-8') as f:
            txt.insert(tk.END, f.read())
        tk.Button(win, text="GUARDAR Y SINCRONIZAR", bg="#28a745", fg="white", font=("Arial", 10, "bold"),
                  command=lambda: self._save_dual(path, txt.get(1.0, tk.END), db_id)).pack(fill=tk.X)

    def _save_dual(self, path, content, db_id):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            messagebox.showinfo("SIPA", "Artefacto sincronizado correctamente.")
            self.listar_docs()
            self.cargar_roadmap_db()
            self.tab_vital.refresh_timeline() # Refrescar también la cronología
        except Exception as e:
            messagebox.showerror("Error al Guardar", str(e))

    def _init_tab_sipadoc(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" SIPAdoc ")
        container = tk.Frame(tab, padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)
        self.tabla_docs = ttk.Treeview(container, columns=("archivo"), show="headings", height=12)
        self.tabla_docs.heading("archivo", text="Repositorio de Conocimiento (.md)")
        self.tabla_docs.pack(fill=tk.BOTH, expand=True)
        self.tabla_docs.bind("<Double-1>", lambda e: self.abrir_editor(source="sipadoc"))
        btns = tk.Frame(container); btns.pack(pady=10)
        tk.Button(btns, text="EDITAR", command=lambda: self.abrir_editor(source="sipadoc"), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="REFRESCAR", command=self.listar_docs, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="GUI EXTERNA", command=self.lanzar_sipadoc_gui, bg="#bbdefb").pack(side=tk.LEFT, padx=5)
        self.listar_docs()

    def _init_tab_roadmap(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" Roadmap & Estrategia ")
        filter_frame = tk.Frame(tab, pady=10); filter_frame.pack(fill=tk.X)
        tk.Label(filter_frame, text="Contexto (N1):").pack(side=tk.LEFT, padx=5)
        self.combo_n1 = ttk.Combobox(filter_frame, values=["ALL"] + SIPA_LEVEL_1, state="readonly", width=15)
        self.combo_n1.set("ALL"); self.combo_n1.pack(side=tk.LEFT, padx=5)
        tk.Label(filter_frame, text="Acción (N2):").pack(side=tk.LEFT, padx=5)
        self.combo_n2 = ttk.Combobox(filter_frame, values=["ALL"] + SIPA_LEVEL_2, state="readonly", width=15)
        self.combo_n2.set("ALL"); self.combo_n2.pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="APLICAR FILTRO", command=self.cargar_roadmap_db).pack(side=tk.LEFT, padx=10)
        tk.Button(filter_frame, text="+ NUEVO HITO (SIPAdoc)", command=self.lanzar_sipadoc_gui, bg="#d1ffd1").pack(side=tk.RIGHT, padx=20)
        paned = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        cols = ("id", "fecha", "n1", "n2", "tarea", "vinculo")
        self.tabla_road = ttk.Treeview(paned, columns=cols, show="headings")
        for c in cols[:-1]: self.tabla_road.heading(c, text=c.capitalize())
        self.tabla_road.heading("vinculo", text="Archivo")
        self.tabla_road.column("id", width=40)
        self.tabla_road.column("vinculo", width=0, stretch=tk.NO)
        paned.add(self.tabla_road, weight=3)
        self.tabla_road.bind("<<TreeviewSelect>>", self.on_roadmap_select)
        self.tabla_road.bind("<Double-1>", lambda e: self.abrir_editor(source="roadmap"))
        self.txt_road_detail = tk.Text(paned, bg="#fdfdfd", font=("Consolas", 10), wrap=tk.WORD)
        paned.add(self.txt_road_detail, weight=2)
        self.cargar_roadmap_db()

    def cargar_roadmap_db(self):
        for item in self.tabla_road.get_children(): self.tabla_road.delete(item)
        try:
            for r in self.db.obtener_roadmap_filtrado(self.combo_n1.get(), self.combo_n2.get()):
                self.tabla_road.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], r[5]))
        except Exception as e: print(f"Error cargar Roadmap: {e}")

    def listar_docs(self):
        for item in self.tabla_docs.get_children(): self.tabla_docs.delete(item)
        if os.path.exists(self.knowledge_dir):
            for f in sorted(os.listdir(self.knowledge_dir)):
                if f.endswith(".md"): self.tabla_docs.insert("", tk.END, values=(f,))

    def on_roadmap_select(self, event):
        sel = self.tabla_road.selection()
        if not sel: return
        try:
            detalle = self.db.obtener_detalle_roadmap(self.tabla_road.item(sel)['values'][0])
            self.txt_road_detail.delete(1.0, tk.END)
            self.txt_road_detail.insert(tk.END, detalle if detalle else "Doble clic para ver archivo.")
        except: pass

    def _init_tab_telemetria(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text=" Telemetría ")
        container = tk.Frame(tab, padx=20, pady=10); container.pack(expand=True, fill=tk.BOTH)
        self.tabla = ttk.Treeview(container, columns=("f","d","e"), show="headings", height=8)
        for c, t in zip(("f","d","e"), ("Sesión", "Segs", "Estado")): self.tabla.heading(c, text=t)
        self.tabla.tag_configure('irregular', background='#ffe6e6', foreground='#cc0000')
        self.tabla.tag_configure('optimo', foreground='#008800')
        self.tabla.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.txt_logs = tk.Text(container, height=10, bg="#000", fg="#00FF00", font=("Consolas", 9))
        self.txt_logs.pack(fill=tk.BOTH, expand=True, pady=10)
        for log in self.logs_recibidos: self.txt_logs.insert(tk.END, f"> {log}\n")
        self.txt_logs.config(state=tk.DISABLED)
        tk.Button(container, text="REFRESCAR", command=self.cargar_datos).pack(pady=5)
        self.cargar_datos()

    def _init_tab_auditoria_db(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text=" Auditoría DB ")
        tk.Button(tab, text="CERTIFICAR INTEGRIDAD CITADEL", command=self.run_db_test, bg="#d4a017").pack(pady=10)
        self.console_audit = tk.Text(tab, bg="#2d2d2d", fg="#88ff88", font=("Consolas", 10))
        self.console_audit.pack(fill=tk.BOTH, expand=True)

    def cargar_datos(self):
        for item in self.tabla.get_children(): self.tabla.delete(item)
        try:
            for r in self.db.obtener_metricas_recientes(20):
                tag = 'irregular' if r[2] == 'IRREGULAR' else 'optimo'
                self.tabla.insert("", tk.END, values=(r[0], f"{r[1]:.4f}", r[2]), tags=(tag,))
        except: pass

    def run_db_test(self):
        script = os.path.join(self.root_dir, "test_db_full.py")
        res = subprocess.run([sys.executable, script], capture_output=True, text=True, cwd=self.root_dir)
        self.console_audit.delete(1.0, tk.END); self.console_audit.insert(tk.END, res.stdout + res.stderr)

    def lanzar_sipadoc_gui(self):
        script = os.path.join(self.root_dir, "sipadoc_gui.py")
        if os.path.exists(script): subprocess.Popen([sys.executable, script], cwd=self.root_dir)

    def run(self): self.window.mainloop()