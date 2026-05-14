import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# ---------------------------------------------------------
# GESTIÓN DE RUTAS (SIPA_PROJECT ROOT)
# ---------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------------------------------------
# IMPORTS DESDE EL PAQUETE CORE Y EDITORES
# ---------------------------------------------------------
try:
    from core.persistence import PersistenceManager
    from core import config
    from editors.type_user_editor import TypeUserEditor
    from editors.user_editor import UserEditor  # Importamos el nuevo editor
except ImportError as e:
    print(f"CRITICAL ERROR: No se pudieron cargar los módulos.")
    print(f"Detalle: {e}")
    sys.exit(1)

# ---------------------------------------------------------
# CLASE PRINCIPAL: SipaCurMain
# ---------------------------------------------------------
class SipaCurMain(tk.Tk):
    def __init__(self, db_instance):
        super().__init__()
        self.db = db_instance 
        self.title("SIPAcur - Control & Edit Engine v0.2.6")
        self.geometry("1100x700")
        
        # Paleta Admin Oficial SIPA
        self.colors = {
            'bg': "#f8f9fa",
            'side': "#2c3e50",
            'accent': "#3498db",
            'text_side': "#ecf0f1",
            'border': "#dee2e6",
            'panel': "#ffffff"
        }
        
        self.setup_ui()

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=self.colors['side'], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="SIPAcur ADMIN", fg="white", bg=self.colors['side'], 
                 font=("Segoe UI", 12, "bold")).pack(pady=30)

        # Navegación - Botones Conectados
        self.add_nav_btn("🛡️ Roles (type_user)", self.show_type_user)
        self.add_nav_btn("👤 Gestión Usuarios", self.show_user) # Botón activado
        
        # Área Principal
        self.main_content = tk.Frame(self, bg=self.colors['bg'])
        self.main_content.pack(side="right", fill="both", expand=True)
        
        self.welcome_label = tk.Label(self.main_content, text="Seleccione un módulo lateral", 
                                     bg=self.colors['bg'], fg="#7f8c8d")
        self.welcome_label.pack(expand=True)

    def add_nav_btn(self, text, command):
        btn = tk.Button(self.sidebar, text=text, command=command,
                        bg=self.colors['side'], fg=self.colors['text_side'],
                        font=("Segoe UI", 10), anchor="w", padx=20, 
                        relief="flat", cursor="hand2", activebackground="#34495e")
        btn.pack(fill="x", pady=2)

    def _clear_main_content(self):
        """Limpia el contenedor principal antes de cargar un nuevo módulo."""
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def show_type_user(self):
        self._clear_main_content()
        editor = TypeUserEditor(self.main_content, self.db, self.colors)
        editor.pack(fill="both", expand=True)

    def show_user(self):
        """Carga el editor de perfiles de usuario (user_editor.py)."""
        self._clear_main_content()
        editor = UserEditor(self.main_content, self.db, self.colors)
        editor.pack(fill="both", expand=True)

# ---------------------------------------------------------
# ARRANQUE DEL SISTEMA
# ---------------------------------------------------------
if __name__ == "__main__":
    try:
        # Instancia única del Kernel
        db_manager = PersistenceManager() 
        
        if db_manager.is_connected():
            app = SipaCurMain(db_manager)
            app.mainloop()
        else:
            print("[-] No se pudo establecer conexión con el Kernel SIPA.")
            
    except Exception as e:
        print(f"Error fatal al iniciar la interfaz SIPAcur: {e}")