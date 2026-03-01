import tkinter as tk
from tkinter import ttk, messagebox
import os
from .base_tab import BaseTab

class ProfileTab(BaseTab):
    def __init__(self, parent, db, color_config):
        super().__init__(parent, db, color_config)
        self.fields = {} 
        self.create_widgets()

    def create_widgets(self):
        # Scroll para columna única
        canvas = tk.Canvas(self, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=950)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- SECCIÓN 1: IDENTIDAD Y ROL ---
        sec_id = self._create_section(self.scrollable_frame, "IDENTIDAD Y ROL")
        tk.Label(sec_id, text="TIPO DE USUARIO", bg=self.colors['panel'], font=("Segoe UI", 8, "bold"), fg=self.colors['accent']).pack(anchor="w", padx=20)
        self.cmb_type = ttk.Combobox(sec_id, state="readonly")
        self.cmb_type.pack(fill="x", padx=20, pady=(0, 10))
        self._load_user_types()

        self.fields["nombre_completo"] = self._add_text_field(sec_id, "NOMBRE COMPLETO", 1)
        self.fields["profesion_principal"] = self._add_text_field(sec_id, "PROFESIÓN PRINCIPAL", 1)
        self.fields["biografia_corta"] = self._add_text_field(sec_id, "BIOGRAFÍA CORTA", 3)

        # --- SECCIÓN 2: DOCUMENTACIÓN Y LEGAL ---
        sec_legal = self._create_section(self.scrollable_frame, "DOCUMENTACIÓN LEGAL")
        self.fields["dni"] = self._add_text_field(sec_legal, "DNI", 1)
        self.fields["n_seg_soc"] = self._add_text_field(sec_legal, "Nº SEGURIDAD SOCIAL", 1)
        self.fields["carnet_conducir"] = self._add_text_field(sec_legal, "CARNET CONDUCIR", 1)
        self.fields["datos_legales_json"] = self._add_text_field(sec_legal, "OTROS DATOS LEGALES (JSON)", 1)

        # --- SECCIÓN 3: FINANZAS ---
        sec_fin = self._create_section(self.scrollable_frame, "FINANZAS / VAULT")
        self.fields["cta_banco_1"] = self._add_text_field(sec_fin, "CUENTA BANCARIA 1", 1)
        self.fields["cta_banco_2"] = self._add_text_field(sec_fin, "CUENTA BANCARIA 2", 1)
        self.fields["card_number_1"] = self._add_text_field(sec_fin, "TARJETA 1", 1)
        self.fields["card_number_2"] = self._add_text_field(sec_fin, "TARJETA 2", 1)
        self.fields["datos_finanzas_json"] = self._add_text_field(sec_fin, "METADATOS FINANCIEROS (JSON)", 1)

        # --- SECCIÓN 4: CONTACTO Y REDES ---
        sec_contact = self._create_section(self.scrollable_frame, "CONTACTO Y REDES")
        self.fields["email_1"] = self._add_text_field(sec_contact, "EMAIL PRINCIPAL", 1)
        self.fields["email_2"] = self._add_text_field(sec_contact, "EMAIL SECUNDARIO", 1)
        self.fields["red_1"] = self._add_text_field(sec_contact, "RED SOCIAL 1", 1)
        self.fields["red_2"] = self._add_text_field(sec_contact, "RED SOCIAL 2", 1)
        self.fields["red_3"] = self._add_text_field(sec_contact, "RED SOCIAL 3", 1)
        self.fields["datos_contacto_json"] = self._add_text_field(sec_contact, "OTROS CONTACTOS (JSON)", 1)
        self.fields["redes_sociales_json"] = self._add_text_field(sec_contact, "ESTRUCTURA RRSS (JSON)", 1)
        self.fields["config_seguridad"] = self._add_text_field(sec_contact, "CONFIGURACIÓN SEGURIDAD", 1)

        # BOTÓN GUARDAR
        self.btn_save = tk.Button(self.scrollable_frame, text="GUARDAR EN DB Y KNOWLEDGE", 
                                 bg=self.colors['accent'], fg="white", 
                                 font=("Segoe UI", 12, "bold"), relief="flat",
                                 command=self.inject_data, pady=15)
        self.btn_save.pack(fill="x", padx=100, pady=40)

    def _create_section(self, parent, title):
        frame = tk.LabelFrame(parent, text=f" {title} ", bg=self.colors['panel'], 
                              fg=self.colors['accent'], font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        frame.pack(fill="x", pady=10, padx=20)
        return frame

    def _load_user_types(self):
        """Carga dinámica de roles desde la base de datos."""
        try:
            self.db._cursor.execute("SELECT id, nombre FROM type_user ORDER BY id ASC")
            tipos = self.db._cursor.fetchall()
            self.cmb_type['values'] = [f"{t[0]} - {t[1]}" for t in tipos]
            if tipos: self.cmb_type.current(0)
        except Exception as e:
            print(f"Error cargando tipos: {e}")
            self.cmb_type['values'] = ["1 - Administrador (Manual)"]

    def inject_data(self):
        """Guarda el perfil en sistema.db y genera el Markdown."""
        form_data = {k: v.get("1.0", "end-1c").strip() for k, v in self.fields.items()}
        
        # Obtenemos el ID del rol seleccionado
        try:
            type_id = self.cmb_type.get().split(" - ")[0]
        except:
            type_id = 1

        # Para tu test, forzamos ID 1 si es tu perfil
        user_id = 1 
        
        try:
            # 1. SQL dinámico para los campos actuales
            cols = ["id", "type_user_id"] + list(form_data.keys())
            placeholders = ", ".join(["?"] * len(cols))
            sql = f"INSERT OR REPLACE INTO user ({', '.join(cols)}) VALUES ({placeholders})"
            
            vals = [user_id, type_id] + list(form_data.values())
            
            self.db._cursor.execute(sql, vals)
            self.db._conn.commit()

            # 2. Generación del Markdown
            safe_name = form_data['nombre_completo'].replace(' ', '_').lower()
            data_for_md = form_data.copy()
            data_for_md['id'] = user_id
            data_for_md['type_user_id'] = type_id
            
            self._generate_markdown(data_for_md, safe_name)
            
            messagebox.showinfo("SIPA v0.2.6", f"¡Éxito! Usuario {user_id} guardado en DB y Knowledge.")
        except Exception as e:
            messagebox.showerror("Error al inyectar", str(e))

    def _generate_markdown(self, data, safe_name):
        path = os.path.join("data", "knowledge")
        if not os.path.exists(path): os.makedirs(path)
        file_path = os.path.join(path, f"user_{safe_name}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# 👤 PERFIL: {data['nombre_completo']}\n\n")
            for key, value in data.items():
                f.write(f"- **{key.upper()}**: {value}\n")