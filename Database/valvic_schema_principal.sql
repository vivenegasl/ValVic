-- ================================================================
--  ValVic — Schema PostgreSQL normalizado
--  Nivel: 3NF / BCNF con consideraciones de 4NF
--  ACID: Foreign keys, constraints, triggers, transacciones
-- ================================================================

-- ── Extensiones necesarias ────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- búsqueda de texto


-- ================================================================
--  CATÁLOGOS
--  Tablas de referencia inmutables. Eliminan dependencias
--  transitivas en todas las tablas que usan estos valores.
--  Normalizan: tipo text, estado text, red text, canal text, etc.
-- ================================================================

-- Tipos de negocio (clínica, restaurante, spa, etc.)
-- Elimina la dependencia transitiva: tabla.tipo → nombre_tipo
CREATE TABLE tipos_negocio (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE,
  icono  text                          -- emoji representativo
);

INSERT INTO tipos_negocio (nombre, icono) VALUES
  ('Clínica / Salud',     '🦷'),
  ('Restaurante / Café',  '🍽️'),
  ('Spa / Belleza',       '🌿'),
  ('Gimnasio / Fitness',  '💪'),
  ('Tienda online',       '🛍️'),
  ('Agencia',             '⚡'),
  ('Otro',                '🏢');


-- Catálogo de servicios que ofrece ValVic
-- Elimina: servicios text[] en clientes (viola 1NF y 4NF)
CREATE TABLE tipos_servicio (
  id              smallint PRIMARY KEY AUTO_INCREMENT,
  slug            text     NOT NULL UNIQUE, -- 'citas', 'contenido', etc.
  nombre          text     NOT NULL,
  descripcion     text,
  precio_proyecto numeric(10,2),           -- precio único de implementación
  precio_mensual  numeric(10,2)            -- precio recurrente mensual
);

INSERT INTO tipos_servicio (slug, nombre, descripcion, precio_proyecto, precio_mensual) VALUES
  ('citas',          'Asistente de citas IA',    'Agenda y recordatorio automático por WhatsApp', 135.00, 80.00),
  ('contenido',      'Creador de contenido IA',  'Posts semanales para redes sociales',           135.00, 80.00),
  ('reportes',       'Centro de reportes IA',    'Reporte semanal automático',                    110.00, 55.00),
  ('automatizacion', 'Automatización a medida',  'Flujos personalizados',                         NULL,   NULL),
  ('web',            'Sitio web profesional',    'Landing page + SEO',                            250.00, 50.00);


-- Redes sociales disponibles
-- Elimina: red text en posts (dependencia transitiva)
CREATE TABLE redes_sociales (
  id       smallint PRIMARY KEY AUTO_INCREMENT,
  slug     text     NOT NULL UNIQUE,  -- 'instagram', 'facebook', etc.
  nombre   text     NOT NULL,
  color    text,                      -- hex para UI
  icono    text                       -- emoji o nombre del ícono
);

INSERT INTO redes_sociales (slug, nombre, color, icono) VALUES
  ('instagram', 'Instagram', '#E1306C', '📸'),
  ('facebook',  'Facebook',  '#1877F2', '👤'),
  ('linkedin',  'LinkedIn',  '#0A66C2', '💼');


-- Días de la semana (para programación de posts)
-- Elimina: dia text en posts
CREATE TABLE dias_semana (
  id     smallint PRIMARY KEY,        -- 1=Lunes ... 7=Domingo (ISO)
  nombre text     NOT NULL UNIQUE
);

