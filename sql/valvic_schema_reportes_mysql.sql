-- ================================================================
--  ValVic — Schema de Reportes MySQL (Convertido de PostgreSQL)
-- ================================================================

-- ================================================================
--  CATÁLOGOS ADICIONALES (amplían el schema principal)
-- ================================================================

INSERT INTO tipos_negocio (nombre, icono) VALUES
  ('Inmobiliaria',       '🏢'),
  ('Automotriz',         '🚗'),
  ('Hotel / Alojamiento','🏨'),
  ('Educación privada',  '🎓'),
  ('Jurídico / Notaría', '⚖️'),
  ('Clínica Estética',   '✨')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


CREATE TABLE fuentes_dato (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE,
  descripcion TEXT
);

INSERT INTO fuentes_dato (nombre, descripcion) VALUES
  ('automatico_valvic', 'Calculado desde las tablas de citas/posts de ValVic'),
  ('manual_cliente',    'Ingresado manualmente por el cliente vía formulario'),
  ('integracion_api',   'Obtenido de API externa (POS, CRM, etc.)')
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


CREATE TABLE frecuencias_reporte (
  id     SMALLINT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL UNIQUE,
  dias   SMALLINT NOT NULL
);

INSERT INTO frecuencias_reporte (nombre, dias) VALUES
  ('semanal',   7),
  ('mensual',  30),
  ('trimestral',90)
AS new ON DUPLICATE KEY UPDATE nombre=new.nombre;


-- ================================================================
--  PERÍODOS DE REPORTE
-- ================================================================

DROP TABLE IF EXISTS reportes CASCADE;

CREATE TABLE reportes (
  id               CHAR(36)    PRIMARY KEY DEFAULT (UUID()),
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  contrato_id      CHAR(36)    NOT NULL,
  frecuencia_id    SMALLINT    NOT NULL,
  periodo_inicio   DATE        NOT NULL,
  periodo_fin      DATE        NOT NULL,
  -- Estado del reporte
  generado_at      DATETIME,
  enviado_at       DATETIME,
  aprobado_by      VARCHAR(100),
  -- Análisis IA
  analisis_ia      TEXT,
  recomendaciones  TEXT,
  -- Control
  UNIQUE KEY uk_rep_rango (contrato_id, periodo_inicio, periodo_fin),
  FOREIGN KEY (contrato_id) REFERENCES contratos(id) ON DELETE RESTRICT,
  FOREIGN KEY (frecuencia_id) REFERENCES frecuencias_reporte(id),
  CHECK (periodo_fin > periodo_inicio)
);


-- ================================================================
--  CAPA 1: MÉTRICAS UNIVERSALES
-- ================================================================

CREATE TABLE metricas_universales (
  reporte_id          CHAR(36) PRIMARY KEY,
  ingresos_total      DECIMAL(14,2),
  ingresos_anterior   DECIMAL(14,2),
  gastos_total        DECIMAL(14,2),
  ticket_promedio     DECIMAL(10,2),
  transacciones_total INT,
  clientes_total      INT,
  clientes_nuevos     INT,
  clientes_recurrentes INT,
  tasa_retencion      DECIMAL(5,2),
  citas_programadas   INT,
  citas_completadas   INT,
  citas_canceladas    INT,
  citas_inasistencia  INT,
  tasa_asistencia     DECIMAL(5,2),
  posts_generados     INT,
  posts_publicados    INT,
  nps_score           SMALLINT CHECK (nps_score BETWEEN -100 AND 100),
  reseñas_positivas   SMALLINT,
  reseñas_negativas   SMALLINT,
  calificacion_promedio DECIMAL(3,2) CHECK (calificacion_promedio BETWEEN 0 AND 5),
  fuente_financiero_id  SMALLINT,
  fuente_clientes_id    SMALLINT,
  fuente_satisfaccion_id SMALLINT,
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE,
  FOREIGN KEY (fuente_financiero_id) REFERENCES fuentes_dato(id),
  FOREIGN KEY (fuente_clientes_id) REFERENCES fuentes_dato(id),
  FOREIGN KEY (fuente_satisfaccion_id) REFERENCES fuentes_dato(id)
);


-- ================================================================
--  CAPA 2: EXTENSIONES POR TIPO DE NEGOCIO
-- ================================================================

