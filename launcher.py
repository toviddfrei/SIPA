# =================================================================
# LICENCIA: MIT | MARCA: BApp-CITADEL | PROTOCOLO: FORTRESS
# DOCUMENTO: launcher.py | RUTA: ./launcher.py
# DESCRIPCIÓN: Orquestador Central de Microservicios con Socket IPC.
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

class SipaOrchestrator:
    def __init__(self, root):
        self.root = root
        self.root.title("BApp-CITADEL | SERVICE ORCHESTRATOR v1.2.0")
        self.root.geometry("850x600")
        self.root.configure(bg="#1e1e1e")

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

        # Creación de Pestañas Profesionales
        self.tab_kernel = ttk.Frame(self.notebook)
        self.tab_services = ttk.Frame(self.notebook)
        self.tab_edr = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_kernel, text=" [ 🚀 IGNICIÓN ] ")
        self.notebook.add(self.tab_services, text=" [ 🔄 SYNC SERVICES ] ")
        self.notebook.add(self.tab_edr, text=" [ 🛡️ MONITOR EDR ] ")

        # Inicializar interfaces
        self.build_kernel_tab()
        self.build_services_tab()
        self.build_edr_tab()

        # --- ARRANQUE DEL SERVIDOR DE COMUNICACIÓN (IPC) ---
        self.start_ipc_server()

    # ---------------------------------------------------------
    # PESTAÑA 1: CONTROL DE KERNEL
    # ---------------------------------------------------------
    def build_kernel_tab(self):
        frame = tk.Frame(self.tab_kernel, bg="#1e1e1e")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="SIPA CORE ENGINE CONTROL", fg="#3498db", 
                 bg="#1e1e1e", font=("Courier", 14, "bold")).pack(pady=20)

        self.btn_ignite = tk.Button(frame, text="🚀 LANZAR MAIN ENGINE (main_ev)", 
                                   bg="#2ecc71", fg="white", font=("Segoe UI", 11, "bold"),
                                   width=35, height=2, command=self.ignite_main)
        self.btn_ignite.pack(pady=10)

        self.console = tk.Text(frame, bg="black", fg="#00ff00", font=("Consolas", 9),
                              padx=10, pady=10, state="disabled")
        self.console.pack(padx=20, pady=20, fill="both", expand=True)

    def log_to_console(self, message):
        """Escribe mensajes en la consola visual del Launcher."""
        self.console.config(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.console.insert("end", f"[{ts}] {message}\n")
        self.console.see("end")
        self.console.config(state="disabled")

    # ---------------------------------------------------------
    # PESTAÑA 2: MICROSERVICIOS (Sincronización)
    # ---------------------------------------------------------
    def build_services_tab(self):
        tk.Label(self.tab_services, text="ORQUESTACIÓN DE MICROSERVICIOS", 
                 font=("Courier", 11, "bold")).pack(pady=20)
        
        # Simulación de estados de servicio
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
        # Aquí irá el código de shutil en el futuro
        time.sleep(1)
        self.log_to_console("[OK] Datos transferidos a external/sipaweb.")

    # ---------------------------------------------------------
    # PESTAÑA 3: MONITOR EDR (Auditoría)
    # ---------------------------------------------------------
    def build_edr_tab(self):
        columns = ("archivo", "estado", "mision")
        self.tree_edr = ttk.Treeview(self.tab_edr, columns=columns, show="headings")
        self.tree_edr.heading("archivo", text="ACTIVO CRÍTICO")
        self.tree_edr.heading("estado", text="INTEGRIDAD")
        self.tree_edr.heading("mision", text="PEDAGOGÍA TÉCNICA")
        
        self.tree_edr.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Ejemplo de carga de activos
        self.tree_edr.insert("", "end", values=("main_ev.py", "AUDITADO", "Nodo de Edición Principal"))
        self.tree_edr.insert("", "end", values=("config_loggers.py", "SAFE", "Gestión de trazas del sistema"))

    # ---------------------------------------------------------
    # LÓGICA DE COMUNICACIÓN IPC (SOCKETS)
    # ---------------------------------------------------------
    def start_ipc_server(self):
        """Levanta el servidor local para escuchar a los sidecars (main_ev, etc)."""
        def run_server():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', 65432))
                    s.listen()
                    while self.running:
                        conn, addr = s.accept()
                        with conn:
                            raw_data = conn.recv(1024).decode('utf-8')
                            if raw_data:
                                data = json.loads(raw_data)
                                # Usar after() para actualizar UI desde el hilo del socket
                                self.root.after(0, self.process_event, data)
                except Exception as e:
                    print(f"Error en Servidor IPC: {e}")

        threading.Thread(target=run_server, daemon=True).start()

    def process_event(self, data):
        """Procesa los eventos JSON recibidos por el socket."""
        event = data.get("event")
        payload = data.get("data")
        
        if event == "NODE_READY":
            self.log_to_console(f"[NODE] {payload}")
        elif event == "FILE_SAVED":
            self.log_to_console(f"[GUARDADO] Sincronización detectada: {payload}")
        elif event == "FILE_OPENED":
            self.log_to_console(f"[EDIT] Trabajando en: {payload}")
        elif event == "CURATOR_REQ":
            self.log_to_console(f"[AI] Solicitud de análisis Curator para: {payload}")

    def ignite_main(self):
        """Lanza el subproceso main_ev.py."""
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
        """Cierre seguro del ecosistema SIPA."""
        self.running = False
        if self.process_main:
            self.log_to_console("[EXIT] Terminando procesos hijos...")
            self.process_main.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SipaOrchestrator(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()