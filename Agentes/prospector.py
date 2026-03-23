"""
prospector.py  — ValVic Multi-Vertical
═══════════════════════════════════════════════════════════════════════════════
Prospector genérico que funciona con cualquier vertical configurada en YAML.

Uso:
  python prospector.py --vertical dental --ciudad Santiago --cantidad 50
  python prospector.py --vertical spa --ciudad Valparaiso --cantidad 30
  python prospector.py --vertical psicologos --ciudad Santiago --cantidad 40 --test
  python prospector.py --listar-verticales
  python prospector.py --vertical dental --solo-revisar
  python prospector.py --vertical dental --resumen
  python prospector.py --vertical dental --solo-exportar

Agregar un vertical nuevo:
  1. Crear verticals/nuevo_rubro.yaml (copiar dental.yaml como base)
  2. Correr: python prospector.py --vertical nuevo_rubro --ciudad Santiago
  ← cero cambios de código
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import asyncio
import csv
import logging
import time
import argparse
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import anthropic
from pydantic import BaseModel
from pydantic import Field

# Carga opcional de PyYAML
try:
    import yaml
    YAML_OK = True
except ImportError:
    YAML_OK = False

from subagente_db import SubagenteDB, ProspectoNuevo, ProspectoCalificado

# ─── logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)s  %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger("prospector")

# ─── credenciales ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
DIALOG360_KEY     = os.getenv("DIALOG360_API_KEY", "")
DIALOG360_PHONE   = os.getenv("DIALOG360_PHONE_ID", "")

claude_sync  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
claude_async = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

VERTICALS_DIR  = Path(__file__).parent.parent / "verticals"
MAX_PARALELO   = 8
PAUSA_ENVIO    = 3.0
MAX_ENVIOS_DIA = 100


# ════════════════════════════════════════════════════════════════════════════
#  CARGA DE CONFIGURACIÓN VERTICAL
# ════════════════════════════════════════════════════════════════════════════

def cargar_vertical(nombre: str) -> dict:
    """
    Carga el archivo YAML del vertical.
    Lanza FileNotFoundError si no existe, ValueError si es inválido.
    """
    if not YAML_OK:
        raise ImportError(
            "PyYAML no está instalado. Ejecuta: pip install pyyaml"
        )

    ruta = VERTICALS_DIR / f"{nombre}.yaml"
    if not ruta.exists():
        disponibles = [f.stem for f in VERTICALS_DIR.glob("*.yaml")]
        raise FileNotFoundError(
            f"Vertical '{nombre}' no encontrado en {VERTICALS_DIR}.\n"
            f"Disponibles: {', '.join(disponibles)}"
        )

    with open(ruta, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Validación mínima
    campos_req = ["id", "nombre_rubro", "agente_nombre", "busqueda", "problema", "precios"]
    faltantes  = [c for c in campos_req if c not in cfg]
    if faltantes:
        raise ValueError(f"Faltan campos en {ruta}: {faltantes}")

    return cfg


def listar_verticales() -> list[str]:
    """Devuelve los verticales disponibles."""
    if not VERTICALS_DIR.exists():
        return []
    return sorted(f.stem for f in VERTICALS_DIR.glob("*.yaml"))


# ════════════════════════════════════════════════════════════════════════════
#  SUBAGENTE BUSCADOR (genérico — usa queries del YAML)
# ════════════════════════════════════════════════════════════════════════════

def _places_query(
    query: str, zona: str, pagetoken: str = "", vertical: str = ""
) -> tuple[list[ProspectoNuevo], str]:
    """Una llamada a Google Places API (Nueva v1) para traer teléfono en 1 sola llamada."""
    headers = {
        "X-Goog-Api-Key": GOOGLE_PLACES_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.internationalPhoneNumber,places.rating,places.userRatingCount,places.websiteUri,places.googleMapsUri,nextPageToken",
        "Content-Type": "application/json"
    }
    
    body = {
        "textQuery": f"{query} en {zona} Chile",
        "languageCode": "es",
        "regionCode": "CL"
    }
    if pagetoken:
        body["pageToken"] = pagetoken

    try:
        resp = httpx.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers=headers, json=body, timeout=15,
        )
        resp.raise_for_status()
        data   = resp.json()
        nuevos = []
        for r in data.get("places", []):
            nombre = r.get("displayName", {}).get("text", "")
            tel    = r.get("internationalPhoneNumber") or r.get("nationalPhoneNumber", "")
            
            nuevos.append(ProspectoNuevo(
                nombre_negocio = nombre,
                telefono       = tel,
                ciudad         = zona,
                direccion      = r.get("formattedAddress", ""),
                rating         = float(r.get("rating", 0)),
                resenas        = int(r.get("userRatingCount", 0)),
                maps_url       = r.get("googleMapsUri", ""),
                place_id       = r.get("id", ""),
                website        = r.get("websiteUri", ""),
                fuente         = "google_places",
                vertical       = vertical,
            ))
        return nuevos, data.get("nextPageToken", "")
    except Exception as e:
        log.warning(f"Places error '{query} en {zona}': {e}")
        return [], ""


def _fallback_ia(cfg: dict, ciudad: str, cantidad: int) -> list[ProspectoNuevo]:
    """Claude genera lista cuando no hay Google Places API key."""
    nombre_rubro = cfg["nombre_rubro"]
    vertical_id  = cfg["id"]
    log.info(f"Sin Google Places → Claude genera lista estimada de {nombre_rubro}")

    prompt = f"""Lista {cantidad} negocios del tipo "{nombre_rubro}" en {ciudad}, Chile.
