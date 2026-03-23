"""
actualizar_openers.py
─────────────────────────────────────────────────────────────────────────────
Regenera los mensajes opener de los prospectos ya calificados usando
el prompt de ventas mejorado.

Útil cuando iteras el prompt y quieres actualizar mensajes sin re-buscar
todos los prospectos desde cero.

Uso:
  python actualizar_openers.py                    → actualiza todos los listos
  python actualizar_openers.py --id 42            → actualiza solo el id 42
  python actualizar_openers.py --preview          → muestra 3 ejemplos sin guardar
  python actualizar_openers.py --cantidad 20      → actualiza los top 20 por puntuación
─────────────────────────────────────────────────────────────────────────────
"""

import os
import json
import asyncio
import argparse
import logging
from datetime import datetime

import anthropic
from subagente_db import SubagenteDB
from prompts_ventas import PROMPT_OPENER_VETERINARIAS

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)s  %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger("actualizar-openers")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
claude_async      = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
db                = SubagenteDB()

MAX_PARALELO = 5   # más conservador que la calificación — Sonnet tiene límites más bajos


async def generar_opener_uno(p: dict) -> dict:
    """Genera un mensaje opener mejorado para un prospecto."""
    prompt = PROMPT_OPENER_VETERINARIAS.format(
        nombre  = p["nombre_negocio"],
        ciudad  = p.get("ciudad", "Chile"),
        rating  = p.get("rating", 0),
        resenas = p.get("resenas", p.get("reseñas", 0)),
    )

    try:
        resp = await claude_async.messages.create(
            model      = "claude-sonnet-4-20250514",  # Sonnet para calidad del opener
            max_tokens = 200,
            messages   = [{"role": "user", "content": prompt}]
        )
        opener = resp.content[0].text.strip()
        return {"id": p["id"], "nombre": p["nombre_negocio"], "opener": opener, "ok": True}
    except Exception as e:
        log.error(f"Error en {p['nombre_negocio']}: {e}")
        return {"id": p["id"], "nombre": p["nombre_negocio"], "opener": "", "ok": False}


async def actualizar_lote(prospectos: list[dict], solo_preview: bool = False):
    """Regenera openers en paralelo y actualiza la DB."""
    semaforo = asyncio.Semaphore(MAX_PARALELO)

    async def con_semaforo(p: dict) -> dict:
        async with semaforo:
            return await generar_opener_uno(p)

    log.info(f"Regenerando openers para {len(prospectos)} prospectos (Sonnet)...")
    t0 = asyncio.get_event_loop().time()

    resultados = await asyncio.gather(
        *[con_semaforo(p) for p in prospectos],
        return_exceptions=True,
    )

    duracion   = asyncio.get_event_loop().time() - t0
    actualizados = 0
    errores      = 0

    for r in resultados:
        if isinstance(r, Exception) or not r["ok"]:
            errores += 1
            continue

        if solo_preview:
            print(f"\n{'─' * 55}")
            print(f"  [{r['nombre']}]")
            print(f"{'─' * 55}")
            print(r["opener"])
        else:
            db.actualizar(r["id"], {"mensaje_draft": r["opener"]})
            actualizados += 1
            log.info(f"  Actualizado: {r['nombre']}")

    if not solo_preview:
        print(f"\n  Actualizados: {actualizados} | Errores: {errores} | Tiempo: {duracion:.1f}s")
    print()


def main():
    parser = argparse.ArgumentParser(description="Actualizar mensajes opener de prospectos")
    parser.add_argument("--id",       type=int, default=None, help="Actualizar solo un ID")
    parser.add_argument("--cantidad", type=int, default=100,  help="Cuántos actualizar")
    parser.add_argument("--preview",  action="store_true",    help="Mostrar ejemplos sin guardar")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY no configurada")
        return

    db.init()

    if args.id:
        # Actualizar un prospecto específico
        import sqlite3
        from pathlib import Path
        with sqlite3.connect(Path("prospectos_vet.db")) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM prospectos WHERE id = ?", (args.id,)).fetchone()
        if not row:
            print(f"No encontrado: id={args.id}")
            return
        asyncio.run(actualizar_lote([dict(row)], solo_preview=args.preview))
    else:
        limite     = 3 if args.preview else args.cantidad
        prospectos = db.obtener_por_estado("mensaje_listo", limite)
        if not prospectos:
            print("No hay prospectos en estado 'mensaje_listo'")
            return
        asyncio.run(actualizar_lote(prospectos, solo_preview=args.preview))


if __name__ == "__main__":
    main()
