"""
backup_mysql.py
─────────────────────────────────────────────────────────────────────────────
Backup automatizado de MySQL HeatWave para ValVic.

Flujo:
  1. mysqldump de valvic_db → archivo .sql
  2. Comprimir con gzip → .sql.gz
  3. Encriptar con openssl aes-256-cbc → .sql.gz.enc
  4. Subir a Oracle Object Storage via OCI SDK
  5. Eliminar backups LOCALES con más de RETENTION_DAYS días
  6. Logging completo en /var/log/valvic/backup.log

Uso manual (prueba):
  python backup_mysql.py            → backup completo
  python backup_mysql.py --test     → sólo valida credenciales sin subir
  python backup_mysql.py --dry-run  → muestra lo que haría sin ejecutar nada

Cron (3 AM, definido en setup_oracle.sh):
  0 3 * * * /opt/valvic/venv/bin/python /opt/valvic/app/backup_mysql.py
─────────────────────────────────────────────────────────────────────────────
"""

import argparse
import gzip
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import oci
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator

# ── Cargar .env ─────────────────────────────────────────────────────────────
load_dotenv()

# ── Constantes ───────────────────────────────────────────────────────────────
LOG_FILE       = Path(os.getenv("BACKUP_LOG_FILE", "/var/log/valvic/backup.log"))
BACKUP_DIR     = Path(os.getenv("BACKUP_LOCAL_DIR", "/tmp/valvic_backups"))
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))

# ── Logger ───────────────────────────────────────────────────────────────────
def _build_logger() -> logging.Logger:
    """Configura el logger con salida a archivo y consola."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("valvic-backup")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler archivo
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Handler consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


log = _build_logger()


# ── Modelos Pydantic v2 ──────────────────────────────────────────────────────
class MySQLConfig(BaseModel):
    host:     str
    port:     int = 3306
    user:     str
    password: str
    database: str

    @field_validator("host", "user", "password", "database")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v


class OCIConfig(BaseModel):
    config_file:  str
    profile:      str
    namespace:    str
    bucket_name:  str
    prefix:       str = "backups/valvic"

    @field_validator("namespace", "bucket_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v


class BackupConfig(BaseModel):
    mysql:          MySQLConfig
    oci:            OCIConfig
    encryption_key: str   # passphrase para openssl AES-256-CBC
    retention_days: int = RETENTION_DAYS

    @field_validator("encryption_key")
    @classmethod
    def key_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("BACKUP_ENCRYPTION_KEY no puede estar vacía")
        return v


# ── Helpers de proceso ───────────────────────────────────────────────────────
def _run(cmd: list[str], env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta un comando externo con logging y manejo de errores."""
    log.debug("Ejecutando: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env or os.environ.copy(),
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Comando falló (código {result.returncode}): {result.stderr.strip()}"
        )
    return result


# ── Etapas del backup ────────────────────────────────────────────────────────
def step_dump(cfg: BackupConfig, sql_path: Path) -> None:
    """Paso 1: mysqldump de todas las tablas de valvic_db."""
    log.info("▶ Paso 1/4 — mysqldump de %s...", cfg.mysql.database)

    env = os.environ.copy()
    # Evitar que mysqldump pida contraseña interactivamente
    env["MYSQL_PWD"] = cfg.mysql.password

    cmd = [
        "mysqldump",
        f"--host={cfg.mysql.host}",
        f"--port={cfg.mysql.port}",
        f"--user={cfg.mysql.user}",
        "--single-transaction",        # consistent read sin bloquear
        "--routines",                  # incluir stored procedures
        "--triggers",                  # incluir triggers
        "--set-gtid-purged=OFF",       # compatible con HeatWave
        "--default-character-set=utf8mb4",
        "--result-file", str(sql_path),
        cfg.mysql.database,
    ]

    _run(cmd, env=env)
    size_mb = sql_path.stat().st_size / 1_048_576
    log.info("   Dump completado → %s (%.2f MB)", sql_path.name, size_mb)


def step_compress(sql_path: Path, gz_path: Path) -> None:
    """Paso 2: comprimir el dump con gzip."""
    log.info("▶ Paso 2/4 — Comprimiendo con gzip...")

    with sql_path.open("rb") as f_in, gzip.open(gz_path, "wb", compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)

    size_mb = gz_path.stat().st_size / 1_048_576
    log.info("   Comprimido → %s (%.2f MB)", gz_path.name, size_mb)