CREATE TABLE metricas_clinica (
  reporte_id              CHAR(36) PRIMARY KEY,
  horas_disponibles       DECIMAL(6,1),
  horas_ocupadas          DECIMAL(6,1),
  tasa_ocupacion          DECIMAL(5,2),
  procedimiento_top_1     VARCHAR(100),
  procedimiento_top_1_qty INT,
  procedimiento_top_2     VARCHAR(100),
  procedimiento_top_2_qty INT,
  procedimiento_top_3     VARCHAR(100),
  procedimiento_top_3_qty INT,
  tiempo_espera_promedio  SMALLINT,
  ingresos_seguros        DECIMAL(12,2),
  ingresos_particular     DECIMAL(12,2),
  pacientes_lista_espera  INT,
  complicaciones          INT DEFAULT 0,
  derivaciones            INT,
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

CREATE TABLE metricas_inmobiliaria (
  reporte_id              CHAR(36) PRIMARY KEY,
  propiedades_activas     INT,
  propiedades_nuevas      INT,
  propiedades_vendidas    INT,
  propiedades_arrendadas  INT,
  valor_cartera_total     DECIMAL(16,2),
  valor_vendido           DECIMAL(16,2),
  comision_total          DECIMAL(14,2),
  comision_promedio_pct   DECIMAL(5,2),
  visitas_realizadas      INT,
  leads_recibidos         INT,
  leads_calificados       INT,
  tasa_conversion_visita  DECIMAL(5,2),
  tasa_conversion_cierre  DECIMAL(5,2),
  dias_promedio_cierre    SMALLINT,
  operaciones_venta       INT,
  operaciones_arriendo    INT,
  operaciones_comercial   INT,
  precio_m2_promedio      DECIMAL(10,2),
  zona_top               VARCHAR(100),
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

CREATE TABLE metricas_automotriz (
  reporte_id              CHAR(36) PRIMARY KEY,
  vehiculos_vendidos      INT,
  vehiculos_nuevos_vendidos INT,
  vehiculos_usados_vendidos INT,
  valor_promedio_vehiculo DECIMAL(14,2),
  margen_promedio_pct     DECIMAL(5,2),
  financiamientos_cerrados INT,
  stock_disponible        INT,
  ordenes_trabajo         INT,
  ordenes_completadas     INT,
  tiempo_entrega_promedio DECIMAL(4,1),
  ingresos_taller         DECIMAL(12,2),
  servicios_top_1         VARCHAR(100),
  servicios_top_1_qty     INT,
  repuestos_vendidos_valor DECIMAL(12,2),
  llamadas_seguimiento    INT,
  clientes_satisfechos    INT,
  garantias_activadas     INT,
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

CREATE TABLE metricas_hotel (
  reporte_id              CHAR(36) PRIMARY KEY,
  habitaciones_total      SMALLINT,
  noches_disponibles      INT,
  noches_vendidas         INT,
  tasa_ocupacion          DECIMAL(5,2),
  adr                     DECIMAL(10,2),
  revpar                  DECIMAL(10,2),
  goppar                  DECIMAL(10,2),
  ingresos_habitaciones   DECIMAL(14,2),
  ingresos_restaurante    DECIMAL(14,2),
  ingresos_spa            DECIMAL(14,2),
  ingresos_eventos        DECIMAL(14,2),
  ingresos_otros          DECIMAL(14,2),
  huespedes_total         INT,
  huespedes_nacionales    INT,
  huespedes_extranjeros   INT,
  estadia_promedio_noches DECIMAL(4,1),
  reservas_directas       INT,
  reservas_ota            INT,
  tasa_reservas_directas  DECIMAL(5,2),
  canal_top_1             VARCHAR(100),
  canal_top_1_pct         DECIMAL(5,2),
  canal_top_2             VARCHAR(100),
  canal_top_2_pct         DECIMAL(5,2),
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

CREATE TABLE metricas_educacion (
  reporte_id              CHAR(36) PRIMARY KEY,
  matriculados_total      INT,
  matriculados_nuevos     INT,
  matriculados_egresados  INT,
  tasa_renovacion         DECIMAL(5,2),
  lista_espera            INT,
  programas_activos       SMALLINT,
  programa_top_1          VARCHAR(100),
  programa_top_1_qty      INT,
  ocupacion_promedio_aula DECIMAL(5,2),
  arancel_promedio        DECIMAL(10,2),
  tasa_morosidad          DECIMAL(5,2),
  cobranza_recuperada     DECIMAL(12,2),
  becas_otorgadas         INT,
  valor_becas             DECIMAL(12,2),
  docentes_activos        SMALLINT,
  ratio_alumno_docente    DECIMAL(5,1),
  tasa_aprobacion         DECIMAL(5,2),
  nps_alumnos             SMALLINT CHECK (nps_alumnos BETWEEN -100 AND 100),
  nps_apoderados          SMALLINT CHECK (nps_apoderados BETWEEN -100 AND 100),
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

CREATE TABLE metricas_juridico (
  reporte_id              CHAR(36) PRIMARY KEY,
  casos_activos           INT,
  casos_nuevos            INT,
  casos_cerrados          INT,
  casos_ganados           INT,
  tasa_exito              DECIMAL(5,2),
  duracion_promedio_dias  INT,
  tipo_caso_top_1         VARCHAR(100),
  tipo_caso_top_1_qty     INT,
  tipo_caso_top_2         VARCHAR(100),
  tipo_caso_top_2_qty     INT,
  honorarios_fijos        DECIMAL(14,2),
  honorarios_exito        DECIMAL(14,2),
  honorarios_pendientes   DECIMAL(14,2),
  tasa_cobranza           DECIMAL(5,2),
  abogados_activos        SMALLINT,
  casos_por_abogado       DECIMAL(5,1),
  horas_facturables       DECIMAL(8,1),
  escrituras_firmadas     INT,
  protocolizaciones       INT,
  autorizaciones          INT,
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

CREATE TABLE metricas_restaurante (
  reporte_id              CHAR(36) PRIMARY KEY,
  reservas_total          INT,
  cubiertos_total         INT,
  cubiertos_promedio_dia  DECIMAL(6,1),
  tasa_ocupacion_mesas    DECIMAL(5,2),
  no_shows                INT,
  ingresos_salon          DECIMAL(12,2),
  ingresos_delivery       DECIMAL(12,2),
  ingresos_takeaway       DECIMAL(12,2),
  ticket_promedio_salon   DECIMAL(8,2),
  ticket_promedio_delivery DECIMAL(8,2),
  plataformas_delivery    TEXT,
  plato_top_1             VARCHAR(100),
  plato_top_1_qty         INT,
  plato_top_2             VARCHAR(100),
  plato_top_2_qty         INT,
  plato_top_3             VARCHAR(100),
  plato_top_3_qty         INT,
  bebida_top_1            VARCHAR(100),
  bebida_top_1_qty        INT,
  costo_materia_prima     DECIMAL(12,2),
  food_cost_pct           DECIMAL(5,2),
  merma_pct               DECIMAL(5,2),
  personal_cocina         SMALLINT,
  personal_sala           SMALLINT,
  ventas_por_empleado     DECIMAL(10,2),
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

CREATE TABLE metricas_spa (
  reporte_id              CHAR(36) PRIMARY KEY,
  sesiones_total          INT,
  sesiones_por_dia        DECIMAL(5,1),
  tasa_ocupacion_salas    DECIMAL(5,2),
  duracion_promedio_min   SMALLINT,
  tratamiento_top_1       VARCHAR(100),
  tratamiento_top_1_qty   INT,
  tratamiento_top_1_ingreso DECIMAL(10,2),
  tratamiento_top_2       VARCHAR(100),
  tratamiento_top_2_qty   INT,
  tratamiento_top_3       VARCHAR(100),
  tratamiento_top_3_qty   INT,
  clientes_primera_vez    INT,
  clientes_paquete        INT,
  paquetes_vendidos       INT,
  ingresos_paquetes       DECIMAL(12,2),
  tasa_conversion_paquete DECIMAL(5,2),
  ingresos_productos      DECIMAL(12,2),
  productos_top_1         VARCHAR(100),
  productos_top_1_qty     INT,
  terapeutas_activos      SMALLINT,
  sesiones_por_terapeuta  DECIMAL(5,1),
  ingresos_por_terapeuta  DECIMAL(10,2),
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

-- ================================================================
--  CAPA 3: MÉTRICAS CUSTOM (EAV tipado)
-- ================================================================

CREATE TABLE catalogo_metricas_custom (
  id              SMALLINT PRIMARY KEY AUTO_INCREMENT,
  tipo_negocio_id SMALLINT,
  clave           VARCHAR(50) NOT NULL,
  etiqueta        VARCHAR(100) NOT NULL,
  tipo_dato       VARCHAR(20) NOT NULL CHECK (tipo_dato IN ('numero', 'porcentaje', 'texto', 'moneda', 'entero')),
  unidad          VARCHAR(20),
  descripcion     TEXT,
  fuente_id       SMALLINT,
  UNIQUE KEY uk_tipo_clave (tipo_negocio_id, clave),
  FOREIGN KEY (tipo_negocio_id) REFERENCES tipos_negocio(id),
  FOREIGN KEY (fuente_id) REFERENCES fuentes_dato(id)
);

CREATE TABLE metricas_custom (
  id              CHAR(36) PRIMARY KEY DEFAULT (UUID()),
  reporte_id      CHAR(36) NOT NULL,
  metrica_id      SMALLINT NOT NULL,
  valor_numero    DECIMAL(16,4),
  valor_texto     TEXT,
  fuente_id       SMALLINT,
  notas           TEXT,
  UNIQUE KEY uk_rep_metrica (reporte_id, metrica_id),
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE,
  FOREIGN KEY (metrica_id) REFERENCES catalogo_metricas_custom(id),
  FOREIGN KEY (fuente_id) REFERENCES fuentes_dato(id)
);

-- ================================================================
--  FORMULARIO DE INGRESO MANUAL
-- ================================================================

CREATE TABLE ingresos_manuales (
  id              CHAR(36) PRIMARY KEY DEFAULT (UUID()),
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reporte_id      CHAR(36) NOT NULL,
  campo           VARCHAR(100) NOT NULL,
  valor_anterior  TEXT,
  valor_nuevo     TEXT NOT NULL,
  ingresado_por   VARCHAR(100),
  FOREIGN KEY (reporte_id) REFERENCES reportes(id) ON DELETE CASCADE
);

DELIMITER //
CREATE TRIGGER check_reporte_aprobado
BEFORE INSERT ON ingresos_manuales
FOR EACH ROW
BEGIN
  DECLARE v_aprobado VARCHAR(100);
  SELECT aprobado_by INTO v_aprobado FROM reportes WHERE id = NEW.reporte_id;
  IF v_aprobado IS NOT NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede modificar un reporte ya aprobado';
  END IF;
END;
//
DELIMITER ;

-- ================================================================
--  PROCEDURE MYSQL: CALCULAR MÉTRICAS AUTOMÁTICAS
-- ================================================================

DELIMITER //
CREATE PROCEDURE calcular_metricas_automaticas(IN p_reporte_id CHAR(36))
BEGIN
  DECLARE v_contrato_id    CHAR(36);
  DECLARE v_periodo_inicio DATE;
  DECLARE v_periodo_fin    DATE;
  DECLARE v_citas_prog     INT;
  DECLARE v_citas_comp     INT;
  DECLARE v_citas_canc     INT;
  DECLARE v_citas_noas     INT;
  DECLARE v_posts_gen      INT;
  DECLARE v_posts_pub      INT;
  DECLARE v_tasa_asistencia DECIMAL(5,2);

  DECLARE v_estado_prog SMALLINT;
  DECLARE v_estado_conf SMALLINT;
  DECLARE v_estado_comp SMALLINT;
  DECLARE v_estado_canc SMALLINT;
  DECLARE v_estado_noas SMALLINT;
  DECLARE v_estado_pub SMALLINT;

  SELECT id INTO v_estado_prog FROM estados_cita WHERE nombre = 'programada';
  SELECT id INTO v_estado_conf FROM estados_cita WHERE nombre = 'confirmada';
  SELECT id INTO v_estado_comp FROM estados_cita WHERE nombre = 'completada';
  SELECT id INTO v_estado_canc FROM estados_cita WHERE nombre = 'cancelada';
  SELECT id INTO v_estado_noas FROM estados_cita WHERE nombre = 'no_asistio';
  SELECT id INTO v_estado_pub  FROM estados_post WHERE nombre = 'publicado';

  SELECT contrato_id, periodo_inicio, periodo_fin
  INTO v_contrato_id, v_periodo_inicio, v_periodo_fin
  FROM reportes WHERE id = p_reporte_id;

  SELECT
    SUM(CASE WHEN estado_id IN (v_estado_prog, v_estado_conf) THEN 1 ELSE 0 END),
    SUM(CASE WHEN estado_id = v_estado_comp THEN 1 ELSE 0 END),
    SUM(CASE WHEN estado_id = v_estado_canc THEN 1 ELSE 0 END),
    SUM(CASE WHEN estado_id = v_estado_noas THEN 1 ELSE 0 END)
  INTO v_citas_prog, v_citas_comp, v_citas_canc, v_citas_noas
  FROM citas
  WHERE contrato_id = v_contrato_id AND fecha BETWEEN v_periodo_inicio AND v_periodo_fin;

  IF (v_citas_comp + IFNULL(v_citas_noas,0)) > 0 THEN
    SET v_tasa_asistencia = ROUND((v_citas_comp / (v_citas_comp + v_citas_noas)) * 100, 2);
  END IF;

  SELECT
    COUNT(*),
    SUM(CASE WHEN estado_id = v_estado_pub THEN 1 ELSE 0 END)
  INTO v_posts_gen, v_posts_pub
  FROM posts
  WHERE contrato_id = v_contrato_id AND created_at BETWEEN v_periodo_inicio AND v_periodo_fin;

  INSERT INTO metricas_universales (
    reporte_id,
    citas_programadas, citas_completadas, citas_canceladas, citas_inasistencia,
    tasa_asistencia,
    posts_generados, posts_publicados,
    fuente_financiero_id, fuente_clientes_id
  ) VALUES (
    p_reporte_id,
    IFNULL(v_citas_prog, 0), IFNULL(v_citas_comp, 0), IFNULL(v_citas_canc, 0), IFNULL(v_citas_noas, 0),
    v_tasa_asistencia,
    IFNULL(v_posts_gen, 0), IFNULL(v_posts_pub, 0),
    (SELECT id FROM fuentes_dato WHERE nombre = 'manual_cliente'),
    (SELECT id FROM fuentes_dato WHERE nombre = 'automatico_valvic')
  )
  ON DUPLICATE KEY UPDATE
    citas_programadas  = VALUES(citas_programadas),
    citas_completadas  = VALUES(citas_completadas),
    citas_canceladas   = VALUES(citas_canceladas),
    citas_inasistencia = VALUES(citas_inasistencia),
    tasa_asistencia    = VALUES(tasa_asistencia),
    posts_generados    = VALUES(posts_generados),
    posts_publicados   = VALUES(posts_publicados);

  UPDATE reportes SET generado_at = NOW() WHERE id = p_reporte_id;
END;
//
DELIMITER ;


-- ================================================================
--  VISTAS
-- ================================================================

CREATE OR REPLACE VIEW v_reporte_completo AS
SELECT
  r.id                  AS reporte_id,
  r.periodo_inicio,
  r.periodo_fin,
  r.analisis_ia,
  fr.nombre             AS frecuencia,
  cl.nombre_negocio,
  cl.tono,
  cl.diferenciador,
  cl.promo_activa,
  tn.nombre             AS tipo_negocio,
  mu.ingresos_total,
  mu.ingresos_anterior,
  CASE
    WHEN mu.ingresos_anterior > 0
    THEN ROUND(((mu.ingresos_total - mu.ingresos_anterior) / mu.ingresos_anterior) * 100, 2)
  END                   AS crecimiento_ingresos_pct,
  mu.ticket_promedio,
  mu.transacciones_total,
  mu.clientes_total,
  mu.clientes_nuevos,
  mu.clientes_recurrentes,
  mu.tasa_retencion,
  mu.citas_programadas,
  mu.citas_completadas,
  mu.tasa_asistencia,
  mu.posts_generados,
  mu.posts_publicados,
  mu.nps_score,
  mu.calificacion_promedio
FROM reportes r
JOIN contratos           con ON con.id = r.contrato_id
JOIN clientes             cl ON cl.id  = con.cliente_id
JOIN tipos_negocio        tn ON tn.id  = cl.tipo_id
JOIN frecuencias_reporte  fr ON fr.id  = r.frecuencia_id
LEFT JOIN metricas_universales mu ON mu.reporte_id = r.id;


CREATE OR REPLACE VIEW v_reporte_resumen_kpis AS
SELECT
  r.id             AS reporte_id,
  cl.nombre_negocio,
  r.periodo_inicio,
  r.periodo_fin,
  mu.ingresos_total,
  mu.clientes_total,
  mu.tasa_asistencia,
  mu.nps_score,
  mu.posts_publicados,
  CASE
    WHEN mu.ingresos_anterior > 0 AND mu.ingresos_total IS NOT NULL
    THEN ROUND(((mu.ingresos_total - mu.ingresos_anterior) / mu.ingresos_anterior) * 100, 1)
    ELSE NULL
  END              AS variacion_ingresos_pct,
  r.analisis_ia,
  r.recomendaciones
FROM reportes r
JOIN contratos con ON con.id = r.contrato_id
JOIN clientes  cl  ON cl.id  = con.cliente_id
LEFT JOIN metricas_universales mu ON mu.reporte_id = r.id;

-- ================================================================
--  ÍNDICES
-- ================================================================

CREATE INDEX idx_reportes_contrato    ON reportes (contrato_id, periodo_inicio DESC);
CREATE INDEX idx_reportes_pendientes  ON reportes (generado_at, enviado_at);
CREATE INDEX idx_metricas_custom_rep  ON metricas_custom (reporte_id);
CREATE INDEX idx_ingresos_manuales    ON ingresos_manuales (reporte_id, created_at DESC);
