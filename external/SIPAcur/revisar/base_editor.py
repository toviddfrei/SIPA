import tkinter as tk
from tkinter import ttk

class BaseEditor(tk.Frame):
    def __init__(self, parent, db, colors, table_name, columns):
        super().__init__(parent, bg=colors['bg'])
        self.db = db
        self.colors = colors
        self.table_name = table_name
        self.columns = columns # Lista de tuplas: (ID_interno, Texto_Cabecera)
        
        self._setup_base_layout()

    def _setup_base_layout(self):
        # 1. TÍTULO
        self.lbl_title = tk.Label(self, text=f"GESTIÓN DE {self.table_name.upper()}", 
                                 bg=self.colors['bg'], font=("Segoe UI", 14, "bold"))
        self.lbl_title.pack(pady=20, padx=20, anchor="w")

        # 2. TABLA (TREEVIEW)
        self.tree_frame = tk.Frame(self, bg="white")
        self.tree_frame.pack(fill="both", expand=True, padx=20)
        
        col_ids = [c[0] for c in self.columns]
        self.tree = ttk.Treeview(self.tree_frame, columns=col_ids, show="headings")
        
        for col_id, col_text in self.columns:
            self.tree.heading(col_id, text=col_text)
            self.tree.column(col_id, width=150)
        
        self.tree.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # 3. FORMULARIO DINÁMICO (Se rellena en la clase hija)
        self.edit_frame = tk.LabelFrame(self, text=" Edición de Datos ", bg="white", padx=20, pady=10)
        self.edit_frame.pack(fill="x", padx=20, pady=20)

        # 4. BOTONERA CRUD
        self.btn_box = tk.Frame(self, bg=self.colors['bg'])
        self.btn_box.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_new = tk.Button(self.btn_box, text="➕ NUEVO", bg="#27ae60", fg="white", relief="flat", padx=15)
        self.btn_new.pack(side="left", padx=5)
        
        self.btn_save = tk.Button(self.btn_box, text="💾 GUARDAR CAMBIOS", bg="#2980b9", fg="white", relief="flat", padx=15)
        self.btn_save.pack(side="left", padx=5)
        
        self.btn_delete = tk.Button(self.btn_box, text="🗑️ ELIMINAR", bg="#c0392b", fg="white", relief="flat", padx=15)
        self.btn_delete.pack(side="right", padx=5)