def step_encrypt(gz_path: Path, enc_path: Path, passphrase: str) -> None:
    """Paso 3: encriptar con openssl AES-256-CBC + PBKDF2 (salted)."""
    log.info("▶ Paso 3/4 — Encriptando con AES-256-CBC (openssl)...")

    cmd = [
        "openssl", "enc",
        "-aes-256-cbc",
        "-pbkdf2",          # PBKDF2 key derivation (más seguro que -md md5)
        "-iter", "100000",  # 100k iteraciones
        "-in",  str(gz_path),
        "-out", str(enc_path),
        "-pass", f"env:BACKUP_ENC_PASS",
    ]

    env = os.environ.copy()
    env["BACKUP_ENC_PASS"] = passphrase

    _run(cmd, env=env)
    size_mb = enc_path.stat().st_size / 1_048_576
    log.info("   Encriptado → %s (%.2f MB)", enc_path.name, size_mb)


def step_upload(cfg: BackupConfig, enc_path: Path, object_name: str) -> None:
    """Paso 4: subir el archivo encriptado a Oracle Object Storage."""
    log.info("▶ Paso 4/4 — Subiendo a OCI Object Storage (bucket: %s)...", cfg.oci.bucket_name)

    try:
        oci_cfg = oci.config.from_file(
            file_location=cfg.oci.config_file,
            profile_name=cfg.oci.profile,
        )
        oci.config.validate_config(oci_cfg)
    except Exception as exc:
        raise RuntimeError(f"OCI config inválida: {exc}") from exc

    client = oci.object_storage.ObjectStorageClient(oci_cfg)
    full_object_name = f"{cfg.oci.prefix}/{object_name}"

    with enc_path.open("rb") as f_data:
        file_size = enc_path.stat().st_size
        client.put_object(
            namespace_name=cfg.oci.namespace,
            bucket_name=cfg.oci.bucket_name,
            object_name=full_object_name,
            put_object_body=f_data,
            content_length=file_size,
            content_type="application/octet-stream",
        )

    size_mb = file_size / 1_048_576
    log.info(
        "   Subido → oci://%s/%s/%s (%.2f MB)",
        cfg.oci.namespace,
        cfg.oci.bucket_name,
        full_object_name,
        size_mb,
    )


def step_cleanup_local(backup_dir: Path, retention_days: int) -> None:
    """Elimina backups locales con más de `retention_days` días."""
    log.info("▶ Limpieza — eliminando backups locales >%d días...", retention_days)
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=retention_days)
    removed = 0

    for f in backup_dir.glob("valvic_backup_*.enc"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            f.unlink()
            log.info("   Eliminado: %s", f.name)
            removed += 1

    if removed == 0:
        log.info("   Sin archivos para eliminar.")
    else:
        log.info("   %d archivo(s) eliminado(s).", removed)


# ── Validación de herramientas del sistema ───────────────────────────────────
def _check_system_tools() -> None:
    """Verifica que mysqldump y openssl estén disponibles."""
    missing = []
    for tool in ("mysqldump", "openssl"):
        if shutil.which(tool) is None:
            missing.append(tool)
    if missing:
        raise EnvironmentError(
            f"Herramientas requeridas no encontradas en PATH: {', '.join(missing)}"
        )


# ── Carga de configuración desde .env ────────────────────────────────────────
def _load_config() -> BackupConfig:
    """Lee variables de entorno y construye BackupConfig (valida con Pydantic v2)."""
    return BackupConfig(
        mysql=MySQLConfig(
            host=os.getenv("MYSQL_HOST", ""),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", ""),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DB", "valvic_db"),
        ),
        oci=OCIConfig(
            config_file=os.getenv("OCI_CONFIG_FILE", "/opt/valvic/.oci/config"),
            profile=os.getenv("OCI_PROFILE", "DEFAULT"),
            namespace=os.getenv("OCI_NAMESPACE", ""),
            bucket_name=os.getenv("OCI_BUCKET_NAME", "valvic-backups"),
            prefix=os.getenv("OCI_BACKUP_PREFIX", "backups/valvic"),
        ),
        encryption_key=os.getenv("BACKUP_ENCRYPTION_KEY", ""),
        retention_days=int(os.getenv("BACKUP_RETENTION_DAYS", str(RETENTION_DAYS))),
    )


