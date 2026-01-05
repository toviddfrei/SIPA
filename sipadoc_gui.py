# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: sipadoc_gui.py
# Módulo: SIPAdoc (Generador de Artefactos de Documentación)
# Versión: 0.2.5 | Fecha: 03/01/2026
# Autor: Daniel Miñana & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Interfaz evolucionada Gris/Azul. 
# Corregido conflicto de variables en pestañas SPEC y CHAT.
# Implementada limpieza independiente y firma pedagógica.
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os

class SipaDocPersistence:
    """CLASE: SipaDocPersistence | OBJETIVO: Almacenamiento de artefactos."""
    def __init__(self):
        self.knowledge_path = "data/knowledge/"
        self._ensure_path()

    def _ensure_path(self):
        if not os.path.exists(self.knowledge_path):
            os.makedirs(self.knowledge_path)

    def save(self, content, filename):
        full_path = os.path.join(self.knowledge_path, filename)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return full_path
        except Exception as e:
            return f"Error: {str(e)}"

class SipaDocGUI:
    """CLASE: SipaDocGUI | OBJETIVO: Panel Root Moderno (Gris/Azul)."""
    def __init__(self, root):
        self.root = root
        self.root.title("SIPA | DOCUMENTATION MODULE v0.2.5")
        self.root.geometry("900x900")
        
        self.color_bg = "#2B2D30"
        self.color_panel = "#1E1F22"
        self.color_accent = "#3574F0"
        self.color_text = "#DFE1E5"
        
        self.root.configure(bg=self.color_bg)
        self.persistence = SipaDocPersistence()
        
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.color_bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.color_panel, foreground=self.color_text, padding=[15, 5])
        style.map("TNotebook.Tab", background=[("selected", self.color_accent)], foreground=[("selected", "#FFFFFF")])
        style.configure("TFrame", background=self.color_panel)
        style.configure("TLabel", background=self.color_panel, foreground=self.color_text, font=("Segoe UI", 10))

    def get_pedagogical_header(self, filename, module, description):
        return (
            f"# ARTEFACTO: {filename}\n\n"
            f"```text\n"
            f"PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático\n"
            f"Módulo: {module} | Generado por: SIPAdoc v0.2.5\n"
            f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            f"Autor: Daniel Miñana & Gemini\n"
            f"----------------------------------------------------------\n"
            f"DESCRIPCIÓN: {description}\n"
            "```\n\n"
        )

    def _add_text_field(self, parent, label, height=5):
        container = ttk.Frame(parent)
        container.pack(fill="x", padx=15, pady=5)
        ttk.Label(container, text=label).pack(anchor="w")
        t = tk.Text(container, height=height, bg="#1E1F22", fg="#DFE1E5", 
                    insertbackground=self.color_accent, font=("Consolas", 11), 
                    relief="flat", padx=10, pady=10, highlightthickness=1, 
                    highlightbackground="#4B4D51", highlightcolor=self.color_accent)
        t.pack(fill="x", pady=5)
        return t

    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg=self.color_panel, height=60)
        header_frame.pack(fill="x", side="top")
        tk.Label(header_frame, text="SIPA ENGINE | ARTEFACT GENERATOR", 
                 bg=self.color_panel, fg=self.color_accent, font=("Segoe UI", 12, "bold")).pack(pady=15)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=20, pady=20)

        # --- TAB 1: DAILY ACTIVITY ---
        self.tab_daily = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_daily, text=" DAILY ACTIVITY ")
        
        self.daily_mod = tk.StringVar(value="SIPAdel")
        self._create_mod_selector(self.tab_daily, self.daily_mod)
        self.daily_goals = self._add_text_field(self.tab_daily, "OBJETIVOS DEL DÍA")
        self.daily_hits = self._add_text_field(self.tab_daily, "HITOS ALCANZADOS")
        self.daily_blocks = self._add_text_field(self.tab_daily, "BLOQUEOS IDENTIFICADOS")
        self._create_save_btn(self.tab_daily, "PROCESAR Y LIMPIAR ARTEFACTO", self.save_daily)

        # --- TAB 2: TECHNICAL SPEC --- (Variables con prefijo 'spec_')
        self.tab_spec = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_spec, text=" TECHNICAL SPEC ")
        
        self.spec_mod = tk.StringVar(value="SIPAdel")
        self._create_mod_selector(self.tab_spec, self.spec_mod)
        self.spec_logic = self._add_text_field(self.tab_spec, "LÓGICA DE NEGOCIO / FUNCIONALIDAD", height=10)
        self.spec_data = self._add_text_field(self.tab_spec, "ESQUEMA DE DATOS", height=10)
        self._create_save_btn(self.tab_spec, "GRABAR ESPECIFICACIÓN", self.save_tech)

        # --- TAB 3: CHAT --- (Variables con prefijo 'chat_')
        self.tab_chat = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_chat, text=" CHAT HISTORY ")
        
        self.chat_mod = tk.StringVar(value="SIPAdel")
        self._create_mod_selector(self.tab_chat, self.chat_mod)
        self.chat_q = self._add_text_field(self.tab_chat, "QUESTIONS (PREGUNTAS REALIZADAS)", height=10)
        self.chat_a = self._add_text_field(self.tab_chat, "ANSWERS (RESPUESTAS OBTENIDAS)", height=10)
        self._create_save_btn(self.tab_chat, "GRABAR CONVERSACIÓN CHAT", self.save_chat)

    def _create_mod_selector(self, parent, var):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=15, pady=10)
        ttk.Label(frame, text="Módulo Afectado:").pack(side="left")
        ttk.Combobox(frame, textvariable=var, 
                     values=["SIPA", "SIPAdoc", "SIPAbap", "SIPAdel", "SIPAcur", "FHS-CyberAudit"]).pack(side="left", padx=10)

    def _create_save_btn(self, parent, text, command):
        tk.Button(parent, text=text, command=command, bg=self.color_accent, fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=10, cursor="hand2").pack(pady=20, fill="x", padx=15)

    def save_daily(self):
        module = self.daily_mod.get()
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        fname = f"{ts}_DAILY_{module.upper()}.md"
        header = self.get_pedagogical_header(fname, module, "Registro de actividad diaria.")
        body = f"## 🎯 OBJETIVOS\n\n{self.daily_goals.get('1.0', tk.END).strip()}\n\n## ✅ HITOS\n\n{self.daily_hits.get('1.0', tk.END).strip()}\n\n## ⚠️ BLOQUEOS\n\n{self.daily_blocks.get('1.0', tk.END).strip()}\n"
        self.persistence.save(header + body, fname)
        messagebox.showinfo("SIPA Success", "Daily guardado.")
        for f in [self.daily_goals, self.daily_hits, self.daily_blocks]: f.delete('1.0', tk.END)

    def save_tech(self):
        module = self.spec_mod.get()
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        fname = f"{ts}_SPEC_{module.upper()}.md"
        header = self.get_pedagogical_header(fname, module, "Especificación técnica detallada.")
        body = f"## ⚙️ LÓGICA DE NEGOCIO\n\n{self.spec_logic.get('1.0', tk.END).strip()}\n\n## 📊 ESQUEMA DE DATOS\n\n{self.spec_data.get('1.0', tk.END).strip()}\n"
        self.persistence.save(header + body, fname)
        messagebox.showinfo("SIPA Success", "Especificación técnica guardada.")
        for f in [self.spec_logic, self.spec_data]: f.delete('1.0', tk.END)

    def save_chat(self):
        module = self.chat_mod.get()
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        fname = f"{ts}_CHAT_{module.upper()}.md"
        header = self.get_pedagogical_header(fname, module, "Chat de conversación (IA Learning).")
        body = f"## ⚙️ PREGUNTA REALIZADA\n\n{self.chat_q.get('1.0', tk.END).strip()}\n\n## 📊 RESPUESTA OBTENIDA\n\n{self.chat_a.get('1.0', tk.END).strip()}\n"
        self.persistence.save(header + body, fname)
        messagebox.showinfo("SIPA Chat", "Conversación almacenada.")
        for f in [self.chat_q, self.chat_a]: f.delete('1.0', tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = SipaDocGUI(root)
    root.mainloop()