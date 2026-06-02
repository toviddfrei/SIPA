# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: sipa_utils.py (BIBLIOTECA COMPARTIDA INTERNA)
# Módulo: SIPAutils
# Versión: 1.0.0 | Fecha: 22/05/2026
# ==========================================================

import os
import unicodedata

def blindar_formatos_fecha(datos_mapa):
    """
    Sanea y homogeneiza las fechas de cualquier dataset en el ecosistema SIPA.
    Transforma formatos YYYY-MM-DD o DD-MM-YYYY con guiones a DD/MM/YYYY con barras.
    """
    if not datos_mapa:
        return []
        
    for item in datos_mapa:
        # 1. Forzar presencia de claves críticas
        if "fecha_entrada" not in item or str(item.get("fecha_entrada")).strip() in ["", "None", "N/A"]:
            item["fecha_entrada"] = "01/01/1990"
        
        if "ultima_modificacion" not in item or str(item.get("ultima_modificacion")).strip() in ["", "None", "N/A"]:
            item["ultima_modificacion"] = item["fecha_entrada"]
        
        # 2. Corregir formato si viene con guiones
        for clave in ["fecha_entrada", "ultima_modificacion"]:
            valor_fecha = str(item[clave])
            if "-" in valor_fecha:
                try:
                    partes = valor_fecha.split(" ")[0].split("-")
                    if len(partes) == 3:
                        if len(partes[0]) == 4:  # YYYY-MM-DD
                            item[clave] = f"{partes[2]}/{partes[1]}/{partes[0]}"
                        else:  # DD-MM-YYYY
                            item[clave] = f"{partes[0]}/{partes[1]}/{partes[2]}"
                except Exception:
                    item[clave] = "01/01/1990" if clave == "fecha_entrada" else item["fecha_entrada"]
                    
    return datos_mapa

def obtener_peso_digital_mb(ruta):
    """Calcula el tamaño en Megabytes de un archivo o directorio de forma segura."""
    total = 0
    if os.path.exists(ruta):
        if os.path.isdir(ruta):
            for dirpath, _, filenames in os.walk(ruta):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp): 
                        total += os.path.getsize(fp)
        else:
            total = os.path.getsize(ruta)
    return total / (1024 * 1024)

def calcular_gasto_estructural(base_dir):
    """Calcula el porcentaje de peso consumido puramente por el software vs datos."""
    peso_sipa_total = obtener_peso_digital_mb(base_dir)
    peso_data = obtener_peso_digital_mb(os.path.join(base_dir, "data"))
    
    peso_sistema_puro = max(0, peso_sipa_total - peso_data)
    porcentaje_gasto = round((peso_sistema_puro / peso_sipa_total) * 100, 2) if peso_sipa_total > 0 else 0.0
    
    return porcentaje_gasto

def normalizar_cadena_insensible(txt):
    """Elimina acentos, diéresis y fuerza minúsculas para comparaciones e índices."""
    if not txt:
        return ""
    return "".join(c for c in unicodedata.normalize('NFD', txt.lower()) if unicodedata.category(c) != 'Mn')

def sincronizar_contexto_hito_labels(hito_id_texto, hitos_cache, lbl_proyecto, lbl_crono):
    """
    Sincroniza reactivamente las etiquetas de interfaz (Proyecto y Cronograma) 
    al cambiar la selección de un hito en un combo box.
    Aplica el patrón de extracción e indexación robusta compartida por Tiempo y Finanzas.
    """
    if not hito_id_texto or "SIN ASIGNAR" in hito_id_texto:
        lbl_proyecto.setText("<b>Proyecto:</b> -")
        lbl_crono.setText("<b>Crono Tipo:</b> -")
        return None

    # Extracción homogénea mediante troceo por primer espacio
    id_real = hito_id_texto.split(" ")[0].strip()
    info_hito = hitos_cache.get(id_real)
    
    if info_hito:
        lbl_proyecto.setText(f"<b>Proyecto:</b> {info_hito.get('id_proyecto', '-')}")
        lbl_crono.setText(f"<b>Crono Tipo:</b> {info_hito.get('id_cronograma_tipo', '-')}")
        return id_real
    else:
        lbl_proyecto.setText("<b>Proyecto:</b> -")
        lbl_crono.setText("<b>Crono Tipo:</b> -")
        return None