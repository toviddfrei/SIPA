# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automatizado
# Archivo: main_ev.py (Nodo de Edición - Sidecar Mode)
# ==========================================================

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json

# --- 1. PROTOCOLO DE SEGURIDAD Y AUDITORÍA (Sentinel) ---
try:
    from external.sentinel_fhs_CA import sentinel_v002_fhs_CA as sentinel
    if not sentinel.sonda.ejecutar_auditoria(sys.argv[0]):
        print("❌ [BLOQUEO FORENSE] Integridad comprometida.")
        sys.exit(1)
except ImportError:
    print("⚠️ Sentinel no encontrado. Continuando en modo desarrollo.")

# --- 2. CONFIGURACIÓN DE RUTAS Y LOGGERS ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from core.persistence_old import PersistenceManager
from core.logger.config_loggers import setup_logger

# ==========================================================
# CLASE PRINCIPAL: SIPA_UI_ENGINE
# ==========================================================
class SipaMainEngine(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Adaptación al Logger Genérico (Desempaquetado de Tupla)
        log_res = setup_logger()
        self.logger, self.log_memoria = log_res if isinstance(log_res, tuple) else (log_res, [])

        self.title("SIPA Engine v0.4.0 | Knowledge Editor Node")
        self.geometry("1250x850")
        
        # Conexión al Kernel de Persistencia
        self.db = PersistenceManager()
        self.db.connect()
        
        # Configuración de rutas de datos
        self.knowledge_dir = os.path.join(ROOT_DIR, "data", "knowledge")
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)

        # Paleta Admin Oficial SIPA
        self.colors = {
            'bg': "#f8f9fa",
            'side': "#2c3e50",
            'accent': "#3498db",
            'text_side': "#ecf0f1",
            'panel': "#ffffff",
            'border': "#dee2e6"
        }
        
        self.current_file_path = None
        self.setup_ui()
        
        # Notificar al Launcher que el motor ha arrancado
        self.notify_launcher("NODE_READY", "Editor de conocimiento operativo.")

    def notify_launcher(self, event_type, details):
        """Envía señales al Launcher (Orquestador) vía Socket Local."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5) # No bloquear si el launcher no está
                s.connect(('127.0.0.1', 65432))
                message = json.dumps({"event": event_type, "data": details})
                s.sendall(message.encode('utf-8'))
        except Exception:
            # Silencioso: El editor debe funcionar aunque el launcher esté cerrado
            pass

    def setup_ui(self):
        # SIDEBAR
        self.sidebar = tk.Frame(self, bg=self.colors['side'], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="SIPA SYSTEM", fg="white", bg=self.colors['side'], 
                 font=("Consolas", 12, "bold")).pack(pady=30)

        self.add_nav_btn("📂 Explorador MD", self.show_sipadoc_tree)
        self.add_nav_btn("📊 Telemetría", lambda: print("Módulo Telemetría"))
        
        # ÁREA DE CONTENIDO
        self.main_content = tk.Frame(self, bg=self.colors['bg'])
        self.main_content.pack(side="right", fill="both", expand=True)
        
        self.show_sipadoc_tree()

    def add_nav_btn(self, text, command):
        btn = tk.Button(self.sidebar, text=text, command=command,
                        bg=self.colors['side'], fg=self.colors['text_side'],
                        font=("Segoe UI", 10), anchor="w", padx=20, 
                        relief="flat", cursor="hand2", activebackground="#34495e")
        btn.pack(fill="x", pady=2)

    def _clear_main(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def show_sipadoc_tree(self):
        self._clear_main()
        self.paned = ttk.PanedWindow(self.main_content, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Contenedor del Árbol
        tree_container = tk.Frame(self.paned, bg="white")
        self.tree = ttk.Treeview(tree_container, selectmode="browse")
        self.tree.heading("#0", text="Directorio data/knowledge", anchor="w")
        sb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.paned.add(tree_container, weight=1)

        # Contenedor del Editor
        editor_container = tk.Frame(self.paned, bg="white", highlightbackground=self.colors['border'], highlightthickness=1)
        self.text_editor = tk.Text(editor_container, font=("Consolas", 11), undo=True, padx=15, pady=15, relief="flat")
        self.text_editor.pack(fill="both", expand=True)
        
        btn_frame = tk.Frame(editor_container, bg=self.colors['bg'])
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="💾 GUARDAR CAMBIOS", bg="#2ecc71", fg="white", 
                  font=("Segoe UI", 9, "bold"), command=self.save_content, pady=8).pack(side="left", fill="x", expand=True)
        
        tk.Button(btn_frame, text="🔍 ANALIZAR (CURATOR)", bg=self.colors['accent'], fg="white", 
                  font=("Segoe UI", 9), command=self.run_curator_analysis, pady=8).pack(side="left", fill="x", expand=True)
        
        self.paned.add(editor_container, weight=3)

        self.tree.bind("<<TreeviewSelect>>", self.on_file_select)
        self.populate_tree("", self.knowledge_dir)

    def populate_tree(self, parent, path):
        try:
            for item in sorted(os.listdir(path)):
                if item.startswith('.') or item == "__pycache__": continue
                full_path = os.path.join(path, item)
                node = self.tree.insert(parent, "end", text=item, open=False, values=(full_path,))
                if os.path.isdir(full_path):
                    self.populate_tree(node, full_path)
        except Exception as e:
            self.logger.error(f"Error al poblar árbol: {e}")

    def on_file_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        file_path = self.tree.item(selected[0])['values'][0]
        if os.path.isfile(file_path):
            self.current_file_path = file_path
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_editor.delete(1.0, tk.END)
                self.text_editor.insert(tk.END, content)
                self.notify_launcher("FILE_OPENED", os.path.basename(file_path))
            except Exception as e:
                messagebox.showerror("Error de lectura", str(e))

    def save_content(self):
        if not self.current_file_path:
            messagebox.showwarning("Atención", "Seleccione un archivo primero.")
            return
        try:
            content = self.text_editor.get(1.0, tk.END).strip()
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Notificación al Logger y al Launcher
            self.logger.info(f"Archivo guardado: {self.current_file_path}")
            self.notify_launcher("FILE_SAVED", os.path.basename(self.current_file_path))
            
            messagebox.showinfo("SIPA", "Sincronización de artefacto completada.")
        except Exception as e:
            self.logger.error(f"Fallo al guardar: {e}")
            messagebox.showerror("Error al guardar", str(e))

    def run_curator_analysis(self):
        if not self.current_file_path: return
        self.notify_launcher("CURATOR_REQ", os.path.basename(self.current_file_path))
        messagebox.showinfo("Curator", f"Analizando: {os.path.basename(self.current_file_path)}\n(Llamada a external/curator/ preparada)")

# --- ARRANQUE DEL NODO ---
if __name__ == "__main__":
    app = SipaMainEngine()
    app.mainloop()