# ── Flujo principal ──────────────────────────────────────────────────────────
def run_backup(cfg: BackupConfig, dry_run: bool = False) -> int:
    """
    Ejecuta el pipeline completo de backup.

    Retorna:
        0 → éxito
        1 → fallo (con log de error)
    """
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"valvic_backup_{ts}"

    # Directorio de trabajo temporal (eliminado en caso de fallo)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="valvic_bkp_", dir=BACKUP_DIR))

    sql_path = work_dir / f"{base_name}.sql"
    gz_path  = work_dir / f"{base_name}.sql.gz"
    enc_path = BACKUP_DIR / f"{base_name}.sql.gz.enc"   # destino final local

    t_start = datetime.now()
    log.info("=" * 60)
    log.info("INICIO BACKUP ValVic — %s", ts)
    log.info("Base de datos: %s @ %s:%s", cfg.mysql.database, cfg.mysql.host, cfg.mysql.port)
    log.info("Bucket OCI:    %s / %s", cfg.oci.bucket_name, cfg.oci.prefix)
    log.info("=" * 60)

    if dry_run:
        log.info("[DRY-RUN] No se ejecutará ninguna acción real.")
        log.info("[DRY-RUN] Archivo destino sería: %s", enc_path)
        return 0

    try:
        # 1. Dump
        step_dump(cfg, sql_path)

        # 2. Compress
        step_compress(sql_path, gz_path)
        sql_path.unlink()   # liberar espacio inmediatamente

        # 3. Encrypt
        step_encrypt(gz_path, enc_path, cfg.encryption_key)
        gz_path.unlink()    # liberar espacio

        # 4. Upload
        object_name = enc_path.name
        step_upload(cfg, enc_path, object_name)

        # 5. Cleanup local
        step_cleanup_local(BACKUP_DIR, cfg.retention_days)

        elapsed = (datetime.now() - t_start).total_seconds()
        final_size_mb = enc_path.stat().st_size / 1_048_576
        log.info("=" * 60)
        log.info(
            "BACKUP EXITOSO — %.1fs | Archivo: %s | Tamaño: %.2f MB",
            elapsed,
            enc_path.name,
            final_size_mb,
        )
        log.info("=" * 60)
        return 0

    except Exception as exc:
        log.exception("ERROR CRÍTICO en backup: %s", exc)

        # Idempotencia: limpiar archivos parciales para no dejar huérfanos
        for orphan in (sql_path, gz_path, enc_path):
            if orphan.exists():
                orphan.unlink()
                log.warning("   Archivo huérfano eliminado: %s", orphan.name)

        log.error("=" * 60)
        log.error("BACKUP FALLIDO — ver detalles arriba")
        log.error("=" * 60)
        return 1

    finally:
        # Directorio temporal siempre se elimina
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


def run_test(cfg: BackupConfig) -> int:
    """Valida credenciales MySQL y OCI sin hacer backup real."""
    log.info("▶ Modo --test: validando credenciales...")
    errors = 0

    # Test MySQL
    try:
        env = os.environ.copy()
        env["MYSQL_PWD"] = cfg.mysql.password
        result = _run(
            [
                "mysql",
                f"--host={cfg.mysql.host}",
                f"--port={cfg.mysql.port}",
                f"--user={cfg.mysql.user}",
                "--execute=SELECT VERSION();",
                cfg.mysql.database,
            ],
            env=env,
            check=True,
        )
        log.info("   MySQL OK — %s", result.stdout.strip().split("\n")[-1])
    except Exception as exc:
        log.error("   MySQL FALLÓ: %s", exc)
        errors += 1

    # Test OCI
    try:
        oci_cfg = oci.config.from_file(
            file_location=cfg.oci.config_file,
            profile_name=cfg.oci.profile,
        )
        oci.config.validate_config(oci_cfg)
        client = oci.object_storage.ObjectStorageClient(oci_cfg)
        client.get_namespace()
        log.info("   OCI OK — namespace: %s", cfg.oci.namespace)
    except Exception as exc:
        log.error("   OCI FALLÓ: %s", exc)
        errors += 1

    if errors == 0:
        log.info("✅ Todas las credenciales son válidas.")
    else:
        log.error("❌ %d credencial(es) con errores. Revisar .env y ~/.oci/config", errors)

    return errors


# ── Punto de entrada ─────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="ValVic — Backup automatizado MySQL → OCI Object Storage"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Sólo validar credenciales sin ejecutar backup",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar lo que haría sin ejecutar ninguna acción",
    )
    args = parser.parse_args()

    # Verificar herramientas del sistema
    try:
        _check_system_tools()
    except EnvironmentError as exc:
        log.error("%s", exc)
        sys.exit(1)

    # Cargar y validar configuración
    try:
        cfg = _load_config()
    except Exception as exc:
        log.error("Configuración inválida: %s", exc)
        sys.exit(1)

    if args.test:
        sys.exit(run_test(cfg))
    else:
        sys.exit(run_backup(cfg, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
