import sys
import os
import re
import markdown
# Importaciones corregidas para compatibilidad total con PySide6 y sipa.py
from PySide6.QtWidgets import (
    QWidget, QTextEdit, QTextBrowser, QVBoxLayout, 
    QHBoxLayout, QFileDialog, QToolBar, QLabel, QTabWidget, QSplitter, QStyle, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QTextCursor, QPdfWriter, QPageSize

# --- CONFIGURACIÓN DE RUTAS DE LATIDO (Heartbeat) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
NOMBRE_SCRIPT = os.path.splitext(os.path.basename(__file__))[0]
ARCHIVO_LIVE = os.path.join(CURRENT_DIR, f".{NOMBRE_SCRIPT}.live")

THEME_SIPA_FINAL = """
    body { 
        font-family: 'Segoe UI', Arial, sans-serif; 
        padding: 30px; background-color: #ffffff; color: #222222; 
        line-height: 1.5; white-space: pre-wrap;
    }
    h1 { color: #005fb8; border-bottom: 1px solid #dddddd; padding-bottom: 5px; }
    h2 { color: #005fb8; margin-top: 20px; border-bottom: 1px solid #eeeeee; }
    pre { background-color: #f4f4f4; padding: 15px; border-radius: 5px; border: 1px solid #cccccc; font-family: 'Consolas', monospace; font-size: 12px; }
    code { background-color: #eeeeee; color: #d14; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
    th, td { border: 1px solid #cccccc; padding: 8px; text-align: left; }
    th { background-color: #f9f9f9; }
    blockquote { border-left: 5px solid #005fb8; background: #f0f7ff; margin: 0; padding: 10px 15px; font-style: italic; }
"""

class EditorTab(QWidget):
    def __init__(self, parent_editor, file_path=None):
        super().__init__()
        self.parent_editor = parent_editor
        self.file_path = file_path
        self.init_ui()
        if file_path:
            self.load_file(file_path)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.textChanged.connect(self.update_preview)
        self.editor.textChanged.connect(self.parent_editor.update_stats)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        layout.addWidget(self.splitter)

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.editor.setPlainText(f.read())
        except Exception as e:
            print(f"Error cargando archivo: {e}")

    def update_preview(self):
        raw_text = self.editor.toPlainText()
        clean_text = re.sub(r'^---.*?---\s*', '', raw_text, flags=re.DOTALL)
        html = markdown.markdown(clean_text, extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'])
        full_html = f"<html><head><style>{THEME_SIPA_FINAL}</style></head><body>{html}</body></html>"
        self.preview.setHtml(full_html)


class SIPAMarkdownEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Levantar señal de vida del servicio
        self.crear_senal_vida()
        self.init_ui()

    def crear_senal_vida(self):
        """Crea la señal física en disco de que el servicio está corriendo."""
        try:
            with open(ARCHIVO_LIVE, 'w') as f:
                f.write("RUNNING")
        except Exception as e:
            print(f"Error al escribir señal de vida en Editor: {e}")

    def borrar_senal_vida(self):
        """Limpia el token en disco para actualizar el monitor."""
        try:
            if os.path.exists(ARCHIVO_LIVE):
                os.remove(ARCHIVO_LIVE)
        except Exception as e:
            print(f"Error al borrar señal de vida en Editor: {e}")

    def closeEvent(self, event):
        """Intercepta el cierre de la ventana/pestaña para la detección."""
        self.borrar_senal_vida()
        event.accept()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = QToolBar("SIPA Editor Toolbar")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolbar.setStyleSheet("background: #f8f9fa; border-bottom: 1px solid #ddd; color: #333;")
        layout.addWidget(self.toolbar)

        self.add_btn("Nuevo", QStyle.StandardPixmap.SP_FileIcon, self.add_new_tab)
        self.add_btn("Abrir", QStyle.StandardPixmap.SP_DialogOpenButton, self.file_open)
        self.add_btn("Guardar", QStyle.StandardPixmap.SP_DialogSaveButton, self.file_save)
        self.add_btn("Como...", QStyle.StandardPixmap.SP_DriveHDIcon, self.file_save_as)
        self.toolbar.addSeparator()
        
        # Formato
        act_bold = QAction("Negrita", self)
        act_bold.triggered.connect(lambda: self.current_insert("**", "**"))
        self.toolbar.addAction(act_bold)

        act_italic = QAction("Itálica", self)
        act_italic.triggered.connect(lambda: self.current_insert("*", "*"))
        self.toolbar.addAction(act_italic)

        self.toolbar.addAction(QAction("🔗 Link", self, triggered=lambda: self.current_insert("[", "](url)")))
        self.toolbar.addAction(QAction("</> Código", self, triggered=lambda: self.current_insert("```\n", "\n```")))
        self.toolbar.addAction(QAction("📊 Tabla", self, triggered=self.insert_table))
        self.toolbar.addSeparator()

        self.add_btn("HTML", QStyle.StandardPixmap.SP_DialogHelpButton, self.export_html)
        self.add_btn("PDF", QStyle.StandardPixmap.SP_FileLinkIcon, self.export_pdf)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tabs)

        self.add_new_tab()

    def add_btn(self, text, pixmap, func):
        action = QAction(self.style().standardIcon(pixmap), text, self)
        action.triggered.connect(func)
        self.toolbar.addAction(action)

    def add_new_tab(self, path=None):
        name = os.path.basename(path) if path else "Sin Título"
        new_tab = EditorTab(self, path)
        index = self.tabs.addTab(new_tab, name)
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.current_tab().editor.clear()
            self.current_tab().file_path = None
            self.tabs.setTabText(0, "Sin Título")

    def current_tab(self):
        return self.tabs.currentWidget()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", "Markdown (*.md *.txt)")
        if path: self.add_new_tab(path)

    def file_save(self):
        tab = self.current_tab()
        if not tab.file_path:
            self.file_save_as()
        else:
            self._save_to_disk(tab.file_path)

    def file_save_as(self):
        tab = self.current_tab()
        path, _ = QFileDialog.getSaveFileName(self, "Guardar como...", "", "Markdown (*.md)")
        if path:
            if not path.endswith('.md'): path += '.md'
            tab.file_path = path
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))
            self._save_to_disk(path)

    def _save_to_disk(self, path):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.current_tab().editor.toPlainText())
        except Exception as e:
            print(f"Error al guardar: {e}")

    def current_insert(self, prefix, suffix):
        cursor = self.current_tab().editor.textCursor()
        cursor.insertText(f"{prefix}{cursor.selectedText()}{suffix}")

    def insert_table(self):
        self.current_tab().editor.insertPlainText("\n| Tit | Tit |\n| --- | --- |\n| Val | Val |\n")

    def update_stats(self):
        pass

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar HTML", "", "HTML (*.html)")
        if path:
            if not path.endswith('.html'): path += '.html'
            raw = self.current_tab().editor.toPlainText()
            clean = re.sub(r'^---.*?---\s*', '', raw, flags=re.DOTALL)
            html = markdown.markdown(clean, extensions=['tables', 'fenced_code'])
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"<html><head><style>{THEME_SIPA_FINAL}</style></head><body>{html}</body></html>")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar PDF", "", "PDF (*.pdf)")
        if path:
            if not path.endswith('.pdf'): path += '.pdf'
            writer = QPdfWriter(path)
            # Solución al error de sintaxis/mapeo de PySide6 para tamaño A4
            writer.setPageSize(QPageSize(QPageSize.A4))
            self.current_tab().preview.print(writer)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = SIPAMarkdownEditor()
    # Le indicamos que se comporte como ventana independiente si se ejecuta directo
    editor.setWindowFlags(Qt.Window)
    editor.setWindowTitle("SIPA | Editor de Documentación Markdown")
    editor.resize(1024, 768)
    editor.show()
    
    codigo_salida = app.exec()
    
    # Asegurar la destrucción del latido por si falla la ventana
    try:
        if os.path.exists(ARCHIVO_LIVE):
            os.remove(ARCHIVO_LIVE)
    except:
        pass
        
    sys.exit(codigo_salida)