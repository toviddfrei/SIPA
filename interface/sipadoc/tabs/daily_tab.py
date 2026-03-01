import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab

class DailyTab(BaseTab):
    def __init__(self, parent, db, color_config):
        super().__init__(parent, db, color_config)
        self.create_widgets()

    def create_widgets(self):
        # Contenedor con fondo gris claro
        main_frame = tk.Frame(self, bg=self.colors['bg'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Panel Blanco para el contenido
        panel = tk.Frame(main_frame, bg=self.colors['panel'], 
                         highlightbackground=self.colors['border'], highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=10, pady=10)

        # Título con color de marca
        tk.Label(panel, text="REGISTRO DE ACTIVIDAD DIARIA", 
                 fg=self.colors['accent'], bg=self.colors['panel'], 
                 font=("Segoe UI", 12, "bold")).pack(pady=(15, 10))

        # Campos usando el método heredado de BaseTab
        self.txt_hitos = self._add_text_field(panel, "HITOS LOGRADOS (N1/N2)", height=10)
        self.txt_objetivos = self._add_text_field(panel, "OBJETIVOS PRÓXIMA SESIÓN", height=5)

        # Botón de Inyección
        btn_save = tk.Button(panel, text="💾 REGISTRAR ACTIVIDAD", 
                            bg=self.colors['accent'], fg="white", 
                            font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=10)
        btn_save.pack(pady=20)