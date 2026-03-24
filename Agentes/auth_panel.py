"""
auth_panel.py — Módulo de autenticación JWT para el panel CRM de ValVic.

Proporciona:
  - Hash y verificación de contraseñas con bcrypt
  - Generación y validación de tokens JWT (HS256, 24h, cookie HttpOnly+Secure+Strict)
  - Registro e inicio de sesión en usuarios_panel (MySQL HeatWave o SQLite dev)
  - FastAPI Dependency `requiere_auth` — inyectar en cualquier endpoint protegido
  - Router completo: /api/auth/login, /api/auth/logout, /api/auth/me, /api/register

NO usar como middleware global. Inyectar `requiere_auth` explícitamente en cada
endpoint que requiera autenticación para control granular y auditoría clara.
"""

import os
import uuid
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Annotated

import jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, field_validator

log = logging.getLogger("auth_panel")

# ── Configuración ──────────────────────────────────────────────────────────────
JWT_SECRET    = os.getenv("JWT_SECRET", "CAMBIAR-este-secreto-en-produccion-minimo-64-chars")
JWT_ALGORITHM = "HS256"
JWT_TTL_HOURS = 24
COOKIE_NAME   = "vv_token"

# Producción: MySQL HeatWave (Oracle). Desarrollo: SQLite local.
USAR_MYSQL  = bool(os.getenv("MYSQL_HOST"))
MYSQL_HOST  = os.getenv("MYSQL_HOST", "")
MYSQL_PORT  = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER  = os.getenv("MYSQL_USER", "valvic_app")
MYSQL_PASS  = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB    = os.getenv("MYSQL_DB", "valvic_db")

# Determina si el servidor corre con HTTPS (producción Oracle)
IS_HTTPS = os.getenv("ENVIRONMENT", "development") == "production"

# SQLite local (solo desarrollo sin MYSQL_HOST)
AUTH_DB = Path(__file__).parent / "auth_local.db"

# ── Contexto bcrypt ────────────────────────────────────────────────────────────
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ════════════════════════════════════════════════════════════════════════════════
#  PYDANTIC v2 SCHEMAS
# ════════════════════════════════════════════════════════════════════════════════

class RegisterInput(BaseModel):
    """Schema de entrada para registro de nuevo usuario del panel."""
    email:          EmailStr
    password:       str
    nombre_negocio: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class LoginInput(BaseModel):
    """Schema de entrada para el login en el panel CRM."""
    email:    EmailStr
    password: str


class UsuarioPayload(BaseModel):
    """
    Payload mínimo del JWT — solo los datos necesarios para operar.
    Principio de mínimo privilegio: NO incluir password_hash ni datos sensibles.
    """
    id:             str
    email:          str
    nombre_negocio: str


class LoginResponse(BaseModel):
    """Respuesta exitosa de login."""
    ok:             bool = True
    nombre_negocio: str


class RegisterResponse(BaseModel):
    """Respuesta exitosa de registro."""
    ok:             bool = True
    id:             str
    nombre_negocio: str


# ════════════════════════════════════════════════════════════════════════════════
#  FUNCIONES CRIPTOGRÁFICAS PURAS — sin dependencias de BD
# ════════════════════════════════════════════════════════════════════════════════

