import json
import os
import random
import time
from datetime import datetime, timezone

CARPETA_SALIDA = "./entrada_json"
os.makedirs(CARPETA_SALIDA, exist_ok=True)
ESTACIONES = [
    {"id": "EST-SEV-01", "nombre": "Embalse del Pintado", "provincia": "Sevilla"},
    {"id": "EST-COR-02", "nombre": "Embalse de Iznájar", "provincia": "Córdoba"},
    {"id": "EST-JAE-03", "nombre": "Embalse del Tranco", "provincia": "Jaén"},
    {"id": "EST-CAD-04", "nombre": "Embalse de Guadalcacín", "provincia": "Cádiz"},
]

print(f"Iniciando simulación de telemetría en {CARPETA_SALIDA} (Ctrl+C para parar)...")
contador = 1
try:
    while True:
        nombre_tmp = os.path.join(CARPETA_SALIDA, f"telemetria_{contador:04d}.tmp")
        nombre_final = os.path.join(CARPETA_SALIDA, f"telemetria_{contador:04d}.json")
        dado = random.random()
        if dado < 0.10:
            # 10% de JSON malformado para probar la rama de errores (DLQ)
            contenido = '{"id_evento": ' + str(contador) + ', "estacion": "CORRUPTO_SIN_CIERRE"}'

            with open(nombre_tmp, "w", encoding="utf-8") as f:
                f.write(contenido)
                tipo = "CORRUPTO"
        else:
            estacion = random.choice(ESTACIONES)
            es_alerta = dado < 0.30
            temp = round(random.uniform(36.5, 43.0), 2) if es_alerta else round(random.uniform(14.0, 32.0), 2)
            estado = "ALERTA" if es_alerta else "NORMAL"
            evento = {
            "id_evento": contador,
            "estacion_id": estacion["id"],
            "estacion_nombre": estacion["nombre"],
            "provincia": estacion["provincia"],
            "temperatura_c": temp,
            "caudal_m3s": round(random.uniform(5.0, 120.0), 2),
            "estado": estado,
            "timestamp": datetime.now(timezone.utc).isoformat()
            }
            with open(nombre_tmp, "w", encoding="utf-8") as f:
                json.dump(evento, f, ensure_ascii=False)
                tipo = estado
                os.replace(nombre_tmp, nombre_final)
                print(f"[{contador:04d}] Generado ({tipo}): {nombre_final}")
                contador += 1
                time.sleep(2)
except KeyboardInterrupt:
    print("\nSimulación detenida por el usuario.")