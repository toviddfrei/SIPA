#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =================================================================
# PROYECTO SIPA - Sistema de Gestión Operativa Integrada
# Archivo: sipa_switch.py
# Módulo: External Services / Switch Conmutador de Módulos (VLAN Core Link)
# Versión: 2.0.0-PoE | Fecha: 02/06/2026
# Autor: Daniel Miñana Montero & Gemini
# -----------------------------------------------------------------
# DESCRIPCIÓN: Infraestructura de Red de Software del Ecosistema.
#              Auto-descubre el entorno y alimenta (PoE) el sys.path
#              conmutando las VLANs críticas de dependencias de forma 
#              unificada sin necesidad de alimentación manual externa.
# =================================================================

import os
import sys
import logging

class ExternalSwitch:
    """
    Switch Lógico de Capa 3.
    Auto-detecta la topología física del proyecto y conmuta dinámicamente
    los buses de datos y las interfaces de los módulos en el bus de Python.
    """
    _vlan_link_up = False

    @classmethod
    def conectar_poe(cls):
        """
        Levanta los trunks de red y energiza de forma autónoma el sys.path.
        No requiere parámetros externos: calcula las rutas por proximidad de nodo.
        """
        if cls._vlan_link_up:
            return
            
        logger = logging.getLogger("SIPA.ExternalSwitch")
        logger.info("🎛️ [Switch-PoE] Inicializando mapeo automático de puertos de red...")

        # 🛰️ AUTO-DESCUBRIMIENTO DE TOPOLOGÍA (Cálculo exacto de nodos)
        # El nodo actual es la interfaz de la carpeta 'external/'
        nodo_external = os.path.dirname(os.path.abspath(__file__))
        # El Core Trunk sube un nivel para consolidar la raíz '/SIPA'
        nodo_raiz_sipa = os.path.abspath(os.path.join(nodo_external, ".."))

        # 🗺️ MAPA DE CONMUTACIÓN DE SEGMENTOS (Las 3 VLANs esenciales)
        vlan_segments = {
            "VLAN-10-CORE": nodo_raiz_sipa,                           # Acceso troncal a sipa_utils y core/
            "VLAN-20-EXT" : nodo_external,                            # Acceso cruzado a herramientas en external/
            "VLAN-30-ECO" : os.path.join(nodo_external, "SIPAeco")    # Puerto específico de la Suite Económica
        }

        # ⚡ INYECCIÓN DE ENERGÍA DE RUTAS (PoE Link Loop)
        for vlan_id, ruta_fisica in vlan_segments.items():
            if os.path.exists(ruta_fisica):
                if ruteo_valido := (ruta_fisica not in sys.path):
                    # Insertamos en la posición 0 para dar máxima prioridad de conmutación
                    sys.path.insert(0, ruta_fisica)
                    logger.info(f"🔌 [Port Link UP] {vlan_id} acoplada al bus. Ruta: {ruta_fisica}")
            else:
                logger.error(f"🚨 [Port Link DOWN] Fallo crítico de hardware en {vlan_id}. Ruta no hallada: {ruta_fisica}")

        cls._vlan_link_up = True
        logger.info("🟢 [SWITCH PoE] Transmisión estable. Todo el tráfico de dependencias está conmutado.")


# =====================================================================
# 🔬 TEST DE DIAGNÓSTICO EN FRÍO (Ping de bucle de retorno)
# =====================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("⚡ Realizando test de conectividad del Switch aislado...")
    ExternalSwitch.conectar_poe()
    print("\n📋 Estado actual del enrutamiento de Python (sys.path):")
    for p in sys.path[:4]:
        print(f" -> Link: {p}")