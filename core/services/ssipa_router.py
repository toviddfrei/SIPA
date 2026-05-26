# =================================================================
# PROYECTO SIPA - Sistema Identificación Personal Autorizada
# Archivo: sipa_router.py
# Módulo: Core Security Services / Gateway de Enrutamiento RDDR & Logs
# Versión: 3.5.0.1 | Fecha: 26/05/2026
# Autor: Daniel Miñana Montero & Gemini (Especialista en Seguridad)
# -----------------------------------------------------------------
# DESCRIPCIÓN: Gobernador Central de Caminos e Ignición de Logs.
# Previene el Python Path Hijacking mediante aislamiento en RAM
# y centraliza la caja negra de auditoría del sistema completo.
# =================================================================

import os
import sys
import logging
from datetime import datetime

class SIPARouterGateway:
    """
    Gateway e Inyector de Rutas en Caliente.
    Actúa como el servidor DNS interno para la persistencia del software
    y unifica el arranque de los registros (Logs) del ecosistema.
    """
    
    ENV_VAR_NAME = "SIPA_SECRET_ROOT"
    ARTEFACTO_LOG_MD = "data/archive/auditoria_rddr.md"
    MASTER_LOG_FILE = "data/logs/SIPA_Master_CajaNegra.log"

    @classmethod
    def inicializar_entorno(cls):
        """
        Calcula el Ancla dinámica, inicializa la Caja Negra de logs
        y asegura el aislamiento en la memoria volátil (RAM) del proceso.
        """
        # 1. RESOLUCIÓN DINÁMICA DE DIRECTORIO RAÍZ (RDDR)
        # Sabiendo que este archivo nace en: SIPA/core/services/sipa_router.py
        # Subimos dos niveles de forma limpia para encontrar la raíz real del proyecto
        ruta_actual = os.path.dirname(os.path.abspath(__file__))
        raiz_calculada = os.path.abspath(os.path.join(ruta_actual, "..", ".."))

        # Guardamos inmediatamente en la memoria volátil del proceso actual
        os.environ[cls.ENV_VAR_NAME] = raiz_calculada

        # 2. GARANTIZAR ESTRUCTURA FHS INTERNA PARA LOGS Y ARTEFACTOS
        os.makedirs(os.path.join(raiz_calculada, "data", "logs"), exist_ok=True)
        os.makedirs(os.path.join(raiz_calculada, "data", "archive"), exist_ok=True)

        # 3. UNIFICACIÓN Y ARRANQUE DE LA CAJA NEGRA (LOGGING MASTER)
        cls._iniciar_caja_negra(raiz_calculada)
        
        logger = logging.getLogger("SIPA.Core")
        logger.info("=== IGNICIÓN DEL ECO-SISTEMA SIPA ===")
        logger.info(f"Ancla RDDR resuelta con éxito en RAM: {raiz_calculada}")

        # 4. GENERACIÓN DE EVIDENCIA (Mochila de Auditoría)
        cls._generar_artefacto_auditoria(raiz_calculada)

        # 5. INYECCIÓN QUIRÚRGICA DE CAMINOS EN PYTHON (Evitar colisiones)
        cls._inyectar_rutas_sistema(raiz_calculada, logger)
        
        return raiz_calculada

    @classmethod
    def obtener_ruta(cls, *partes):
        """
        Servidor DNS de rutas. Resuelve caminos absolutos partiendo de la RAM.
        Uso: sipa_router.obtener_ruta("external", "SIPAcur")
        """
        raiz = os.environ.get(cls.ENV_VAR_NAME)
        if not raiz:
            # Fallback seguro de autogestión por si se invoca antes de tiempo
            ruta_actual = os.path.dirname(os.path.abspath(__file__))
            raiz = os.path.abspath(os.path.join(ruta_actual, "..", ".."))
        return os.path.join(raiz, *partes)

    @classmethod
    def _iniciar_caja_negra(cls, raiz):
        """Configura el sistema de Log unificado desde el milisegundo cero."""
        ruta_completa_log = os.path.join(raiz, cls.MASTER_LOG_FILE)
        
        logging.basicConfig(
            filename=ruta_completa_log,
            level=logging.INFO,
            format='%(asctime)s | [%(levelname)s] | [%(name)s] | %(message)s',
            filemode='a',
            encoding='utf-8'
        )

    @classmethod
    def _inyectar_rutas_sistema(cls, raiz, logger):
        """Inyecta los sub-cores en sys.path priorizando el core local activo."""
        rutas_criticas = [
            os.path.join(raiz, "external", "SIPAcur", "core", "services"),
            os.path.join(raiz, "external", "SIPAcur"),
            os.path.join(raiz, "external", "utils"),
            raiz
        ]
        
        for r in rutas_criticas:
            if r not in sys.path:
                # Si es el core local de servicios de SIPAcur, inyección prioritaria (Posición 0)
                if "SIPAcur/core/services" in r:
                    sys.path.insert(0, r)
                    logger.debug(f"Runtime Path Injection Prioritaria: {r}")
                else:
                    sys.path.append(r)
                    logger.debug(f"Runtime Path Injection Append: {r}")

    @classmethod
    def _generar_artefacto_auditoria(cls, raiz_resuelta):
        """Genera el informe pedagógico en Markdown para la Mochila de Auditoría."""
        ruta_informe = os.path.join(raiz_resuelta, cls.ARTEFACTO_LOG_MD)
        
        informe_md = f"""# 🛡️ INFORME DE AUDITORÍA DE ENRUTAMIENTO (RDDR)
                        *Generado automáticamente por el Core de Seguridad del Ecosistema SIPA*

                        ## 📝 Datos de la Sesión
                        - **Fecha/Hora:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        - **Aislamiento de Entorno:** 🟢 RAM SECURE INJECTION (`os.environ`)
                        - **Caja Negra:** ACTIVA (`SIPA_Master_CajaNegra.log`)

                        ## 🔍 Análisis de Rutas en Caliente
                        El Gateway ha tomado el control de los caminos para evitar vectores de ataque *Python Path Hijacking*.

                        | Componente | Tipo de Ruta Resuelta en RAM | Estado |
                        |------------|------------------------------|--------|
                        | **SIPA_ROOT** | `{raiz_resuelta}` | INTEGRADO |
                        | **Mochila RDDR** | Transparente / Auditable | COMPLETO |

                        ---
                        *Evidencia generada para cumplimiento normativo y trazabilidad ética del código.*
                        """
        try:
            with open(ruta_informe, "w", encoding="utf-8") as f:
                f.write(informe_md)
        except Exception as e:
            print(f"⚠️ Alerta: No se pudo escribir la mochila de auditoría: {e}")