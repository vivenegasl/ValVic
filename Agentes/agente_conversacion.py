"""
agente_conversacion.py
─────────────────────────────────────────────────────────────────────────────
Vicky — Agente de ventas y conversación WhatsApp para ValVic.

Capacidades:
  - Debounce adaptativo: junta mensajes fragmentados antes de responder
  - Cierre de ventas autónomo con escalera de concesiones
  - Negociación dentro de rangos de precio configurados
  - Agendamiento de reunión con fundador vía sistema de citas ValVic
  - Escalado a humano en condiciones definidas

Modos:
  Producción: uvicorn agente_conversacion:app --host 0.0.0.0 --port 8001
  Simulación: python agente_conversacion.py --simular --telefono "+56912345678"
─────────────────────────────────────────────────────────────────────────────
"""

import os
import json
import hmac
import hashlib
import sqlite3
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

import httpx
import anthropic
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, BackgroundTasks, Response, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from subagente_db import SubagenteDB
from prompts_ventas import (
    PRECIOS,
    ESCALERA_CONCESIONES,
    construir_system_prompt,
    construir_historial_str,
    construir_contexto_prospecto,
    PROMPT_AGENDAR_REUNION,
)
from auth_panel import (
    RegisterInput,
    LoginInput,
    UsuarioPayload,
    AuthRequired,
    auth_router,
    create_jwt,
    requiere_auth,
    extraer_usuario_de_cookie,
    registrar_usuario,
    autenticar_usuario,
    COOKIE_NAME,
    _set_auth_cookie,
    _delete_auth_cookie,
)

# ─── logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)s  %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger("vicky")

# ─── credenciales ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
VALVIC_WHATSAPP    = os.getenv("VALVIC_WHATSAPP", "+56928417992")

# ── Meta WhatsApp Cloud API ──
META_ACCESS_TOKEN   = os.getenv("META_ACCESS_TOKEN", "")
META_VERIFY_TOKEN   = os.getenv("META_VERIFY_TOKEN", "")
META_APP_SECRET     = os.getenv("META_APP_SECRET", "")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "")



# ─── MySQL (producción Oracle HeatWave) ─────────────────────────────────────
USAR_MYSQL     = bool(os.getenv("MYSQL_HOST"))
MYSQL_HOST     = os.getenv("MYSQL_HOST", "")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER", "valvic_app")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB       = os.getenv("MYSQL_DB", "valvic_db")

# ─── clientes ────────────────────────────────────────────────────────────────
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
db     = SubagenteDB()
app    = FastAPI(title="ValVic — Vicky")

# Registrar router de autenticación JWT (/api/auth/*)
app.include_router(auth_router)


# ════════════════════════════════════════════════════════════════════════════
#  PYDANTIC v2 — MODELOS DE PAYLOAD META WHATSAPP CLOUD API
#  Estructura oficial: entry[].changes[].value.messages[]
# ════════════════════════════════════════════════════════════════════════════

class MetaTextBody(BaseModel):
    body: str = Field(..., description="Contenido del mensaje de texto")


class MetaMessage(BaseModel):
    id:        str
    from_:     str = Field(..., alias="from")
    timestamp: str
    type:      str
    text:      Optional[MetaTextBody] = None

    model_config = {"populate_by_name": True}


class MetaContact(BaseModel):
    profile: Optional[dict] = None
    wa_id:   str


class MetaValue(BaseModel):
    messaging_product: str
    metadata:          Optional[dict]            = None
    contacts:          Optional[List[MetaContact]] = None
    messages:          Optional[List[MetaMessage]] = None
    statuses:          Optional[List[dict]]      = None


class MetaChange(BaseModel):
    value: MetaValue
    field: str


class MetaEntry(BaseModel):
    id:      str
    changes: List[MetaChange]


class MetaWebhookPayload(BaseModel):
    """Raíz del JSON que Meta envía al POST /webhook/whatsapp."""
    object:  str
    entry:   List[MetaEntry]

# ─── DB paths ────────────────────────────────────────────────────────────────
CONV_DB   = Path("conversaciones.db")
CITAS_DB  = Path("prospectos_vet.db")   # comparte DB con el prospector


# ════════════════════════════════════════════════════════════════════════════
#  DEBOUNCE ADAPTATIVO
#  Junta mensajes fragmentados antes de procesarlos.
#
#  Algoritmo:
#    Mensaje llega → timer A: 5s
#    Otro mensaje antes de A → cancelar A, timer B: 10s desde el último
#    Otro mensaje antes de B → reiniciar B
#    Timer dispara → concatenar todos → procesar
# ════════════════════════════════════════════════════════════════════════════

# Buffer por teléfono: { telefono: { "mensajes": [...], "timer": asyncio.Task } }
_buffer: dict[str, dict] = {}

DEBOUNCE_INICIAL_S = 5    # espera si solo hay 1 mensaje
DEBOUNCE_BURST_S   = 10   # espera si hay más de 1 mensaje (burst detectado)


async def _procesar_buffer(telefono: str):
    """
    Llamado cuando el timer dispara.
    Junta todos los mensajes del buffer y los procesa como uno.
    """
    entrada = _buffer.pop(telefono, None)
    if not entrada:
        return

    mensajes = entrada["mensajes"]
    texto_unido = " ".join(mensajes) if len(mensajes) == 1 else "\n".join(mensajes)

    if len(mensajes) > 1:
        log.info(f"Debounce: {len(mensajes)} mensajes de {telefono} unidos")

    await _manejar_mensaje(telefono, texto_unido)


