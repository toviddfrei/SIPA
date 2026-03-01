import tkinter as tk
from tkinter import ttk
import sys
import os

# Asegurar alcance de los módulos internos (Subimos dos niveles a la raíz)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# --- IMPORT CORREGIDO: Usamos el núcleo actual ---
try:
    from core.persistence import PersistenceManager
except ImportError:
    from core.persistence_old import PersistenceManager # Backup por si acaso

from tabs.profile_tab import ProfileTab 
from tabs.daily_tab import DailyTab

class SipaDocMain:
    def __init__(self, root):
        self.root = root
        self.root.title("SIPA | DOCUMENTATION MODULE v0.2.6") # Actualizado a la par de SIPAcur
        self.root.geometry("1000x900")
        
        # Inicialización del Kernel de Datos
        self.db = PersistenceManager()
        # Nota: persistence.py ya conecta en el __init__ normalmente
        
        self.colors = {
            'bg': "#f4f4f4",
            'panel': "#ffffff",
            'accent': "#0078d4",
            'border': "#d1d1d1",
            'text': "#333333"
        }

        style = ttk.Style()
        style.theme_use('clam')
        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self.root, bg=self.colors['accent'], height=60)
        header.pack(fill="x", side="top")
        tk.Label(header, text="SIPA ENGINE | FACTORÍA v0.2.6", 
                 bg=self.colors['accent'], fg="white", 
                 font=("Segoe UI", 12, "bold")).pack(pady=15)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Inyección de Pestañas con la DB real
        self.tab_profile = ProfileTab(self.notebook, self.db, self.colors)
        self.notebook.add(self.tab_profile, text=" PERFIL ")
        
        self.tab_daily = DailyTab(self.notebook, self.db, self.colors)
        self.notebook.add(self.tab_daily, text=" DAILY ACTIVITY ")

if __name__ == "__main__":
    root = tk.Tk()
    app = SipaDocMain(root) 
    root.mainloop()