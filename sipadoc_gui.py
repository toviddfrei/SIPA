# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: sipadoc_gui.py
# Módulo: SIPAdoc (Generador de Artefactos de Documentación)
# Versión: 0.2.5 | Fecha: 06/01/2026
# Autor: Daniel Miñana & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Interfaz Estándar consolidada.
# Pestañas: Daily, Tech Spec, Chat, Perfil, Trayectoria e Hitos.
# Sincronización íntegra con el Kernel Citadel y archivos .md.
# Gestión profesional de evidencias documentales JPG/PDF.
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import sys
import logging
import shutil

# Forzamos alcance al core para persistencia
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.persistence import PersistenceManager
from core.config import (
    SIPA_LEVEL_1, SIPA_LEVEL_2, 
    DIR_EVID_LABORAL, DIR_EVID_FORMAT
)

class SipaDocGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SIPA | DOCUMENTATION MODULE v0.2.5")
        self.root.geometry("950x950")
        
        # Paleta de colores ESTÁNDAR
        self.color_bg = "#f0f0f0"
        self.color_panel = "#ffffff"
        self.color_accent = "#0056b3"
        self.color_text = "#333333"
        
        self.root.configure(bg=self.color_bg)
        
        # Conexión al Kernel y rutas
        self.db = PersistenceManager()
        self.db.connect()
        self.logger = logging.getLogger("SIPA_Doc")
        self.knowledge_path = "data/knowledge/"
        
        # Estado de evidencias
        self.list_evidencias = []
        self.pdf_adjunto = None
        
        if not os.path.exists(self.knowledge_path):
            os.makedirs(self.knowledge_path)
        
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.color_bg, borderwidth=1)
        style.configure("TNotebook.Tab", background="#e1e1e1", foreground="#333", padding=[15, 5])
        style.map("TNotebook.Tab", background=[("selected", self.color_accent)], foreground=[("selected", "#FFFFFF")])
        style.configure("TFrame", background=self.color_panel)
        style.configure("TLabel", background=self.color_panel, foreground=self.color_text)

    def _create_dual_selector(self, parent, var_n1, var_n2):
        """Genera los selectores obligatorios para el Roadmap."""
        frame = tk.Frame(parent, bg=self.color_panel, pady=10)
        frame.pack(fill="x", padx=20)
        
        tk.Label(frame, text="CONTEXTO (N1):", font=("Segoe UI", 9, "bold")).pack(side="left")
        cb1 = ttk.Combobox(frame, textvariable=var_n1, values=SIPA_LEVEL_1, state="readonly", width=18)
        cb1.pack(side="left", padx=10)
        
        tk.Label(frame, text="ACCIÓN (N2):", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(20, 0))
        cb2 = ttk.Combobox(frame, textvariable=var_n2, values=SIPA_LEVEL_2, state="readonly", width=18)
        cb2.pack(side="left", padx=10)

    def _add_text_field(self, parent, label, height=5):
        container = tk.Frame(parent, bg=self.color_panel)
        container.pack(fill="x", padx=20, pady=5)
        tk.Label(container, text=label, fg=self.color_accent, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        t = tk.Text(container, height=height, bg="white", fg="#333", 
                    font=("Consolas", 10), relief="solid", borderwidth=1, padx=10, pady=10)
        t.pack(fill="x", pady=5)
        return t

    def get_pedagogical_header(self, filename, module, description):
        return (
            f"# ARTEFACTO: {filename}\n"
            f"```text\n"
            f"PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático\n"
            f"Módulo: {module} | Generado por: SIPAdoc v0.2.5\n"
            f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            f"Autor: Daniel Miñana & Gemini\n"
            f"----------------------------------------------------------\n"
            f"DESCRIPCIÓN: {description}\n"
            f"```\n\n"
        )

    def create_widgets(self):
        header = tk.Frame(self.root, bg=self.color_accent, height=60)
        header.pack(fill="x", side="top")
        tk.Label(header, text="SIPA ENGINE | FACTORÍA DE DOCUMENTACIÓN v0.2.5", 
                 bg=self.color_accent, fg="white", font=("Segoe UI", 12, "bold")).pack(pady=15)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # --- TAB 1: IDENTITY ---
        self.tab_identity = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_identity, text=" PERFIL ")
        self.id_n1 = tk.StringVar(value="PERSONAL"); self.id_n2 = tk.StringVar(value="PERFIL")
        self._create_dual_selector(self.tab_identity, self.id_n1, self.id_n2)
        self.id_bio = self._add_text_field(self.tab_identity, "👤 BIO PROFESIONAL / RESUMEN", height=10)
        self.id_skills = self._add_text_field(self.tab_identity, "🛠️ SKILLS Y COMPETENCIAS", height=5)
        tk.Button(self.tab_identity, text="ACTUALIZAR PERFIL PROPIETARIO", bg="#28a745", fg="white", font=("Segoe UI", 10, "bold"), command=self.save_identity, pady=10).pack(pady=15, padx=20, fill="x")

        # --- TAB 2: DAILY ACTIVITY ---
        self.tab_daily = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_daily, text=" DAILY ACTIVITY ")
        self.daily_n1 = tk.StringVar(value=SIPA_LEVEL_1[0]); self.daily_n2 = tk.StringVar(value="TAREA")
        self._create_dual_selector(self.tab_daily, self.daily_n1, self.daily_n2)
        self.daily_goals = self._add_text_field(self.tab_daily, "🎯 OBJETIVOS DEL DÍA", height=3)
        self.daily_hits = self._add_text_field(self.tab_daily, "✅ HITOS ALCANZADOS", height=5)
        self.daily_blocks = self._add_text_field(self.tab_daily, "⚠️ BLOQUEOS IDENTIFICADOS", height=3)
        tk.Button(self.tab_daily, text="PROCESAR DAILY Y ESCALAR A ROADMAP", bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"), command=self.save_daily, pady=10).pack(pady=15, padx=20, fill="x")

        # --- TAB 3: TECHNICAL SPEC ---
        self.tab_spec = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_spec, text=" TECHNICAL SPEC ")
        self.spec_n1 = tk.StringVar(value=SIPA_LEVEL_1[0]); self.spec_n2 = tk.StringVar(value="PROYECTO")
        self._create_dual_selector(self.tab_spec, self.spec_n1, self.spec_n2)
        self.spec_title = self._add_text_field(self.tab_spec, "📌 TÍTULO DE LA ESPECIFICACIÓN", height=1)
        self.spec_logic = self._add_text_field(self.tab_spec, "⚙️ LÓGICA DE NEGOCIO / FUNCIONALIDAD", height=7)
        self.spec_data = self._add_text_field(self.tab_spec, "📊 ESQUEMA DE DATOS", height=5)
        tk.Button(self.tab_spec, text="GRABAR ESPECIFICACIÓN TÉCNICA", bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"), command=self.save_tech, pady=10).pack(pady=15, padx=20, fill="x")

        # --- TAB 4: CHAT HISTORY ---
        self.tab_chat = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_chat, text=" CHAT HISTORY ")
        self.chat_n1 = tk.StringVar(value=SIPA_LEVEL_1[0]); self.chat_n2 = tk.StringVar(value="TAREA")
        self._create_dual_selector(self.tab_chat, self.chat_n1, self.chat_n2)
        self.chat_q = self._add_text_field(self.tab_chat, "❓ QUESTIONS (PREGUNTAS IA)", height=8)
        self.chat_a = self._add_text_field(self.tab_chat, "💡 ANSWERS (RESPUESTAS / INSIGHTS)", height=8)
        tk.Button(self.tab_chat, text="GUARDAR CONVERSACIÓN ESTRATÉGICA", bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"), command=self.save_chat, pady=10).pack(pady=15, padx=20, fill="x")

        # --- TAB 5: CAREER (TRAYECTORIA PROFESIONAL Y FORMATIVA) ---
        self.tab_career = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_career, text=" TRAYECTORIA ")
        frame_tipo = tk.Frame(self.tab_career, bg=self.color_panel, pady=10)
        frame_tipo.pack(fill="x", padx=20)
        tk.Label(frame_tipo, text="ÁMBITO:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.career_type = tk.StringVar(value="LABORAL")
        cb_tipo = ttk.Combobox(frame_tipo, textvariable=self.career_type, values=["LABORAL", "FORMATIVA"], state="readonly", width=15)
        cb_tipo.pack(side="left", padx=10)
        self.career_entidad = self._add_text_field(self.tab_career, "🏢 EMPRESA / INSTITUCIÓN", height=1)
        self.career_rol = self._add_text_field(self.tab_career, "📝 PUESTO / TÍTULO DEL CURSO", height=1)
        frame_dates = tk.Frame(self.tab_career, bg=self.color_panel); frame_dates.pack(fill="x", padx=20, pady=5)
        tk.Label(frame_dates, text="INICIO (YYYY-MM-DD):").pack(side="left")
        self.ent_f_inicio = tk.Entry(frame_dates, width=12); self.ent_f_inicio.pack(side="left", padx=5)
        tk.Label(frame_dates, text="FIN (YYYY-MM-DD):", padx=10).pack(side="left")
        self.ent_f_fin = tk.Entry(frame_dates, width=12); self.ent_f_fin.pack(side="left", padx=5)
        self.check_actual = tk.IntVar()
        tk.Checkbutton(frame_dates, text="Actualmente", variable=self.check_actual, bg=self.color_panel).pack(side="left", padx=10)
        self.career_resumen = self._add_text_field(self.tab_career, "📋 RESUMEN BREVE (Para Roadmap)", height=2)
        self.career_desc = self._add_text_field(self.tab_career, "📖 DETALLE COMPLETO (MD)", height=6)
        frame_files = tk.LabelFrame(self.tab_career, text=" 📂 EVIDENCIAS DOCUMENTALES ", bg=self.color_panel, padx=10, pady=10)
        frame_files.pack(fill="x", padx=20, pady=10)
        tk.Button(frame_files, text="+ Adjuntar Imágenes (JPG)", command=self.add_images).pack(side="left", padx=5)
        tk.Button(frame_files, text="+ Adjuntar Título (PDF)", command=self.add_pdf).pack(side="left", padx=5)
        self.lbl_evid_status = tk.Label(frame_files, text="Sin archivos adjuntos", font=("Segoe UI", 8, "italic"))
        self.lbl_evid_status.pack(side="right")
        tk.Button(self.tab_career, text="REGISTRAR EN TRAYECTORIA DE VIDA", bg="#0056b3", fg="white", font=("Segoe UI", 10, "bold"), command=self.save_career_full, pady=10).pack(pady=15, padx=20, fill="x")

        # --- TAB 6: ACHIEVEMENTS (HITOS) ---
        self.tab_hits = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_hits, text=" HITOS ")
        self.hits_n1 = tk.StringVar(value="LOGROS"); self.hits_n2 = tk.StringVar(value="CERTIFICACION")
        self._create_dual_selector(self.tab_hits, self.hits_n1, self.hits_n2)
        self.hits_title = self._add_text_field(self.tab_hits, "🏆 TÍTULO DEL HITO / LOGRO", height=1)
        self.hits_detail = self._add_text_field(self.tab_hits, "📜 DETALLE TÉCNICO Y VALIDACIÓN", height=10)
        tk.Button(self.tab_hits, text="CERTIFICAR HITO EN SIPA", bg="#ffc107", fg="black", font=("Segoe UI", 10, "bold"), command=self.save_hits, pady=10).pack(pady=15, padx=20, fill="x")

    # ----------------------------------------------------------------------
    # MÉTODOS DE APOYO Y UTILIDADES
    # ----------------------------------------------------------------------
    def _clear(self, fields):
        for f in fields: 
            if isinstance(f, tk.Text): f.delete('1.0', tk.END)
            elif isinstance(f, tk.Entry): f.delete(0, tk.END)

    def add_images(self):
        files = filedialog.askopenfilenames(title="Seleccionar Certificados (JPG)", filetypes=[("Imágenes JPG", "*.jpg *.jpeg")])
        if files:
            self.list_evidencias = list(files)[:4]
            self.lbl_evid_status.config(text=f"{len(self.list_evidencias)} imágenes listas", fg="#28a745")
            self.logger.info(f"Imágenes seleccionadas: {len(self.list_evidencias)}")

    def add_pdf(self):
        file = filedialog.askopenfilename(title="Seleccionar Título Oficial (PDF)", filetypes=[("Documento PDF", "*.pdf")])
        if file:
            self.pdf_adjunto = file
            self.lbl_evid_status.config(text="PDF listo para procesar", fg="#28a745")
            self.logger.info(f"PDF seleccionado: {file}")

    # ----------------------------------------------------------------------
    # MÉTODOS DE PERSISTENCIA (SINCRONIZACIÓN MD + SQLITE)
    # ----------------------------------------------------------------------
    def save_identity(self):
        n1, n2 = self.id_n1.get(), self.id_n2.get()
        fname = "perfil_propietario.md"
        header = self.get_pedagogical_header(fname, "IDENTITY", "Perfil Propietario del Sistema SIPA.")
        body = f"## 👤 BIO\n{self.id_bio.get('1.0', tk.END).strip()}\n\n## 🛠️ SKILLS\n{self.id_skills.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(datetime.now().strftime("%Y-%m-%d"), n1, n2, "Actualización Perfil", "", fname)
        messagebox.showinfo("SIPA", "Perfil Propietario actualizado correctamente.")

    def save_daily(self):
        n1, n2 = self.daily_n1.get(), self.daily_n2.get()
        ts_db, ts_file = datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y%m%d_%H%M")
        hits = self.daily_hits.get('1.0', tk.END).strip()
        fname = f"{ts_file}_{n2.upper()}_DAILY.md"
        header = self.get_pedagogical_header(fname, n1, "Registro de actividad diaria.")
        body = f"## 🎯 OBJETIVOS\n{self.daily_goals.get('1.0', tk.END).strip()}\n\n## ✅ HITOS\n{hits}\n\n## ⚠️ BLOQUEOS\n{self.daily_blocks.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(ts_db, n1, n2, f"Daily: {hits[:60]}...", "", fname)
        messagebox.showinfo("SIPA v0.2.5", "Sincronización Total: DB + MD")
        self._clear([self.daily_goals, self.daily_hits, self.daily_blocks])

    def save_tech(self):
        n1, n2 = self.spec_n1.get(), self.spec_n2.get()
        ts_db, ts_file = datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y%m%d_%H%M")
        title = self.spec_title.get('1.0', tk.END).strip()
        fname = f"{ts_file}_{n2.upper()}_{title.replace(' ', '_')}.md"
        header = self.get_pedagogical_header(fname, n1, f"Especificación: {title}")
        body = f"## ⚙️ LÓGICA\n{self.spec_logic.get('1.0', tk.END).strip()}\n\n## 📊 DATOS\n{self.spec_data.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(ts_db, n1, n2, f"Spec: {title}", "", fname)
        messagebox.showinfo("SIPA v0.2.5", "Documentación técnica persistida.")
        self._clear([self.spec_title, self.spec_logic, self.spec_data])

    def save_chat(self):
        n1, n2 = self.chat_n1.get(), self.chat_n2.get()
        ts_db, ts_file = datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y%m%d_%H%M")
        fname = f"{ts_file}_{n2.upper()}_CHAT.md"
        header = self.get_pedagogical_header(fname, n1, "Historial de consulta IA.")
        body = f"## ❓ PREGUNTA\n{self.chat_q.get('1.0', tk.END).strip()}\n\n## 💡 RESPUESTA\n{self.chat_a.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(ts_db, n1, n2, f"Chat: {n1} Insight", "", fname)
        messagebox.showinfo("SIPA v0.2.5", "Conversación almacenada correctamente.")
        self._clear([self.chat_q, self.chat_a])

    def save_hits(self):
        n1, n2 = self.hits_n1.get(), self.hits_n2.get()
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        title = self.hits_title.get('1.0', tk.END).strip()
        fname = f"{ts}_HITO_{title.replace(' ', '_')}.md"
        header = self.get_pedagogical_header(fname, "HITS", f"Logro: {title}")
        body = f"## 🏆 LOGRO\n{title}\n\n## 📜 DETALLE\n{self.hits_detail.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(datetime.now().strftime("%Y-%m-%d"), n1, n2, f"Hito: {title}", "", fname)
        messagebox.showinfo("SIPA", "Hito certificado y escalado a Roadmap.")
        self._clear([self.hits_title, self.hits_detail])

    def save_career_full(self):
        try:
            tipo = self.career_type.get()
            entidad = self.career_entidad.get('1.0', tk.END).strip()
            rol = self.career_rol.get('1.0', tk.END).strip()
            f_ini = self.ent_f_inicio.get().strip()
            f_fin = self.ent_f_fin.get().strip()
            es_actual = self.check_actual.get()
            resumen = self.career_resumen.get('1.0', tk.END).strip()
            detalle = self.career_desc.get('1.0', tk.END).strip()
            
            if not entidad or not rol: raise ValueError("Entidad y Puesto obligatorios.")
            
            # --- MEJORA SIPA: Generamos el nombre base UNIFICADO primero ---
            fecha_str = datetime.now().strftime('%Y%m%d')
            entidad_safe = "".join([c for c in entidad if c.isalnum() or c==' ']).replace(' ','_')
            base_filename = f"{fecha_str}_{tipo}_{entidad_safe}"
            fname = f"{base_filename}.md"
            # --------------------------------------------------------------

            dest_folder = DIR_EVID_LABORAL if tipo == "LABORAL" else DIR_EVID_FORMAT
            
            nombres_img = []
            for i, p in enumerate(self.list_evidencias):
                # Usamos el base_filename para que las imágenes también sean rastreables
                nuevo = f"{base_filename}_img{i+1}{os.path.splitext(p)[1]}"
                shutil.copy(p, dest_folder / nuevo); nombres_img.append(nuevo)
            while len(nombres_img) < 4: nombres_img.append(None)

            nombre_pdf = None
            if self.pdf_adjunto:
                # --- SOLUCIÓN AL MACHACADO: Nombre idéntico al .md ---
                nombre_pdf = f"{base_filename}.pdf"
                shutil.copy(self.pdf_adjunto, dest_folder / nombre_pdf)

            # Guardar el .md con el nombre unificado
            with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f:
                f.write(self.get_pedagogical_header(fname, tipo, f"Registro {tipo}") + f"## RESUMEN\n{resumen}\n\n## DETALLE\n{detalle}")

            self.db.insert_trayectoria({
                'tipo': tipo, 'entidad': entidad, 'cargo': rol, 'f_inicio': f_ini,
                'f_fin': f_fin if not es_actual else "Actual", 'actualmente': es_actual,
                'resumen': resumen, 'vinculo_md': fname, 'img1': nombres_img[0],
                'img2': nombres_img[1], 'pdf': nombre_pdf
            })
            
            messagebox.showinfo("SIPA", "Trayectoria registrada con éxito."); 
            self._clear([self.career_entidad, self.career_rol, self.career_resumen, self.career_desc])
            self.list_evidencias = []; self.pdf_adjunto = None; self.lbl_evid_status.config(text="Sin archivos", fg="black")
            
        except Exception as e: 
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk(); app = SipaDocGUI(root); root.mainloop()