Usa nombres realistas y típicos del rubro chileno. Varia tamanios y zonas.
RESPONDE SOLO con JSON valido:
[
  {{"nombre": "Nombre del negocio",
    "direccion": "Av. Ejemplo 1234, {ciudad}",
    "telefono": "+5622XXXXXXXX",
    "rating": 4.5,
    "resenas": 87,
    "website": ""}}
]
Genera exactamente {cantidad}. Algunos sin telefono (null). Algunos con website (URL completa)."""

    try:
        resp = claude_sync.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 4000,
            messages   = [{"role": "user", "content": prompt}]
        )
        texto = resp.content[0].text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        datos = json.loads(texto)
        return [
            ProspectoNuevo(
                nombre_negocio = d["nombre"],
                telefono       = d.get("telefono"),
                ciudad         = ciudad,
                direccion      = d.get("direccion", ""),
                rating         = float(d.get("rating", 0)),
                resenas        = int(d.get("resenas", 0)),
                website        = d.get("website", ""),
                fuente         = "ia_estimado",
                vertical       = vertical_id,
            )
            for d in datos
        ]
    except Exception as e:
        log.error(f"Fallback IA error: {e}")
        return []


def buscar_negocios(cfg: dict, ciudad: str, cantidad: int) -> list[ProspectoNuevo]:
    """
    Busca hasta `cantidad` negocios usando las queries del YAML del vertical.
    Estrategia: múltiples queries × zonas × páginas.
    """
    if not GOOGLE_PLACES_KEY:
        return _fallback_ia(cfg, ciudad, cantidad)

    ciudad_lower = ciudad.lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    zonas_map    = cfg["busqueda"].get("zonas_default", {})
    zonas        = zonas_map.get(ciudad_lower, [ciudad])
    queries      = cfg["busqueda"]["queries"]
    vertical_id  = cfg["id"]

    todas:      list[ProspectoNuevo] = []
    ids_vistos: set[str]             = set()

    log.info(f"Buscando {cantidad} {cfg['nombre_rubro']} en {ciudad}...")

    for query in queries:
        if len(todas) >= cantidad:
            break
        for zona in zonas:
            if len(todas) >= cantidad:
                break
            pagetoken = ""
            for _ in range(3):
                if len(todas) >= cantidad:
                    break
                nuevos, pagetoken = _places_query(query, zona, pagetoken, vertical_id)
                for p in nuevos:
                    clave = p.place_id or p.nombre_negocio.lower()
                    if clave not in ids_vistos:
                        ids_vistos.add(clave)
                        todas.append(p)
                if not pagetoken:
                    break
                time.sleep(2)
        log.info(f"  {len(todas)} encontrados hasta ahora")

    log.info(f"Total: {len(todas)} (objetivo: {cantidad})")
    return todas[:cantidad]


# ════════════════════════════════════════════════════════════════════════════
#  DETECCIÓN DE WEB
# ════════════════════════════════════════════════════════════════════════════

def evaluar_web(website: str) -> str:
    """
    Evalúa el estado del sitio web de un prospecto.
    Devuelve: 'sin_web' | 'web_basica' | 'web_buena'
    """
    if not website:
        return "sin_web"

    # Si solo tiene redes sociales (Facebook, Instagram) no tiene web propia
    redes = ["facebook.com", "instagram.com", "tiktok.com", "twitter.com"]
    if any(red in website.lower() for red in redes):
        return "sin_web"

    # Tiene URL → asumir web básica (verificación real requeriría fetch)
    return "web_basica"


# ════════════════════════════════════════════════════════════════════════════
#  SUBAGENTE CALIFICADOR PARALELO (Haiku, lee el YAML)
# ════════════════════════════════════════════════════════════════════════════

async def _calificar_uno(prospecto: dict, cfg: dict) -> ProspectoCalificado:
    """
    Califica un prospecto usando el contexto del vertical (cfg).
    Genera mensaje personalizado. Persiste inmediatamente en DB.
    """
    nombre       = prospecto["nombre_negocio"]
    ciudad       = prospecto.get("ciudad", "")
    rating       = prospecto.get("rating", 0)
    resenas      = prospecto.get("resenas", prospecto.get("reseñas", 0))
    tiene_tel    = bool(prospecto.get("telefono"))
    website      = prospecto.get("website", "")
    estado_web   = evaluar_web(website)

    # Determinar producto sugerido según detección web
    det_web     = cfg.get("deteccion_web", {})
    cfg_web     = det_web.get(estado_web, {})
    pitch_web   = cfg_web.get("pitch")
    prod_suger  = cfg_web.get("producto_sugerido", cfg["producto_principal"])

    # Observación según volumen de reseñas
    obs_cfg    = cfg.get("observaciones_por_volumen", {})
    umbral_alt = obs_cfg.get("umbral_alto", 50)
    umbral_med = obs_cfg.get("umbral_medio", 15)
    if resenas >= umbral_alt:
        observacion = obs_cfg.get("alto", "Tienen un volumen importante de reseñas")
    elif resenas >= umbral_med:
        observacion = obs_cfg.get("medio", "Tienen buena reputación en la zona")
    else:
        observacion = obs_cfg.get("bajo", "Vi que están en la zona")

    # Precios del vertical
    precios    = cfg["precios"]
    prod       = prod_suger
    if prod == "bundle":
        precio_str = f"${precios.get('bundle_mensual_lista', 120)}/mes + ${precios.get('bundle_impl_lista', 180)} implementación"
    elif prod == "web":
        precio_str = f"${precios.get('web_mensual_lista', 50)}/mes + ${precios.get('web_impl_lista', 100)} implementación"
    else:
        precio_str = f"${precios.get('citas_mensual_lista', 80)}/mes + ${precios.get('citas_impl_lista', 100)} implementación"

    # Contexto de pitch de web (si aplica)
    pitch_web_str = f"\nPitch de web (priorizar): {pitch_web}" if pitch_web else ""

    system_prompt = f"""Eres el equipo de ventas de ValVic (automatizacion IA para negocios en Chile).

