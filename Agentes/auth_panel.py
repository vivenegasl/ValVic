"""
auth_panel.py — Módulo de autenticación JWT para el panel CRM de ValVic.

Proporciona:
  - Hash y verificación de contraseñas con bcrypt
  - Generación y validación de tokens JWT (cookie HttpOnly)
  - Registro e inicio de sesión en usuarios_panel (MySQL o SQLite)
  - Helper de extracción de usuario desde Request (sin middleware mágico)

NO usar como middleware. Llamar explícitamente en cada endpoint que requiera auth.
"""

import os
import uuid
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException
from pydantic import BaseModel, EmailStr

log = logging.getLogger("auth_panel")

# ── Configuración ────────────────────────────────────────────────────────────
JWT_SECRET    = os.getenv("JWT_SECRET", "CAMBIAR-este-secreto-en-produccion-minimo-64-chars")
JWT_ALGORITHM = "HS256"
JWT_TTL_HOURS = 24
COOKIE_NAME   = "vv_token"

# Backend MySQL si está configurado, SQLite como fallback local
USAR_MYSQL  = bool(os.getenv("MYSQL_HOST"))
MYSQL_HOST  = os.getenv("MYSQL_HOST", "")
MYSQL_PORT  = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER  = os.getenv("MYSQL_USER", "valvic_app")
MYSQL_PASS  = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB    = os.getenv("MYSQL_DB", "valvic_db")

# SQLite local (solo desarrollo)
AUTH_DB = Path(__file__).parent / "auth_local.db"

# ── Contexto bcrypt ──────────────────────────────────────────────────────────
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ════════════════════════════════════════════════════════════════════════════
#  PYDANTIC SCHEMAS
# ════════════════════════════════════════════════════════════════════════════

class RegisterInput(BaseModel):
    email:         EmailStr
    password:      str
    nombre_negocio: str


class LoginInput(BaseModel):
    email:    EmailStr
    password: str


class UsuarioPayload(BaseModel):
    """Payload del JWT — datos mínimos necesarios para operar."""
    id:             str
    email:          str
    nombre_negocio: str


# ════════════════════════════════════════════════════════════════════════════
#  FUNCIONES PURAS — sin dependencias de BD
# ════════════════════════════════════════════════════════════════════════════

def hash_password(plain: str) -> str:
    """Retorna el hash bcrypt de la contraseña."""
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt."""
    return _pwd_ctx.verify(plain, hashed)


def create_jwt(payload: UsuarioPayload) -> str:
    """
    Genera un JWT firmado con HS256.
    Incluye 'exp' (24h) y 'iat' en el payload.
    """
    now = datetime.now(timezone.utc)
    data = {
        "sub":             payload.id,
        "email":           payload.email,
        "nombre_negocio":  payload.nombre_negocio,
        "iat":             now,
        "exp":             now + timedelta(hours=JWT_TTL_HOURS),
    }
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    """
    Decodifica y valida el JWT.
    Retorna el payload como dict, o None si es inválido/expirado.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        log.warning("JWT expirado")
        return None
    except jwt.InvalidTokenError as e:
        log.warning(f"JWT inválido: {e}")
        return None


def extraer_usuario_de_cookie(request: Request) -> UsuarioPayload:
    """
    Extrae y valida el usuario desde la cookie JWT.

    IMPORTANTE: Llamar explícitamente en cada endpoint protegido.
    NO es un middleware — no se aplica automáticamente.

    Lanza HTTPException(401) si:
      - La cookie no existe
      - El JWT es inválido o expirado
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")

    return UsuarioPayload(
        id             = payload["sub"],
        email          = payload["email"],
        nombre_negocio = payload["nombre_negocio"],
    )


# ════════════════════════════════════════════════════════════════════════════
#  BACKEND SQLite (desarrollo local)
# ════════════════════════════════════════════════════════════════════════════

def _init_auth_sqlite() -> None:
    """Crea la tabla usuarios_panel en SQLite si no existe."""
    with sqlite3.connect(AUTH_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_panel (
                id             TEXT    PRIMARY KEY,
                email          TEXT    NOT NULL UNIQUE,
                password_hash  TEXT    NOT NULL,
                nombre_negocio TEXT    NOT NULL DEFAULT '',
                rol            TEXT    NOT NULL DEFAULT 'operador',
                activo         INTEGER NOT NULL DEFAULT 1,
                ultimo_acceso  TEXT,
                created_at     TEXT    NOT NULL
            )
        """)
        conn.commit()


