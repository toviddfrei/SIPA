# interface/sipadoc/tabs/base_tab.py
import tkinter as tk
from tkinter import ttk

class BaseTab(ttk.Frame):
    def __init__(self, parent, db, color_config):
        super().__init__(parent)
        self.db = db  # Inyección de la conexión única
        self.colors = color_config
        self.configure(style="TFrame") # Hereda el estilo visual
        
    def _add_text_field(self, parent, label, height=3):
        """Método estandarizado para todas las pestañas."""
        container = tk.Frame(parent, bg=self.colors['panel'])
        container.pack(fill="x", padx=20, pady=5)
        
        tk.Label(container, text=label, 
                 fg=self.colors['accent'], 
                 font=("Segoe UI", 9, "bold"), 
                 bg=self.colors['panel']).pack(anchor="w")
        
        t = tk.Text(container, height=height, font=("Consolas", 10), 
                    relief="solid", borderwidth=1, padx=10, pady=5)
        t.pack(fill="x")
        return t