TIPO DE NEGOCIO: {cfg["nombre_rubro"]}
PROBLEMA PRINCIPAL: {cfg["problema"]["descripcion"]}
GANCHO ECONOMICO: {cfg["problema"]["gancho_economico"]}

PUNTUACION (1-10):
- 8-10: Alto volumen (sugiere demanda real), rubro bien alineado
- 5-7: Tamnio mediano, vale la pena contactar
- 1-4: Pocos datos o rubro marginal para ValVic
- Sin telefono: maximo 6 puntos

MENSAJE WHATSAPP (solo si puntuacion >= 5):
- Max 4 lineas
- Primera linea: nombre del negocio + observacion especifica
- Segunda linea: el problema concreto del rubro
- Tercera linea: una pregunta cerrada (responde si/no)
- Tono: persona real, no empresa
- Agente se llama: {cfg["agente_nombre"]}
- NO mencionar ValVic, NO precios, NO links
- Si estado_web = sin_web y hay pitch de web: empezar por ahi
- Si es web, el pitch cambia el problema (visibilidad vs citas perdidas)
- Si puntuacion < 5: mensaje_draft = ""

RESPONDE SOLO con JSON valido:
{{
  "puntuacion": 8,
  "razon": "razon breve",
  "mensaje_draft": "Hola, vi que tienen [Nombre]...",
  "producto_sugerido": "producto"
}}"""

    user_prompt = f"""NEGOCIO A EVALUAR:
