"""
subagente_db.py
─────────────────────────────────────────────────────────────────────────────
Subagente de persistencia para el prospector de ValVic.

Responsabilidad única: leer y escribir prospectos en la base de datos.
No sabe nada de Claude, WhatsApp, ni Google Places.

Soporta dos backends:
  - SQLite  → desarrollo local (por defecto, sin configuración)
  - MySQL   → producción en Oracle HeatWave (activar con variables de entorno)

El orquestador elige el backend automáticamente según las variables de entorno.
Cuando Oracle esté listo, solo cambias las variables — el resto del código
no cambia.

Herramientas disponibles para los agentes:
  guardar_prospectos(lista)        → INSERT OR IGNORE masivo
  actualizar_prospecto(id, campos) → UPDATE campos específicos
  obtener_por_estado(estado, n)    → SELECT con filtro y orden
  obtener_no_contactados(n)        → listos con teléfono y sin enviar
  marcar_contactado(id)            → estado → "contactado" + timestamp
  marcar_descartado(id, razon)     → estado → "descartado"
  contar_por_estado()              → resumen del pipeline
  existe_por_nombre(nombre)        → deduplicación rápida
─────────────────────────────────────────────────────────────────────────────
"""

import os
import sqlite3
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

log = logging.getLogger("subagente-db")

# ─── Variables de entorno para MySQL ─────────────────────────────────────────
MYSQL_HOST     = os.getenv("MYSQL_HOST", "")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER", "")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB       = os.getenv("MYSQL_DB", "valvic_db")

# Si todas las variables MySQL están presentes → usar MySQL, sino → SQLite
USAR_MYSQL = all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB])

DB_PATH = Path("prospectos_vet.db")


# ════════════════════════════════════════════════════════════════════════════
#  MODELOS PYDANTIC v2
# ════════════════════════════════════════════════════════════════════════════

class ProspectoNuevo(BaseModel):
    """Datos de entrada al guardar un prospecto recién encontrado."""
    nombre_negocio: str
    telefono:       Optional[str]  = None
    ciudad:         str
    direccion:      str            = ""
    rating:         float          = 0.0
    reseñas:        int            = 0
    maps_url:       str            = ""
    place_id:       str            = ""
    fuente:         str            = "google_places"
    vertical:       str            = ""
    website:        str            = ""


class ProspectoCalificado(BaseModel):
    """Resultado de calificación que el subagente DB debe persistir."""
    id:             int
    puntuacion:     int   = Field(ge=1, le=10)
    razon_ia:       str
    mensaje_draft:  str
    url_wame:       str   = ""
    estado:         str   = "mensaje_listo"


class ResultadoDB(BaseModel):
    """Respuesta estándar del subagente DB."""
    ok:           bool
    afectados:    int   = 0
    error:        Optional[str] = None
    datos:        Optional[list[dict]] = None


# ════════════════════════════════════════════════════════════════════════════
#  BACKEND SQLITE (desarrollo local)
# ════════════════════════════════════════════════════════════════════════════

def _init_sqlite():
    """Crea la tabla si no existe. Idempotente."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prospectos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid            TEXT    UNIQUE NOT NULL,
                nombre_negocio  TEXT    NOT NULL,
                telefono        TEXT,
                ciudad          TEXT    NOT NULL DEFAULT '',
                direccion       TEXT    DEFAULT '',
                rating          REAL    DEFAULT 0,
                reseñas         INTEGER DEFAULT 0,
                maps_url        TEXT    DEFAULT '',
                place_id        TEXT    UNIQUE,
                fuente          TEXT    DEFAULT 'google_places',
                vertical        TEXT    DEFAULT '',
                website         TEXT    DEFAULT '',
                estado          TEXT    NOT NULL DEFAULT 'nuevo',
                puntuacion      INTEGER DEFAULT 0,
                razon_ia        TEXT    DEFAULT '',
                mensaje_draft   TEXT    DEFAULT '',
                url_wame        TEXT    DEFAULT '',
                enviado_at      TEXT,
                created_at      TEXT    NOT NULL,
                updated_at      TEXT    NOT NULL
            )
        """)
        # Índices para queries frecuentes
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_estado ON prospectos (estado, puntuacion DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ciudad ON prospectos (ciudad)"
        )
        conn.commit()


