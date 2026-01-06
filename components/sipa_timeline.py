# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: components/sipa_timeline.py
# Módulo: SIPA-Vital (Diseño Simétrico Adaptativo)
# ==========================================================

import tkinter as tk
from tkinter import ttk
from datetime import datetime

class SipaTimeline(tk.Frame):
    def __init__(self, parent, db_manager):
        super().__init__(parent, bg="#f4f7f6")
        self.db = db_manager
        
        # 1. Configuración del Canvas dinámico
        self.canvas = tk.Canvas(self, bg="#f4f7f6", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f4f7f6")

        # 2. El "Ancla" de centrado automático
        # Creamos la ventana interna pero guardamos el ID para re-centrarla
        self.window_id = self.canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="n"
        )

        # 3. Eventos de redimensionamiento (La clave del centrado)
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.refresh_timeline()

    def _on_frame_configure(self, event):
        """Actualiza el área de scroll cuando cambia el contenido."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Re-centra la ventana cuando el usuario maximiza o cambia el tamaño."""
        canvas_width = event.width
        # Movemos el punto de anclaje de la ventana al centro exacto del canvas
        self.canvas.coords(self.window_id, canvas_width / 2, 0)

    def refresh_timeline(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        eventos = self.db.obtener_roadmap_filtrado(n1="TRAYECTORIA")
        self._add_master_header(eventos)

        if not eventos:
            tk.Label(self.scrollable_frame, text="Esperando nuevos hitos de trayectoria...", 
                     bg="#f4f7f6", font=("Segoe UI", 12, "italic")).pack(pady=50)
            return

        for ev in eventos:
            detalle_ext = self.db.obtener_detalle_roadmap(ev[0])
            self._render_clean_card(ev, detalle_ext)

    def _add_master_header(self, eventos):
        header = tk.Frame(self.scrollable_frame, bg="#ffffff", bd=1, relief="solid")
        header.pack(fill="x", pady=(20, 30), padx=50)
        
        tk.Label(header, text="CRONOGRAMA VITAL - TRAYECTORIA PROFESIONAL", 
                 font=("Segoe UI", 14, "bold"), bg="#ffffff", fg="#1a237e").pack(pady=15, padx=100)

    def _render_clean_card(self, data, detalle):
        _, fecha, _, n2, titulo, _ = data
        side = "left" if n2 == "LABORAL" else "right"
        color = "#0d47a1" if n2 == "LABORAL" else "#2e7d32"
        
        row = tk.Frame(self.scrollable_frame, bg="#f4f7f6")
        row.pack(fill="x", pady=15)

        row.columnconfigure(0, weight=1, uniform="group")
        row.columnconfigure(1, minsize=100) 
        row.columnconfigure(2, weight=1, uniform="group")

        time_frame = tk.Frame(row, bg="#f4f7f6")
        time_frame.grid(row=0, column=1)
        tk.Label(time_frame, text="●", fg=color, bg="#f4f7f6", font=("Arial", 14)).pack()
        tk.Label(time_frame, text=fecha[:7], font=("Consolas", 9, "bold"), bg="#f4f7f6", fg="#666").pack()

        card = tk.Frame(row, bg="#ffffff", bd=0)
        col_idx = 0 if side == "left" else 2
        card.grid(row=0, column=col_idx, sticky="ew", padx=30)

        border = tk.Frame(card, bg=color, width=4)
        border.pack(side=side, fill="y")

        inner = tk.Frame(card, bg="#ffffff", padx=15, pady=10)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text=titulo.upper(), font=("Segoe UI", 10, "bold"), 
                 bg="#ffffff", fg="#222", anchor="w").pack(fill="x")
        
        desc_corta = (detalle[:250] + '...') if len(detalle) > 250 else detalle
        tk.Label(inner, text=desc_corta, font=("Segoe UI", 9), bg="#ffffff", 
                 fg="#555", wraplength=300, justify="left").pack(anchor="w", pady=(5,0))