- Nombre: {nombre}
- Ciudad: {ciudad}
- Google: {rating} estrellas con {resenas} resenas
- Tiene telefono: {"Si" if tiene_tel else "No"}
- Estado web: {estado_web}
- Observacion: {observacion}
{pitch_web_str}

PRODUCTO A OFRECER: {prod} (Precio: {precio_str})"""

    db = SubagenteDB()

    try:
        resp = await claude_async.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 500,
            system     = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages   = [{"role": "user", "content": user_prompt}]
        )
        texto = resp.content[0].text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        datos = json.loads(texto)

        puntuacion    = max(1, min(10, int(datos.get("puntuacion", 1))))
        mensaje_draft = datos.get("mensaje_draft", "") if puntuacion >= 5 else ""

        url_wame = ""
        if tiene_tel and mensaje_draft:
            tel = str(prospecto["telefono"]).replace("+", "").replace(" ", "").replace("-", "")
            if not tel.startswith("56"):
                tel = "56" + tel.lstrip("0")
            url_wame = f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje_draft)}"

        resultado = ProspectoCalificado(
            id            = prospecto["id"],
            puntuacion    = puntuacion,
            razon_ia      = datos.get("razon", ""),
            mensaje_draft = mensaje_draft,
            url_wame      = url_wame,
            estado        = "mensaje_listo" if puntuacion >= 5 else "descartado",
        )

        await db.persistir_calificacion_async(resultado)
        log.info(f"  [{puntuacion}/10] {nombre} → {prod}: {datos.get('razon', '')[:50]}")
        return resultado

    except Exception as e:
        log.error(f"Error calificando {nombre}: {e}")
        fallback = ProspectoCalificado(
            id=prospecto["id"], puntuacion=1,
            razon_ia=str(e), mensaje_draft="", estado="descartado",
        )
        await db.persistir_calificacion_async(fallback)
        return fallback


async def calificar_lote(prospectos: list[dict], cfg: dict) -> list[ProspectoCalificado]:
    """Califica todos en paralelo. Cada uno persiste al terminar."""
    semaforo = asyncio.Semaphore(MAX_PARALELO)

    async def con_semaforo(p: dict) -> ProspectoCalificado:
        async with semaforo:
            return await _calificar_uno(p, cfg)

    log.info(f"Calificando {len(prospectos)} prospectos en paralelo...")
    t0 = asyncio.get_event_loop().time()

    resultados = await asyncio.gather(
        *[con_semaforo(p) for p in prospectos],
        return_exceptions=True,
    )

    duracion = asyncio.get_event_loop().time() - t0
    validos  = [r for r in resultados if isinstance(r, ProspectoCalificado)]
    log.info(f"Completado: {len(validos)}/{len(prospectos)} en {duracion:.1f}s")
    return validos


# ════════════════════════════════════════════════════════════════════════════
#  ENVÍO
# ════════════════════════════════════════════════════════════════════════════

def procesar_envio(p: dict, modo_test: bool = False) -> dict:
    nombre   = p["nombre_negocio"]
    telefono = p.get("telefono", "")
    mensaje  = p.get("mensaje_draft", "")

    if not telefono:
        return {"ok": False, "metodo": "sin_telefono", "nombre": nombre}
    if not mensaje:
        return {"ok": False, "metodo": "sin_mensaje", "nombre": nombre}

    tel = str(telefono).replace("+", "").replace(" ", "").replace("-", "")
    if not tel.startswith("56"):
        tel = "56" + tel.lstrip("0")
    url_wame = f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"

    if modo_test:
        log.info(f"[TEST] → {nombre}: {mensaje[:60]}...")
        return {"ok": True, "metodo": "test", "url_wame": url_wame, "nombre": nombre}

    if DIALOG360_KEY and DIALOG360_PHONE:
        template_name = os.getenv("DIALOG360_TEMPLATE_NAME", "contacto_frio_valvic")
        try:
            resp = httpx.post(
                "https://waba.360dialog.io/v1/messages",
                headers = {"D360-API-KEY": DIALOG360_KEY, "Content-Type": "application/json"},
                json    = {
                    "to": f"+{tel}",
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": "es"},
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": mensaje}
                                ]
                            }
                        ]
                    }
                },
                timeout = 10,
            )
            resp.raise_for_status()
            return {"ok": True, "metodo": "360dialog", "url_wame": url_wame, "nombre": nombre}
        except Exception as e:
            log.error(f"360dialog error {nombre}: {e}")
            return {"ok": False, "metodo": "360dialog", "error": str(e), "nombre": nombre}

    return {"ok": True, "metodo": "wame_link", "url_wame": url_wame, "nombre": nombre}


# ════════════════════════════════════════════════════════════════════════════
#  EXPORTAR CSV
# ════════════════════════════════════════════════════════════════════════════

def exportar_csv(db: SubagenteDB, vertical: str, ruta: Optional[str] = None) -> str:
    if not ruta:
        ts   = datetime.now().strftime("%Y%m%d_%H%M")
        ruta = f"prospectos_{vertical}_{ts}.csv"

    prospectos  = db.obtener_por_estado_vertical("mensaje_listo", vertical, 500)
    prospectos += db.obtener_por_estado_vertical("contactado",    vertical, 500)

    if not prospectos:
        log.info(f"Sin prospectos para exportar ({vertical})")
        return ruta

    campos = ["id", "nombre_negocio", "telefono", "ciudad", "rating", "resenas",
              "puntuacion", "estado", "razon_ia", "mensaje_draft",
              "link_whatsapp", "google_maps", "website", "enviado_at", "created_at"]

    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for p in prospectos:
            url = p.get("url_wame", "")
            if not url and p.get("telefono") and p.get("mensaje_draft"):
                tel = str(p["telefono"]).replace("+", "").replace(" ", "").replace("-", "")
                if not tel.startswith("56"):
                    tel = "56" + tel.lstrip("0")
                url = f"https://wa.me/{tel}?text={urllib.parse.quote(p['mensaje_draft'])}"
            writer.writerow({
                "id":            p["id"],
                "nombre_negocio":p["nombre_negocio"],
                "telefono":      p.get("telefono", ""),
                "ciudad":        p.get("ciudad", ""),
                "rating":        p.get("rating", 0),
                "resenas":       p.get("resenas", p.get("reseñas", 0)),
                "puntuacion":    p.get("puntuacion", 0),
                "estado":        p.get("estado", ""),
                "razon_ia":      p.get("razon_ia", ""),
                "mensaje_draft": p.get("mensaje_draft", ""),
                "link_whatsapp": url,
                "google_maps":   p.get("maps_url", ""),
                "website":       p.get("website", ""),
                "enviado_at":    p.get("enviado_at", ""),
                "created_at":    p.get("created_at", ""),
            })

    log.info(f"CSV: {ruta} ({len(prospectos)} prospectos)")
    return ruta


# ════════════════════════════════════════════════════════════════════════════
#  ORQUESTADOR PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════

async def orquestar(cfg: dict, ciudad: str, cantidad: int, modo_test: bool, enviar: bool):
    db     = SubagenteDB()
    nombre = cfg["nombre_rubro"]
    agente = cfg["agente_nombre"]
    inicio = datetime.now()

    print(f"""