def _sqlite_registrar(email: str, password_hash: str, nombre_negocio: str) -> dict:
    ahora   = datetime.now().isoformat()
    user_id = str(uuid.uuid4())
    with sqlite3.connect(AUTH_DB) as conn:
        try:
            conn.execute(
                """INSERT INTO usuarios_panel
                   (id, email, password_hash, nombre_negocio, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, email.lower(), password_hash, nombre_negocio, ahora),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="El email ya está registrado")
    return {"id": user_id, "email": email.lower(), "nombre_negocio": nombre_negocio}


def _sqlite_autenticar(email: str) -> Optional[dict]:
    with sqlite3.connect(AUTH_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM usuarios_panel WHERE email = ? AND activo = 1",
            (email.lower(),),
        ).fetchone()
    return dict(row) if row else None


def _sqlite_actualizar_acceso(user_id: str) -> None:
    with sqlite3.connect(AUTH_DB) as conn:
        conn.execute(
            "UPDATE usuarios_panel SET ultimo_acceso = ? WHERE id = ?",
            (datetime.now().isoformat(), user_id),
        )
        conn.commit()


# ════════════════════════════════════════════════════════════════════════════
#  BACKEND MySQL (producción — Oracle HeatWave)
# ════════════════════════════════════════════════════════════════════════════

async def _mysql_registrar(email: str, password_hash: str, nombre_negocio: str) -> dict:
    try:
        import aiomysql
    except ImportError:
        raise HTTPException(status_code=500, detail="aiomysql no instalado")

    user_id = str(uuid.uuid4())
    ahora   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASS,
            db=MYSQL_DB, charset="utf8mb4",
        )
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    """INSERT INTO usuarios_panel
                       (id, email, password_hash, nombre_negocio, created_at)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (user_id, email.lower(), password_hash, nombre_negocio, ahora),
                )
            except Exception as e:
                if "Duplicate" in str(e) or "1062" in str(e):
                    raise HTTPException(status_code=409, detail="El email ya está registrado")
                raise
        await conn.commit()
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"MySQL registrar error: {e}")
        raise HTTPException(status_code=500, detail="Error de base de datos")
    return {"id": user_id, "email": email.lower(), "nombre_negocio": nombre_negocio}


async def _mysql_autenticar(email: str) -> Optional[dict]:
    try:
        import aiomysql
    except ImportError:
        return None

    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASS,
            db=MYSQL_DB, charset="utf8mb4",
        )
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM usuarios_panel WHERE email = %s AND activo = 1 LIMIT 1",
                (email.lower(),),
            )
            row = await cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        log.error(f"MySQL autenticar error: {e}")
        return None


async def _mysql_actualizar_acceso(user_id: str) -> None:
    try:
        import aiomysql
    except ImportError:
        return

    try:
        conn = await aiomysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASS,
            db=MYSQL_DB, charset="utf8mb4",
        )
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE usuarios_panel SET ultimo_acceso = NOW() WHERE id = %s",
                (user_id,),
            )
        await conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"MySQL actualizar_acceso error: {e}")


# ════════════════════════════════════════════════════════════════════════════
#  API PÚBLICA — llamar desde agente_conversacion.py
# ════════════════════════════════════════════════════════════════════════════

async def registrar_usuario(email: str, password: str, nombre_negocio: str) -> dict:
    """
    Crea un nuevo usuario en usuarios_panel.
    Retorna {"id", "email", "nombre_negocio"}.
    Lanza HTTPException(409) si el email ya existe.
    """
    pwd_hash = hash_password(password)
    if USAR_MYSQL:
        return await _mysql_registrar(email, pwd_hash, nombre_negocio)
    _init_auth_sqlite()
    return _sqlite_registrar(email, pwd_hash, nombre_negocio)


async def autenticar_usuario(email: str, password: str) -> Optional[dict]:
    """
    Verifica credenciales. Retorna el registro del usuario o None.
    Actualiza `ultimo_acceso` en caso de éxito.
    """
    if USAR_MYSQL:
        usuario = await _mysql_autenticar(email)
    else:
        _init_auth_sqlite()
        usuario = _sqlite_autenticar(email)

    if not usuario:
        return None
    if not verify_password(password, usuario["password_hash"]):
        return None

    # Actualizar último acceso (non-blocking)
    if USAR_MYSQL:
        await _mysql_actualizar_acceso(usuario["id"])
    else:
        _sqlite_actualizar_acceso(usuario["id"])

    return usuario