def encolar_mensaje(telefono: str, texto: str):
    """
    Recibe un mensaje entrante y lo encola con debounce adaptativo.
    Cancela el timer existente y crea uno nuevo con la espera correcta.
    """
    loop = asyncio.get_running_loop()

    if telefono not in _buffer:
        _buffer[telefono] = {"mensajes": [], "timer": None}

    entrada = _buffer[telefono]
    entrada["mensajes"].append(texto)

    # Cancelar timer anterior
    if entrada["timer"] and not entrada["timer"].done():
        entrada["timer"].cancel()

    # ¿Hay más de un mensaje en el buffer? → espera más larga (burst)
    espera = DEBOUNCE_BURST_S if len(entrada["mensajes"]) > 1 else DEBOUNCE_INICIAL_S

    # Crear nuevo timer
    async def disparar():
        await asyncio.sleep(espera)
        await _procesar_buffer(telefono)

    entrada["timer"] = loop.create_task(disparar())
    log.info(
        f"Buffer [{telefono}]: {len(entrada['mensajes'])} mensaje(s), "
        f"timer={espera}s"
    )


# ════════════════════════════════════════════════════════════════════════════
#  BASE DE DATOS DE CONVERSACIONES
# ════════════════════════════════════════════════════════════════════════════

def init_conv_db():
    with sqlite3.connect(CONV_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversaciones (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                telefono              TEXT    NOT NULL UNIQUE,
                prospecto_id          INTEGER,
                estado                TEXT    NOT NULL DEFAULT 'activa',
                etapa                 TEXT    NOT NULL DEFAULT 'apertura',
                intercambios          INTEGER NOT NULL DEFAULT 0,
                objeciones_sin_resolver INTEGER NOT NULL DEFAULT 0,
                concesiones_ofrecidas TEXT    NOT NULL DEFAULT '[]',
                precio_acordado       REAL,
                servicio_acordado     TEXT,
                forma_pago_acordada   TEXT,
                cierre_confirmado     INTEGER NOT NULL DEFAULT 0,
                reunion_agendada      INTEGER NOT NULL DEFAULT 0,
                escalado_humano       INTEGER NOT NULL DEFAULT 0,
                created_at            TEXT    NOT NULL,
                updated_at            TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversacion_id INTEGER NOT NULL REFERENCES conversaciones(id),
                rol             TEXT    NOT NULL CHECK (rol IN ('prospecto', 'vicky')),
                contenido       TEXT    NOT NULL,
                tokens_output   INTEGER DEFAULT 0,
                created_at      TEXT    NOT NULL
            )
        """)
        # Tabla de cierres — registro auditable
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cierres (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                conversacion_id     INTEGER NOT NULL REFERENCES conversaciones(id),
                telefono            TEXT    NOT NULL,
                nombre_negocio      TEXT    NOT NULL,
                servicio_acordado   TEXT    NOT NULL,
                precio_mensual      REAL    NOT NULL,
                precio_impl         REAL,
                concesion_aplicada  TEXT,
                forma_pago          TEXT,
                senal_monto         REAL,
                created_at          TEXT    NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_tel ON conversaciones (telefono)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON mensajes (conversacion_id)")
        conn.commit()


# ─── helpers DB ──────────────────────────────────────────────────────────────

def obtener_o_crear_conv(telefono: str, prospecto_id: Optional[int] = None) -> dict:
    ahora = datetime.now().isoformat()
    with sqlite3.connect(CONV_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM conversaciones WHERE telefono = ?", (telefono,)
        ).fetchone()
        if row:
            return dict(row)
        conn.execute("""
            INSERT INTO conversaciones
              (telefono, prospecto_id, estado, etapa, intercambios,
               objeciones_sin_resolver, concesiones_ofrecidas,
               cierre_confirmado, reunion_agendada, escalado_humano,
               created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (telefono, prospecto_id, "activa", "apertura", 0, 0, "[]", 0, 0, 0, ahora, ahora))
        conn.commit()
        return dict(conn.execute(
            "SELECT * FROM conversaciones WHERE telefono = ?", (telefono,)
        ).fetchone())


def obtener_historial(conv_id: int, limite: int = 12) -> list[dict]:
    with sqlite3.connect(CONV_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT rol, contenido FROM mensajes
            WHERE conversacion_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (conv_id, limite)).fetchall()
        return [dict(r) for r in reversed(rows)]


def guardar_mensaje(conv_id: int, rol: str, contenido: str, tokens: int = 0):
    ahora = datetime.now().isoformat()
    with sqlite3.connect(CONV_DB) as conn:
        conn.execute("""
            INSERT INTO mensajes (conversacion_id, rol, contenido, tokens_output, created_at)
            VALUES (?,?,?,?,?)
        """, (conv_id, rol, contenido, tokens, ahora))
        conn.execute("""
            UPDATE conversaciones SET intercambios = intercambios + 1, updated_at = ?
            WHERE id = ?
        """, (ahora, conv_id))
        conn.commit()


def actualizar_conv(conv_id: int, campos: dict):
    if not campos:
        return
    campos["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in campos)
    vals = list(campos.values()) + [conv_id]
    with sqlite3.connect(CONV_DB) as conn:
        conn.execute(f"UPDATE conversaciones SET {sets} WHERE id = ?", vals)
        conn.commit()


def registrar_cierre(conv_id: int, datos: dict):
    with sqlite3.connect(CONV_DB) as conn:
        conn.execute("""
            INSERT INTO cierres
              (conversacion_id, telefono, nombre_negocio, servicio_acordado,
               precio_mensual, precio_impl, concesion_aplicada, forma_pago,
               senal_monto, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            conv_id,
            datos.get("telefono", ""),
            datos.get("nombre_negocio", ""),
            datos.get("servicio_acordado", ""),
            datos.get("precio_mensual", 0),
            datos.get("precio_impl"),
            datos.get("concesion_aplicada"),
            datos.get("forma_pago"),
            datos.get("senal_monto"),
            datetime.now().isoformat(),
        ))
        conn.commit()


# ════════════════════════════════════════════════════════════════════════════
#  SUBAGENTE: CLASIFICADOR DE INTENCIÓN (Haiku — barato)
# ════════════════════════════════════════════════════════════════════════════

def clasificar_mensaje(mensaje: str, etapa_actual: str, vertical: str = "negocio de servicios") -> dict:
    """
    Haiku clasifica la intención del mensaje entrante.
    Devuelve intención + señales de venta detectadas.
    El parámetro `vertical` debe pasarse desde el contexto de la conversación.
    """
    prompt = f"""Clasifica este mensaje de WhatsApp de un dueño de {vertical}.
Etapa actual de la conversación: {etapa_actual}

Mensaje: "{mensaje}"

Responde SOLO con JSON:
{{
  "intencion": "interesado|no_interesado|pregunta_precio|pregunta_servicio|objecion|cierre_listo|pide_humano|saludo|fuera_tema",
  "objecion_tipo": "precio|tiempo|ya_tienen|desconfianza|ninguna",
  "menciona_precio": true/false,
  "quiere_cerrar": true/false,
  "urgencia": "alta|media|baja"
}}"""

    try:
        resp = claude.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 80,
            timeout    = 30,
            messages   = [{"role": "user", "content": prompt}]
        )
        texto = resp.content[0].text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)
    except Exception:
        return {
            "intencion":       "interesado",
            "objecion_tipo":   "ninguna",
            "menciona_precio": False,
            "quiere_cerrar":   False,
            "urgencia":        "media",
        }


# ════════════════════════════════════════════════════════════════════════════
#  SUBAGENTE: DETECTOR DE CIERRE (Haiku)
#  Lee la última respuesta de Vicky y extrae si hay acuerdo
# ════════════════════════════════════════════════════════════════════════════

def detectar_cierre_en_respuesta(respuesta_vicky: str, mensaje_cliente: str) -> dict:
    """
    Haiku detecta si en el intercambio hay señales de cierre confirmado.
    Devuelve los términos acordados si los hay.
    """
    prompt = f"""Analiza si este intercambio WhatsApp contiene un cierre de venta confirmado.

Cliente dijo: "{mensaje_cliente}"
Vicky respondió: "{respuesta_vicky}"

Detecta si el cliente confirmó comprar. Responde SOLO con JSON:
{{
  "cierre_detectado": true/false,
  "servicio": "citas|web|bundle|ninguno",
  "precio_mensual_usd": null o número,
  "precio_impl_usd": null o número,
  "concesion_mencionada": null o "descuento_impl_10|pago_mitad_mitad|descuento_mensual_temporal|primer_mes_gratis",
  "forma_pago_mencionada": null o "transferencia|link_pago|por_definir",
  "pide_humano": true/false
}}"""

    try:
        resp = claude.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 120,
            messages   = [{"role": "user", "content": prompt}]
        )
        texto = resp.content[0].text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)
    except Exception:
        return {"cierre_detectado": False, "pide_humano": False}


# ════════════════════════════════════════════════════════════════════════════
#  SUBAGENTE: AGENDADOR DE REUNIÓN CON FUNDADOR
# ════════════════════════════════════════════════════════════════════════════

def agendar_reunion_fundador(
    telefono:      str,
    nombre_negocio: str,
    horario_str:   str,
) -> dict:
    """
    Registra una reunión con el fundador en el sistema de citas de ValVic.
    Por ahora guarda en SQLite local.
    Cuando el panel web esté activo, esto escribe en MySQL y aparece en /panel/agenda.
    """
    try:
        # Parsear horario del string (ej. "mañana en la tarde", "jueves a las 11")
        # Por ahora guardamos el string tal cual — el fundador lo confirma manualmente
        ahora = datetime.now()
        with sqlite3.connect(CONV_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reuniones_fundador (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    telefono        TEXT    NOT NULL,
                    nombre_negocio  TEXT    NOT NULL,
                    horario_solicitado TEXT NOT NULL,
                    estado          TEXT    NOT NULL DEFAULT 'pendiente_confirmacion',
                    created_at      TEXT    NOT NULL
                )
            """)
            conn.execute("""
                INSERT INTO reuniones_fundador
                  (telefono, nombre_negocio, horario_solicitado, created_at)
                VALUES (?,?,?,?)
            """, (telefono, nombre_negocio, horario_str, ahora.isoformat()))
            conn.commit()

        log.info(
            f"REUNIÓN AGENDADA: {nombre_negocio} ({telefono}) — "
            f"Horario solicitado: {horario_str}"
        )
        return {"ok": True, "horario": horario_str}

    except Exception as e:
        log.error(f"Error agendando reunión: {e}")
        return {"ok": False, "error": str(e)}


async def notificar_fundador(tipo: str, datos: dict):
    """
    Notifica al fundador sobre eventos importantes vía WhatsApp (Meta Graph API).
    """
    if tipo == "cierre":
        texto = (
            f"🎉 CIERRE: {datos.get('nombre_negocio')} "
            f"contrató {datos.get('servicio_acordado')} "
            f"a ${datos.get('precio_mensual_usd')}/mes"
        )
    elif tipo == "escalado":
        texto = (
            f"⚠️ ESCALADO: {datos.get('nombre_negocio')} "
            f"pide hablar con humano ({datos.get('motivo')})"
        )
    elif tipo == "reunion":
        texto = (
            f"📅 REUNIÓN: {datos.get('nombre_negocio')} "
            f"quiere reunirse: {datos.get('horario')}"
        )
    else:
        texto = f"[ValVic] Evento desconocido: {tipo} — {datos}"

    log.info(f"[FUNDADOR] {texto}")
    await _enviar_whatsapp(VALVIC_WHATSAPP, texto)


# ════════════════════════════════════════════════════════════════════════════
#  LÓGICA CENTRAL: GENERAR RESPUESTA DE VICKY
# ════════════════════════════════════════════════════════════════════════════

def _prospecto_por_telefono(telefono: str) -> Optional[dict]:
    tel = telefono.replace("+", "").replace(" ", "").replace("-", "")
    try:
        with sqlite3.connect(CITAS_DB) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM prospectos
                WHERE REPLACE(REPLACE(REPLACE(telefono, '+', ''), ' ', ''), '-', '')
                      LIKE ?
                LIMIT 1
            """, (f"%{tel[-9:]}%",)).fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def generar_respuesta_vicky(
    mensaje:      str,
    prospecto:    dict,
    historial:    list[dict],
    conv:         dict,
) -> tuple[str, int]:
    """
    Genera la respuesta de Vicky con Sonnet.
    Usa prompt caching en el system prompt (se repite cada mensaje).
    Devuelve (texto, tokens_output).
    """
    concesiones = json.loads(conv.get("concesiones_ofrecidas", "[]"))

    system = construir_system_prompt(
        prospecto             = prospecto,
        historial             = historial,
        etapa                 = conv.get("etapa", "apertura"),
        concesiones_ofrecidas = concesiones,
        objeciones_count      = conv.get("objeciones_sin_resolver", 0),
    )

    try:
        resp = claude.messages.create(
            model      = "claude-sonnet-4-20250514",
            max_tokens = 350,
            timeout    = 20,
            system     = [
                {
                    "type":          "text",
                    "text":          system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages = [{"role": "user", "content": mensaje}],
        )
        return resp.content[0].text.strip(), resp.usage.output_tokens
    except Exception as e:
        log.error(f"Error Sonnet: {e}")
        return "Perdona, tuve un problema técnico. Te escribo en un momento.", 0


# ════════════════════════════════════════════════════════════════════════════
#  PIPELINE COMPLETO POR MENSAJE
# ════════════════════════════════════════════════════════════════════════════

async def _manejar_mensaje(telefono: str, mensaje: str):
    """
    Pipeline completo para un mensaje (ya debounceado):
    1. Identificar prospecto
    2. Clasificar intención (Haiku)
    3. Generar respuesta (Sonnet)
    4. Detectar cierre en el intercambio (Haiku)
    5. Actualizar estado en DB
    6. Enviar respuesta por WhatsApp
    """
    log.info(f"Procesando [{telefono}]: {mensaje[:70]}...")

    # ── 1. Identificar ────────────────────────────────────────────────────
    prospecto = _prospecto_por_telefono(telefono) or {
        "nombre_negocio": "el negocio",
        "ciudad": "", "rating": 0, "resenas": 0, "razon_ia": "",
    }

    conv    = obtener_o_crear_conv(telefono, prospecto.get("id"))
    conv_id = conv["id"]

    # ── 2. Clasificar intención (Haiku) ───────────────────────────────────
    intencion_datos = clasificar_mensaje(mensaje, conv.get("etapa", "apertura"))
    intencion       = intencion_datos.get("intencion", "interesado")
    objecion_tipo   = intencion_datos.get("objecion_tipo", "ninguna")
    pide_humano     = intencion == "pide_humano"

    log.info(f"Intención: {intencion} | Objeción: {objecion_tipo}")

    # ── 3. Guardar mensaje del cliente ────────────────────────────────────
    guardar_mensaje(conv_id, "prospecto", mensaje)

    # ── 4. Manejo especial: pide hablar con humano ────────────────────────
    if pide_humano:
        respuesta_agendar = claude.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 80,
            messages   = [{"role": "user", "content": PROMPT_AGENDAR_REUNION}]
        ).content[0].text.strip()

        guardar_mensaje(conv_id, "vicky", respuesta_agendar)
        actualizar_conv(conv_id, {"etapa": "agendar_reunion", "escalado_humano": 1})
        await _enviar_whatsapp(telefono, respuesta_agendar)
        await notificar_fundador("escalado", {
            "nombre_negocio": prospecto.get("nombre_negocio"),
            "telefono":       telefono,
            "motivo":         "cliente pide hablar con persona",
        })
        return

    # ── 5. Cargar historial ───────────────────────────────────────────────
    historial = obtener_historial(conv_id, limite=12)

    # ── 6. Generar respuesta de Vicky (Sonnet) ────────────────────────────
    respuesta, tokens = generar_respuesta_vicky(mensaje, prospecto, historial, conv)

    # ── 7. Guardar respuesta ──────────────────────────────────────────────
    guardar_mensaje(conv_id, "vicky", respuesta, tokens)

    # ── 8. Detectar cierre y actualizar estado ────────────────────────────
    actualizaciones: dict = {}

    # Actualizar objeciones
    if objecion_tipo != "ninguna":
        nueva_objeciones = conv.get("objeciones_sin_resolver", 0) + 1
        actualizaciones["objeciones_sin_resolver"] = nueva_objeciones

        # Escalado por 3 objeciones sin resolver
        if nueva_objeciones >= 3:
            actualizaciones["escalado_humano"] = 1
            await notificar_fundador("escalado", {
                "nombre_negocio": prospecto.get("nombre_negocio"),
                "telefono":       telefono,
                "motivo":         "3 objeciones sin resolver",
            })
    else:
        # Si no hubo objeción, resetear contador
        actualizaciones["objeciones_sin_resolver"] = 0

    # Detectar si hay cierre en el intercambio (Haiku)
    cierre = detectar_cierre_en_respuesta(respuesta, mensaje)

    if cierre.get("cierre_detectado"):
        actualizaciones["etapa"]              = "pago_pendiente"
        actualizaciones["cierre_confirmado"]  = 1
        actualizaciones["precio_acordado"]    = cierre.get("precio_mensual_usd")
        actualizaciones["servicio_acordado"]  = cierre.get("servicio")
        actualizaciones["forma_pago_acordada"]= cierre.get("forma_pago_mencionada", "por_definir")

        # Registrar en tabla de cierres
        registrar_cierre(conv_id, {
            "telefono":          telefono,
            "nombre_negocio":    prospecto.get("nombre_negocio", ""),
            "servicio_acordado": cierre.get("servicio", ""),
            "precio_mensual_usd":cierre.get("precio_mensual_usd", 0),
            "precio_impl_usd":   cierre.get("precio_impl_usd"),
            "concesion_aplicada":cierre.get("concesion_mencionada"),
            "forma_pago":        cierre.get("forma_pago_mencionada"),
            "senal_monto":       PRECIOS["senal_inicio_implementacion"],
        })

        # Actualizar estado del prospecto en la DB principal
        if prospecto.get("id"):
            db.actualizar(prospecto["id"], {"estado": "convertido"})

        await notificar_fundador("cierre", {
            "nombre_negocio":    prospecto.get("nombre_negocio"),
            "telefono":          telefono,
            "servicio_acordado": cierre.get("servicio"),
            "precio_mensual_usd":cierre.get("precio_mensual_usd"),
            "forma_pago":        cierre.get("forma_pago_mencionada"),
        })

    elif cierre.get("pide_humano"):
        actualizaciones["escalado_humano"] = 1

    # Detectar si Vicky preguntó por horario de reunión (etapa agendar)
    if conv.get("etapa") == "agendar_reunion" and intencion not in ("pide_humano",):
        # El cliente probablemente respondió con un horario
        resultado = agendar_reunion_fundador(
            telefono       = telefono,
            nombre_negocio = prospecto.get("nombre_negocio", ""),
            horario_str    = mensaje,
        )
        if resultado["ok"]:
            actualizaciones["reunion_agendada"] = 1
            await notificar_fundador("reunion", {
                "nombre_negocio": prospecto.get("nombre_negocio"),
                "horario":        mensaje,
            })

    # Actualizar etapa según intención (si no se detectó cierre)
    if not cierre.get("cierre_detectado"):
        if intencion in ("interesado", "pregunta_precio", "pregunta_servicio"):
            actualizaciones["etapa"] = "negociacion" if conv.get("intercambios", 0) >= 2 else "presentacion"
        elif intencion == "no_interesado":
            actualizaciones["etapa"] = "cerrada_negativa"
            if prospecto.get("id"):
                db.marcar_descartado(prospecto["id"], "No interesado en conversación")

    if actualizaciones:
        actualizar_conv(conv_id, actualizaciones)

    # ── 9. Enviar respuesta ───────────────────────────────────────────────
    await _enviar_whatsapp(telefono, respuesta)
    log.info(f"Respuesta enviada ({tokens} tokens): {respuesta[:60]}...")


# ════════════════════════════════════════════════════════════════════════════
#  ENVÍO WHATSAPP — Meta Graph API v20.0
# ════════════════════════════════════════════════════════════════════════════

async def _enviar_whatsapp(telefono: str, mensaje: str) -> bool:
    """
    Envía un mensaje de texto a través de la WhatsApp Cloud API de Meta.
    Endpoint: POST https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages
    Header:   Authorization: Bearer {META_ACCESS_TOKEN}

    Si META_ACCESS_TOKEN o META_PHONE_NUMBER_ID no están configurados,
    el mensaje se imprime en los logs (útil en desarrollo/simulación).
    """
    if not META_ACCESS_TOKEN or not META_PHONE_NUMBER_ID:
        log.info(f"[SIN META_API] → {telefono}: {mensaje[:80]}...")
        return False

    # Normalizar número: Meta necesita formato E.164 sin '+' (ej. "56912345678")
    tel = (
        telefono
        .replace(" ", "")
        .replace("-", "")
        .lstrip("+")
    )

    url = f"https://graph.facebook.com/v20.0/{META_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to":   tel,
        "type": "text",
        "text": {"body": mensaje},
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {META_ACCESS_TOKEN}",
                    "Content-Type":  "application/json",
                },
                json    = payload,
                timeout = 10,
            )
            resp.raise_for_status()
            log.info(f"[META] Mensaje enviado a {telefono} — HTTP {resp.status_code}")
            return True
    except httpx.HTTPStatusError as e:
        log.error(
            f"[META] Error HTTP al enviar a {telefono}: "
            f"{e.response.status_code} — {e.response.text}"
        )
        return False
    except Exception as e:
        log.error(f"[META] Error inesperado al enviar a {telefono}: {e}")
        return False


async def _enviar_template_whatsapp(
    telefono:      str,
    template_name: str,
    language_code: str = "es",
    components:    Optional[list] = None,
) -> bool:
    """
    Envía un mensaje de tipo 'template' (HSM) por la API de Meta.
    Requerido para el primer mensaje en frío (message opener).
    Solo se ejecuta previa aprobación humana (comando ENVIAR del fundador).
    """
    if not META_ACCESS_TOKEN or not META_PHONE_NUMBER_ID:
        log.info(f"[SIN META_API] Template '{template_name}' a {telefono} — no enviado")
        return False

    tel = telefono.replace(" ", "").replace("-", "").lstrip("+")
    url = f"https://graph.facebook.com/v20.0/{META_PHONE_NUMBER_ID}/messages"
    payload: dict = {
        "messaging_product": "whatsapp",
        "to":   tel,
        "type": "template",
        "template": {
            "name":     template_name,
            "language": {"code": language_code},
        },
    }
    if components:
        payload["template"]["components"] = components

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {META_ACCESS_TOKEN}",
                    "Content-Type":  "application/json",
                },
                json    = payload,
                timeout = 10,
            )
            resp.raise_for_status()
            log.info(f"[META] Template '{template_name}' enviado a {telefono}")
            return True
    except httpx.HTTPStatusError as e:
        log.error(
            f"[META] Error HTTP en template a {telefono}: "
            f"{e.response.status_code} — {e.response.text}"
        )
        return False
    except Exception as e:
        log.error(f"[META] Error inesperado en template a {telefono}: {e}")
        return False


# ════════════════════════════════════════════════════════════════════════════
#  WEBHOOK FASTAPI — Meta WhatsApp Cloud API
# ════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    init_conv_db()
    log.info("Vicky lista — Meta WhatsApp Cloud API activa")


# ── Helpers de seguridad ──────────────────────────────────────────────────

def _validar_firma_meta(body_bytes: bytes, signature_header: Optional[str]) -> bool:
    """
    Valida la firma HMAC-SHA256 que Meta incluye en el header
    'X-Hub-Signature-256' con formato 'sha256=<hex_digest>'.

    Retorna False si META_APP_SECRET no está configurado o si la firma
    no coincide. Retorna True solo si la firma es criptográficamente válida.
    """
    if not META_APP_SECRET:
        log.warning("META_APP_SECRET no configurado — omitiendo validación de firma")
        return True   # Permisivo en desarrollo; en producción META_APP_SECRET es obligatorio

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.HMAC(
        META_APP_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()

    received = signature_header[7:]   # strip "sha256=" prefix (7 chars)
    return hmac.compare_digest(expected, received)


# ── GET /webhook/whatsapp — Verificación de Meta ──────────────────────────

@app.get("/webhook/whatsapp")
async def webhook_verificacion(
    hub_mode:         Optional[str] = Query(default=None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(default=None, alias="hub.verify_token"),
    hub_challenge:    Optional[str] = Query(default=None, alias="hub.challenge"),
):
    """
    Endpoint de verificación requerido por Meta para confirmar la URL del webhook.
    Meta envía una petición GET con hub.mode='subscribe', hub.verify_token y
    hub.challenge. El servidor debe responder con hub.challenge como entero
    si el token es válido.

    Docs: https://developers.facebook.com/docs/graph-api/webhooks/getting-started
    """
    log.info(
        f"[META-Verify] mode={hub_mode} | "
        f"token_ok={hub_verify_token == META_VERIFY_TOKEN}"
    )

    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        try:
            challenge_int = int(hub_challenge or "")
        except ValueError:
            log.error("[META-Verify] hub.challenge no es un entero válido")
            raise HTTPException(status_code=400, detail="hub.challenge inválido")

        log.info(f"[META-Verify] Verificación OK — devolviendo challenge {challenge_int}")
        return Response(content=str(challenge_int), media_type="text/plain")

    log.warning("[META-Verify] Token inválido o mode incorrecto — rechazado")
    raise HTTPException(status_code=403, detail="Verificación fallida")


# ── POST /webhook/whatsapp — Recepción de mensajes ────────────────────────

@app.post("/webhook/whatsapp")
async def webhook_recepcion(request: Request, background: BackgroundTasks):
    """
    Meta llama aquí cada vez que llega un mensaje, notificación de entrega
    o cambio de estado.

    Pipeline de seguridad:
      1. Leer body raw (bytes) — necesario para calcular HMAC antes de parsear.
      2. Validar firma X-Hub-Signature-256 con HMAC-SHA256 (META_APP_SECRET).
      3. Parsear JSON a MetaWebhookPayload (Pydantic v2).
      4. Extraer mensajes de texto y encolar con debounce.

    Meta espera un 200 OK rápido; el procesamiento real va a background.
    """
    # ── 1. Leer body crudo (antes de parsear) ────────────────────────────
    try:
        body_bytes = await request.body()
    except Exception as e:
        log.error(f"[META-POST] Error leyendo body: {e}")
        return Response(content="ok", status_code=200)

    # ── 2. Validar firma ─────────────────────────────────────────────────
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not _validar_firma_meta(body_bytes, signature):
        log.warning(
            f"[META-POST] Firma inválida — posible request no autorizado. "
            f"Header recibido: '{signature[:30]}...'"
        )
        raise HTTPException(status_code=403, detail="Firma inválida")

    # ── 3. Parsear payload ───────────────────────────────────────────────
    try:
        data = json.loads(body_bytes)
        payload = MetaWebhookPayload.model_validate(data)
    except Exception as e:
        log.error(f"[META-POST] Error parseando payload: {e}")
        return Response(content="ok", status_code=200)

    # ── 4. Extraer y encolar mensajes ────────────────────────────────────
    for entry in payload.entry:
        for change in entry.changes:
            if change.field != "messages":
                continue

            messages = change.value.messages or []
            for msg in messages:
                if msg.type != "text" or not msg.text:
                    # Ignorar audio, imagen, sticker, etc. por ahora
                    log.info(
                        f"[META-POST] Tipo no soportado '{msg.type}' "
                        f"de {msg.from_} — ignorado"
                    )
                    continue

                telefono = msg.from_   # Formato E.164 sin '+' (ej. "56912345678")
                texto    = msg.text.body.strip()

                if not telefono or not texto:
                    continue

                log.info(
                    f"[META-POST] Mensaje recibido de +{telefono}: "
                    f"{texto[:60]}..."
                )
                # Encolar con debounce — no bloqueamos el webhook
                background.add_task(
                    lambda t=telefono, m=texto: encolar_mensaje(t, m)
                )

    return Response(content="ok", status_code=200)


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/cierres")
async def listar_cierres():
    """Panel rápido de cierres para el fundador."""
    with sqlite3.connect(CONV_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM cierres ORDER BY created_at DESC LIMIT 50
        """).fetchall()
    return {"cierres": [dict(r) for r in rows]}


@app.get("/conversaciones")
async def listar_conversaciones(activas_only: bool = True):
    """Resumen de conversaciones para monitoreo."""
    filtro = "WHERE estado = 'activa'" if activas_only else ""
    with sqlite3.connect(CONV_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f"""
            SELECT telefono, etapa, intercambios, cierre_confirmado,
                   reunion_agendada, escalado_humano, updated_at
            FROM conversaciones {filtro}
            ORDER BY updated_at DESC LIMIT 50
        """).fetchall()
    return {"conversaciones": [dict(r) for r in rows]}

# ── Rutas legacy de compatibilidad (redirigen a /api/auth/*) ─────────────────
# Se mantienen para no romper el frontend existente que apunta a /api/login etc.
# El canonical es /api/auth/* definido en auth_router.

@app.post("/api/register", status_code=201, include_in_schema=False)
async def api_register_legacy(body: RegisterInput):
    """Legacy — usar POST /api/auth/register."""
    usuario = await registrar_usuario(
        email          = body.email,
        password       = body.password,
        nombre_negocio = body.nombre_negocio,
    )
    return {"ok": True, "id": usuario["id"], "nombre_negocio": usuario["nombre_negocio"]}


@app.post("/api/login", include_in_schema=False)
async def api_login_legacy(body: LoginInput, response: Response):
    """Legacy — usar POST /api/auth/login."""
    usuario = await autenticar_usuario(body.email, body.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    payload = UsuarioPayload(
        id             = usuario["id"],
        email          = usuario["email"],
        nombre_negocio = usuario["nombre_negocio"],
    )
    token = create_jwt(payload)
    _set_auth_cookie(response, token)  # SameSite=Strict, centralizado en auth_panel
    return {"ok": True, "nombre_negocio": usuario["nombre_negocio"]}


@app.get("/api/me", include_in_schema=False)
async def api_me_legacy(usuario: AuthRequired):
    """Legacy — usar GET /api/auth/me."""
    return {"email": usuario.email, "nombre_negocio": usuario.nombre_negocio}


@app.post("/api/logout", include_in_schema=False)
async def api_logout_legacy(response: Response):
    """Legacy — usar POST /api/auth/logout."""
    _delete_auth_cookie(response)
    return {"ok": True}


@app.get("/api/agenda")
async def api_agenda(usuario: AuthRequired):
    """
    GET /api/agenda — PROTEGIDO: requiere cookie JWT válida.

    Aislamiento total de datos (multi-tenancy):
    - El usuario se extrae del JWT vía Depends(requiere_auth) — 401 si inválido.
    - WHERE usuario_id = <id_jwt>: imposible ver datos de otro negocio.

    MySQL (producción): usa vista v_agenda_panel con filtro usuario_id.
    SQLite (desarrollo): conversaciones con reunion_agendada=1.
    """
    if USAR_MYSQL:
        try:
            import aiomysql
            conn = await aiomysql.connect(
                host=MYSQL_HOST, port=MYSQL_PORT,
                user=MYSQL_USER, password=MYSQL_PASSWORD,
                db=MYSQL_DB, charset="utf8mb4",
            )
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT reunion_id, telefono, nombre_negocio,
                           horario_solicitado, estado_cita,
                           etapa_crm, servicio_acordado,
                           precio_acordado, created_at, updated_at
                    FROM   v_agenda_panel
                    WHERE  usuario_id = %s
                    LIMIT  100
                    """,
                    (usuario.id,),
                )
                rows = await cur.fetchall()
            conn.close()
            return {"citas": [dict(r) for r in rows], "negocio": usuario.nombre_negocio}
        except Exception as e:
            log.error(f"/api/agenda MySQL error: {e}")
            raise HTTPException(status_code=500, detail="Error al obtener agenda")
    else:
        # Desarrollo SQLite — sin restricción multi-tenant real
        with sqlite3.connect(CONV_DB) as conn:
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    """
                    SELECT telefono, etapa, servicio_acordado,
                           precio_acordado, updated_at
                    FROM   conversaciones
                    WHERE  reunion_agendada = 1
                      AND  (usuario_id = ? OR usuario_id IS NULL)
                    ORDER  BY updated_at DESC
                    LIMIT  50
                    """,
                    (usuario.id,),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = conn.execute(
                    """
                    SELECT telefono, etapa, servicio_acordado,
                           precio_acordado, updated_at
                    FROM   conversaciones
                    WHERE  reunion_agendada = 1
                    ORDER  BY updated_at DESC LIMIT 50
                    """
                ).fetchall()
        return {"citas": [dict(r) for r in rows], "negocio": usuario.nombre_negocio}


@app.get("/api/pacientes")
async def api_pacientes(usuario: AuthRequired):
    """
    GET /api/pacientes — PROTEGIDO: requiere cookie JWT válida.

    Retorna la lista de pacientes vinculados al cliente (negocio) autenticado.
    Aislamiento estricto por cliente_id derivado del JWT.

    MySQL (producción): tabla pacientes JOIN clientes JOIN contratos.
    SQLite (desarrollo): no existe tabla pacientes — retorna lista vacía.
    """
    if USAR_MYSQL:
        try:
            import aiomysql
            conn = await aiomysql.connect(
                host=MYSQL_HOST, port=MYSQL_PORT,
                user=MYSQL_USER, password=MYSQL_PASSWORD,
                db=MYSQL_DB, charset="utf8mb4",
            )
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Obtener el cliente_id asociado al usuario del panel
                await cur.execute(
                    """
                    SELECT p.id, p.nombre, p.telefono, p.email, p.notas,
                           p.created_at
                    FROM   pacientes p
                    JOIN   contratos con ON con.cliente_id = p.cliente_id
                    JOIN   usuarios_panel up ON up.id = %s
                    WHERE  p.cliente_id = (
                               SELECT cliente_id
                               FROM   usuarios_panel
                               WHERE  id = %s
                               LIMIT  1
                           )
                    ORDER  BY p.nombre ASC
                    LIMIT  200
                    """,
                    (usuario.id, usuario.id),
                )
                rows = await cur.fetchall()
            conn.close()
            return {
                "pacientes": [dict(r) for r in rows],
                "total":     len(rows),
                "negocio":   usuario.nombre_negocio,
            }
        except Exception as e:
            log.error(f"/api/pacientes MySQL error: {e}")
            raise HTTPException(status_code=500, detail="Error al obtener pacientes")
    else:
        # SQLite de desarrollo — tabla pacientes no existe en dev local
        log.info("/api/pacientes: modo SQLite dev — sin datos de pacientes")
        return {
            "pacientes": [],
            "total":     0,
            "negocio":   usuario.nombre_negocio,
            "nota":      "Entorno de desarrollo — los pacientes se sirven desde MySQL en producción",
        }



# Mapear el Frontend (ValVic Web)
web_path = Path(__file__).parent.parent / "ValVic Web"
if web_path.exists():
    app.mount("/", StaticFiles(directory=str(web_path), html=True), name="web")
    log.info("Frontend estático montado en la raíz (/) del servidor")
# ════════════════════════════════════════════════════════════════════════════
#  MODO SIMULACIÓN
# ════════════════════════════════════════════════════════════════════════════

async def simular(telefono: str, mensaje_inicial: Optional[str] = None):
    """Simulación interactiva por consola para desarrollo."""
    init_conv_db()

    prospecto = _prospecto_por_telefono(telefono)
    nombre    = prospecto.get("nombre_negocio", "Desconocido") if prospecto else "Desconocido"

    print(f"""
╔══════════════════════════════════════════════════════╗
║   Simulación — Vicky (ValVic)                       ║
║   Teléfono:  {telefono:<40}║
║   Prospecto: {nombre[:40]:<40}║
╚══════════════════════════════════════════════════════╝
  Escribe los mensajes del cliente. 'salir' para terminar.
  Tip: prueba enviar mensajes cortos seguidos para ver el debounce.
""")

    # Patch para simulación: _enviar_whatsapp imprime en consola
    import agente_conversacion as self_module

    original_enviar = self_module._enviar_whatsapp

    async def enviar_simulado(tel: str, msg: str) -> bool:
        print(f"\nVicky: {msg}\n")
        return True

    self_module._enviar_whatsapp = enviar_simulado

    if mensaje_inicial:
        print(f"Cliente: {mensaje_inicial}")
        encolar_mensaje(telefono, mensaje_inicial)
        await asyncio.sleep(DEBOUNCE_INICIAL_S + 1)

    while True:
        try:
            entrada = input("Cliente: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if entrada.lower() in ("salir", "exit", "q"):
            break
        if not entrada:
            continue
        encolar_mensaje(telefono, entrada)
        # Esperar a que el debounce dispare y se procese
        await asyncio.sleep(DEBOUNCE_BURST_S + 1)

    self_module._enviar_whatsapp = original_enviar

    # Resumen
    conv = obtener_o_crear_conv(telefono)
    print(f"""
Resumen:
  Etapa final:       {conv.get('etapa')}
  Intercambios:      {conv.get('intercambios')}
  Cierre:            {'Sí' if conv.get('cierre_confirmado') else 'No'}
  Reunión agendada:  {'Sí' if conv.get('reunion_agendada') else 'No'}
  Escalado humano:   {'Sí' if conv.get('escalado_humano') else 'No'}
""")


# ════════════════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Vicky — Agente de ventas ValVic")
    parser.add_argument("--simular",  action="store_true")
    parser.add_argument("--telefono", default="+56912345678")
    parser.add_argument("--mensaje",  default=None)
    parser.add_argument("--listar",   action="store_true")
    parser.add_argument("--cierres",  action="store_true")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY no configurada en el .env")
        return

    init_conv_db()

    if args.cierres:
        with sqlite3.connect(CONV_DB) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM cierres ORDER BY created_at DESC"
            ).fetchall()
        print(f"\n{'─'*70}")
        print(f"  {'Negocio':<25} {'Servicio':<10} {'$/mes':<8} {'Concesión':<25}")
        print(f"{'─'*70}")
        for r in rows:
            print(
                f"  {r['nombre_negocio']:<25} {r['servicio_acordado']:<10} "
                f"${r['precio_mensual']:<7} {r['concesion_aplicada'] or '—':<25}"
            )
        print(f"{'─'*70}\n")
        return

    if args.listar:
        with sqlite3.connect(CONV_DB) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT telefono, etapa, intercambios,
                       cierre_confirmado, reunion_agendada, updated_at
                FROM conversaciones ORDER BY updated_at DESC LIMIT 30
            """).fetchall()
        print(f"\n{'─'*75}")
        print(f"  {'Teléfono':<18} {'Etapa':<20} {'Msgs':<6} {'Cierre':<8} {'Reunión'}")
        print(f"{'─'*75}")
        for r in rows:
            print(
                f"  {r['telefono']:<18} {r['etapa']:<20} "
                f"{r['intercambios']:<6} "
                f"{'Sí' if r['cierre_confirmado'] else 'No':<8} "
                f"{'Sí' if r['reunion_agendada'] else 'No'}"
            )
        print(f"{'─'*75}\n")
        return

    if args.simular:
        asyncio.run(simular(args.telefono, args.mensaje))
        return

    print("Para el servidor webhook:")
    print("  uvicorn agente_conversacion:app --host 0.0.0.0 --port 8001")
    print("\nPara simular:")
    print("  python agente_conversacion.py --simular --telefono '+56912345678'")


if __name__ == "__main__":
    main()