def _sqlite_guardar_masivo(prospectos: list[ProspectoNuevo]) -> ResultadoDB:
    """INSERT OR IGNORE masivo — idempotente por place_id o nombre."""
    if not prospectos:
        return ResultadoDB(ok=True, afectados=0)

    guardados = 0
    errores   = []
    ahora     = datetime.now().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        for p in prospectos:
            # place_id como clave de deduplicación; si no hay, usar nombre+ciudad
            clave_unica = p.place_id if p.place_id else f"{p.nombre_negocio}_{p.ciudad}".lower()
            try:
                cur = conn.execute("""
                    INSERT OR IGNORE INTO prospectos
                      (uuid, nombre_negocio, telefono, ciudad, direccion,
                       rating, reseñas, maps_url, place_id, fuente,
                       estado, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    str(uuid.uuid4()),
                    p.nombre_negocio,
                    p.telefono,
                    p.ciudad,
                    p.direccion,
                    p.rating,
                    p.reseñas,
                    p.maps_url,
                    clave_unica,
                    p.fuente,
                    "nuevo",
                    ahora, ahora,
                ))
                if cur.rowcount > 0:
                    guardados += 1
            except Exception as e:
                errores.append(f"{p.nombre_negocio}: {e}")

        conn.commit()

    msg = f"{len(errores)} errores: {errores[:3]}" if errores else None
    return ResultadoDB(ok=True, afectados=guardados, error=msg)


def _sqlite_actualizar(id: int, campos: dict) -> ResultadoDB:
    """UPDATE campos específicos por id."""
    if not campos:
        return ResultadoDB(ok=True, afectados=0)
    campos["updated_at"] = datetime.now().isoformat()
    sets  = ", ".join(f"{k} = ?" for k in campos)
    vals  = list(campos.values()) + [id]
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(f"UPDATE prospectos SET {sets} WHERE id = ?", vals)
            conn.commit()
            return ResultadoDB(ok=True, afectados=cur.rowcount)
    except Exception as e:
        log.error(f"Error actualizando id={id}: {e}")
        return ResultadoDB(ok=False, error=str(e))


def _sqlite_obtener(estado: str, limite: int) -> ResultadoDB:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM prospectos
            WHERE estado = ?
            ORDER BY puntuacion DESC, created_at DESC
            LIMIT ?
        """, (estado, limite)).fetchall()
        return ResultadoDB(ok=True, datos=[dict(r) for r in rows])


def _sqlite_no_contactados(limite: int) -> ResultadoDB:
    """Prospectos listos, con teléfono, que no han sido contactados."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM prospectos
            WHERE estado       = 'mensaje_listo'
              AND telefono     IS NOT NULL
              AND enviado_at   IS NULL
            ORDER BY puntuacion DESC
            LIMIT ?
        """, (limite,)).fetchall()
        return ResultadoDB(ok=True, datos=[dict(r) for r in rows])


def _sqlite_contar() -> ResultadoDB:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT estado, COUNT(*) as total
            FROM prospectos
            GROUP BY estado
            ORDER BY total DESC
        """).fetchall()
        return ResultadoDB(ok=True, datos=[{"estado": r[0], "total": r[1]} for r in rows])


def _sqlite_existe(nombre: str, ciudad: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT 1 FROM prospectos
            WHERE LOWER(nombre_negocio) = LOWER(?)
              AND LOWER(ciudad) = LOWER(?)
            LIMIT 1
        """, (nombre, ciudad)).fetchone()
        return row is not None


