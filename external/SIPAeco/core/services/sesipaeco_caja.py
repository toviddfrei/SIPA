#!/usr/bin/env python3
# -*- coding: utf-8 -*-\n
import os
import hashlib
from datetime import datetime

class SESIPAecoCajaService:
    def __init__(self, core_base):
        self.core = core_base
        
        # Obtenemos la raíz absoluta real del ecosistema (subiendo desde la ubicación del script)
        # Esto nos asegura que estemos donde estemos, apunte bien a tu carpeta de datos de usuario
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
        
        self.ruta_online = os.path.join(base_dir, "SIPA/data/finanzas/cta_online")
        self.ruta_ahorro = os.path.join(base_dir, "SIPA/data/finanzas/cta_ahorro")
        
        os.makedirs(self.ruta_online, exist_ok=True)
        os.makedirs(self.ruta_ahorro, exist_ok=True)

    def calcular_hash_registro(self, fecha, concepto, importe):
        """Genera una firma SHA-256 única para evitar la duplicidad de apuntes mensuales."""
        payload = f"{fecha.strip()}_{concepto.strip()}_{str(importe).strip()}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def procesar_txt_extracto(self, file_path, tipo_cuenta):
        """
        Parsea el extracto real delimitado por '|'.
        Mapeo: Col 0 = Fecha, Col 1 = Concepto, Col 3 = Importe, Col 4 = Saldo.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo no existe en la ruta: {file_path}")

        # Tolerancia híbrida de codificación para caracteres como 'Ó' o '€'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='iso-8859-1') as f:
                lineas = f.readlines()

        saldo_detectado = 0.0
        nuevos_registros = 0
        duplicados_omitidos = 0

        master_data = self.core._load_json(self.core.cronogramas_path)
        
        if "finanzas_globales" not in master_data:
            master_data["finanzas_globales"] = {
                "balances_apertura": {"ONLINE": 0.0, "AHORRO": 0.0},
                "historico_bancario": []
            }
        
        fin_globales = master_data["finanzas_globales"]
        hashes_existentes = {tx["hash_id"] for tx in fin_globales.get("historico_bancario", []) if "hash_id" in tx}

        # Procesar líneas del extracto
        for linea in lineas:
            linea_clean = linea.strip()
            if not linea_clean or "|" not in linea_clean:
                continue

            partes = linea_clean.split("|")
            # Tu estructura real tiene al menos 5 columnas críticas (0 a 4)
            if len(partes) >= 5:
                fecha = partes[0].strip()
                concepto = partes[1].strip()
                importe_raw = partes[3].strip()
                saldo_raw = partes[4].strip()

                try:
                    importe = float(importe_raw)
                    # Capturamos el último saldo leído como reflejo del estado de la cuenta
                    saldo_detectado = float(saldo_raw)
                except ValueError:
                    continue  # Si la línea es una cabecera y no convierte a float, la salta de forma segura

                # Validar duplicidad mediante la firma SHA-256 inmutable
                hash_tx = self.calcular_hash_registro(fecha, concepto, importe)
                
                if hash_tx in hashes_existentes:
                    duplicados_omitidos += 1
                    continue

                # Insertar en el histórico si es un registro inédito
                fin_globales["historico_bancario"].append({
                    "hash_id": hash_tx,
                    "fecha": fecha,
                    "concepto": concepto,
                    "importe": importe,
                    "cuenta": tipo_cuenta,
                    "fecha_importacion": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                nuevos_registros += 1

        # Actualizar el balance oficial de la cuenta con el último dato procesado
        if nuevos_registros > 0 or saldo_detectado != 0.0:
            fin_globales["balances_apertura"][tipo_cuenta] = saldo_detectado

        self.core._save_json(self.core.cronogramas_path, master_data)

        return {
            "saldo_apertura": saldo_detectado,
            "nuevos": nuevos_registros,
            "duplicados": duplicados_omitidos
        }