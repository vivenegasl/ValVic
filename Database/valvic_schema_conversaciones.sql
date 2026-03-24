-- ═══════════════════════════════════════════════════════════════════════════
-- valvic_schema_conversaciones.sql
-- Schema MySQL HeatWave para las tablas del Agente Vicky (conversaciones).
--
-- APLICAR: mysql -h $MYSQL_HOST -u valvic_app -p valvic_db < valvic_schema_conversaciones.sql
-- PRERREQUISITO: valvic_schema_principal.sql ya ejecutado (misma BD)
-- ═══════════════════════════════════════════════════════════════════════════

USE valvic_db;

-- ─── CATÁLOGO: estados de conversación ────────────────────────────────────
-- Cumple: "Estados BBDD como FK a tabla de estados — NUNCA TEXT libre"
CREATE TABLE IF NOT EXISTS estados_conversacion (
    id          TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    codigo      VARCHAR(30)      NOT NULL UNIQUE,
    descripcion VARCHAR(100)     NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO estados_conversacion (id, codigo, descripcion) VALUES
    (1, 'activa',            'Conversación en curso'),
    (2, 'presentacion',      'Vicky presentando el producto'),
    (3, 'negociacion',       'Cliente en fase de negociación'),
    (4, 'pago_pendiente',    'Cierre acordado, pendiente de pago'),
    (5, 'cerrada_positiva',  'Venta cerrada y confirmada'),
    (6, 'cerrada_negativa',  'Cliente no interesado'),
    (7, 'agendar_reunion',   'Cliente quiere hablar con humano'),
    (8, 'escalada',          'Escalada a fundador por objeciones');

-- ─── CATÁLOGO: estados de cita ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS estados_cita (
    id          TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    codigo      VARCHAR(30)      NOT NULL UNIQUE,
    descripcion VARCHAR(100)     NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO estados_cita (id, codigo, descripcion) VALUES
    (1, 'pendiente_confirmacion', 'Solicitada, esperando confirmar horario'),
    (2, 'confirmada',             'Horario confirmado con ambas partes'),
    (3, 'realizada',              'Reunión efectuada'),
    (4, 'cancelada',              'Cancelada por alguna parte'),
    (5, 'reagendada',             'Reprogramada a otro horario');

-- ─── CONVERSACIONES ────────────────────────────────────────────────────────
-- PK: UUID() — cumple "PKs UUID en toda tabla expuesta al exterior"
-- usuario_id: FK al negocio cliente que usa el panel (nullable porque
--   las conversaciones llegan por webhook antes de que exista la sesión).
CREATE TABLE IF NOT EXISTS conversaciones (
    id                        CHAR(36)         NOT NULL DEFAULT (UUID()),
    usuario_id                CHAR(36)         DEFAULT NULL,  -- FK → usuarios_panel.id
    telefono                  VARCHAR(20)      NOT NULL,
    prospecto_id              CHAR(36)         DEFAULT NULL,  -- FK a prospectos.uuid
    estado_id                 TINYINT UNSIGNED NOT NULL DEFAULT 1,
    etapa                     VARCHAR(30)      NOT NULL DEFAULT 'apertura',
    intercambios              SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    objeciones_sin_resolver   TINYINT UNSIGNED NOT NULL DEFAULT 0,
    concesiones_ofrecidas     JSON             NOT NULL DEFAULT (JSON_ARRAY()),
    precio_acordado           DECIMAL(10,2)    DEFAULT NULL,
    servicio_acordado         VARCHAR(50)      DEFAULT NULL,
    forma_pago_acordada       VARCHAR(30)      DEFAULT NULL,
    cierre_confirmado         TINYINT(1)       NOT NULL DEFAULT 0,
    reunion_agendada          TINYINT(1)       NOT NULL DEFAULT 0,
    escalado_humano           TINYINT(1)       NOT NULL DEFAULT 0,
    vertical                  VARCHAR(50)      DEFAULT NULL,
    created_at                DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_telefono (telefono),
    KEY idx_estado (estado_id),
    KEY idx_updated (updated_at),
    KEY idx_etapa (etapa),
    KEY idx_usuario (usuario_id),
    CONSTRAINT fk_conv_estado  FOREIGN KEY (estado_id)
        REFERENCES estados_conversacion(id) ON UPDATE CASCADE,
    CONSTRAINT fk_conv_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios_panel(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ALTER para bases ya existentes (idempotente)
ALTER TABLE conversaciones
    ADD COLUMN IF NOT EXISTS usuario_id CHAR(36) DEFAULT NULL AFTER id,
    ADD KEY IF NOT EXISTS idx_usuario (usuario_id);

-- ─── MENSAJES ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mensajes (
    id               CHAR(36)         NOT NULL DEFAULT (UUID()),
    conversacion_id  CHAR(36)         NOT NULL,
    rol              ENUM('prospecto','vicky') NOT NULL,
    contenido        TEXT             NOT NULL,
    tokens_output    SMALLINT UNSIGNED DEFAULT 0,
    created_at       DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_conv (conversacion_id),
    KEY idx_created (created_at),
    CONSTRAINT fk_msg_conv FOREIGN KEY (conversacion_id)
        REFERENCES conversaciones(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── CIERRES ───────────────────────────────────────────────────────────────
-- Registro auditable de cada venta cerrada por Vicky
CREATE TABLE IF NOT EXISTS cierres (
    id                  CHAR(36)         NOT NULL DEFAULT (UUID()),
    conversacion_id     CHAR(36)         NOT NULL,
    telefono            VARCHAR(20)      NOT NULL,
    nombre_negocio      VARCHAR(150)     NOT NULL,
    servicio_acordado   VARCHAR(50)      NOT NULL,
    precio_mensual      DECIMAL(10,2)    NOT NULL DEFAULT 0,
    precio_impl         DECIMAL(10,2)    DEFAULT NULL,
    concesion_aplicada  VARCHAR(50)      DEFAULT NULL,
    forma_pago          VARCHAR(30)      DEFAULT NULL,
    senal_monto         DECIMAL(10,2)    DEFAULT NULL,
    created_at          DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_cierre_conv (conversacion_id),
    KEY idx_cierre_tel (telefono),
    KEY idx_cierre_fecha (created_at),
    CONSTRAINT fk_cierre_conv FOREIGN KEY (conversacion_id)
        REFERENCES conversaciones(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── REUNIONES CON FUNDADOR ────────────────────────────────────────────────
-- usuario_id: identifica a QUÉ negocio cliente pertenece esta reunión.
-- Es la columna clave para el filtro multi-tenant en /api/agenda.
CREATE TABLE IF NOT EXISTS reuniones_fundador (
    id                   CHAR(36)         NOT NULL DEFAULT (UUID()),
    usuario_id           CHAR(36)         NOT NULL,  -- FK → usuarios_panel.id (OBLIGATORIO)
    conversacion_id      CHAR(36)         DEFAULT NULL,
    telefono             VARCHAR(20)      NOT NULL,
    nombre_negocio       VARCHAR(150)     NOT NULL DEFAULT '',
    horario_solicitado   TEXT             NOT NULL,
    estado_cita_id       TINYINT UNSIGNED NOT NULL DEFAULT 1,
    notas_fundador       TEXT             DEFAULT NULL,
    created_at           DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_reunion_usuario (usuario_id),
    KEY idx_reunion_tel (telefono),
    KEY idx_reunion_estado (estado_cita_id),
    KEY idx_reunion_fecha (created_at),
    CONSTRAINT fk_reunion_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios_panel(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_reunion_conv FOREIGN KEY (conversacion_id)
        REFERENCES conversaciones(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_reunion_estado FOREIGN KEY (estado_cita_id)
        REFERENCES estados_cita(id) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ALTER para bases ya existentes (idempotente)
ALTER TABLE reuniones_fundador
    ADD COLUMN IF NOT EXISTS usuario_id CHAR(36) DEFAULT NULL AFTER id,
    ADD KEY IF NOT EXISTS idx_reunion_usuario (usuario_id);

-- ─── USUARIOS DEL PANEL (para JWT) ────────────────────────────────────────
-- Cada fila = un negocio cliente que usa ValVic (clínica, spa, etc.)
-- El JWT del panel incluye el id de esta tabla en el payload.
CREATE TABLE IF NOT EXISTS usuarios_panel (
    id             CHAR(36)     NOT NULL DEFAULT (UUID()),
    email          VARCHAR(100) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,   -- bcrypt
    nombre_negocio VARCHAR(150) NOT NULL DEFAULT '',  -- "Clínica Dental ABC"
    rol            ENUM('admin','operador') NOT NULL DEFAULT 'operador',
    activo         TINYINT(1)   NOT NULL DEFAULT 1,
    ultimo_acceso  DATETIME     DEFAULT NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ALTER para bases de datos ya existentes (idempotente)
ALTER TABLE usuarios_panel
    ADD COLUMN IF NOT EXISTS nombre_negocio VARCHAR(150) NOT NULL DEFAULT '' AFTER password_hash;

-- ═══════════════════════════════════════════════════════════════════════════
-- Vista v_agenda_panel:
-- Filtra por usuario_id → cada negocio cliente solo ve SUS citas.
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW v_agenda_panel AS
    SELECT
        r.id                  AS reunion_id,
        r.usuario_id,                          -- clave para filtro multi-tenant
        r.telefono,
        r.nombre_negocio,
        r.horario_solicitado,
        ec.codigo             AS estado_cita,
        c.etapa               AS etapa_crm,
        c.cierre_confirmado,
        c.precio_acordado,
        c.servicio_acordado,
        r.notas_fundador,
        r.created_at,
        r.updated_at
    FROM reuniones_fundador r
    JOIN estados_cita ec ON r.estado_cita_id = ec.id
    LEFT JOIN conversaciones c ON r.conversacion_id = c.id
    ORDER BY r.created_at DESC;
-- Uso en API: SELECT ... FROM v_agenda_panel WHERE usuario_id = %s
