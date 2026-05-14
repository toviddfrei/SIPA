import tkinter as tk
from tkinter import ttk, messagebox
from .base_editor import BaseEditor

class TypeUserEditor(BaseEditor):
    def __init__(self, parent, db, colors):
        # Columnas según tu tabla: id, nombre, descripcion
        columns = [("id", "ID"), ("nombre", "ROL / PILAR"), ("descripcion", "DESCRIPCIÓN")]
        super().__init__(parent, db, colors, "type_user", columns)
        
        self._build_specific_form()
        self.bind_events()
        self.load_data()

    def _build_specific_form(self):
        """Campos de entrada para la tabla type_user."""
        frame = self.edit_frame
        
        tk.Label(frame, text="ID (Manual):", bg="white").grid(row=0, column=0, sticky="w", padx=5)
        self.ent_id = tk.Entry(frame, width=10)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(frame, text="Nombre del Rol:", bg="white").grid(row=0, column=2, sticky="w", padx=5)
        self.ent_nombre = tk.Entry(frame, width=25)
        self.ent_nombre.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(frame, text="Descripción:", bg="white").grid(row=1, column=0, sticky="w", padx=5)
        self.ent_desc = tk.Entry(frame, width=60)
        self.ent_desc.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="we")

    def bind_events(self):
        """Eventos de los botones de la clase madre."""
        self.btn_save.config(command=self.save_record)
        self.btn_new.config(command=self.clear_form)
        self.btn_delete.config(command=self.delete_record)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_selected)

    def load_data(self):
        """Lectura directa de la base de datos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # Usamos el cursor del PersistenceManager
            self.db._cursor.execute("SELECT id, nombre, descripcion FROM type_user ORDER BY id ASC")
            rows = self.db._cursor.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=(row['id'], row['nombre'], row['descripcion']))
        except Exception as e:
            messagebox.showerror("Error de Datos", f"No se pudo leer la tabla: {e}")

    def on_item_selected(self, event):
        """Carga el item seleccionado en el formulario."""
        selected = self.tree.selection()
        if not selected: return
        
        values = self.tree.item(selected[0])['values']
        self.clear_form()
        self.ent_id.insert(0, values[0])
        self.ent_nombre.insert(0, values[1])
        self.ent_desc.insert(0, values[2])

    def save_record(self):
        """Guarda o actualiza usando INSERT OR REPLACE."""
        id_val = self.ent_id.get()
        nom_val = self.ent_nombre.get()
        desc_val = self.ent_desc.get()

        if not id_val or not nom_val:
            messagebox.warning("Validación", "ID y Nombre son obligatorios.")
            return

        try:
            sql = "INSERT OR REPLACE INTO type_user (id, nombre, descripcion) VALUES (?, ?, ?)"
            self.db._cursor.execute(sql, (id_val, nom_val, desc_val))
            self.db._conn.commit()
            messagebox.showinfo("Éxito", "Registro guardado correctamente.")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    def delete_record(self):
        """Elimina el rol seleccionado."""
        id_val = self.ent_id.get()
        if not id_val: return

        if messagebox.askyesno("Confirmar", f"¿Eliminar el rol ID {id_val}?"):
            try:
                self.db._cursor.execute("DELETE FROM type_user WHERE id = ?", (id_val,))
                self.db._conn.commit()
                self.load_data()
                self.clear_form()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def clear_form(self):
        self.ent_id.delete(0, tk.END)
        self.ent_nombre.delete(0, tk.END)
        self.ent_desc.delete(0, tk.END)