# ════════════════════════════════════════════════════════════════════════════
#  BACKEND MYSQL (producción — Oracle HeatWave)
#  Se activa automáticamente cuando MYSQL_HOST está configurado
# ════════════════════════════════════════════════════════════════════════════

async def _mysql_guardar_masivo(prospectos: list[ProspectoNuevo]) -> ResultadoDB:
    """
    Equivalente async de _sqlite_guardar_masivo para MySQL.
    Usa aiomysql — solo disponible cuando Oracle está activo.
    """
    try:
        import aiomysql  # noqa: import tardío — no falla si no está instalado
    except ImportError:
        return ResultadoDB(ok=False, error="aiomysql no instalado: pip install aiomysql")

    if not prospectos:
        return ResultadoDB(ok=True, afectados=0)

    guardados = 0
    ahora     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            db=MYSQL_DB, charset="utf8mb4", autocommit=False,
        )
        async with conn.cursor() as cur:
            for p in prospectos:
                clave = p.place_id if p.place_id else f"{p.nombre_negocio}_{p.ciudad}".lower()
                await cur.execute("""
                    INSERT IGNORE INTO prospectos
                      (uuid, nombre_negocio, telefono, ciudad, direccion,
                       rating, reseñas, maps_url, place_id, fuente,
                       estado, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    str(uuid.uuid4()),
                    p.nombre_negocio, p.telefono, p.ciudad, p.direccion,
                    p.rating, p.reseñas, p.maps_url, clave, p.fuente,
                    "nuevo", ahora, ahora,
                ))
                if cur.rowcount > 0:
                    guardados += 1
        await conn.commit()
        conn.close()
        return ResultadoDB(ok=True, afectados=guardados)
    except Exception as e:
        log.error(f"MySQL guardar_masivo error: {e}")
        return ResultadoDB(ok=False, error=str(e))


async def _mysql_obtener(estado: str, limite: int) -> ResultadoDB:
    try:
        import aiomysql
    except ImportError:
        return ResultadoDB(ok=False, error="aiomysql no instalado")
    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            db=MYSQL_DB, charset="utf8mb4",
        )
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM prospectos WHERE estado = %s ORDER BY puntuacion DESC, created_at DESC LIMIT %s",
                (estado, limite),
            )
            rows = await cur.fetchall()
        conn.close()
        return ResultadoDB(ok=True, datos=list(rows))
    except Exception as e:
        log.error(f"MySQL obtener error: {e}")
        return ResultadoDB(ok=False, error=str(e))


async def _mysql_no_contactados(limite: int) -> ResultadoDB:
    try:
        import aiomysql
    except ImportError:
        return ResultadoDB(ok=False, error="aiomysql no instalado")
    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            db=MYSQL_DB, charset="utf8mb4",
        )
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM prospectos WHERE estado = 'mensaje_listo' AND telefono IS NOT NULL AND enviado_at IS NULL ORDER BY puntuacion DESC LIMIT %s",
                (limite,),
            )
            rows = await cur.fetchall()
        conn.close()
        return ResultadoDB(ok=True, datos=list(rows))
    except Exception as e:
        log.error(f"MySQL no_contactados error: {e}")
        return ResultadoDB(ok=False, error=str(e))


async def _mysql_contar() -> ResultadoDB:
    try:
        import aiomysql
    except ImportError:
        return ResultadoDB(ok=False, error="aiomysql no instalado")
    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            db=MYSQL_DB, charset="utf8mb4",
        )
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT estado, COUNT(*) as total FROM prospectos GROUP BY estado ORDER BY total DESC"
            )
            rows = await cur.fetchall()
        conn.close()
        return ResultadoDB(ok=True, datos=[{"estado": r[0], "total": r[1]} for r in rows])
    except Exception as e:
        log.error(f"MySQL contar error: {e}")
        return ResultadoDB(ok=False, error=str(e))


async def _mysql_existe(nombre: str, ciudad: str) -> bool:
    try:
        import aiomysql
    except ImportError:
        return False
    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            db=MYSQL_DB, charset="utf8mb4",
        )
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM prospectos WHERE LOWER(nombre_negocio) = LOWER(%s) AND LOWER(ciudad) = LOWER(%s) LIMIT 1",
                (nombre, ciudad),
            )
            row = await cur.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        log.error(f"MySQL existe error: {e}")
        return False


async def _mysql_actualizar(id: int, campos: dict) -> ResultadoDB:
    try:
        import aiomysql
    except ImportError:
        return ResultadoDB(ok=False, error="aiomysql no instalado")

    if not campos:
        return ResultadoDB(ok=True, afectados=0)
    campos["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sets = ", ".join(f"{k} = %s" for k in campos)
    vals = list(campos.values()) + [id]

    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            db=MYSQL_DB, charset="utf8mb4",
        )
        async with conn.cursor() as cur:
            await cur.execute(f"UPDATE prospectos SET {sets} WHERE id = %s", vals)
        await conn.commit()
        conn.close()
        return ResultadoDB(ok=True, afectados=1)
    except Exception as e:
        log.error(f"MySQL actualizar error: {e}")
        return ResultadoDB(ok=False, error=str(e))


# ════════════════════════════════════════════════════════════════════════════
#  API PÚBLICA DEL SUBAGENTE
#  El resto del código SOLO usa estas funciones — nunca llama SQLite/MySQL directo
# ════════════════════════════════════════════════════════════════════════════

class SubagenteDB:
    """
    Interfaz única para persistencia.
    Elige el backend automáticamente según las variables de entorno.

    Uso:
        db = SubagenteDB()
        db.init()
        resultado = db.guardar_masivo(lista_de_prospectos)
        listos    = db.obtener_no_contactados(30)
    """

    def __init__(self):
        self.backend = "mysql" if USAR_MYSQL else "sqlite"
        log.info(f"SubagenteDB iniciado — backend: {self.backend.upper()}")

    def init(self):
        """Inicializa la base de datos (crea tablas si no existen)."""
        if self.backend == "sqlite":
            _init_sqlite()
            log.info(f"SQLite inicializado: {DB_PATH}")
        else:
            log.info("MySQL — asumiendo que el schema ya fue ejecutado en Oracle")

    # ── Escritura ────────────────────────────────────────────────────────────

    def guardar_masivo(self, prospectos: list[ProspectoNuevo]) -> ResultadoDB:
        """
        Guarda una lista de prospectos nuevos.
        Idempotente — ejecutar dos veces no duplica registros.
        """
        if self.backend == "mysql":
            import asyncio
            return asyncio.run(_mysql_guardar_masivo(prospectos))
        return _sqlite_guardar_masivo(prospectos)

    async def guardar_masivo_async(self, prospectos: list[ProspectoNuevo]) -> ResultadoDB:
        """Versión async para usar dentro de coroutines."""
        if self.backend == "mysql":
            return await _mysql_guardar_masivo(prospectos)
        # SQLite no es async-native pero es suficientemente rápido para esto
        return _sqlite_guardar_masivo(prospectos)

    def actualizar(self, id: int, campos: dict) -> ResultadoDB:
        """Actualiza campos específicos de un prospecto por id."""
        if self.backend == "mysql":
            import asyncio
            return asyncio.run(_mysql_actualizar(id, campos))
        return _sqlite_actualizar(id, campos)

    async def actualizar_async(self, id: int, campos: dict) -> ResultadoDB:
        """Versión async de actualizar."""
        if self.backend == "mysql":
            return await _mysql_actualizar(id, campos)
        return _sqlite_actualizar(id, campos)

    def persistir_calificacion(self, r: ProspectoCalificado) -> ResultadoDB:
        """
        Persiste el resultado de calificación de un prospecto.
        Llamada directa después de que el subagente calificador termina.
        """
        campos = {
            "estado":        r.estado,
            "puntuacion":    r.puntuacion,
            "razon_ia":      r.razon_ia,
            "mensaje_draft": r.mensaje_draft,
            "url_wame":      r.url_wame,
        }
        return self.actualizar(r.id, campos)

    async def persistir_calificacion_async(self, r: ProspectoCalificado) -> ResultadoDB:
        """Versión async de persistir_calificacion — usar dentro de gather()."""
        campos = {
            "estado":        r.estado,
            "puntuacion":    r.puntuacion,
            "razon_ia":      r.razon_ia,
            "mensaje_draft": r.mensaje_draft,
            "url_wame":      r.url_wame,
        }
        return await self.actualizar_async(r.id, campos)

    def marcar_contactado(self, id: int) -> ResultadoDB:
        return self.actualizar(id, {
            "estado":     "contactado",
            "enviado_at": datetime.now().isoformat(),
        })

    def marcar_descartado(self, id: int, razon: str = "") -> ResultadoDB:
        return self.actualizar(id, {
            "estado":   "descartado",
            "razon_ia": razon,
        })

    # ── Lectura ──────────────────────────────────────────────────────────────

    def obtener_por_estado(self, estado: str, limite: int = 100) -> list[dict]:
        if self.backend == "mysql":
            import asyncio
            resultado = asyncio.run(_mysql_obtener(estado, limite))
        else:
            resultado = _sqlite_obtener(estado, limite)
        return resultado.datos or []

    def obtener_no_contactados(self, limite: int = 30) -> list[dict]:
        """
        Prospectos listos para contactar:
        - estado = 'mensaje_listo'
        - tienen teléfono
        - no han sido enviados aún
        Ordenados por puntuación descendente.
        """
        if self.backend == "mysql":
            import asyncio
            resultado = asyncio.run(_mysql_no_contactados(limite))
        else:
            resultado = _sqlite_no_contactados(limite)
        return resultado.datos or []

    def contar_por_estado(self) -> dict[str, int]:
        if self.backend == "mysql":
            import asyncio
            resultado = asyncio.run(_mysql_contar())
        else:
            resultado = _sqlite_contar()
        if not resultado.datos:
            return {}
        return {r["estado"]: r["total"] for r in resultado.datos}

    def existe(self, nombre: str, ciudad: str) -> bool:
        """Verificación rápida de duplicados antes de llamar a Places API."""
        if self.backend == "mysql":
            import asyncio
            return asyncio.run(_mysql_existe(nombre, ciudad))
        return _sqlite_existe(nombre, ciudad)

    def total(self) -> int:
        conteo = self.contar_por_estado()
        return sum(conteo.values())

    async def obtener_por_estado_async(self, estado: str, limite: int = 100) -> list[dict]:
        if self.backend == "mysql":
            import asyncio
            resultado = await _mysql_obtener(estado, limite)
        else:
            resultado = _sqlite_obtener(estado, limite)
        return resultado.datos or []

    async def obtener_no_contactados_async(self, limite: int = 30) -> list[dict]:
        if self.backend == "mysql":
            import asyncio
            resultado = await _mysql_no_contactados(limite)
        else:
            resultado = _sqlite_no_contactados(limite)
        return resultado.datos or []

    async def contar_por_estado_async(self) -> dict[str, int]:
        if self.backend == "mysql":
            import asyncio
            resultado = await _mysql_contar()
        else:
            resultado = _sqlite_contar()
        if not resultado.datos:
            return {}
        return {r["estado"]: r["total"] for r in resultado.datos}

    async def existe_async(self, nombre: str, ciudad: str) -> bool:
        if self.backend == "mysql":
            import asyncio
            return await _mysql_existe(nombre, ciudad)
        return _sqlite_existe(nombre, ciudad)

    async def marcar_contactado_async(self, id: int) -> ResultadoDB:
        return await self.actualizar_async(id, {
            "estado":     "contactado",
            "enviado_at": datetime.now().isoformat(),
        })

    async def marcar_descartado_async(self, id: int, razon: str = "") -> ResultadoDB:
        return await self.actualizar_async(id, {
            "estado":   "descartado",
            "razon_ia": razon,
        })

    # ── Diagnóstico ──────────────────────────────────────────────────────────

    def resumen(self) -> str:
        """String formateado para imprimir el estado del pipeline."""
        stats = self.contar_por_estado()
        if not stats:
            return "  Pipeline vacío"
        lineas = []
        total  = 0
        for estado, cnt in sorted(stats.items(), key=lambda x: -x[1]):
            barra = "█" * min(cnt, 25) + "░" * max(0, 25 - min(cnt, 25))
            lineas.append(f"  {estado:<22} {barra} {cnt}")
            total += cnt
        lineas.append(f"  {'─' * 50}")
        lineas.append(f"  {'TOTAL':<22}{'':>26} {total}")

    # â”€â”€ Multi-vertical â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def obtener_por_estado_vertical(self, estado: str, vertical: str, limite: int = 100) -> list[dict]:
        resultado = _sqlite_obtener_vertical(estado, vertical, limite)
        return resultado.datos or []

    def obtener_no_contactados_vertical(self, vertical: str, limite: int = 30) -> list[dict]:
        resultado = _sqlite_no_contactados_vertical(vertical, limite)
        return resultado.datos or []

    def resumen_vertical(self, vertical: str) -> str:
        stats = _sqlite_contar_vertical(vertical).datos or []
        if not stats:
            return "  Pipeline vacÃ­o"
        lineas = []
        total  = 0
        for s in stats:
            cnt   = s["total"]
            barra = "â–ˆ" * min(cnt, 25) + "â–‘" * max(0, 25 - min(cnt, 25))
            lineas.append(f"  {s['estado']:<22} {barra} {cnt}")
            total += cnt
        lineas.append(f"  {'â”€' * 50}")
        lineas.append(f"  {'TOTAL':<22}{'':<26} {total}")
        return "\n".join(lineas)

    async def obtener_por_estado_vertical_async(self, estado: str, vertical: str, limite: int = 100) -> list[dict]:
        resultado = _sqlite_obtener_vertical(estado, vertical, limite)
        return resultado.datos or []

    async def obtener_no_contactados_vertical_async(self, vertical: str, limite: int = 30) -> list[dict]:
        resultado = _sqlite_no_contactados_vertical(vertical, limite)
        return resultado.datos or []


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  HELPERS PRIVADOS MULTI-VERTICAL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def _sqlite_obtener_vertical(estado: str, vertical: str, limite: int) -> ResultadoDB:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM prospectos
            WHERE estado = ? AND (vertical = ? OR vertical IS NULL OR vertical = '')
            ORDER BY puntuacion DESC, created_at DESC
            LIMIT ?
        """, (estado, vertical, limite)).fetchall()
        return ResultadoDB(ok=True, datos=[dict(r) for r in rows])


def _sqlite_no_contactados_vertical(vertical: str, limite: int) -> ResultadoDB:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM prospectos
            WHERE estado = 'mensaje_listo'
              AND telefono IS NOT NULL
              AND enviado_at IS NULL
              AND (vertical = ? OR vertical IS NULL OR vertical = '')
            ORDER BY puntuacion DESC
            LIMIT ?
        """, (vertical, limite)).fetchall()
        return ResultadoDB(ok=True, datos=[dict(r) for r in rows])


def _sqlite_contar_vertical(vertical: str) -> ResultadoDB:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT estado, COUNT(*) as total FROM prospectos
            WHERE vertical = ? OR vertical IS NULL OR vertical = ''
            GROUP BY estado ORDER BY total DESC
        """, (vertical,)).fetchall()
        return ResultadoDB(ok=True, datos=[{"estado": r[0], "total": r[1]} for r in rows])