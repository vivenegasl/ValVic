-- ================================================================
--  ValVic — Schema MySQL: Prospección y Conversaciones
--  Ejecutar en Oracle HeatWave DESPUÉS del schema principal
--  (valvic_schema_principal.sql)
--
--  Tablas que crea:
--    prospectos         → leads encontrados por el prospector
--    conversaciones     → una por número de teléfono
--    mensajes           → historial de cada conversación
--    cierres            → registro auditable de ventas cerradas
--    reuniones_fundador → solicitudes de reunión con el equipo
-- ================================================================

-- ── Extensión: si no existe la DB, crear primero ─────────────────
-- En Oracle HeatWave las DBs se crean en el panel web.
-- Este script asume que ya existe la DB configurada en MYSQL_DB.


-- ================================================================
--  TABLA: prospectos
--  Negocios encontrados por el agente prospector.
--  Equivalente al prospectos_vet.db de SQLite local.
-- ================================================================
CREATE TABLE IF NOT EXISTS prospectos (
    id              INT             NOT NULL AUTO_INCREMENT,
    uuid            VARCHAR(36)     NOT NULL,
    nombre_negocio  VARCHAR(200)    NOT NULL,
    telefono        VARCHAR(30),
    ciudad          VARCHAR(100)    NOT NULL DEFAULT '',
    direccion       VARCHAR(300)    DEFAULT '',
    rating          DECIMAL(3,1)    DEFAULT 0,
    resenas         INT             DEFAULT 0,
    maps_url        VARCHAR(500)    DEFAULT '',
    place_id        VARCHAR(200),
    fuente          VARCHAR(50)     NOT NULL DEFAULT 'google_places',
    estado          VARCHAR(30)     NOT NULL DEFAULT 'nuevo',
    puntuacion      TINYINT         DEFAULT 0,
    razon_ia        TEXT,
    mensaje_draft   TEXT,
    url_wame        VARCHAR(1000)   DEFAULT '',
    enviado_at      DATETIME,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_uuid     (uuid),
    UNIQUE KEY uq_place_id (place_id),
    KEY idx_estado     (estado, puntuacion DESC),
    KEY idx_ciudad     (ciudad),
    KEY idx_telefono   (telefono),
    KEY idx_created    (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
--  TABLA: conversaciones
--  Una conversación por número de teléfono.
--  Registra la etapa de venta y el estado del proceso.
-- ================================================================
CREATE TABLE IF NOT EXISTS conversaciones (
    id                      INT             NOT NULL AUTO_INCREMENT,
    telefono                VARCHAR(30)     NOT NULL,
    prospecto_id            INT,
    estado                  VARCHAR(30)     NOT NULL DEFAULT 'activa',
    etapa                   VARCHAR(50)     NOT NULL DEFAULT 'apertura',
    intercambios            INT             NOT NULL DEFAULT 0,
    objeciones_sin_resolver INT             NOT NULL DEFAULT 0,
    concesiones_ofrecidas   TEXT            NOT NULL DEFAULT '[]',
    precio_acordado         DECIMAL(10,2),
    servicio_acordado       VARCHAR(50),
    forma_pago_acordada     VARCHAR(50),
    cierre_confirmado       TINYINT(1)      NOT NULL DEFAULT 0,
    reunion_agendada        TINYINT(1)      NOT NULL DEFAULT 0,
    escalado_humano         TINYINT(1)      NOT NULL DEFAULT 0,
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                            ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_telefono (telefono),
    KEY idx_estado    (estado),
    KEY idx_etapa     (etapa),
    KEY idx_updated   (updated_at DESC),
    CONSTRAINT fk_conv_prospecto
        FOREIGN KEY (prospecto_id) REFERENCES prospectos(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
--  TABLA: mensajes
--  Historial completo de cada conversación.
-- ================================================================
CREATE TABLE IF NOT EXISTS mensajes (
    id              INT             NOT NULL AUTO_INCREMENT,
    conversacion_id INT             NOT NULL,
    rol             ENUM('prospecto','vicky') NOT NULL,
    contenido       TEXT            NOT NULL,
    tokens_output   INT             DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_conv_id  (conversacion_id, created_at),
    CONSTRAINT fk_msg_conversacion
        FOREIGN KEY (conversacion_id) REFERENCES conversaciones(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
--  TABLA: cierres
--  Registro auditable de cada venta cerrada.
--  No se puede modificar — solo insertar.
-- ================================================================
CREATE TABLE IF NOT EXISTS cierres (
    id                  INT             NOT NULL AUTO_INCREMENT,
    conversacion_id     INT             NOT NULL,
    telefono            VARCHAR(30)     NOT NULL,
    nombre_negocio      VARCHAR(200)    NOT NULL,
    servicio_acordado   VARCHAR(50)     NOT NULL,
    precio_mensual      DECIMAL(10,2)   NOT NULL,
    precio_impl         DECIMAL(10,2),
    concesion_aplicada  VARCHAR(100),
    forma_pago          VARCHAR(50),
    senal_monto         DECIMAL(10,2),
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_created (created_at DESC),
    CONSTRAINT fk_cierre_conversacion
        FOREIGN KEY (conversacion_id) REFERENCES conversaciones(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
--  TABLA: reuniones_fundador
--  Solicitudes de reunión coordinadas por Vicky.
--  Cuando el panel web esté activo, esto alimenta /panel/agenda.
-- ================================================================
CREATE TABLE IF NOT EXISTS reuniones_fundador (
    id                  INT             NOT NULL AUTO_INCREMENT,
    telefono            VARCHAR(30)     NOT NULL,
    nombre_negocio      VARCHAR(200)    NOT NULL,
    horario_solicitado  VARCHAR(300)    NOT NULL,
    estado              VARCHAR(30)     NOT NULL DEFAULT 'pendiente_confirmacion',
    notas               TEXT,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_estado   (estado),
    KEY idx_created  (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
--  VISTAS ÚTILES
-- ================================================================

-- Pipeline de prospección con resumen de conversación
CREATE OR REPLACE VIEW v_pipeline_ventas AS
SELECT
    p.id,
    p.nombre_negocio,
    p.telefono,
    p.ciudad,
    p.rating,
    p.resenas,
    p.puntuacion,
    p.estado               AS estado_prospecto,
    p.razon_ia,
    c.etapa                AS etapa_conversacion,
    c.intercambios,
    c.cierre_confirmado,
    c.precio_acordado,
    c.servicio_acordado,
    c.reunion_agendada,
    c.escalado_humano,
    p.created_at,
    p.updated_at
FROM prospectos p
LEFT JOIN conversaciones c ON c.prospecto_id = p.id
ORDER BY p.puntuacion DESC, p.updated_at DESC;


-- Resumen de ventas cerradas con datos completos
CREATE OR REPLACE VIEW v_cierres_detalle AS
SELECT
    cl.id,
    cl.created_at,
    cl.nombre_negocio,
    cl.telefono,
    cl.servicio_acordado,
    cl.precio_mensual,
    cl.precio_impl,
    cl.concesion_aplicada,
    cl.forma_pago,
    cl.senal_monto,
    -- MRR estimado (solo mensualidad, sin impl)
    cl.precio_mensual                   AS mrr_aporte,
    -- ARR estimado
    cl.precio_mensual * 12              AS arr_estimado
FROM cierres cl
ORDER BY cl.created_at DESC;


-- Conversaciones activas con último mensaje
CREATE OR REPLACE VIEW v_conversaciones_activas AS
SELECT
    conv.id,
    conv.telefono,
    p.nombre_negocio,
    p.ciudad,
    conv.etapa,
    conv.intercambios,
    conv.objeciones_sin_resolver,
    conv.cierre_confirmado,
    conv.escalado_humano,
    -- Último mensaje del prospecto
    (
        SELECT m.contenido
        FROM mensajes m
        WHERE m.conversacion_id = conv.id
          AND m.rol = 'prospecto'
        ORDER BY m.created_at DESC
        LIMIT 1
    ) AS ultimo_mensaje_cliente,
    conv.updated_at
FROM conversaciones conv
LEFT JOIN prospectos p ON p.id = conv.prospecto_id
WHERE conv.estado = 'activa'
ORDER BY conv.updated_at DESC;


-- ================================================================
--  TRIGGER: updated_at automático en prospectos
-- ================================================================
DROP TRIGGER IF EXISTS trg_prospectos_updated_at;
CREATE TRIGGER trg_prospectos_updated_at
    BEFORE UPDATE ON prospectos
    FOR EACH ROW
    SET NEW.updated_at = NOW();


DROP TRIGGER IF EXISTS trg_conversaciones_updated_at;
CREATE TRIGGER trg_conversaciones_updated_at
    BEFORE UPDATE ON conversaciones
    FOR EACH ROW
    SET NEW.updated_at = NOW();


DROP TRIGGER IF EXISTS trg_reuniones_updated_at;
CREATE TRIGGER trg_reuniones_updated_at
    BEFORE UPDATE ON reuniones_fundador
    FOR EACH ROW
    SET NEW.updated_at = NOW();

-- ── Agregar columnas multi-vertical a prospectos ───────────────
-- Ejecutar solo si la tabla ya existe sin estas columnas:
-- ALTER TABLE prospectos ADD COLUMN vertical VARCHAR(50) DEFAULT '';
-- ALTER TABLE prospectos ADD COLUMN website VARCHAR(500) DEFAULT '';
-- ALTER TABLE prospectos ADD INDEX idx_vertical (vertical);
