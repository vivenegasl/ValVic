-- ================================================================
--  ValVic — Schema MySQL normalizado (Convertido de PostgreSQL)
--  Nivel: 3NF / BCNF
--  ACID: Foreign keys, constraints, triggers, transacciones
-- ================================================================

-- ================================================================
--  CATÁLOGOS
-- ================================================================

CREATE TABLE tipos_negocio (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL UNIQUE,
  icono  VARCHAR(20)
);

INSERT INTO tipos_negocio (nombre, icono) VALUES
  ('Clínica / Salud',     '🦷'),
  ('Restaurante / Café',  '🍽️'),
  ('Spa / Belleza',       '🌿'),
  ('Gimnasio / Fitness',  '💪'),
  ('Tienda online',       '🛍️'),
  ('Agencia',             '⚡'),
  ('Inmobiliaria',        '🏢'),
  ('Automotriz',          '🚗'),
  ('Otro',                '🏢')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


CREATE TABLE tipos_servicio (
  id              SMALLINT PRIMARY KEY AUTO_INCREMENT,
  slug            VARCHAR(50) NOT NULL UNIQUE,
  nombre          VARCHAR(100) NOT NULL,
  descripcion     TEXT,
  precio_proyecto DECIMAL(10,2),
  precio_mensual  DECIMAL(10,2)
);

INSERT INTO tipos_servicio (slug, nombre, descripcion, precio_proyecto, precio_mensual) VALUES
  ('citas',          'Asistente de citas IA',    'Agenda y recordatorio automático', 135.00, 80.00),
  ('contenido',      'Creador de contenido IA',  'Posts semanales',           135.00, 80.00),
  ('reportes',       'Centro de reportes IA',    'Reporte semanal automático',110.00, 55.00),
  ('automatizacion', 'Automatización a medida',  'Flujos personalizados',     NULL,   NULL),
  ('web',            'Sitio web profesional',    'Landing page + SEO',        250.00, 50.00)
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


CREATE TABLE redes_sociales (
  id       SMALLINT PRIMARY KEY AUTO_INCREMENT,
  slug     VARCHAR(50) NOT NULL UNIQUE,
  nombre   VARCHAR(50) NOT NULL,
  color    VARCHAR(20),
  icono    VARCHAR(20)
);

INSERT INTO redes_sociales (slug, nombre, color, icono) VALUES
  ('instagram', 'Instagram', '#E1306C', '📸'),
  ('facebook',  'Facebook',  '#1877F2', '👤'),
  ('linkedin',  'LinkedIn',  '#0A66C2', '💼')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


CREATE TABLE dias_semana (
  id     SMALLINT PRIMARY KEY,
  nombre VARCHAR(20) NOT NULL UNIQUE
);

