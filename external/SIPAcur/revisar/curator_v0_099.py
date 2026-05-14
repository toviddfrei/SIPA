# ==========================================================
# PROYECTO SIPA - SISTEMA DE INTELIGENCIA DE PERFIL AUTOMATIZADO
# Módulo: DocCurator (Curador de Inteligencia Profesional)
# Versión: 1.0.9 | Estado: FILTRO DE SEGURIDAD /POSTS/PUBLIC/
# ==========================================================

import os
import re
import hashlib
import logging
import sys
from datetime import datetime
from collections import Counter

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("SIPAcur")

try:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
except ImportError:
    print("❌ Error: fpdf2 no instalado. Ejecuta: pip install fpdf2")
    sys.exit(1)

class PDF_Engine(FPDF):
    def header(self):
        self.set_font("helvetica", 'B', 8); self.set_text_color(150)
        self.cell(0, 10, 'SIPAWEB ECOSYSTEM | DOSSIER PROFESIONAL FILTRADO', align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def footer(self):
        self.set_y(-15); self.set_font("helvetica", 'I', 8); self.set_text_color(170)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')

class DocCurator:
    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        # La salida siempre a data/output
        self.pdf_output_path = os.path.join(os.path.dirname(self.root_path), "output")
        os.makedirs(self.pdf_output_path, exist_ok=True)

        self.EXCLUDE_NAMES = {'__pycache__', '.git', 'venv', 'node_modules', 'old'}
        self.STOPWORDS = {"este", "esta", "para", "como", "pero", "donde", "cuando", "desde", "todo", "con"}
        
        self.global_counter = Counter()
        self.milestones = []
        
        self.contacto = {
            "nombre": "DANIEL MIÑANA MONTERO",
            "puesto": "Técnico IT / Logística / Administración",
            "email": "mimodbland@gmail.com",
            "telefono": "+34 603 399 703",
            "linkedin": "www.linkedin.com/in/danielminanamontero",
            "ubicacion": "España"
        }
        self.perfiles_activos = ["tecnologico", "logistica", "administracion"]

    def extract_duration(self, content):
        match = re.search(r'Duración en meses\s*[\*]*\s*[:]?\s*(.*)', content, re.IGNORECASE)
        if match:
            valor = match.group(1).replace('*', '').replace('meses', '').strip()
            return f"{valor} meses"
        return "N/D"

    def sanitize_for_pdf(self, text):
        if not text: return ""
        text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
        text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        chars = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ñ':'n','Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U','Ñ':'N','•':'-'}
        for k, v in chars.items(): text = text.replace(k, v)
        return text.encode('latin-1', 'replace').decode('latin-1').replace('`', '').strip()

    def process_docs(self):
        print(f"\n{'='*95}\n 🔍 ESCANEO DE SEGURIDAD (SOLO /POSTS/PUBLIC/): {self.root_path}\n{'='*95}")
        print(f"{'ARCHIVO':<40} | {'PESO':<8} | {'HASH':<8} | {'ESTADO'}")
        print(f"{'-'*95}")

        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_NAMES]
            
            # --- FILTRO CRÍTICO ---
            # Solo procesamos si la ruta contiene 'posts/public'
            is_public_path = "posts/public" in root.replace("\\", "/")

            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    
                    if not is_public_path:
                        # Ignoramos silenciosamente o listamos como privado
                        continue

                    try:
                        stats = os.stat(path)
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            raw = f.read()
                        
                        file_hash = hashlib.sha256(raw.encode()).hexdigest()[:8]
                        meta = self.extract_metadata(raw)
                        
                        # ADN
                        content_clean = re.sub(r'^---\s*\n.*?\n---\s*\n', '', raw, flags=re.DOTALL)
                        words = re.findall(r'\b\w{4,}\b', content_clean.lower())
                        self.global_counter.update([w for w in words if w not in self.STOPWORDS])

                        print(f"{file[:40]:<40} | {round(stats.st_size/1024,1):>5} KB | {file_hash:<8} | [PUBLICO]")

                        self.milestones.append({
                            "is_training": "formativa" in path.lower(),
                            "content": content_clean,
                            "meta": meta,
                            "date": meta["fecha_orden"]
                        })
                    except Exception as e: print(f"Error {file}: {e}")
        
        self.milestones.sort(key=lambda x: x['date'], reverse=True)
        self.print_console_dna()

    def extract_metadata(self, content):
        meta = {"perfil": [], "fecha_inicio": "N/D", "fecha_fin": "Pres.", "fecha_orden": "1900-01-01", "entidad": "SIPA", "titulo": "Hito"}
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            for line in match.group(1).split('\n'):
                if ':' in line:
                    k, v = [x.strip() for x in line.split(':', 1)]
                    k = k.lower()
                    if k == "perfil": meta["perfil"] = [p.strip().lower() for p in v.split(',')]
                    elif k == "fecha_inicio": 
                        meta["fecha_inicio"] = v
                        try: meta["fecha_orden"] = datetime.strptime(v, "%d/%m/%Y").strftime("%Y-%m-%d")
                        except: pass
                    elif k == "fecha_fin": meta["fecha_fin"] = v
                    elif k == "entidad": meta["entidad"] = v
                    elif k == "titulo": meta["titulo"] = v
        return meta

    def print_console_dna(self):
        print(f"\n{'='*95}\n 📊 TELEMETRÍA ADN SEMÁNTICO\n{'='*95}")
        for word, count in self.global_counter.most_common(10):
            bar = "█" * (count if count < 40 else 40)
            print(f"{word:<15} | {count:>3} {bar}")
        print(f"{'='*95}\n ✔ FILTRADOS {len(self.milestones)} HITOS PÚBLICOS PARA PDF.\n")

    def draw_contact_header(self, pdf):
        pdf.set_font("helvetica", 'B', 24); pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 12, self.contacto["nombre"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", 'B', 13); pdf.set_text_color(41, 128, 185)
        pdf.cell(0, 8, self.contacto["puesto"].upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", '', 9); pdf.set_text_color(80)
        pdf.cell(0, 5, f"Email: {self.contacto['email']} | Tel: {self.contacto['telefono']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4); pdf.set_draw_color(41, 128, 185); pdf.set_line_width(0.6); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(8)

    def render_milestone(self, pdf, m):
        if pdf.get_y() > 240: pdf.add_page()
        pdf.set_font("helvetica", 'B', 11); pdf.set_text_color(44, 62, 80)
        pdf.set_fill_color(41, 128, 185); pdf.rect(15, pdf.get_y() + 1, 2, 5, style='F')
        pdf.set_x(20)
        titulo = f"{m['meta']['titulo'].upper()} | {m['meta']['entidad'].upper()}"
        pdf.multi_cell(175, 7, self.sanitize_for_pdf(titulo), align='L')
        
        pdf.set_font("helvetica", 'I', 9); pdf.set_text_color(127, 140, 141); pdf.set_x(20)
        dur = self.extract_duration(m['content'])
        pdf.cell(0, 5, self.sanitize_for_pdf(f"{m['meta']['fecha_inicio']} - {m['meta']['fecha_fin']} | {dur}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

        for linea in m['content'].split('\n'):
            linea = linea.strip()
            if not linea or "Duración en meses" in linea: continue
            if linea.startswith('#'):
                pdf.ln(1); pdf.set_font("helvetica", 'B', 9); pdf.set_text_color(41, 128, 185); pdf.set_x(15)
                pdf.cell(0, 6, self.sanitize_for_pdf(linea.lstrip('#')), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            elif linea.startswith(('-', '*')):
                pdf.set_font("helvetica", '', 10); pdf.set_text_color(0); pdf.set_x(20)
                pdf.multi_cell(0, 5, f"- {self.sanitize_for_pdf(linea[1:])}")
            else:
                pdf.set_font("helvetica", '', 10); pdf.set_text_color(0); pdf.set_x(15)
                pdf.multi_cell(0, 5, self.sanitize_for_pdf(linea))
        pdf.ln(4)

    def generate_outputs(self):
        print(f"🚀 Generando PDFs en {self.pdf_output_path}...")
        for perf in self.perfiles_activos:
            pdf = PDF_Engine(); pdf.alias_nb_pages(); pdf.add_page(); pdf.set_margins(15, 15, 15)
            self.draw_contact_header(pdf)
            pdf.set_font("helvetica", 'B', 15); pdf.set_text_color(41, 128, 185)
            pdf.cell(0, 10, f"PERFIL PROFESIONAL: {perf.upper()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(2)
            for m in self.milestones:
                if not m["is_training"] and perf.lower() in m["meta"]["perfil"]:
                    self.render_milestone(pdf, m)
            pdf.ln(5); pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 8, "FORMACIÓN ACADÉMICA", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for m in self.milestones:
                if m["is_training"]: self.render_milestone(pdf, m)
            pdf.output(os.path.join(self.pdf_output_path, f"CV_SIPA_{perf.upper()}.pdf"))

        # RESUMEN ESTRATÉGICO LABORAL + FORMACIÓN
        res = PDF_Engine(); res.alias_nb_pages(); res.add_page(); res.set_margins(15, 15, 15)
        self.draw_contact_header(res)
        res.set_font("helvetica", 'B', 12); res.set_text_color(41, 128, 185)
        res.cell(0, 8, "RESUMEN ESTRATÉGICO SECTORIZADO", new_x=XPos.LMARGIN, new_y=YPos.NEXT); res.ln(2)

        for perf in self.perfiles_activos:
            hitos = [m for m in self.milestones if not m["is_training"] and perf.lower() in m["meta"]["perfil"]]
            if not hitos: continue
            res.set_font("helvetica", 'B', 10); res.set_fill_color(245, 245, 245)
            res.cell(0, 7, f" SECTOR: {perf.upper()}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT); res.ln(1)
            for m in hitos:
                res.set_font("helvetica", 'B', 9); res.set_text_color(50); res.set_x(20)
                y_ini = res.get_y(); res.multi_cell(110, 5, f"[x] {m['meta']['titulo']} @ {m['meta']['entidad']}")
                y_fin = res.get_y(); res.set_y(y_ini); res.set_font("helvetica", 'I', 8); res.set_text_color(100)
                info = f"{m['meta']['fecha_inicio']} - {m['meta']['fecha_fin']} | {self.extract_duration(m['content'])}"
                res.cell(0, 5, self.sanitize_for_pdf(info), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT); res.set_y(max(y_fin, res.get_y()))
            res.ln(2)

        res.ln(4); res.set_font("helvetica", 'B', 11); res.set_fill_color(41, 128, 185); res.set_text_color(255)
        res.cell(0, 8, " FORMACIÓN TÉCNICA Y ACADÉMICA", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT); res.ln(2)
        res.set_text_color(0)
        for m in self.milestones:
            if m["is_training"]:
                res.set_font("helvetica", 'B', 9); res.set_x(20)
                res.multi_cell(140, 5, self.sanitize_for_pdf(f"- {m['meta']['titulo']} ({m['meta']['entidad']})"))
                res.set_y(res.get_y() - 5); res.set_font("helvetica", 'I', 8); res.set_text_color(100)
                res.cell(0, 5, m['meta']['fecha_inicio'], align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT); res.set_text_color(0)
        
        res.output(os.path.join(self.pdf_output_path, "CV_SIPA_RESUMEN_EJECUTIVO.pdf"))

if __name__ == "__main__":
    KNOWLEDGE_BASE = "/home/toviddfrei/SIPA_PROJECT/data/knowledge"
    curador = DocCurator(KNOWLEDGE_BASE)
    curador.process_docs()
    curador.generate_outputs()
    print(f"\n✔ Operación completada. PDFs en: {curador.pdf_output_path}")