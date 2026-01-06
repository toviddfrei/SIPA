# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: sipadoc_gui.py
# Módulo: SIPAdoc (Generador de Artefactos de Documentación)
# Versión: 0.2.5 | Fecha: 06/01/2026
# Autor: Daniel Miñana & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Interfaz Estándar consolidada de documentación.
# Integra la gestión de Trayectoria Vital y el Roadmap SIPA.
# Sincronización íntegra con Kernel Citadel (.md + SQLite).
# EXCELENCIA: Nomenclatura atómica unificada (DNA de Archivo).
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import sys
import logging
import shutil
import re

# Anclaje de rutas para alcance del core y persistencia
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
        
        # Paleta de colores corporativa (Bloque 5 config.py)
        self.color_bg = "#f0f0f0"
        self.color_panel = "#ffffff"
        self.color_accent = "#0056b3"
        self.color_text = "#333333"
        
        self.root.configure(bg=self.color_bg)
        
        # Conexión al Kernel Citadel
        self.db = PersistenceManager()
        self.db.connect()
        self.logger = logging.getLogger("SIPA_Doc")
        self.knowledge_path = "data/knowledge/"
        
        # Estado temporal de adjuntos (Trayectoria)
        self.list_evidencias = []
        self.pdf_adjunto = None
        
        if not os.path.exists(self.knowledge_path):
            os.makedirs(self.knowledge_path)
        
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        """Configuración visual de los componentes ttk."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.color_bg, borderwidth=1)
        style.configure("TNotebook.Tab", background="#e1e1e1", foreground="#333", padding=[15, 5])
        style.map("TNotebook.Tab", background=[("selected", self.color_accent)], foreground=[("selected", "#FFFFFF")])
        style.configure("TFrame", background=self.color_panel)
        style.configure("TLabel", background=self.color_panel, foreground=self.color_text)

    # ----------------------------------------------------------------------
    # MOTOR DE NOMBRADO ATÓMICO (DNA SIPA)
    # ----------------------------------------------------------------------
    def _generar_nombre_atómico(self, n1, prefijo_modulo, texto_referencia):
        """Genera un nombre semántico: YYYYMMDD_HHMM_N1_MODULO_SLUG.md"""
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        n1_clean = re.sub(r'[^\w]', '', n1).upper()
        # Slug de 20 caracteres del texto para dar contexto al archivo
        texto_limpio = re.sub(r'[^\w\s]', '', texto_referencia).strip()
        slug = texto_limpio.replace(" ", "_").upper()[:20]
        if not slug: slug = "DETALLE"
        return f"{ts}_{n1_clean}_{prefijo_modulo.upper()}_{slug}.md"

    # ----------------------------------------------------------------------
    # COMPONENTES REUTILIZABLES (UI)
    # ----------------------------------------------------------------------
    def _create_dual_selector(self, parent, var_n1, var_n2):
        """Genera los selectores obligatorios N1/N2 para taxonomía SIPA."""
        frame = tk.Frame(parent, bg=self.color_panel, pady=10)
        frame.pack(fill="x", padx=20)
        
        tk.Label(frame, text="CONTEXTO (N1):", font=("Segoe UI", 9, "bold")).pack(side="left")
        cb1 = ttk.Combobox(frame, textvariable=var_n1, values=SIPA_LEVEL_1, state="readonly", width=18)
        cb1.pack(side="left", padx=10)
        
        tk.Label(frame, text="ACCIÓN (N2):", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(20, 0))
        cb2 = ttk.Combobox(frame, textvariable=var_n2, values=SIPA_LEVEL_2, state="readonly", width=18)
        cb2.pack(side="left", padx=10)

    def _add_text_field(self, parent, label, height=5):
        """Añade un campo de texto con label estandarizado."""
        container = tk.Frame(parent, bg=self.color_panel)
        container.pack(fill="x", padx=20, pady=5)
        tk.Label(container, text=label, fg=self.color_accent, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        t = tk.Text(container, height=height, bg="white", fg="#333", 
                    font=("Consolas", 10), relief="solid", borderwidth=1, padx=10, pady=10)
        t.pack(fill="x", pady=5)
        return t

    def get_pedagogical_header(self, filename, module, description):
        """Genera la cabecera estándar para archivos Markdown del sistema."""
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

    # ----------------------------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ (TABS)
    # ----------------------------------------------------------------------
    def create_widgets(self):
        header = tk.Frame(self.root, bg=self.color_accent, height=60)
        header.pack(fill="x", side="top")
        tk.Label(header, text="SIPA ENGINE | FACTORÍA DE DOCUMENTACIÓN v0.2.5", 
                 bg=self.color_accent, fg="white", font=("Segoe UI", 12, "bold")).pack(pady=15)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # TAB 1: IDENTITY (Perfil Propietario)
        self.tab_identity = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_identity, text=" PERFIL ")
        self.id_n1 = tk.StringVar(value="PERSONAL"); self.id_n2 = tk.StringVar(value="PERFIL")
        self._create_dual_selector(self.tab_identity, self.id_n1, self.id_n2)
        self.id_bio = self._add_text_field(self.tab_identity, "👤 BIO PROFESIONAL / RESUMEN", height=10)
        self.id_skills = self._add_text_field(self.tab_identity, "🛠️ SKILLS Y COMPETENCIAS", height=5)
        tk.Button(self.tab_identity, text="ACTUALIZAR PERFIL PROPIETARIO", bg="#28a745", fg="white", font=("Segoe UI", 10, "bold"), command=self.save_identity, pady=10).pack(pady=15, padx=20, fill="x")

        # TAB 2: DAILY ACTIVITY
        self.tab_daily = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_daily, text=" DAILY ACTIVITY ")
        self.daily_n1 = tk.StringVar(value=SIPA_LEVEL_1[0]); self.daily_n2 = tk.StringVar(value="TAREA")
        self._create_dual_selector(self.tab_daily, self.daily_n1, self.daily_n2)
        self.daily_goals = self._add_text_field(self.tab_daily, "🎯 OBJETIVOS DEL DÍA", height=3)
        self.daily_hits = self._add_text_field(self.tab_daily, "✅ HITOS ALCANZADOS", height=5)
        self.daily_blocks = self._add_text_field(self.tab_daily, "⚠️ BLOQUEOS IDENTIFICADOS", height=3)
        tk.Button(self.tab_daily, text="PROCESAR DAILY Y ESCALAR A ROADMAP", bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"), command=self.save_daily, pady=10).pack(pady=15, padx=20, fill="x")

        # TAB 3: TECHNICAL SPEC
        self.tab_spec = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_spec, text=" TECHNICAL SPEC ")
        self.spec_n1 = tk.StringVar(value=SIPA_LEVEL_1[0]); self.spec_n2 = tk.StringVar(value="SPEC")
        self._create_dual_selector(self.tab_spec, self.spec_n1, self.spec_n2)
        self.spec_title = self._add_text_field(self.tab_spec, "📌 TÍTULO DE LA ESPECIFICACIÓN", height=1)
        self.spec_logic = self._add_text_field(self.tab_spec, "⚙️ LÓGICA DE NEGOCIO / FUNCIONALIDAD", height=7)
        self.spec_data = self._add_text_field(self.tab_spec, "📊 ESQUEMA DE DATOS", height=5)
        tk.Button(self.tab_spec, text="GRABAR ESPECIFICACIÓN TÉCNICA", bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"), command=self.save_tech, pady=10).pack(pady=15, padx=20, fill="x")

        # TAB 4: CHAT HISTORY
        self.tab_chat = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_chat, text=" CHAT HISTORY ")
        self.chat_n1 = tk.StringVar(value=SIPA_LEVEL_1[0]); self.chat_n2 = tk.StringVar(value="CHAT")
        self._create_dual_selector(self.tab_chat, self.chat_n1, self.chat_n2)
        self.chat_q = self._add_text_field(self.tab_chat, "❓ QUESTIONS (PREGUNTAS IA)", height=8)
        self.chat_a = self._add_text_field(self.tab_chat, "💡 ANSWERS (RESPUESTAS / INSIGHTS)", height=8)
        tk.Button(self.tab_chat, text="GUARDAR CONVERSACIÓN ESTRATÉGICA", bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"), command=self.save_chat, pady=10).pack(pady=15, padx=20, fill="x")

        # TAB 5: CAREER (Cronograma Vital - Solo Laboral/Formativa)
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
        tk.Button(frame_files, text="+ Imágenes (JPG)", command=self.add_images).pack(side="left", padx=5)
        tk.Button(frame_files, text="+ Título (PDF)", command=self.add_pdf).pack(side="left", padx=5)
        self.lbl_evid_status = tk.Label(frame_files, text="Sin archivos adjuntos", font=("Segoe UI", 8, "italic"))
        self.lbl_evid_status.pack(side="right")
        tk.Button(self.tab_career, text="REGISTRAR EN TRAYECTORIA VITAL", bg="#0056b3", fg="white", font=("Segoe UI", 10, "bold"), command=self.save_career_full, pady=10).pack(pady=15, padx=20, fill="x")

        # TAB 6: ACHIEVEMENTS (Roadmap SIPA - Hitos Estratégicos)
        self.tab_hits = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_hits, text=" HITOS ")
        self.hits_n1 = tk.StringVar(value="LOGROS"); self.hits_n2 = tk.StringVar(value="HITO")
        self._create_dual_selector(self.tab_hits, self.hits_n1, self.hits_n2)
        
        frame_temporal = tk.Frame(self.tab_hits, bg=self.color_panel)
        frame_temporal.pack(fill="x", padx=20, pady=5)
        tk.Label(frame_temporal, text="📅 FECHA ENTREGABLE (META):").pack(side="left")
        self.ent_fecha_meta = tk.Entry(frame_temporal, width=12)
        self.ent_fecha_meta.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_fecha_meta.pack(side="left", padx=5)
        tk.Label(frame_temporal, text="✅ FECHA CONSEGUIDO (REAL):", padx=10).pack(side="left")
        self.ent_fecha_real = tk.Entry(frame_temporal, width=12)
        self.ent_fecha_real.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_fecha_real.pack(side="left", padx=5)

        self.hits_title = self._add_text_field(self.tab_hits, "🏆 TÍTULO DEL HITO / LOGRO", height=1)
        self.hits_detail = self._add_text_field(self.tab_hits, "📜 DETALLE TÉCNICO Y VALIDACIÓN", height=10)
        tk.Button(self.tab_hits, text="CERTIFICAR HITO EN ROADMAP SIPA", bg="#ffc107", fg="black", font=("Segoe UI", 10, "bold"), command=self.save_hits, pady=10).pack(pady=15, padx=20, fill="x")

    # ----------------------------------------------------------------------
    # MÉTODOS DE APOYO (UTILIDADES)
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

    def add_pdf(self):
        file = filedialog.askopenfilename(title="Seleccionar Título Oficial (PDF)", filetypes=[("Documento PDF", "*.pdf")])
        if file:
            self.pdf_adjunto = file
            self.lbl_evid_status.config(text="PDF listo para procesar", fg="#28a745")

    # ----------------------------------------------------------------------
    # MÉTODOS DE PERSISTENCIA (SINCRONIZACIÓN MD + SQLITE)
    # ----------------------------------------------------------------------
    def save_identity(self):
        n1, n2 = self.id_n1.get(), self.id_n2.get()
        fname = "perfil_propietario.md"
        header = self.get_pedagogical_header(fname, "IDENTITY", "Perfil Propietario.")
        body = f"## 👤 BIO\n{self.id_bio.get('1.0', tk.END).strip()}\n\n## 🛠️ SKILLS\n{self.id_skills.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(datetime.now().strftime("%Y-%m-%d"), n1, n2, "Actualización Perfil", "", fname)
        messagebox.showinfo("SIPA", "Perfil Propietario actualizado.")

    def save_daily(self):
        n1, n2 = self.daily_n1.get(), self.daily_n2.get()
        hits_text = self.daily_hits.get('1.0', tk.END).strip()
        fname = self._generar_nombre_atómico(n1, "DAILY", hits_text)
        header = self.get_pedagogical_header(fname, n1, "Registro diario.")
        body = f"## 🎯 OBJETIVOS\n{self.daily_goals.get('1.0', tk.END).strip()}\n\n## ✅ HITOS\n{hits_text}\n\n## ⚠️ BLOQUEOS\n{self.daily_blocks.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(datetime.now().strftime("%Y-%m-%d"), n1, n2, f"Daily: {hits_text[:60]}", "", fname)
        messagebox.showinfo("SIPA", f"Daily guardado: {fname}")
        self._clear([self.daily_goals, self.daily_hits, self.daily_blocks])

    def save_tech(self):
        n1, n2 = self.spec_n1.get(), self.spec_n2.get()
        title = self.spec_title.get('1.0', tk.END).strip()
        fname = self._generar_nombre_atómico(n1, "SPEC", title)
        header = self.get_pedagogical_header(fname, n1, f"Especificación: {title}")
        body = f"## ⚙️ LÓGICA\n{self.spec_logic.get('1.0', tk.END).strip()}\n\n## 📊 DATOS\n{self.spec_data.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(datetime.now().strftime("%Y-%m-%d"), n1, n2, f"Spec: {title}", "", fname)
        messagebox.showinfo("SIPA", f"Spec persistida: {fname}")
        self._clear([self.spec_title, self.spec_logic, self.spec_data])

    def save_chat(self):
        n1, n2 = self.chat_n1.get(), self.chat_n2.get()
        pregunta = self.chat_q.get('1.0', tk.END).strip()
        fname = self._generar_nombre_atómico(n1, "CHAT", pregunta)
        header = self.get_pedagogical_header(fname, n1, "Consulta IA.")
        body = f"## ❓ PREGUNTA\n{pregunta}\n\n## 💡 RESPUESTA\n{self.chat_a.get('1.0', tk.END).strip()}\n"
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
        self.db.agregar_hito_roadmap(datetime.now().strftime("%Y-%m-%d"), n1, n2, f"Chat: {pregunta[:40]}", "", fname)
        messagebox.showinfo("SIPA", f"Conversación almacenada: {fname}")
        self._clear([self.chat_q, self.chat_a])

    def save_hits(self):
        n1, n2 = self.hits_n1.get(), self.hits_n2.get()
        title = self.hits_title.get('1.0', tk.END).strip()
        f_meta = self.ent_fecha_meta.get().strip()
        f_real = self.ent_fecha_real.get().strip()
        if not title:
            messagebox.showwarning("SIPA", "Título obligatorio.")
            return
        fname = self._generar_nombre_atómico(n1, "HITO", title)
        try:
            header = self.get_pedagogical_header(fname, n1, f"Hito: {title}")
            body = f"## 📅 CONTROL TEMPORAL\n- Meta: {f_meta}\n- Real: {f_real}\n\n## 🏆 LOGRO\n{title}\n\n## 📜 DETALLE\n{self.hits_detail.get('1.0', tk.END).strip()}"
            with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f: f.write(header + body)
            self.db.agregar_hito_roadmap(f_real, n1, n2, title, f"Meta: {f_meta}", fname)
            self.db.agregar_hito_estrategico(title, "Certificado", f"{f_meta} 23:59:59", "COMPLETADO")
            messagebox.showinfo("SIPA", f"Hito certificado: {fname}")
            self._clear([self.hits_title, self.hits_detail])
        except Exception as e: messagebox.showerror("Error", str(e))

    def save_career_full(self):
        try:
            tipo = self.career_type.get()
            entidad = self.career_entidad.get('1.0', tk.END).strip()
            rol = self.career_rol.get('1.0', tk.END).strip()
            if not entidad or not rol: raise ValueError("Entidad y Puesto obligatorios.")
            fname = self._generar_nombre_atómico(tipo, "TRA", entidad)
            dest_folder = DIR_EVID_LABORAL if tipo == "LABORAL" else DIR_EVID_FORMAT
            nombres_img = []
            for i, p in enumerate(self.list_evidencias):
                nuevo = f"{fname.replace('.md','')}_img{i+1}{os.path.splitext(p)[1]}"
                shutil.copy(p, dest_folder / nuevo); nombres_img.append(nuevo)
            while len(nombres_img) < 4: nombres_img.append(None)
            nombre_pdf = None
            if self.pdf_adjunto:
                nombre_pdf = f"{fname.replace('.md','')}.pdf"
                shutil.copy(self.pdf_adjunto, dest_folder / nombre_pdf)
            with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f:
                f.write(self.get_pedagogical_header(fname, tipo, f"Registro {tipo}") + f"## RESUMEN\n{self.career_resumen.get('1.0', tk.END)}\n\n## DETALLE\n{self.career_desc.get('1.0', tk.END)}")
            self.db.insert_trayectoria({
                'tipo': tipo, 'entidad': entidad, 'cargo': rol, 'f_inicio': self.ent_f_inicio.get(),
                'f_fin': self.ent_f_fin.get() if not self.check_actual.get() else "Actual",
                'actualmente': self.check_actual.get(), 'resumen': self.career_resumen.get('1.0', tk.END),
                'vinculo_md': fname, 'img1': nombres_img[0], 'img2': nombres_img[1], 'pdf': nombre_pdf
            })
            messagebox.showinfo("SIPA", f"Trayectoria registrada: {fname}")
            self._clear([self.career_entidad, self.career_rol, self.career_resumen, self.career_desc])
            self.list_evidencias = []; self.pdf_adjunto = None; self.lbl_evid_status.config(text="Sin archivos", fg="black")
        except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk(); app = SipaDocGUI(root); root.mainloop()