# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: main_dashboard.py
# Módulo: SIPAbap / SIPAdel (Interfaz de Control)
# Versión: 0.2.5 | Fecha: 05/01/2026
# Autor: Daniel Miñana
# ----------------------------------------------------------
# DESCRIPCIÓN: Panel Root principal. Implementa el cuaderno
# de pestañas para gestión modular y la visualización de
# telemetría en tiempo real desde la base de datos.
# Incluye visor de logs de auditoría (Caja Negra).
# ==========================================================

import tkinter as tk
from tkinter import ttk
from core.config import APP_TITLE, BG_COLOR_PRIMARY, NUMBER_VERSION
from core.persistence import PersistenceManager

class MainDashboard:
    def __init__(self, logs_inicio=None):
        # 1. Configuración de la Ventana Principal
        self.window = tk.Tk()
        # Mantenemos la versión 0.2.5 explícita según tus instrucciones
        self.window.title(f"{APP_TITLE} - Root Panel v0.2.5")
        self.window.geometry("1000x750")
        self.window.configure(bg="#1e1e1e") # Fondo oscuro profesional
        
        # Guardamos la telemetría recibida del arranque (Ignición)
        self.logs_recibidos = logs_inicio if logs_inicio else []
        
        # Inicializamos el gestor de base de datos para las consultas
        self.db = PersistenceManager()
        self.db.connect()

        # 2. Header Superior
        self.header = tk.Frame(self.window, bg=BG_COLOR_PRIMARY, height=60)
        self.header.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(self.header, text="SIPA ENGINE: PANEL DE CONTROL ESTRATÉGICO", 
                 fg="white", bg=BG_COLOR_PRIMARY, 
                 font=("Consolas", 14, "bold")).pack(pady=15)

        # 3. Contenedor de Pestañas (Notebook)
        # Esto permite que SIPA sea escalable (Telemetría, Citadel, Curator...)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # --- PESTAÑA 1: TELEMETRÍA Y RENDIMIENTO ---
        self.tab_telemetria = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_telemetria, text=" Telemetría / Salud ")
        self._build_telemetria_ui()

        # --- PESTAÑA 2: ESTADO DE MÓDULOS (Placeholder) ---
        self.tab_modulos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_modulos, text=" Estado de Módulos ")
        tk.Label(self.tab_modulos, text="Próximamente: Control de SIPAdoc y CITADEL", 
                 fg="gray").pack(pady=50)

    def _build_telemetria_ui(self):
        """Construye la interfaz de análisis de datos de arranque."""
        container = tk.Frame(self.tab_telemetria)
        container.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        # Título de sección: Métricas
        tk.Label(container, text="HISTÓRICO DE RENDIMIENTO (IGNICIÓN)", 
                 font=("Arial", 11, "bold")).pack(anchor="w", pady=(5, 5))

        # Tabla de datos (Treeview)
        columnas = ("fecha", "duracion", "estado")
        self.tabla = ttk.Treeview(container, columns=columnas, show="headings", height=8)
        
        self.tabla.heading("fecha", text="Timestamp de Sesión")
        self.tabla.heading("duracion", text="Duración Arranque (s)")
        self.tabla.heading("estado", text="Evaluación SIPAdel")
        
        self.tabla.column("fecha", width=300)
        self.tabla.column("duracion", width=150, anchor="center")
        self.tabla.column("estado", width=150, anchor="center")
        
        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        
        self.tabla.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        scrollbar.place(in_=self.tabla, relx=1.0, rely=0, relheight=1.0, bordermode="outside")

        # --- VISOR DE LOGS DE AUDITORÍA (Caja Negra) ---
        tk.Label(container, text="TELEMETRÍA DE AUDITORÍA (CAJA NEGRA)", 
                 font=("Consolas", 10, "bold"), fg="#555").pack(anchor="w", pady=(15, 5))
        
        self.txt_logs = tk.Text(container, height=10, bg="#000000", 
                               fg="#00FF00", font=("Consolas", 9),
                               padx=10, pady=10)
        self.txt_logs.pack(fill=tk.BOTH, expand=True)
        
        # Inyectamos los logs de la sesión actual (auditoría de archivos)
        for log in self.logs_recibidos:
            self.txt_logs.insert(tk.END, f"> {log}\n")
        
        self.txt_logs.see(tk.END) # Scroll automático al último log
        self.txt_logs.config(state=tk.DISABLED) # Bloqueo para integridad

        # Configuración de colores para alertas en tabla
        self.tabla.tag_configure('irregular', background='#ffe6e6', foreground='red')
        self.tabla.tag_configure('optimo', foreground='green')

        # Botón para refrescar datos desde la DB
        btn_refresh = tk.Button(container, text="ACTUALIZAR DATOS DB", 
                               command=self.cargar_datos, 
                               bg="#f0f0f0", relief="groove")
        btn_refresh.pack(side=tk.BOTTOM, pady=10)

        self.cargar_datos()

    def cargar_datos(self):
        """Extrae la información de sistema.db y la inyecta en la tabla."""
        # Limpiar datos previos
        for item in self.tabla.get_children():
            self.tabla.delete(item)
            
        # Consultar a la base de datos (SIPAdel)
        registros = self.db.obtener_metricas_recientes(limite=20)
        
        for reg in registros:
            # reg: (timestamp, duracion, estado)
            evaluacion = reg[2]
            tag = 'irregular' if evaluacion == 'IRREGULAR' else 'optimo'
            
            # Formateamos la duración a 4 decimales para mayor precisión
            duracion_fmt = f"{reg[1]:.4f}"
            
            self.tabla.insert("", tk.END, values=(reg[0], duracion_fmt, evaluacion), tags=(tag,))

    def run(self):
        """Inicia el bucle principal de la interfaz."""
        self.window.mainloop()