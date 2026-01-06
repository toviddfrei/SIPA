# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: sipadoc_gui.py
# Módulo: SIPAdoc (Generador de Artefactos de Documentación)
# Versión: 0.2.5 | Fecha: 06/01/2026
# Autor: Daniel Miñana & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Interfaz Estándar consolidada (Gris/Azul).
# Bloques completos: Daily, Technical Spec y Chat History.
# Categorización dual N1/N2 obligatoria en cada pestaña.
# Sincronización íntegra con el Kernel Citadel y archivos .md.
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import sys

# Forzamos alcance al core para persistencia
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.persistence import PersistenceManager
from core.config import SIPA_LEVEL_1, SIPA_LEVEL_2

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
        self.knowledge_path = "data/knowledge/"
        
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
        
        # Nivel 1
        tk.Label(frame, text="CONTEXTO (N1):", font=("Segoe UI", 9, "bold")).pack(side="left")
        cb1 = ttk.Combobox(frame, textvariable=var_n1, values=SIPA_LEVEL_1, state="readonly", width=18)
        cb1.pack(side="left", padx=10)
        
        # Nivel 2
        tk.Label(frame, text="ACCIÓN (N2):", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(20, 0))
        cb2 = ttk.Combobox(frame, textvariable=var_n2, values=SIPA_LEVEL_2, state="readonly", width=18)
        cb2.pack(side="left", padx=10)

    def _add_text_field(self, parent, label, height=5):
        """Crea un área de texto con etiqueta."""
        container = tk.Frame(parent, bg=self.color_panel)
        container.pack(fill="x", padx=20, pady=5)
        
        tk.Label(container, text=label, fg=self.color_accent, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        
        t = tk.Text(container, height=height, bg="white", fg="#333", 
                    font=("Consolas", 10), relief="solid", borderwidth=1, padx=10, pady=10)
        t.pack(fill="x", pady=5)
        return t

    def get_pedagogical_header(self, filename, module, description):
        """Cabecera estándar v0.2.5 para archivos Markdown."""
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
        # Header Superior
        header = tk.Frame(self.root, bg=self.color_accent, height=60)
        header.pack(fill="x", side="top")
        tk.Label(header, text="SIPA ENGINE | FACTORÍA DE DOCUMENTACIÓN v0.2.5", 
                 bg=self.color_accent, fg="white", font=("Segoe UI", 12, "bold")).pack(pady=15)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # --- TAB 1: DAILY ACTIVITY ---
        self.tab_daily = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_daily, text=" DAILY ACTIVITY ")
        
        self.daily_n1 = tk.StringVar(value=SIPA_LEVEL_1[0])
        self.daily_n2 = tk.StringVar(value="TAREA")
        self._create_dual_selector(self.tab_daily, self.daily_n1, self.daily_n2)
        
        self.daily_goals = self._add_text_field(self.tab_daily, "🎯 OBJETIVOS DEL DÍA", height=3)
        self.daily_hits = self._add_text_field(self.tab_daily, "✅ HITOS ALCANZADOS", height=5)
        self.daily_blocks = self._add_text_field(self.tab_daily, "⚠️ BLOQUEOS IDENTIFICADOS", height=3)
        
        tk.Button(self.tab_daily, text="PROCESAR DAILY Y ESCALAR A ROADMAP", 
                  bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"),
                  command=self.save_daily, pady=10).pack(pady=15, padx=20, fill="x")

        # --- TAB 2: TECHNICAL SPEC ---
        self.tab_spec = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_spec, text=" TECHNICAL SPEC ")
        
        self.spec_n1 = tk.StringVar(value=SIPA_LEVEL_1[0])
        self.spec_n2 = tk.StringVar(value="PROYECTO")
        self._create_dual_selector(self.tab_spec, self.spec_n1, self.spec_n2)
        
        self.spec_title = self._add_text_field(self.tab_spec, "📌 TÍTULO DE LA ESPECIFICACIÓN", height=1)
        self.spec_logic = self._add_text_field(self.tab_spec, "⚙️ LÓGICA DE NEGOCIO / FUNCIONALIDAD", height=7)
        self.spec_data = self._add_text_field(self.tab_spec, "📊 ESQUEMA DE DATOS", height=5)
        
        tk.Button(self.tab_spec, text="GRABAR ESPECIFICACIÓN TÉCNICA", 
                  bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"),
                  command=self.save_tech, pady=10).pack(pady=15, padx=20, fill="x")

        # --- TAB 3: CHAT HISTORY ---
        self.tab_chat = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_chat, text=" CHAT HISTORY ")
        
        self.chat_n1 = tk.StringVar(value=SIPA_LEVEL_1[0])
        self.chat_n2 = tk.StringVar(value="TAREA")
        self._create_dual_selector(self.tab_chat, self.chat_n1, self.chat_n2)
        
        self.chat_q = self._add_text_field(self.tab_chat, "❓ QUESTIONS (PREGUNTAS IA)", height=8)
        self.chat_a = self._add_text_field(self.tab_chat, "💡 ANSWERS (RESPUESTAS / INSIGHTS)", height=8)
        
        tk.Button(self.tab_chat, text="GUARDAR CONVERSACIÓN ESTRATÉGICA", 
                  bg=self.color_accent, fg="white", font=("Segoe UI", 10, "bold"),
                  command=self.save_chat, pady=10).pack(pady=15, padx=20, fill="x")

    def save_daily(self):
        n1, n2 = self.daily_n1.get(), self.daily_n2.get()
        ts_db = datetime.now().strftime("%Y-%m-%d")
        ts_file = datetime.now().strftime("%Y%m%d_%H%M")
        hits = self.daily_hits.get('1.0', tk.END).strip()
        
        # NOMENCLATURA: fecha+hora+tipo+nombre.md
        fname = f"{ts_file}_{n2.upper()}_DAILY.md"
        
        header = self.get_pedagogical_header(fname, n1, "Registro de actividad diaria.")
        body = (f"## 🎯 OBJETIVOS\n{self.daily_goals.get('1.0', tk.END).strip()}\n\n"
                f"## ✅ HITOS\n{hits}\n\n"
                f"## ⚠️ BLOQUEOS\n{self.daily_blocks.get('1.0', tk.END).strip()}\n")
        
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f:
            f.write(header + body)
        
        # Sincronización con Roadmap (usando el nuevo parámetro archivo)
        self.db.agregar_hito_roadmap(ts_db, n1, n2, f"Daily: {hits[:60]}...", "", fname)
        
        messagebox.showinfo("SIPA v0.2.5", "Sincronización Total: DB + MD")
        self._clear([self.daily_goals, self.daily_hits, self.daily_blocks])

    def save_tech(self):
        n1, n2 = self.spec_n1.get(), self.spec_n2.get()
        ts_db = datetime.now().strftime("%Y-%m-%d")
        ts_file = datetime.now().strftime("%Y%m%d_%H%M")
        title = self.spec_title.get('1.0', tk.END).strip()
        title_clean = title.replace(' ', '_')
        
        # NOMENCLATURA: fecha+hora+tipo+nombre.md
        fname = f"{ts_file}_{n2.upper()}_{title_clean}.md"
        
        header = self.get_pedagogical_header(fname, n1, f"Especificación: {title}")
        body = (f"## ⚙️ LÓGICA\n{self.spec_logic.get('1.0', tk.END).strip()}\n\n"
                f"## 📊 DATOS\n{self.spec_data.get('1.0', tk.END).strip()}\n")
        
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f:
            f.write(header + body)
            
        self.db.agregar_hito_roadmap(ts_db, n1, n2, f"Spec: {title}", "", fname)
        messagebox.showinfo("SIPA v0.2.5", "Documentación técnica persistida.")
        self._clear([self.spec_title, self.spec_logic, self.spec_data])

    def save_chat(self):
        n1, n2 = self.chat_n1.get(), self.chat_n2.get()
        ts_db = datetime.now().strftime("%Y-%m-%d")
        ts_file = datetime.now().strftime("%Y%m%d_%H%M")
        
        # NOMENCLATURA: fecha+hora+tipo+nombre.md
        fname = f"{ts_file}_{n2.upper()}_CHAT.md"
        
        header = self.get_pedagogical_header(fname, n1, "Historial de consulta IA.")
        body = (f"## ❓ PREGUNTA\n{self.chat_q.get('1.0', tk.END).strip()}\n\n"
                f"## 💡 RESPUESTA\n{self.chat_a.get('1.0', tk.END).strip()}\n")
        
        with open(os.path.join(self.knowledge_path, fname), "w", encoding="utf-8") as f:
            f.write(header + body)
            
        self.db.agregar_hito_roadmap(ts_db, n1, n2, f"Chat: {n1} Insight", "", fname)
        messagebox.showinfo("SIPA v0.2.5", "Conversación almacenada correctamente.")
        self._clear([self.chat_q, self.chat_a])

    def _clear(self, fields):
        for f in fields: f.delete('1.0', tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = SipaDocGUI(root)
    root.mainloop()

# Firmado: Daniel Miñana | SIPA v0.2.5 - Excellence Final Version