╔══════════════════════════════════════════════════════╗
║   ValVic — Prospector Multi-Vertical                ║
╠══════════════════════════════════════════════════════╣
║   Vertical: {nombre:<41}║
║   Agente:   {agente:<41}║
║   Ciudad:   {ciudad:<41}║
║   Objetivo: {cantidad:<3} prospectos                            ║
║   DB:       {db.backend.upper():<41}║
║   Modo:     {"TEST" if modo_test else "PRODUCCION":<41}║
╚══════════════════════════════════════════════════════╝
""")

    # FASE 1: Buscar
    print("─" * 56)
    print(f"  FASE 1 — Buscando {nombre}...")
    negocios = buscar_negocios(cfg, ciudad, cantidad)
    if not negocios:
        print("  Sin resultados. Verifica ciudad o agrega GOOGLE_PLACES_API_KEY")
        return

    # FASE 2: Guardar en DB
    res = db.guardar_masivo(negocios)
    print(f"  Guardados: {res.afectados} nuevos ({len(negocios) - res.afectados} ya existían)\n")

    # FASE 3: Calificar en paralelo
    nuevos = db.obtener_por_estado_vertical("nuevo", cfg["id"], cantidad)
    if nuevos:
        print(f"{'─' * 56}")
        print(f"  FASE 2 — Calificando {len(nuevos)} prospectos (paralelo, Haiku)...")
        resultados  = await calificar_lote(nuevos, cfg)
        listos      = sum(1 for r in resultados if r.estado == "mensaje_listo")
        descartados = sum(1 for r in resultados if r.estado == "descartado")
        sin_tel     = sum(1 for r in resultados
                         if r.estado == "mensaje_listo" and not r.url_wame)
        print(f"\n  Listos: {listos} | Sin teléfono: {sin_tel} | Descartados: {descartados}")

    # FASE 4: Envío
    listos_db = db.obtener_no_contactados_vertical(cfg["id"], MAX_ENVIOS_DIA)
    print(f"\n{'─' * 56}")
    print(f"  FASE 3 — Envío")
    print(f"  Con teléfono, listos: {len(listos_db)}")
    print(f"  Método: {'360dialog' if DIALOG360_KEY else 'Links wa.me (clic manual)'}")

    if not enviar and not modo_test:
        print("\n  Usa --enviar para enviar o --solo-revisar para revisar uno por uno")
    elif modo_test:
        for p in listos_db[:3]:
            procesar_envio(p, modo_test=True)
    else:
        print(f"\n  CONFIRMAR envío a {min(len(listos_db), MAX_ENVIOS_DIA)} negocios")
        confirmacion = input("  Escribe ENVIAR: ").strip()
        if confirmacion == "ENVIAR":
            enviados = 0
            for p in listos_db[:MAX_ENVIOS_DIA]:
                res_e = procesar_envio(p, modo_test=False)
                if res_e["ok"]:
                    db.marcar_contactado(p["id"])
                    enviados += 1
                    print(f"  [{res_e['metodo']}] {p['nombre_negocio']}")
                time.sleep(PAUSA_ENVIO)
            print(f"\n  Enviados: {enviados}")

    # Siempre exportar CSV
    ts   = datetime.now().strftime("%Y%m%d_%H%M")
    ruta = exportar_csv(db, cfg["id"],
                        f"prospectos_{cfg['id']}_{ciudad.lower()[:8]}_{ts}.csv")

    # Resumen final
    duracion = (datetime.now() - inicio).seconds
    print(f"""