INSERT INTO dias_semana (id, nombre) VALUES
  (1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'),
  (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado'), (7, 'Domingo')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


CREATE TABLE canales_notificacion (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO canales_notificacion (nombre) VALUES
  ('whatsapp'), ('email'), ('sms')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


-- ================================================================
--  ESTADOS
-- ================================================================

CREATE TABLE estados_contacto (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO estados_contacto (nombre) VALUES
  ('nuevo'), ('contactado'), ('en_negociacion'), ('convertido'), ('perdido')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;

CREATE TABLE estados_cliente (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO estados_cliente (nombre) VALUES
  ('activo'), ('pausado'), ('cancelado'), ('moroso')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;

CREATE TABLE estados_contrato (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO estados_contrato (nombre) VALUES
  ('activo'), ('pausado'), ('cancelado'), ('pendiente_pago')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;

CREATE TABLE estados_post (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO estados_post (nombre) VALUES
  ('generado'), ('pendiente_revision'), ('aprobado'), ('publicado'), ('rechazado')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;

CREATE TABLE estados_cita (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO estados_cita (nombre) VALUES
  ('programada'), ('confirmada'), ('completada'), ('cancelada'), ('no_asistio')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;

CREATE TABLE estados_notificacion (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO estados_notificacion (nombre) VALUES
  ('pendiente'), ('enviada'), ('fallida'), ('rebotada')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


-- ================================================================
--  ENTIDADES CORE
-- ================================================================

CREATE TABLE clientes (
  id              CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  nombre_negocio  VARCHAR(200) NOT NULL,
  tipo_id         SMALLINT,
  estado_id       SMALLINT    NOT NULL DEFAULT 1,
  contacto_nombre VARCHAR(150) NOT NULL,
  diferenciador   TEXT,
  tono            VARCHAR(50),
  promo_activa    TEXT,
  sheet_id        VARCHAR(150),
  FOREIGN KEY (tipo_id) REFERENCES tipos_negocio(id) ON UPDATE CASCADE,
  FOREIGN KEY (estado_id) REFERENCES estados_cliente(id)
);


CREATE TABLE contactos (
  id              CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  nombre          VARCHAR(100) NOT NULL,
  negocio         VARCHAR(150),
  contacto        VARCHAR(200) NOT NULL,
  tipo_id         SMALLINT,
  mensaje         TEXT,
  estado_id       SMALLINT    NOT NULL DEFAULT 1,
  cliente_id      CHAR(36),
  origen          VARCHAR(50) NOT NULL DEFAULT 'web',
  ip_hash         VARCHAR(100),
  FOREIGN KEY (tipo_id) REFERENCES tipos_negocio(id) ON UPDATE CASCADE,
  FOREIGN KEY (estado_id) REFERENCES estados_contacto(id),
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL
);


CREATE TABLE contactos_cliente (
  id          CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  cliente_id  CHAR(36)    NOT NULL,
  tipo        VARCHAR(50) NOT NULL,
  valor       VARCHAR(200) NOT NULL,
  es_principal BOOLEAN    NOT NULL DEFAULT FALSE,
  UNIQUE KEY uk_cliente_tipo_valor (cliente_id, tipo, valor),
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
);


CREATE TABLE clientes_redes (
  cliente_id  CHAR(36)     NOT NULL,
  red_id      SMALLINT     NOT NULL,
  usuario     VARCHAR(150),
  activa      BOOLEAN      NOT NULL DEFAULT TRUE,
  PRIMARY KEY (cliente_id, red_id),
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
  FOREIGN KEY (red_id) REFERENCES redes_sociales(id) ON UPDATE CASCADE
);


CREATE TABLE contratos (
  id              CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  cliente_id      CHAR(36)    NOT NULL,
  servicio_id     SMALLINT    NOT NULL,
  estado_id       SMALLINT    NOT NULL DEFAULT 1,
  precio_acordado DECIMAL(10,2),
  fecha_inicio    DATE        NOT NULL DEFAULT (CURRENT_DATE),
  fecha_fin       DATE,
  notas           TEXT,
  UNIQUE KEY uk_cliente_servicio (cliente_id, servicio_id),
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
  FOREIGN KEY (servicio_id) REFERENCES tipos_servicio(id) ON UPDATE CASCADE,
  FOREIGN KEY (estado_id) REFERENCES estados_contrato(id)
);

CREATE TABLE posts (
  id              CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  contrato_id     CHAR(36)    NOT NULL,
  red_id          SMALLINT    NOT NULL,
  dia_id          SMALLINT,
  fecha_programada DATE,
  emoji           VARCHAR(10),
  texto           TEXT        NOT NULL,
  estado_id       SMALLINT    NOT NULL DEFAULT 2,
  publicado_at    DATETIME,
  semana_numero   SMALLINT,
  ano             SMALLINT,
  FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE CASCADE,
  FOREIGN KEY (red_id) REFERENCES redes_sociales(id) ON UPDATE CASCADE,
  FOREIGN KEY (dia_id) REFERENCES dias_semana(id) ON UPDATE CASCADE,
  FOREIGN KEY (estado_id) REFERENCES estados_post(id)
);


CREATE TABLE posts_hashtags (
  post_id   CHAR(36)    NOT NULL,
  hashtag   VARCHAR(100) NOT NULL,
  PRIMARY KEY (post_id, hashtag),
  FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);


CREATE TABLE pacientes (
  id              CHAR(36)  PRIMARY KEY DEFAULT (UUID()),
  created_at      DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
  cliente_id      CHAR(36)  NOT NULL,
  nombre          VARCHAR(150) NOT NULL,
  telefono        VARCHAR(50),
  email           VARCHAR(150),
  notas           TEXT,
  UNIQUE KEY uk_cliente_telefono (cliente_id, telefono),
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
);


CREATE TABLE citas (
  id              CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  contrato_id     CHAR(36)    NOT NULL,
  paciente_id     CHAR(36)    NOT NULL,
  fecha           DATE        NOT NULL,
  hora            TIME        NOT NULL,
  servicio_nombre VARCHAR(150),
  duracion_min    SMALLINT    DEFAULT 60,
  estado_id       SMALLINT    NOT NULL DEFAULT 1,
  notas           TEXT,
  UNIQUE KEY uk_cita_hora (contrato_id, fecha, hora),
  FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE RESTRICT,
  FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE RESTRICT,
  FOREIGN KEY (estado_id) REFERENCES estados_cita(id)
);


CREATE TABLE recordatorios (
  id          CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  cita_id     CHAR(36)    NOT NULL,
  canal_id    SMALLINT    NOT NULL,
  tipo        VARCHAR(50) NOT NULL,
  mensaje     TEXT        NOT NULL,
  estado_id   SMALLINT    NOT NULL DEFAULT 1,
  enviado_at  DATETIME,
  error_msg   TEXT,
  UNIQUE KEY uk_recordatorio (cita_id, canal_id, tipo),
  FOREIGN KEY (cita_id) REFERENCES citas(id) ON DELETE CASCADE,
  FOREIGN KEY (canal_id) REFERENCES canales_notificacion(id),
  FOREIGN KEY (estado_id) REFERENCES estados_notificacion(id)
);

CREATE TABLE notificaciones (
  id              CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  destinatario_tipo VARCHAR(50) NOT NULL,
  destinatario_id CHAR(36)    NOT NULL,
  canal_id        SMALLINT    NOT NULL,
  asunto          VARCHAR(200),
  mensaje         TEXT        NOT NULL,
  estado_id       SMALLINT    NOT NULL DEFAULT 1,
  enviado_at      DATETIME,
  error_msg       TEXT,
  origen_tipo     VARCHAR(50),
  origen_id       CHAR(36),
  FOREIGN KEY (canal_id) REFERENCES canales_notificacion(id),
  FOREIGN KEY (estado_id) REFERENCES estados_notificacion(id)
);

-- ================================================================
--  ÍNDICES
-- ================================================================
CREATE INDEX idx_contactos_estado    ON contactos (estado_id, created_at DESC);
CREATE INDEX idx_contactos_tipo      ON contactos (tipo_id);
CREATE INDEX idx_clientes_estado     ON clientes (estado_id);
CREATE INDEX idx_clientes_tipo       ON clientes (tipo_id);
CREATE INDEX idx_contratos_cliente   ON contratos (cliente_id, estado_id);
CREATE INDEX idx_contratos_servicio  ON contratos (servicio_id);
CREATE INDEX idx_posts_contrato      ON posts (contrato_id, created_at DESC);
CREATE INDEX idx_posts_semana        ON posts (contrato_id, ano, semana_numero);
CREATE INDEX idx_posts_estado        ON posts (estado_id);
CREATE INDEX idx_citas_fecha         ON citas (contrato_id, fecha, hora);
CREATE INDEX idx_citas_estado        ON citas (estado_id);
CREATE INDEX idx_notif_pendientes    ON notificaciones (estado_id, created_at);


-- ================================================================
--  TRIGGERS MySQL
-- ================================================================

DELIMITER //

CREATE TRIGGER set_post_semana_insert_trigger
BEFORE INSERT ON posts
FOR EACH ROW
BEGIN
  IF NEW.fecha_programada IS NOT NULL THEN
    SET NEW.semana_numero = WEEK(NEW.fecha_programada, 1);
    SET NEW.ano = YEAR(NEW.fecha_programada);
  ELSE
    SET NEW.semana_numero = WEEK(NOW(), 1);
    SET NEW.ano = YEAR(NOW());
  END IF;
END;
//

CREATE TRIGGER set_post_semana_update_trigger
BEFORE UPDATE ON posts
FOR EACH ROW
BEGIN
  IF NEW.fecha_programada IS NOT NULL THEN
    SET NEW.semana_numero = WEEK(NEW.fecha_programada, 1);
    SET NEW.ano = YEAR(NEW.fecha_programada);
  END IF;
END;
//

DELIMITER ;


-- ================================================================
--  VISTAS
-- ================================================================

CREATE OR REPLACE VIEW v_contactos AS
SELECT
  c.id, c.created_at, c.nombre, c.negocio, c.contacto,
  tn.nombre  AS tipo_negocio,
  ec.nombre  AS estado,
  c.mensaje, c.cliente_id, c.origen
FROM contactos c
LEFT JOIN tipos_negocio    tn ON tn.id = c.tipo_id
LEFT JOIN estados_contacto ec ON ec.id = c.estado_id;


CREATE OR REPLACE VIEW v_clientes_servicios AS
SELECT
  cl.id, cl.nombre_negocio, cl.tono,
  tn.nombre  AS tipo_negocio,
  ec.nombre  AS estado_cliente,
  ts.slug    AS servicio,
  ts.nombre  AS nombre_servicio,
  con.precio_acordado,
  con.fecha_inicio,
  eco.nombre AS estado_contrato
FROM clientes cl
JOIN tipos_negocio    tn  ON tn.id  = cl.tipo_id
JOIN estados_cliente  ec  ON ec.id  = cl.estado_id
JOIN contratos        con ON con.cliente_id = cl.id
JOIN tipos_servicio   ts  ON ts.id  = con.servicio_id
JOIN estados_contrato eco ON eco.id = con.estado_id;


CREATE OR REPLACE VIEW v_posts AS
SELECT
  p.id, p.created_at, p.texto, p.emoji,
  p.fecha_programada, p.publicado_at,
  rs.slug    AS red,
  rs.nombre  AS nombre_red,
  rs.color   AS color_red,
  ds.nombre  AS dia,
  ep.nombre  AS estado,
  p.semana_numero, p.ano,
  con.cliente_id,
  cl.nombre_negocio AS cliente
FROM posts p
JOIN redes_sociales   rs  ON rs.id  = p.red_id
LEFT JOIN dias_semana ds  ON ds.id  = p.dia_id
JOIN estados_post     ep  ON ep.id  = p.estado_id
JOIN contratos        con ON con.id = p.contrato_id
JOIN clientes         cl  ON cl.id  = con.cliente_id;


CREATE OR REPLACE VIEW v_citas AS
SELECT
  c.id, c.fecha, c.hora, c.servicio_nombre, c.duracion_min, c.notas,
  ec.nombre  AS estado,
  p.nombre   AS paciente,
  p.telefono AS paciente_tel,
  p.email    AS paciente_email,
  con.cliente_id,
  cl.nombre_negocio AS negocio
FROM citas c
JOIN estados_cita   ec  ON ec.id  = c.estado_id
JOIN pacientes       p  ON p.id   = c.paciente_id
JOIN contratos      con ON con.id = c.contrato_id
JOIN clientes        cl ON cl.id  = con.cliente_id;