def hash_password(plain: str) -> str:
    """Retorna el hash bcrypt de la contraseña. NUNCA almacenar texto plano."""
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt de forma segura."""
    return _pwd_ctx.verify(plain, hashed)


def create_jwt(payload: UsuarioPayload) -> str:
    """
    Genera un JWT firmado con HS256 usando JWT_SECRET de .env.
    Incluye 'exp' (24h), 'iat' (emisión) y 'sub' (id de usuario).
    """
    now = datetime.now(timezone.utc)
    data = {
        "sub":            payload.id,
        "email":          payload.email,
        "nombre_negocio": payload.nombre_negocio,
        "iat":            now,
        "exp":            now + timedelta(hours=JWT_TTL_HOURS),
    }
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    """
    Decodifica y valida el JWT.
    Retorna el payload como dict o None si es inválido/expirado.
    PyJWT valida 'exp' automáticamente → no requiere validación manual.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        log.warning("JWT expirado — sesión caducada")
        return None
    except jwt.InvalidTokenError as e:
        log.warning(f"JWT inválido: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════════
#  FASTAPI DEPENDENCY: requiere_auth
#  Inyectar con Depends() en cualquier endpoint que requiera autenticación.
# ════════════════════════════════════════════════════════════════════════════════

def requiere_auth(request: Request) -> UsuarioPayload:
    """
    FastAPI Dependency que verifica la cookie JWT y retorna el usuario.

    Uso:
        @app.get("/api/agenda")
        async def agenda(usuario: Annotated[UsuarioPayload, Depends(requiere_auth)]):
            ...

    Lanza HTTPException(401) si:
      - La cookie `vv_token` no existe
      - El JWT es inválido, está expirado o fue manipulado

    NO es middleware global — se aplica únicamente donde se inyecta.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="No autenticado. Inicia sesión en /panel/login.html",
            headers={"WWW-Authenticate": "Cookie"},
        )

    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida o expirada. Vuelve a iniciar sesión.",
            headers={"WWW-Authenticate": "Cookie"},
        )

    try:
        return UsuarioPayload(
            id=payload["sub"],
            email=payload["email"],
            nombre_negocio=payload["nombre_negocio"],
        )
    except (KeyError, Exception) as e:
        log.error(f"Error construyendo UsuarioPayload desde JWT: {e}")
        raise HTTPException(status_code=401, detail="Token malformado")


# Alias para retrocompatibilidad con código existente
def extraer_usuario_de_cookie(request: Request) -> UsuarioPayload:
    """Alias de `requiere_auth`. Usar con Depends() en nuevos endpoints."""
    return requiere_auth(request)


# Tipo anotado para use con FastAPI Depends — más limpio en firma de función
AuthRequired = Annotated[UsuarioPayload, Depends(requiere_auth)]


# ════════════════════════════════════════════════════════════════════════════════
#  COOKIE HELPER — configuración centralizada y segura
# ════════════════════════════════════════════════════════════════════════════════

def _set_auth_cookie(response: Response, token: str) -> None:
    """
    Setea la cookie JWT con todos los flags de seguridad requeridos por PROYECTO.md:
      - HttpOnly: JS del navegador NO puede leer la cookie (protección XSS)
      - Secure: Solo se envía por HTTPS en producción
      - SameSite=Strict: Máxima protección CSRF — no se envía en cross-site
      - max_age=86400: Expira en 24h (sincronizado con JWT_TTL_HOURS)
    """
    response.set_cookie(
        key      = COOKIE_NAME,
        value    = token,
        httponly = True,
        secure   = IS_HTTPS,      # True en producción HTTPS (Oracle + certbot)
        samesite = "strict",      # PROYECTO.md: SameSite=Strict obligatorio
        max_age  = JWT_TTL_HOURS * 3600,
        path     = "/",
    )


def _delete_auth_cookie(response: Response) -> None:
    """Elimina la cookie JWT invalidando la sesión en el cliente."""
    response.delete_cookie(
        key      = COOKIE_NAME,
        path     = "/",
        httponly = True,
        samesite = "strict",
        secure   = IS_HTTPS,
    )


# ════════════════════════════════════════════════════════════════════════════════
#  BACKEND SQLite — desarrollo local (sin MYSQL_HOST)
# ════════════════════════════════════════════════════════════════════════════════

def _init_auth_sqlite() -> None:
    """Crea la tabla usuarios_panel en SQLite si no existe (solo desarrollo)."""
    with sqlite3.connect(AUTH_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_panel (
                id             TEXT    PRIMARY KEY,
                email          TEXT    NOT NULL UNIQUE,
                password_hash  TEXT    NOT NULL,
                nombre_negocio TEXT    NOT NULL DEFAULT '',
                nombre         TEXT,
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


# ════════════════════════════════════════════════════════════════════════════════
#  BACKEND MySQL — producción Oracle HeatWave
# ════════════════════════════════════════════════════════════════════════════════

async def _mysql_registrar(email: str, password_hash: str, nombre_negocio: str) -> dict:
    try:
        import aiomysql
    except ImportError:
        raise HTTPException(status_code=500, detail="aiomysql no instalado — pip install aiomysql")

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


# ════════════════════════════════════════════════════════════════════════════════
#  API PÚBLICA — funciones reutilizables desde agente_conversacion.py
# ════════════════════════════════════════════════════════════════════════════════

async def registrar_usuario(email: str, password: str, nombre_negocio: str) -> dict:
    """
    Crea un nuevo usuario en usuarios_panel.
    Retorna {"id", "email", "nombre_negocio"}.
    Lanza HTTPException(409) si el email ya existe.
    El password SIEMPRE se hashea con bcrypt — NUNCA plaintext en DB.
    """
    pwd_hash = hash_password(password)
    if USAR_MYSQL:
        return await _mysql_registrar(email, pwd_hash, nombre_negocio)
    _init_auth_sqlite()
    return _sqlite_registrar(email, pwd_hash, nombre_negocio)


async def autenticar_usuario(email: str, password: str) -> Optional[dict]:
    """
    Verifica credenciales contra la DB.
    Retorna el registro del usuario o None.
    Actualiza `ultimo_acceso` en caso de éxito (auditoría).
    IMPORTANTE: No revela si el email existe (defensa contra user enumeration).
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

    # Auditoría de acceso (non-blocking en MySQL)
    if USAR_MYSQL:
        await _mysql_actualizar_acceso(usuario["id"])
    else:
        _sqlite_actualizar_acceso(usuario["id"])

    return usuario


# ════════════════════════════════════════════════════════════════════════════════
#  FASTAPI ROUTER — /api/auth/*
#  Registrar en agente_conversacion.py con: app.include_router(auth_router)
# ════════════════════════════════════════════════════════════════════════════════

auth_router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@auth_router.post("/login", response_model=LoginResponse)
async def auth_login(body: LoginInput, response: Response) -> LoginResponse:
    """
    POST /api/auth/login
    Autentica usuario y setea cookie JWT HttpOnly + Secure + SameSite=Strict.

    - Valida email/password contra tabla usuarios_panel (MySQL o SQLite)
    - Verifica hash bcrypt — NUNCA comparación directa de texto
    - En éxito: genera JWT (HS256, 24h, JWT_SECRET de .env)
    - Retorna 401 con mensaje genérico (no revela si email existe)
    """
    try:
        usuario = await autenticar_usuario(body.email, body.password)
    except Exception as e:
        log.error(f"Error en autenticación: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

    if not usuario:
        # Mensaje genérico para no revelar si el email existe (prevenir enumeration)
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    payload = UsuarioPayload(
        id=usuario["id"],
        email=usuario["email"],
        nombre_negocio=usuario["nombre_negocio"],
    )
    token = create_jwt(payload)
    _set_auth_cookie(response, token)

    log.info(f"Login exitoso: {usuario['email']} ({usuario['nombre_negocio']})")
    return LoginResponse(nombre_negocio=usuario["nombre_negocio"])


@auth_router.post("/logout")
async def auth_logout(response: Response) -> dict:
    """
    POST /api/auth/logout
    Invalida la sesión eliminando la cookie del cliente.
    No requiere autenticación previa — idempotente.
    """
    _delete_auth_cookie(response)
    return {"ok": True, "message": "Sesión cerrada correctamente"}


@auth_router.get("/me", response_model=UsuarioPayload)
async def auth_me(usuario: AuthRequired) -> UsuarioPayload:
    """
    GET /api/auth/me
    Retorna los datos del usuario autenticado según su cookie JWT.
    Retorna 401 si la cookie no existe o el token es inválido/expirado.
    Usado por el panel para confirmar sesión activa al cargar páginas.
    """
    return usuario


@auth_router.post("/register", status_code=201, response_model=RegisterResponse)
async def auth_register(body: RegisterInput) -> RegisterResponse:
    """
    POST /api/auth/register
    Registra un nuevo usuario del panel.
    - Password mínimo 8 caracteres (validado por Pydantic)
    - Retorna 409 si el email ya está registrado
    - Password hasheado con bcrypt antes de persistir
    """
    try:
        usuario = await registrar_usuario(
            email=body.email,
            password=body.password,
            nombre_negocio=body.nombre_negocio,
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error en registro: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

    log.info(f"Nuevo usuario registrado: {body.email}")
    return RegisterResponse(id=usuario["id"], nombre_negocio=usuario["nombre_negocio"])