INSERT INTO dias_semana (id, nombre) VALUES
  (1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'),
  (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado'), (7, 'Domingo');


-- Canales de notificación
-- Elimina: canal text en notificaciones
CREATE TABLE canales_notificacion (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE   -- 'whatsapp', 'email', 'sms'
);

INSERT INTO canales_notificacion (nombre) VALUES
  ('whatsapp'), ('email'), ('sms');


-- ================================================================
--  ESTADOS POR ENTIDAD
--  Cada entidad tiene su propio ciclo de vida.
--  Separar en tablas distintas (en lugar de un estado genérico)
--  elimina dependencias transitivas y hace el sistema más seguro.
-- ================================================================

CREATE TABLE estados_contacto (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE   -- 'nuevo', 'contactado', 'convertido', 'perdido'
);
INSERT INTO estados_contacto (nombre) VALUES
  ('nuevo'), ('contactado'), ('en_negociacion'), ('convertido'), ('perdido');

CREATE TABLE estados_cliente (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE
);
INSERT INTO estados_cliente (nombre) VALUES
  ('activo'), ('pausado'), ('cancelado'), ('moroso');

CREATE TABLE estados_contrato (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE
);
INSERT INTO estados_contrato (nombre) VALUES
  ('activo'), ('pausado'), ('cancelado'), ('pendiente_pago');

CREATE TABLE estados_post (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE
);
INSERT INTO estados_post (nombre) VALUES
  ('generado'), ('pendiente_revision'), ('aprobado'), ('publicado'), ('rechazado');

CREATE TABLE estados_cita (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE
);
INSERT INTO estados_cita (nombre) VALUES
  ('programada'), ('confirmada'), ('completada'), ('cancelada'), ('no_asistio');

CREATE TABLE estados_notificacion (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE
);
INSERT INTO estados_notificacion (nombre) VALUES
  ('pendiente'), ('enviada'), ('fallida'), ('rebotada');


-- ================================================================
--  ENTIDADES CORE
-- ================================================================

-- ── Contactos (leads del formulario web) ─────────────────────
-- 3NF: tipo_id → FK a tipos_negocio (elimina transitiva tipo→nombre)
--       estado_id → FK a estados_contacto
-- BCNF: la PK determina todos los atributos
CREATE TABLE contactos (
  id              uuid        PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  updated_at      DATETIME NOT NULL DEFAULT now(),
  nombre          text        NOT NULL CHECK (length(nombre) BETWEEN 2 AND 100),
  negocio         text        CHECK (length(negocio) <= 150),
  contacto        text        NOT NULL CHECK (length(contacto) BETWEEN 5 AND 200),
  tipo_id         smallint    REFERENCES tipos_negocio(id) ON UPDATE CASCADE,
  mensaje         text        CHECK (length(mensaje) <= 2000),
  estado_id       smallint    NOT NULL REFERENCES estados_contacto(id) DEFAULT 1,
  -- Si se convirtió en cliente, referencia al cliente creado
  cliente_id      uuid,       -- FK se agrega después (referencia circular)
  origen          text        NOT NULL DEFAULT 'web',
  ip_hash         text        -- hash de IP para rate limiting, no la IP real
);


-- ── Clientes (negocios que contratan a ValVic) ────────────────
-- 3NF: tipo_id → FK a tipos_negocio
--       estado_id → FK a estados_cliente
-- 4NF: datos de contacto en tabla separada (múltiples teléfonos/emails)
--       servicios en tabla contratos (relación muchos-a-muchos)
CREATE TABLE clientes (
  id              uuid        PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  updated_at      DATETIME NOT NULL DEFAULT now(),
  nombre_negocio  text        NOT NULL CHECK (length(nombre_negocio) BETWEEN 2 AND 200),
  tipo_id         smallint    REFERENCES tipos_negocio(id) ON UPDATE CASCADE,
  estado_id       smallint    NOT NULL REFERENCES estados_cliente(id) DEFAULT 1,
  -- Contacto principal (desnormalización controlada para acceso rápido)
  contacto_nombre text        NOT NULL,
  -- Datos de configuración del negocio para automatizaciones
  diferenciador   text,       -- "qué hace único al negocio"
  tono            text,       -- 'profesional', 'cercano', 'divertido'
  promo_activa    text,       -- promoción vigente para contenido
  sheet_id        text        -- Google Sheet del cliente (si aplica)
);

-- FK circular resuelta después de CREATE TABLE clientes
ALTER TABLE contactos ADD CONSTRAINT fk_contacto_cliente
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL;


-- ── Contactos del cliente (teléfonos, emails, WhatsApp) ───────
-- 4NF: separa la dependencia multivaluada contactos_cliente
--       Un cliente puede tener múltiples medios de contacto
--       independientes entre sí.
CREATE TABLE contactos_cliente (
  id          uuid        PRIMARY KEY DEFAULT UUID(),
  cliente_id  uuid        NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  tipo        text        NOT NULL CHECK (tipo IN ('whatsapp', 'email', 'telefono', 'instagram', 'facebook')),
  valor       text        NOT NULL CHECK (length(valor) BETWEEN 4 AND 200),
  es_principal boolean    NOT NULL DEFAULT false,
  UNIQUE (cliente_id, tipo, valor)
);

-- Solo un contacto principal por tipo por cliente
CREATE UNIQUE INDEX idx_contacto_principal
  ON contactos_cliente (cliente_id, tipo)
  WHERE es_principal = true;


-- ── Redes contratadas por cliente ────────────────────────────
-- 4NF: separa la dependencia multivaluada cliente ↔ redes_sociales
--       independiente de los servicios contratados
CREATE TABLE clientes_redes (
  cliente_id  uuid     NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  red_id      smallint NOT NULL REFERENCES redes_sociales(id) ON UPDATE CASCADE,
  usuario     text,           -- @usuario en esa red
  activa      boolean  NOT NULL DEFAULT true,
  PRIMARY KEY (cliente_id, red_id)
);


-- ── Contratos (cliente ↔ servicio) ───────────────────────────
-- Resuelve la relación muchos-a-muchos entre clientes y servicios.
-- Elimina servicios text[] que violaba 1NF y 4NF.
-- BCNF: (cliente_id, servicio_id) → todos los demás atributos
CREATE TABLE contratos (
  id              uuid        PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  updated_at      DATETIME NOT NULL DEFAULT now(),
  cliente_id      uuid        NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
  servicio_id     smallint    NOT NULL REFERENCES tipos_servicio(id) ON UPDATE CASCADE,
  estado_id       smallint    NOT NULL REFERENCES estados_contrato(id) DEFAULT 1,
  precio_acordado numeric(10,2), -- puede diferir del precio_base
  fecha_inicio    date        NOT NULL DEFAULT CURRENT_DATE,
  fecha_fin       date,          -- NULL = sin vencimiento
  notas           text,
  UNIQUE (cliente_id, servicio_id)  -- un cliente no repite el mismo servicio
);


-- ================================================================
--  SERVICIO: CONTENIDO IA
-- ================================================================

-- ── Posts generados ───────────────────────────────────────────
-- 3NF: contrato_id → FK (elimina redundar cliente + servicio)
--       red_id → FK a redes_sociales (elimina transitiva red→nombre/color)
--       dia_id → FK a dias_semana (elimina transitiva dia→orden)
--       estado_id → FK a estados_post
-- Los hashtags en tabla separada (4NF: multivaluados independientes)
CREATE TABLE posts (
  id              uuid        PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  contrato_id     uuid        NOT NULL REFERENCES contratos(id) ON DELETE CASCADE,
  red_id          smallint    NOT NULL REFERENCES redes_sociales(id) ON UPDATE CASCADE,
  dia_id          smallint    REFERENCES dias_semana(id) ON UPDATE CASCADE,
  fecha_programada date,
  emoji           text,
  texto           text        NOT NULL CHECK (length(texto) BETWEEN 10 AND 3000),
  estado_id       smallint    NOT NULL REFERENCES estados_post(id) DEFAULT 2,
  publicado_at    DATETIME,
  semana_numero   smallint,   -- número de semana del año para agrupar
  ano             smallint    -- año para agrupar
);

-- ── Hashtags de cada post ─────────────────────────────────────
-- 4NF: los hashtags son multivaluados independientes del día/red
--       Separar permite buscar por hashtag, contar uso, evitar repetición
CREATE TABLE posts_hashtags (
  post_id   uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  hashtag   text NOT NULL CHECK (hashtag ~ '^#[a-zA-ZÀ-ÿ0-9_]+$'),
  PRIMARY KEY (post_id, hashtag)
);


-- ================================================================
--  SERVICIO: CITAS IA
-- ================================================================

-- ── Pacientes/clientes del negocio ───────────────────────────
-- 3NF: separado de citas porque un paciente tiene múltiples citas
--       sus datos no dependen de ninguna cita específica
CREATE TABLE pacientes (
  id              uuid  PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  cliente_id      uuid  NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  nombre          text  NOT NULL CHECK (length(nombre) BETWEEN 2 AND 150),
  telefono        text  CHECK (length(telefono) BETWEEN 5 AND 30),
  email           text  CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  notas           text,
  UNIQUE (cliente_id, telefono)  -- no duplicar paciente por tel en mismo negocio
);

-- ── Citas ─────────────────────────────────────────────────────
-- 3NF: cliente_id + paciente_id como FKs separadas (no transitivas)
--       estado_id → FK a estados_cita
-- BCNF: id determina todos los atributos
CREATE TABLE citas (
  id              uuid        PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  updated_at      DATETIME NOT NULL DEFAULT now(),
  contrato_id     uuid        NOT NULL REFERENCES contratos(id) ON DELETE RESTRICT,
  paciente_id     uuid        NOT NULL REFERENCES pacientes(id) ON DELETE RESTRICT,
  fecha           date        NOT NULL,
  hora            time        NOT NULL,
  servicio_nombre text,       -- "Limpieza dental", "Masaje relajante", etc.
  duracion_min    smallint    DEFAULT 60,
  estado_id       smallint    NOT NULL REFERENCES estados_cita(id) DEFAULT 1,
  notas           text,
  -- Constraint: no doble booking en mismo horario para mismo negocio
  UNIQUE (contrato_id, fecha, hora)
);

-- ── Recordatorios enviados por cita ──────────────────────────
-- 3NF: cita_id + canal_id como FKs (no transitivas)
-- Historial auditable de cada recordatorio
CREATE TABLE recordatorios (
  id          uuid        PRIMARY KEY DEFAULT UUID(),
  created_at  DATETIME NOT NULL DEFAULT now(),
  cita_id     uuid        NOT NULL REFERENCES citas(id) ON DELETE CASCADE,
  canal_id    smallint    NOT NULL REFERENCES canales_notificacion(id),
  tipo        text        NOT NULL CHECK (tipo IN ('24h', '1h', 'confirmacion', 'cancelacion')),
  mensaje     text        NOT NULL,
  estado_id   smallint    NOT NULL REFERENCES estados_notificacion(id) DEFAULT 1,
  enviado_at  DATETIME,
  error_msg   text,
  UNIQUE (cita_id, canal_id, tipo)  -- no enviar el mismo recordatorio dos veces
);


-- ================================================================
--  SERVICIO: REPORTES IA
-- ================================================================

CREATE TABLE reportes (
  id              uuid        PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  contrato_id     uuid        NOT NULL REFERENCES contratos(id) ON DELETE CASCADE,
  periodo_inicio  date        NOT NULL,
  periodo_fin     date        NOT NULL,
  -- KPIs calculados (desnormalización controlada para performance)
  total_citas     smallint,
  citas_completadas smallint,
  citas_canceladas  smallint,
  total_posts     smallint,
  posts_publicados  smallint,
  analisis_ia     text,       -- texto generado por Claude
  enviado_at      DATETIME,
  -- Constraint: un reporte por período por contrato
  UNIQUE (contrato_id, periodo_inicio, periodo_fin),
  CHECK (periodo_fin > periodo_inicio)
);


-- ================================================================
--  NOTIFICACIONES (log de salida)
--  Registro auditable de todas las notificaciones enviadas
-- ================================================================

CREATE TABLE notificaciones (
  id              uuid        PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  -- A quién va (puede ser cliente de ValVic o paciente de un cliente)
  destinatario_tipo text      NOT NULL CHECK (destinatario_tipo IN ('cliente', 'paciente', 'lead')),
  destinatario_id uuid        NOT NULL,  -- FK polimórfica (no se puede FK directo)
  canal_id        smallint    NOT NULL REFERENCES canales_notificacion(id),
  asunto          text,
  mensaje         text        NOT NULL,
  estado_id       smallint    NOT NULL REFERENCES estados_notificacion(id) DEFAULT 1,
  enviado_at      DATETIME,
  error_msg       text,
  -- Referencia al origen de la notificación
  origen_tipo     text        CHECK (origen_tipo IN ('cita', 'post', 'reporte', 'manual')),
  origen_id       uuid
);


-- ================================================================
--  ROW LEVEL SECURITY (RLS)
--  El frontend con anon key solo puede insertar contactos.
--  Todo lo demás requiere service_role (backend/scripts).
-- ================================================================

ALTER TABLE contactos           ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes            ENABLE ROW LEVEL SECURITY;
ALTER TABLE contactos_cliente   ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes_redes      ENABLE ROW LEVEL SECURITY;
ALTER TABLE contratos           ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts               ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts_hashtags      ENABLE ROW LEVEL SECURITY;
ALTER TABLE pacientes           ENABLE ROW LEVEL SECURITY;
ALTER TABLE citas               ENABLE ROW LEVEL SECURITY;
ALTER TABLE recordatorios       ENABLE ROW LEVEL SECURITY;
ALTER TABLE reportes            ENABLE ROW LEVEL SECURITY;
ALTER TABLE notificaciones      ENABLE ROW LEVEL SECURITY;

-- Política: el frontend SOLO puede insertar en contactos
CREATE POLICY "anon_insert_contactos" ON contactos
  FOR INSERT
  TO anon
  WITH CHECK (origen = 'web');

-- Política: nadie puede leer contactos desde el frontend
CREATE POLICY "no_select_contactos" ON contactos
  FOR SELECT
  USING (false);  -- solo service_role puede leer


-- ================================================================
--  ÍNDICES (performance)
-- ================================================================

-- Contactos: búsqueda por estado y fecha
CREATE INDEX idx_contactos_estado    ON contactos (estado_id, created_at DESC);
CREATE INDEX idx_contactos_tipo      ON contactos (tipo_id);

-- Clientes: búsqueda frecuente
CREATE INDEX idx_clientes_estado     ON clientes (estado_id);
CREATE INDEX idx_clientes_tipo       ON clientes (tipo_id);

-- Contratos: por cliente y servicio
CREATE INDEX idx_contratos_cliente   ON contratos (cliente_id, estado_id);
CREATE INDEX idx_contratos_servicio  ON contratos (servicio_id);

-- Posts: por contrato y semana (para el generador semanal)
CREATE INDEX idx_posts_contrato      ON posts (contrato_id, created_at DESC);
CREATE INDEX idx_posts_semana        ON posts (contrato_id, ano, semana_numero);
CREATE INDEX idx_posts_estado        ON posts (estado_id);

-- Búsqueda de texto en posts (para el historial del generador)
CREATE INDEX idx_posts_texto_trgm    ON posts USING gin (texto gin_trgm_ops);

-- Hashtags: buscar posts por hashtag
CREATE INDEX idx_hashtags_tag        ON posts_hashtags (hashtag);

-- Citas: por fecha y estado
CREATE INDEX idx_citas_fecha         ON citas (contrato_id, fecha, hora);
CREATE INDEX idx_citas_estado        ON citas (estado_id);

-- Recordatorios: pendientes de enviar
CREATE INDEX idx_recordatorios_pend  ON recordatorios (estado_id, cita_id)
  WHERE estado_id = 1;  -- solo pendientes

-- Notificaciones: por estado para procesamiento
CREATE INDEX idx_notif_pendientes    ON notificaciones (estado_id, created_at)
  WHERE estado_id = 1;


-- ================================================================
--  TRIGGERS (integridad automática)
-- ================================================================

-- Actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION trigger_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER set_updated_at_contactos
  BEFORE UPDATE ON contactos
  FOR EACH ROW EXECUTE FUNCTION trigger_updated_at();

CREATE TRIGGER set_updated_at_clientes
  BEFORE UPDATE ON clientes
  FOR EACH ROW EXECUTE FUNCTION trigger_updated_at();

CREATE TRIGGER set_updated_at_contratos
  BEFORE UPDATE ON contratos
  FOR EACH ROW EXECUTE FUNCTION trigger_updated_at();

CREATE TRIGGER set_updated_at_citas
  BEFORE UPDATE ON citas
  FOR EACH ROW EXECUTE FUNCTION trigger_updated_at();

-- Trigger: marcar contacto como convertido al crear cliente
CREATE OR REPLACE FUNCTION marcar_contacto_convertido()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  -- Busca un contacto con el mismo email/teléfono y lo marca como convertido
  UPDATE contactos
  SET
    estado_id  = (SELECT id FROM estados_contacto WHERE nombre = 'convertido'),
    cliente_id = NEW.id
  WHERE
    contacto ILIKE '%' || NEW.contacto_nombre || '%'
    AND estado_id != (SELECT id FROM estados_contacto WHERE nombre = 'convertido');
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_cliente_created
  AFTER INSERT ON clientes
  FOR EACH ROW EXECUTE FUNCTION marcar_contacto_convertido();

-- Trigger: poblar semana_numero y ano en posts automáticamente
CREATE OR REPLACE FUNCTION set_post_semana()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.fecha_programada IS NOT NULL THEN
    NEW.semana_numero = EXTRACT(WEEK FROM NEW.fecha_programada)::smallint;
    NEW.ano           = EXTRACT(YEAR FROM NEW.fecha_programada)::smallint;
  ELSE
    NEW.semana_numero = EXTRACT(WEEK FROM now())::smallint;
    NEW.ano           = EXTRACT(YEAR FROM now())::smallint;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER set_post_semana_trigger
  BEFORE INSERT OR UPDATE ON posts
  FOR EACH ROW EXECUTE FUNCTION set_post_semana();


-- ================================================================
--  VISTAS ÚTILES (desnormalización controlada para consultas)
--  Las vistas no rompen la normalización — los datos siguen
--  normalizados en las tablas base.
-- ================================================================

-- Vista: leads con nombre de estado y tipo legibles
CREATE OR REPLACE VIEW v_contactos AS
SELECT
  c.id, c.created_at, c.nombre, c.negocio, c.contacto,
  tn.nombre  AS tipo_negocio,
  ec.nombre  AS estado,
  c.mensaje, c.cliente_id, c.origen
FROM contactos c
LEFT JOIN tipos_negocio    tn ON tn.id = c.tipo_id
LEFT JOIN estados_contacto ec ON ec.id = c.estado_id;

-- Vista: clientes activos con sus servicios
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

-- Vista: posts con toda la info para el generador y el reporte
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

-- Vista: citas con info completa para recordatorios
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
