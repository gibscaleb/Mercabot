#!/usr/bin/env python3
"""
Ejecutar UNA SOLA VEZ después del docker-compose up.
Descarga las imágenes al volumen local y actualiza la BD.

Uso:
    docker exec mercabot_web python /app/descargar_imagenes.py
"""

import os, pathlib, urllib.request, psycopg2

DB = dict(
    host=os.getenv("DB_HOST", "db"),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "password123"),
    dbname=os.getenv("DB_NAME", "mercabot"),
)

IMG_DIR = pathlib.Path("/app/static/img")
IMG_DIR.mkdir(parents=True, exist_ok=True)

# URLs 
IMAGENES = {
    "xb01-xb01-xb01-xb01-xb01xb01xb01": (
        "xbox_series_x.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Xbox_Series_X_Console.png/320px-Xbox_Series_X_Console.png"
    ),
    "xb02-xb02-xb02-xb02-xb02xb02xb02": (
        "xbox_series_s_w.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Xbox_Series_S.png/320px-Xbox_Series_S.png"
    ),
    "xb03-xb03-xb03-xb03-xb03xb03xb03": (
        "xbox_series_s_b.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Xbox_Series_S.png/320px-Xbox_Series_S.png"
    ),
    "ps01-ps01-ps01-ps01-ps01ps01ps01": (
        "ps5_std.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg"
    ),
    "ps02-ps02-ps02-ps02-ps02ps02ps02": (
        "ps5_digital.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg"
    ),
    "ps03-ps03-ps03-ps03-ps03ps03ps03": (
        "ps5_pro.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/PlayStation_5_Digital_Edition_with_DualSense.jpg/320px-PlayStation_5_Digital_Edition_with_DualSense.jpg"
    ),
    "sw01-sw01-sw01-sw01-sw01sw01sw01": (
        "switch_oled.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Nintendo_Switch_OLED_model.png/320px-Nintendo_Switch_OLED_model.png"
    ),
    "sw02-sw02-sw02-sw02-sw02sw02sw02": (
        "switch_neon.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Nintendo-Switch-wJoyCons-BlRd-Standing-Frt.png/320px-Nintendo-Switch-wJoyCons-BlRd-Standing-Frt.png"
    ),
    "sw03-sw03-sw03-sw03-sw03sw03sw03": (
        "switch_lite.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Nintendo_Switch_Lite_representation.png/320px-Nintendo_Switch_Lite_representation.png"
    ),
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer":    "https://en.wikipedia.org/",
    "Accept":     "image/webp,image/apng,image/*,*/*;q=0.8",
}

conn = psycopg2.connect(**DB)
cur = conn.cursor()

print("Descargando imágenes...\n")
ok = 0
fail = 0

for producto_id, (nombre_archivo, url) in IMAGENES.items():
    destino = IMG_DIR / nombre_archivo
    ruta_local = f"/static/img/{nombre_archivo}"

    if destino.exists():
        print(f"  ✓ Ya existe: {nombre_archivo}")
        ok += 1
    else:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            if len(data) < 1000:
                raise Exception(f"Respuesta muy pequeña ({len(data)} bytes) — posible bloqueo")
            destino.write_bytes(data)
            print(f"  ↓ Descargado: {nombre_archivo} ({len(data)//1024} KB)")
            ok += 1
        except Exception as e:
            print(f"  ✗ Error: {nombre_archivo} — {e}")
            fail += 1
            ruta_local = None  # No actualizar si falló la descarga

    if ruta_local:
        cur.execute(
            "UPDATE productos SET imagen_thumbnail = %s WHERE id = %s",
            (ruta_local, producto_id)
        )

conn.commit()
cur.close()
conn.close()

print(f"\n{'✅' if fail == 0 else '⚠️ '} Completado: {ok} OK, {fail} errores")
if fail > 0:
    print("   Para los productos con error, sube la imagen manualmente desde el panel admin.")