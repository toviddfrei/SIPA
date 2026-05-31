#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ubicación: core/services/sesipaeco_caja.py
Descripción: Motor de gestión financiera, parseo de extractos y control elástico de costes.
             AÑADIDO: Cálculo existencial del valor real de la hora y proyecciones.
Autor: Daniel Miñana Montero (Modificado para integración predictiva)
"""

import os
import hashlib
from datetime import datetime

class SESIPAecoCajaService:
    def __init__(self, core_base):
        self.core = core_base
        
        # Obtenemos la raíz absoluta real del ecosistema (subiendo desde la ubicación del script)
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
                "historico_bancario": [],
                "previsiones_futuras": []  # Registro dinámico de impactos económicos futuros
            }
        
        fin_globales = master_data["finanzas_globales"]
        hashes_existentes = {tx["hash_id"] for tx in fin_globales.get("historico_bancario", []) if "hash_id" in tx}

        for linea in lineas:
            linea_clean = linea.strip()
            if not linea_clean or "|" not in linea_clean:
                continue

            partes = linea_clean.split("|")
            if len(partes) >= 5:
                fecha = partes[0].strip()
                concepto = partes[1].strip()
                importe_raw = partes[3].strip()
                saldo_raw = partes[4].strip()

                try:
                    importe = float(importe_raw)
                    saldo_detectado = float(saldo_raw)
                except ValueError:
                    continue 

                hash_tx = self.calcular_hash_registro(fecha, concepto, importe)
                
                if hash_tx in hashes_existentes:
                    duplicados_omitidos += 1
                    continue

                fin_globales["historico_bancario"].append({
                    "hash_id": hash_tx,
                    "fecha": fecha,
                    "concepto": concepto,
                    "importe": importe,
                    "cuenta": tipo_cuenta,
                    "fecha_importacion": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                nuevos_registros += 1

        if nuevos_registros > 0 or saldo_detectado != 0.0:
            fin_globales["balances_apertura"][tipo_cuenta] = saldo_detectado

        self.core._save_json(self.core.cronogramas_path, master_data)

        return {
            "saldo_apertura": saldo_detectado,
            "nuevos": nuevos_registros,
            "duplicados": duplicados_omitidos
        }

    # =====================================================================
    # 🔥 NUEVAS EXTENSIONES ESTRATÉGICAS: EL VALOR REAL DE TU HORA
    # =====================================================================

    def obtener_liquidez_actual(self, master_data=None):
        """Calcula la suma real de los saldos de tus cuentas."""
        if not master_data:
            master_data = self.core._load_json(self.core.cronogramas_path)
        balances = master_data.get("finanzas_globales", {}).get("balances_apertura", {"ONLINE": 0.0, "AHORRO": 0.0})
        return sum(balances.values())

    def calcular_tarifa_hora_real(self, master_data=None):
        """
        Calcula dinámicamente el precio de tu hora real basándose en la salud del banco
        y los minutos líquidos / horas de compromiso del mes actual.
        Si no hay datos suficientes, recurre al valor por defecto (Tarifa Respaldo).
        """
        if not master_data:
            master_data = self.core._load_json(self.core.cronogramas_path)
            
        liquidez = self.obtener_liquidez_actual(master_data)
        
        # Conseguir configuración por defecto de respaldo
        config = master_data.get("configuracion", {})
        tarifa_default = float(config.get("precio_hora_default", 25.0))
        
        # Calcular horas estimadas totales comprometidas en el mes actual
        horas_comprometidas_mes = 0.0
        hitos_instanciados = master_data.get("hitos_instanciados", {})
        
        mes_actual = datetime.now().month
        año_actual = datetime.now().year
        
        for h_id, info in hitos_instanciados.items():
            f_fin = info.get("fecha_fin", "")
            try:
                dt_fin = datetime.strptime(f_fin[:10], "%Y-%m-%d")
                if dt_fin.month == mes_actual and dt_fin.year == año_actual:
                    horas_comprometidas_mes += float(info.get("horas_estimadas", 0.0))
            except ValueError:
                continue

        # También sumamos las horas consumidas en las sesiones reales del mes actual
        sesiones = self.core.obtener_sesiones()
        for s in sesiones:
            f_ini = s.get("hora_inicio", "")
            try:
                dt_ini = datetime.strptime(f_ini.split(" ")[0], "%Y-%m-%d")
                if dt_ini.month == mes_actual and dt_ini.year == año_actual:
                    horas_comprometidas_mes += float(s.get("horas_reales", 0.0))
            except ValueError:
                continue

        if horas_comprometidas_mes <= 0:
            return tarifa_default

        # Ley de balance de SIPAeco: Liquidez del banco partida por tus horas de trinchera
        tarifa_calculada = liquidez / horas_comprometidas_mes
        
        # Blindaje para evitar valores absurdos o negativos
        if tarifa_calculada <= 5.0:
            return tarifa_default
            
        return round(tarifa_calculada, 2)

    def inyectar_prevision_economica(self, hito_id, tipo_hito, concepto, importe, fecha_impacto):
        """
        Inyecta un impacto económico futuro (gasto o ingreso previsto) para alimentar la Caja y el Calendario.
        Tipos: 'BASICO' (sin fecha fin fija, recurrente mensual) u 'OPERATIVO' (cronograma).
        """
        master_data = self.core._load_json(self.core.cronogramas_path)
        if "finanzas_globales" not in master_data:
            master_data["finanzas_globales"] = {"balances_apertura": {"ONLINE": 0.0, "AHORRO": 0.0}, "historico_bancario": [], "previsiones_futuras": []}
            
        previsiones = master_data["finanzas_globales"].setdefault("previsiones_futuras", [])
        
        # Generar firma única predictiva
        payload_prev = f"{hito_id}_{fecha_impacto}_{str(importe)}"
        hash_prev = hashlib.sha256(payload_prev.encode('utf-8')).hexdigest()
        
        # Evitar meter dos veces el mismo impacto previsto
        if any(p.get("hash_id") == hash_prev for p in previsiones):
            return False, "Impacto económico ya planificado para esta fecha."

        previsiones.append({
            "hash_id": hash_prev,
            "id_hito_vinculado": hito_id,
            "tipo_hito": tipo_hito, # 'BASICO' o 'OPERATIVO'
            "concepto": concepto,
            "importe": float(importe), # Negativo para costes (alquiler, luz), Positivo para ingresos (marketing, hitos)
            "fecha_impacto": fecha_impacto, # AAAA-MM-DD
            "estado": "PLANIFICADO"
        })
        
        self.core._save_json(self.core.cronogramas_path, master_data)
        return True, "Impacto económico inyectado con éxito."