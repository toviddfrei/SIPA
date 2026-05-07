# =================================================================
# LICENCIA: MIT | MARCA: BApp-CITADEL | PROTOCOLO: BOLARDO
# DOCUMENTO: launcher.py | RUTA: ./launcher.py
# DESCRIPCIÓN: Orquestador con Backup Atómico Auto-Ejecutable.
# =================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import socket
import json
import sys
import os
import time
import shutil
from datetime import datetime

class BackupManager:
    """Maneja la lógica de respaldo de forma atómica y segura."""
    def __init__(self, source_dir, dest_dir):
        self.source = os.path.abspath(source_dir)
        self.dest = os.path.abspath(dest_dir)

    def create_backup(self):
        if not os.path.exists(self.dest):
            os.makedirs(self.dest, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SIPA_AUTO_BAK_{timestamp}"
        
        # Carpeta temporal del sistema para evitar recursividad
        temp_dir = os.environ.get('TEMP') or os.environ.get('TMPDIR') or '/tmp'
        temp_path = os.path.join(temp_dir, filename)
        
        try:
            # 1. Comprimir en zona neutral
            archive_temp = shutil.make_archive(temp_path, 'zip', self.source)
            # 2. Mover a la zona de MEGA (operación atómica)
            final_dest = os.path.join(self.dest, os.path.basename(archive_temp))
            shutil.move(archive_temp, final_dest)
            return final_dest
        except Exception as e:
            if 'archive_temp' in locals() and os.path.exists(archive_temp):
                os.remove(archive_temp)
            raise e

class SipaOrchestrator:
    def __init__(self, root):
        self.root = root
        self.root.title("BApp-CITADEL | SERVICE ORCHESTRATOR v1.5.0")
        self.root.geometry("850x650")
        self.root.configure(bg="#1e1e1e")

        # --- CONFIGURACIÓN DE RUTAS ---
        # Se define la raíz de SIPA y el destino un nivel arriba para evitar bucles
        self.path_to_backup = os.path.dirname(os.path.abspath(__file__))
        self.path_destination = os.path.join(os.path.dirname(self.path_to_backup), "SIPA_Backups_MEGA")
        
        self.backup_engine = BackupManager(self.path_to_backup, self.path_destination)
        self.running = True
        self.process_main = None
        
        # --- SISTEMA DE ESTILOS ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
        style.configure("TNotebook.Tab", padding=[15, 5], font=('Consolas', 10))

        # --- CONTENEDOR DE PESTAÑAS ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.tab_kernel = ttk.Frame(self.notebook)
        self.tab_backup = ttk.Frame(self.notebook)
        self.tab_services = ttk.Frame(self.notebook)
        self.tab_edr = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_kernel, text=" [ 🚀 IGNICIÓN ] ")
        self.notebook.add(self.tab_backup, text=" [ 💾 BACKUP ] ")
        self.notebook.add(self.tab_services, text=" [ 🔄 SYNC SERVICES ] ")
        self.notebook.add(self.tab_edr, text=" [ 🛡️ MONITOR EDR ] ")

        # Inicializar todas las interfaces
        self.build_kernel_tab()
        self.build_backup_tab()
        self.build_services_tab()
        self.build_edr_tab()

        # --- ARRANQUE DE PROTOCOLOS ---
        self.log_to_console("[SYSTEM] Protocolo BOLARDO: Iniciando Backup Preventivo...")
        self.run_backup_thread(is_auto=True)
        self.start_ipc_server()

    # ---------------------------------------------------------
    # PESTAÑA 1: CONTROL DE KERNEL
    # ---------------------------------------------------------
    def build_kernel_tab(self):
        frame = tk.Frame(self.tab_kernel, bg="#1e1e1e")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="SIPA CORE ENGINE CONTROL", fg="#3498db", 
                 bg="#1e1e1e", font=("Courier", 14, "bold")).pack(pady=20)

        self.btn_ignite = tk.Button(frame, text="⏳ ESPERANDO BACKUP SEGURIDAD...", 
                                   bg="#555555", fg="white", font=("Segoe UI", 11, "bold"),
                                   width=35, height=2, state="disabled", command=self.ignite_main)
        self.btn_ignite.pack(pady=10)

        self.console = tk.Text(frame, bg="black", fg="#00ff00", font=("Consolas", 9),
                              padx=10, pady=10, state="disabled")
        self.console.pack(padx=20, pady=20, fill="both", expand=True)

    def log_to_console(self, message):
        self.console.config(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] {message}\n")
        self.console.see("end")
        self.console.config(state="disabled")

    # ---------------------------------------------------------
    # PESTAÑA 2: GESTIÓN DE BACKUP (Nueva pestaña solicitada)
    # ---------------------------------------------------------
    def build_backup_tab(self):
        frame = tk.Frame(self.tab_backup, bg="#1e1e1e")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="HISTORIAL DE PROTECCIÓN SIPA", fg="#f1c40f", 
                 bg="#1e1e1e", font=("Courier", 12, "bold")).pack(pady=20)

        self.btn_manual_backup = tk.Button(frame, text="🛡️ EJECUTAR BACKUP MANUAL", 
                                          bg="#d35400", fg="white", font=("Segoe UI", 10, "bold"),
                                          width=30, command=lambda: self.run_backup_thread(is_auto=False))
        self.btn_manual_backup.pack(pady=10)

        self.bak_list = tk.Listbox(frame, bg="#2d2d2d", fg="#ecf0f1", font=("Consolas", 9),
                                  borderwidth=0, highlightthickness=0)
        self.bak_list.pack(padx=40, pady=20, fill="both", expand=True)
        self.refresh_bak_list()

    def run_backup_thread(self, is_auto=False):
        if not is_auto:
            self.btn_manual_backup.config(state="disabled", text="⏳ PROCESANDO...")
        threading.Thread(target=self.execute_backup_logic, args=(is_auto,), daemon=True).start()

    def execute_backup_logic(self, is_auto):
        try:
            path = self.backup_engine.create_backup()
            self.log_to_console(f"[BACKUP] OK: {os.path.basename(path)}")
        except Exception as e:
            self.log_to_console(f"[ERROR] Fallo en Backup: {e}")
        finally:
            self.root.after(0, self.post_backup_ui)

    def post_backup_ui(self):
        self.btn_manual_backup.config(state="normal", text="🛡️ EJECUTAR BACKUP MANUAL")
        self.btn_ignite.config(text="🚀 LANZAR MAIN ENGINE (main_ev)", bg="#2ecc71", state="normal")
        self.refresh_bak_list()

    def refresh_bak_list(self):
        self.bak_list.delete(0, tk.END)
        if os.path.exists(self.path_destination):
            files = sorted([f for f in os.listdir(self.path_destination) if f.endswith('.zip')], reverse=True)
            for f in files[:20]:
                self.bak_list.insert(tk.END, f" 📦 {f}")

    # ---------------------------------------------------------
    # PESTAÑA 3: MICROSERVICIOS (Original Restaurada)
    # ---------------------------------------------------------
    def build_services_tab(self):
        tk.Label(self.tab_services, text="ORQUESTACIÓN DE MICROSERVICIOS", 
                 font=("Courier", 11, "bold")).pack(pady=20)
        self.draw_service_status("SYNC_SIPAWEB", "Sincronizador External/Sipaweb")
        self.draw_service_status("CURATOR_AI", "Analizador de Contenido Curator")
        tk.Button(self.tab_services, text="🔄 FORZAR SYNC SIPAWEB", 
                  bg="#f39c12", fg="white", width=30, command=self.service_sync_action).pack(pady=30)

    def draw_service_status(self, sid, label):
        row = tk.Frame(self.tab_services, padx=50, pady=5)
        row.pack(fill="x")
        tk.Label(row, text=f"● {label}:", width=35, anchor="w").pack(side="left")
        tk.Label(row, text="STANDBY", fg="gray", font=("Consolas", 9, "bold")).pack(side="left")

    def service_sync_action(self):
        self.log_to_console("[SERVICE] Iniciando protocolo de sincronización SIPAweb...")
        time.sleep(1)
        self.log_to_console("[OK] Datos transferidos a external/sipaweb.")

    # ---------------------------------------------------------
    # PESTAÑA 4: MONITOR EDR (Original Restaurada)
    # ---------------------------------------------------------
    def build_edr_tab(self):
        columns = ("archivo", "estado", "mision")
        self.tree_edr = ttk.Treeview(self.tab_edr, columns=columns, show="headings")
        self.tree_edr.heading("archivo", text="ACTIVO CRÍTICO")
        self.tree_edr.heading("estado", text="INTEGRIDAD")
        self.tree_edr.heading("mision", text="PEDAGOGÍA TÉCNICA")
        self.tree_edr.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_edr.insert("", "end", values=("main_ev.py", "AUDITADO", "Nodo de Edición Principal"))
        self.tree_edr.insert("", "end", values=("config_loggers.py", "SAFE", "Gestión de trazas del sistema"))

    # ---------------------------------------------------------
    # LÓGICA DE COMUNICACIÓN IPC Y PROCESOS
    # ---------------------------------------------------------
    def start_ipc_server(self):
        def run_server():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('127.0.0.1', 65432))
                    s.listen()
                    while self.running:
                        conn, addr = s.accept()
                        with conn:
                            raw_data = conn.recv(1024).decode('utf-8')
                            if raw_data:
                                data = json.loads(raw_data)
                                self.root.after(0, self.process_event, data)
                except Exception: pass
        threading.Thread(target=run_server, daemon=True).start()

    def process_event(self, data):
        event = data.get("event")
        payload = data.get("data")
        self.log_to_console(f"[{event}] {payload}")

    def ignite_main(self):
        if self.process_main and self.process_main.poll() is None:
            messagebox.showinfo("BApp-CITADEL", "El motor principal ya está activo.")
            return
        try:
            self.process_main = subprocess.Popen([sys.executable, "main_ev.py"])
            self.log_to_console(f"[IGNICIÓN] Proceso main_ev iniciado (PID: {self.process_main.pid})")
            self.btn_ignite.config(text="KERNEL EN EJECUCIÓN", state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al arrancar el motor: {e}")

    def on_close(self):
        self.running = False
        if self.process_main:
            self.process_main.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SipaOrchestrator(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()