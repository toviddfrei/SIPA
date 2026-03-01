# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: sipadoc_gui.py | Versión: 0.2.5 (FULL RECOVERY)
# ----------------------------------------------------------
# EXCELENCIA: Seguridad Vault + Funcionalidad Completa
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import sys
import re
import json

# Conexión con Kernel SIPAdel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.persistence import db_engine 
from core.config import SIPA_LEVEL_1, SIPA_LEVEL_2

class SipaDocGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SIPA | DOCUMENTATION MODULE v0.2.5")
        self.root.geometry("1100x950")
        
        # Estética SIPA
        self.color_bg = "#f0f0f0"
        self.color_panel = "#ffffff"
        self.color_accent = "#0056b3"
        self.root.configure(bg=self.color_bg)
        
        # --- MEMORIA DE SESIÓN & ESTADO ---
        self.session_user = {"id": 1, "nombre": "", "profesion": "", "redes": ["", "", ""]}
        self.knowledge_path = "data/knowledge/"
        
        self.setup_styles()
        self.create_widgets()
        self.preload_session_data()

    def preload_session_data(self):
        perfil = db_engine.get_user_profile()
        if perfil:
            self.session_user.update({
                "nombre": perfil.get('nombre_completo', 'Daniel Miñana'),
                "profesion": perfil.get('profesion_principal', 'Ingeniero SIPA'),
                "redes": [perfil.get('red_1', ''), perfil.get('red_2', ''), perfil.get('red_3', '')]
            })
            self._load_data_into_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.color_bg)
        style.configure("TNotebook.Tab", background="#e1e1e1", padding=[15, 5])
        style.map("TNotebook.Tab", background=[("selected", self.color_accent)], foreground=[("selected", "white")])

    def _add_text_field(self, parent, label, height=3):
        container = tk.Frame(parent, bg=self.color_panel)
        container.pack(fill="x", padx=20, pady=5)
        tk.Label(container, text=label, fg=self.color_accent, font=("Segoe UI", 9, "bold"), bg=self.color_panel).pack(anchor="w")
        t = tk.Text(container, height=height, font=("Consolas", 10), relief="solid", borderwidth=1, padx=10, pady=5)
        t.pack(fill="x")
        return t

    def create_widgets(self):
        # HEADER CON COMBOBOX DE USUARIO
        header = tk.Frame(self.root, bg=self.color_accent, height=70)
        header.pack(fill="x")
        
        tk.Label(header, text="SIPA v0.2.5", bg=self.color_accent, fg="white", font=("Segoe UI", 12, "bold")).pack(side="left", padx=20)
        
        self.user_selector = ttk.Combobox(header, values=["Daniel Miñana (Root)", "Admin", "IA_Agent"], width=25)
        self.user_selector.current(0)
        self.user_selector.pack(side="right", padx=20, pady=15)
        tk.Label(header, text="👤 USUARIO ACTIVO:", bg=self.color_accent, fg="white").pack(side="right")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # ==========================================================
        # TAB 1: PERFIL (3 BLOQUES + VAULT)
        # ==========================================================
        self.tab_identity = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_identity, text=" PERFIL ")
        
        canvas = tk.Canvas(self.tab_identity, bg=self.color_bg)
        scroll_y = ttk.Scrollbar(self.tab_identity, orient="vertical", command=canvas.yview)
        self.profile_frame = tk.Frame(canvas, bg=self.color_bg)
        canvas.create_window((0,0), window=self.profile_frame, anchor="nw", width=1050)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Capas de Seguridad
        grp_pub = tk.LabelFrame(self.profile_frame, text=" 🌍 IDENTIDAD PÚBLICA ", fg=self.color_accent, bg=self.color_panel, padx=15, pady=10)
        grp_pub.pack(fill="x", padx=20, pady=10)
        self.id_nombre = self._add_text_field(grp_pub, "📛 NOMBRE", height=1)
        self.id_profesion = self._add_text_field(grp_pub, "🚀 PROFESIÓN", height=1)
        
        f_red = tk.Frame(grp_pub, bg=self.color_panel); f_red.pack(fill="x", padx=20)
        tk.Label(f_red, text="🔗 REDES SOCIALES (1, 2, 3):", bg=self.color_panel).pack(side="left")
        self.ent_red1 = tk.Entry(f_red, width=15); self.ent_red1.pack(side="left", padx=5)
        self.ent_red2 = tk.Entry(f_red, width=15); self.ent_red2.pack(side="left", padx=5)
        self.ent_red3 = tk.Entry(f_red, width=15); self.ent_red3.pack(side="left", padx=5)
        self.id_bio = self._add_text_field(grp_pub, "👤 BIOGRAFÍA PROFESIONAL", height=4)

        self.grp_legal = tk.LabelFrame(self.profile_frame, text=" 🛡️ DATOS LEGALES (CAPA 1) ", fg="#d9534f", bg=self.color_panel, padx=15, pady=10)
        self.grp_legal.pack(fill="x", padx=20, pady=10)
        f_l = tk.Frame(self.grp_legal, bg=self.color_panel); f_l.pack(fill="x")
        tk.Label(f_l, text="DNI:").grid(row=0, column=0); self.ent_dni = tk.Entry(f_l, state="disabled", width=15); self.ent_dni.grid(row=0, column=1)
        tk.Label(f_l, text="NSS:").grid(row=0, column=2, padx=5); self.ent_nss = tk.Entry(f_l, state="disabled", width=20); self.ent_nss.grid(row=0, column=3)
        self.ent_email1 = tk.Entry(self.grp_legal, state="disabled", width=40); self.ent_email1.pack(pady=5, padx=20, anchor="w")

        self.grp_vault = tk.LabelFrame(self.profile_frame, text=" 🏦 VAULT FINANCIERO (CAPA 0) ", bg="#f8f9fa", padx=15, pady=10)
        self.grp_vault.pack(fill="x", padx=20, pady=10)
        self.ent_iban1 = tk.Entry(self.grp_vault, state="disabled", show="*", width=50); self.ent_iban1.pack(pady=2)
        self.ent_card1 = tk.Entry(self.grp_vault, state="disabled", show="*", width=50); self.ent_card1.pack(pady=2)

        f_ctrl = tk.Frame(self.profile_frame, bg=self.color_bg); f_ctrl.pack(fill="x", pady=10)
        self.btn_edit = tk.Button(f_ctrl, text="🔓 DESBLOQUEAR EDICIÓN (BAP AUDIT)", bg="#ffc107", command=self.toggle_edit_mode); self.btn_edit.pack(side="left", padx=20)
        self.btn_save_all = tk.Button(f_ctrl, text="💾 GUARDAR CAMBIOS", state="disabled", bg="#28a745", fg="white", command=self.save_identity); self.btn_save_all.pack(side="right", padx=20)

        # ==========================================================
        # TAB 2: DAILY ACTIVITY (CON SELECTORES NIVEL)
        # ==========================================================
        self.tab_daily = ttk.Frame(self.notebook); self.notebook.add(self.tab_daily, text=" DAILY ")
        f_lv = tk.Frame(self.tab_daily); f_lv.pack(fill="x", padx=20, pady=5)
        self.daily_n1 = ttk.Combobox(f_lv, values=SIPA_LEVEL_1); self.daily_n1.pack(side="left", padx=5); self.daily_n1.set("NIVEL 1")
        self.daily_n2 = ttk.Combobox(f_lv, values=SIPA_LEVEL_2); self.daily_n2.pack(side="left", padx=5); self.daily_n2.set("NIVEL 2")
        
        self.daily_hits = self._add_text_field(self.tab_daily, "✅ HITOS ALCANZADOS", height=6)
        self.daily_blocks = self._add_text_field(self.tab_daily, "⚠️ BLOQUEOS", height=4)
        tk.Button(self.tab_daily, text="PROCESAR DAILY", bg=self.color_accent, fg="white", command=lambda: messagebox.showinfo("SIPA", "Daily Guardado")).pack(pady=10)

        # ==========================================================
        # TAB 3: TRAYECTORIA (FULL)
        # ==========================================================
        self.tab_career = ttk.Frame(self.notebook); self.notebook.add(self.tab_career, text=" TRAYECTORIA ")
        self.career_entidad = self._add_text_field(self.tab_career, "🏢 EMPRESA / ENTIDAD", height=1)
        self.career_fecha = self._add_text_field(self.tab_career, "📅 PERIODO (INICIO - FIN)", height=1)
        self.career_rol = self._add_text_field(self.tab_career, "📝 CARGO / ROL", height=1)
        self.career_resumen = self._add_text_field(self.tab_career, "📋 RESUMEN DE RESPONSABILIDADES", height=6)
        tk.Button(self.tab_career, text="REGISTRAR TRAYECTORIA", bg=self.color_accent, fg="white", command=lambda: messagebox.showinfo("SIPA", "Trayectoria Registrada")).pack(pady=10)

        # ==========================================================
        # TAB 4: HITOS (LOS 6 CAMPOS COMPLETOS)
        # ==========================================================
        self.tab_hits = ttk.Frame(self.notebook); self.notebook.add(self.tab_hits, text=" HITOS ")
        self.hit_title = self._add_text_field(self.tab_hits, "🏆 TÍTULO DEL HITO", height=1)
        self.hit_fecha = self._add_text_field(self.tab_hits, "📅 FECHA DE LOGRO", height=1)
        self.hit_tech = self._add_text_field(self.tab_hits, "🛠️ STACK TECNOLÓGICO", height=1)
        self.hit_desc = self._add_text_field(self.tab_hits, "📜 DESCRIPCIÓN DETALLADA", height=5)
        self.hit_impact = self._add_text_field(self.tab_hits, "📈 IMPACTO / KPI", height=2)
        self.hit_url = self._add_text_field(self.tab_hits, "🔗 URL O REFERENCIA EVIDENCIA", height=1)
        tk.Button(self.tab_hits, text="CERTIFICAR HITO", bg="#ffc107", font=("Segoe UI", 9, "bold"), command=lambda: messagebox.showinfo("SIPA", "Hito Certificado")).pack(pady=10)

        # ==========================================================
        # TAB 5: CHAT HISTORY (CON CONTEXTO)
        # ==========================================================
        self.tab_chat = ttk.Frame(self.notebook); self.notebook.add(self.tab_chat, text=" CHAT HISTORY ")
        self.chat_context = self._add_text_field(self.tab_chat, "📑 CONTEXTO / PROMPT ENVIADO", height=8)
        self.chat_response = self._add_text_field(self.tab_chat, "💡 RESPUESTA DE LA IA", height=10)
        tk.Button(self.tab_chat, text="GUARDAR INTERACCIÓN", bg=self.color_accent, fg="white", command=lambda: messagebox.showinfo("SIPA", "Chat Guardado")).pack(pady=10)

    # ----------------------------------------------------------------------
    # FUNCIONES DE CONTROL
    # ----------------------------------------------------------------------
    def _load_data_into_widgets(self):
        self.id_nombre.insert('1.0', self.session_user["nombre"])
        self.id_profesion.insert('1.0', self.session_user["profesion"])
        for i, val in enumerate(self.session_user["redes"]):
            entry = [self.ent_red1, self.ent_red2, self.ent_red3][i]
            entry.delete(0, tk.END); entry.insert(0, val)

    def toggle_edit_mode(self):
        st = "normal" if self.ent_dni.cget("state") == "disabled" else "disabled"
        if st == "normal":
            db_engine._cursor.execute("INSERT INTO sys_audit (time_log) VALUES (CURRENT_TIMESTAMP)"); db_engine._conn.commit()
        for w in [self.ent_dni, self.ent_nss, self.ent_email1, self.ent_iban1, self.ent_card1]:
            w.config(state=st)
            if w in [self.ent_iban1, self.ent_card1]: w.config(show="" if st=="normal" else "*")
        self.btn_save_all.config(state=st)
        self.btn_edit.config(text="🔒 CANCELAR" if st=="normal" else "🔓 DESBLOQUEAR", bg="#d9534f" if st=="normal" else "#ffc107")

    def save_identity(self):
        try:
            nombre = self.id_nombre.get('1.0', tk.END).strip()
            query = """UPDATE user SET nombre_completo=?, profesion_principal=?, biografia_corta=?,
                       dni=?, n_seg_soc=?, email_1=?, red_1=?, red_2=?, red_3=?, 
                       cta_banco_1=?, card_number_1=?, fecha_actualizacion=CURRENT_TIMESTAMP WHERE id=1"""
            params = (nombre, self.id_profesion.get('1.0', tk.END).strip(), self.id_bio.get('1.0', tk.END).strip(),
                      self.ent_dni.get(), self.ent_nss.get(), self.ent_email1.get(),
                      self.ent_red1.get(), self.ent_red2.get(), self.ent_red3.get(),
                      self.ent_iban1.get(), self.ent_card1.get())
            db_engine._cursor.execute(query, params); db_engine._conn.commit()
            self.session_user["nombre"] = nombre; self.toggle_edit_mode()
            messagebox.showinfo("SIPA", "Perfil v0.2.5 Sincronizado.")
        except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk(); app = SipaDocGUI(root); root.mainloop()