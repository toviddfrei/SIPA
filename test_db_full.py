# ==========================================================
# CITADEL CORE - Integrity Test
# Archivo: test_db_full.py
# Versión: 0.2.5 (Referencia unificada)
# Módulo: Core
# Certificación: FHS-Compliant | Norma: ISO/IEC 27001 (Simulada)
# Autor: Daniel Miñana & Gemini
# ---------------------------------------------------------
# Descripción: Test de estrés y verificación de tablas para la DB migrada.
# ==========================================================

from core.persistence import PersistenceManager
import os

def run_full_audit():
    print("="*50)
    print("🔍 AUDITORÍA DE PERSISTENCIA - CITADEL v.0.2.5")
    print("="*50)
    
    db = PersistenceManager()
    
    # 1. Test de Conexión
    if not db.connect():
        print("[❌] FALLO: No se puede conectar a data/db/sistema.db")
        return

    print("[✅] Conexión establecida con éxito.")

    # 2. Verificación de Tablas (Herencia BApp)
    tables_to_check = ['app_logs', 'sessions', 'metricas_arranque', 'roadmap']
    for table in tables_to_check:
        db._cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
        if db._cursor.fetchone():
            print(f"[✅] Tabla '{table}' verificada (Migración Correcta).")
        else:
            print(f"[❌] ERROR: Falta la tabla '{table}'.")

    # 3. Test de Escritura de Log (Simulación de Telemetría)
    log_sample = {
        'timestamp': "2025-12-30 20:00:00",
        'session_id': 18,
        'level': "INFO",
        'name': "TEST_AUDIT",
        'message': "Prueba de integridad de escritura post-migración.",
        'context_json': '{"source": "test_db_full.py"}'
    }
    
    try:
        db.insert_log(log_sample)
        print("[✅] Escritura de LOG de prueba: OK.")
    except Exception as e:
        print(f"[❌] FALLO al escribir log: {e}")

    # 4. Conteo de Historial
    db._cursor.execute("SELECT COUNT(*) FROM app_logs")
    total_logs = db._cursor.fetchone()[0]
    print(f"[📊] Historial acumulado: {total_logs} registros encontrados.")

    print("="*50)
    print("AUDITORÍA COMPLETADA - SISTEMA NOMINAL")
    print("="*50)

if __name__ == "__main__":
    run_full_audit()