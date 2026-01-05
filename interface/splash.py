import tkinter as tk
from core.config import APP_TITLE, BG_COLOR_PRIMARY, NUMBER_VERSION

class SipaSplash:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Sin bordes
        self.root.geometry("500x350+500+300")
        self.root.configure(bg=BG_COLOR_PRIMARY)
        
        # Título
        tk.Label(self.root, text=APP_TITLE, fg="white", bg=BG_COLOR_PRIMARY, 
                 font=("Arial", 18, "bold")).pack(pady=20)
        
        # Consola de Logs (Matrix style)
        self.log_widget = tk.Text(self.root, height=10, bg="black", fg="#00FF00", 
                                  font=("Consolas", 10), padx=10, pady=10)
        self.log_widget.pack(padx=20, fill=tk.BOTH)
        
        self.root.update()

    def update_status(self, message):
        self.log_widget.insert(tk.END, f"[*] {message}\n")
        self.log_widget.see(tk.END)
        self.root.update()

    def finalize(self):
        self.root.destroy()