╔══════════════════════════════════════════════════════╗
║   COMPLETADO en {duracion}s{" " * (36 - len(str(duracion)))}║
╠══════════════════════════════════════════════════════╣
{chr(10).join(f"║{l:<53}║" for l in db.resumen_vertical(cfg["id"]).split(chr(10)))}
╠══════════════════════════════════════════════════════╣
║   CSV: {ruta[:44]:<44}║
╚══════════════════════════════════════════════════════╝

  Próximos pasos:
  1. Abre el CSV → columna "link_whatsapp" tiene el link wa.me
  2. Haz clic → WhatsApp abre con el mensaje listo
  3. python prospector.py --vertical {cfg["id"]} --solo-revisar
""")


def revisar_interactivo(db: SubagenteDB, cfg: dict, limite: int = 10):
    """Revisión uno por uno con apertura de WhatsApp."""
    listos = db.obtener_no_contactados_vertical(cfg["id"], limite)
    if not listos:
        print("\n  No hay prospectos listos. Corre el agente primero.")
        return

    agente = cfg["agente_nombre"]
    print(f"\n{'=' * 58}")
    print(f"  {cfg['nombre_rubro']} — {len(listos)} prospectos | Agente: {agente}")
    print(f"{'=' * 58}")

    for p in listos:
        print(f"""
{'─' * 58}
  [{p['puntuacion']}/10] {p['nombre_negocio']}
  {p.get('ciudad', '')} | {p.get('rating', 0)}★ ({p.get('resenas', 0)} reseñas)
  Tel: {p.get('telefono', 'Sin teléfono')}
  Web: {p.get('website', '—') or '—'}
  IA:  {p.get('razon_ia', '')}

  MENSAJE ({agente}):
  {'─' * 40}""")
        for linea in (p.get("mensaje_draft") or "Sin mensaje").split("\n"):
            print(f"  {linea}")
        print(f"  {'─' * 40}")
        if p.get("url_wame"):
            print(f"\n  Link: {p['url_wame'][:65]}...")
        print("\n  [a] Abrir WhatsApp  [s] Saltar  [d] Descartar")
        decision = input("\n  Decisión: ").strip().lower()
        if decision == "a":
            if p.get("url_wame"):
                webbrowser.open(p["url_wame"])
            db.marcar_contactado(p["id"])
            print(f"  ✓ Marcado como contactado")
        elif decision == "d":
            db.marcar_descartado(p["id"])
            print(f"  Descartado")


# ════════════════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ValVic — Prospector Multi-Vertical",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python prospector.py --listar-verticales
  python prospector.py --vertical dental --ciudad Santiago --cantidad 50 --test
  python prospector.py --vertical spa --ciudad "Viña del Mar" --cantidad 30
  python prospector.py --vertical psicologos --ciudad Santiago --enviar
  python prospector.py --vertical dental --solo-revisar
  python prospector.py --vertical inmobiliarias --resumen
  python prospector.py --vertical dental --solo-exportar
        """
    )
    parser.add_argument("--vertical",          default=None)
    parser.add_argument("--ciudad",            default="Santiago")
    parser.add_argument("--cantidad",          type=int, default=30)
    parser.add_argument("--test",              action="store_true")
    parser.add_argument("--enviar",            action="store_true")
    parser.add_argument("--solo-revisar",      action="store_true")
    parser.add_argument("--solo-exportar",     action="store_true")
    parser.add_argument("--resumen",           action="store_true")
    parser.add_argument("--listar-verticales", action="store_true")
    args = parser.parse_args()

    if args.listar_verticales:
        verticales = listar_verticales()
        print(f"\nVerticales disponibles ({len(verticales)}):")
        for v in verticales:
            try:
                cfg = cargar_vertical(v)
                print(f"  {v:<20} → {cfg['nombre_rubro']} (agente: {cfg['agente_nombre']})")
            except Exception:
                print(f"  {v:<20} → [error al cargar]")
        print()
        return

    if not args.vertical:
        parser.error("Debes especificar --vertical o --listar-verticales")

    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY no configurada en el .env")
        return

    try:
        cfg = cargar_vertical(args.vertical)
    except (FileNotFoundError, ImportError, ValueError) as e:
        print(f"Error: {e}")
        return

    db = SubagenteDB()
    db.init()

    if args.resumen:
        print(f"\n{'=' * 45}")
        print(f"  {cfg['nombre_rubro']} ({db.backend.upper()})")
        print(f"{'=' * 45}")
        print(db.resumen_vertical(cfg["id"]))
        return

    if args.solo_revisar:
        revisar_interactivo(db, cfg)
        return

    if args.solo_exportar:
        ruta = exportar_csv(db, cfg["id"])
        print(f"  CSV: {ruta}")
        return

    asyncio.run(orquestar(
        cfg       = cfg,
        ciudad    = args.ciudad,
        cantidad  = min(args.cantidad, 150),
        modo_test = args.test,
        enviar    = args.enviar,
    ))


if __name__ == "__main__":
    main()
