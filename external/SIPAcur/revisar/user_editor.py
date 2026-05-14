import tkinter as tk
from tkinter import ttk, messagebox
from .base_editor import BaseEditor

class UserEditor(BaseEditor):
    def __init__(self, parent, db, colors):
        # Columnas básicas para verificar existencia
        columns = [("id", "ID"), ("nombre", "NOMBRE COMPLETO"), ("email", "EMAIL 1")]
        super().__init__(parent, db, colors, "user", columns)
        
        # Eliminamos botones de edición para este paso de "solo lectura"
        self.btn_save.pack_forget()
        self.btn_delete.pack_forget()
        
        self.load_data()

    def load_data(self):
        """Lectura pura de la tabla user."""
        # 1. Limpiar la vista actual
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            # 2. Consulta directa a la tabla
            self.db._cursor.execute("SELECT id, nombre_completo, email_1 FROM user")
            rows = self.db._cursor.fetchall()
            
            # 3. Chivato por consola para ver la realidad de la DB
            print("\n--- [AUDITORÍA DE TABLA USER] ---")
            print(f"Total registros encontrados: {len(rows)}")
            
            for row in rows:
                # Extraemos datos de forma segura (por índice)
                u_id = row[0]
                u_nom = row[1]
                u_mail = row[2]
                
                print(f"-> ID: {u_id} | Nombre: {u_nom} | Email: {u_mail}")
                
                # Insertar en la tabla visual
                self.tree.insert("", "end", values=(u_id, u_nom, u_mail))
            
            print("---------------------------------\n")
                
        except Exception as e:
            print(f"[-] ERROR AL LEER: {e}")
            messagebox.showerror("Error de Lectura", f"No se pudo acceder a 'user': {e}")

    def save_record(self): pass
    def delete_record(self): pass