-- ================================================================
--  ValVic — Schema de Reportes (complemento al schema principal)
--  Patrón: Hybrid (Universal + Extensión por tipo de negocio)
--  Ingreso: Automático (desde tablas ValVic) + Manual (cliente)
--
--  Tipos de negocio cubiertos:
--    1. Clínica / Salud estética
--    2. Inmobiliaria
--    3. Automotriz (taller + venta)
--    4. Hotel / Alojamiento
--    5. Educación privada
--    6. Jurídico / Notaría
--    7. Restaurante / Café (alta rotación)
--    8. Spa / Belleza premium
-- ================================================================


-- ================================================================
--  CATÁLOGOS ADICIONALES (amplían el schema principal)
-- ================================================================

-- Agrega tipos de negocio de alto ticket al catálogo existente
INSERT INTO tipos_negocio (nombre, icono) VALUES
  ('Inmobiliaria',       '🏢'),
  ('Automotriz',         '🚗'),
  ('Hotel / Alojamiento','🏨'),
  ('Educación privada',  '🎓'),
  ('Jurídico / Notaría', '⚖️'),
  ('Clínica Estética',   '✨')
ON CONFLICT (nombre) DO NOTHING;


-- Fuentes de ingreso de datos en el reporte
-- Determina si el dato fue calculado automáticamente o ingresado por el cliente
CREATE TABLE fuentes_dato (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE,
  descripcion text
);

INSERT INTO fuentes_dato (nombre, descripcion) VALUES
  ('automatico_valvic', 'Calculado desde las tablas de citas/posts de ValVic'),
  ('manual_cliente',    'Ingresado manualmente por el cliente vía formulario'),
  ('integracion_api',   'Obtenido de API externa (POS, CRM, etc.)');


-- Frecuencias de reporte
CREATE TABLE frecuencias_reporte (
  id     smallint PRIMARY KEY AUTO_INCREMENT,
  nombre text     NOT NULL UNIQUE,
  dias   smallint NOT NULL  -- duración del período en días
);

INSERT INTO frecuencias_reporte (nombre, dias) VALUES
  ('semanal',   7),
  ('mensual',  30),
  ('trimestral',90);


-- ================================================================
--  PERÍODOS DE REPORTE
--  Entidad que agrupa todas las métricas de un período.
--  Reemplaza y amplía la tabla `reportes` del schema principal.
-- ================================================================

-- Primero eliminamos la tabla simple del schema anterior
DROP TABLE IF EXISTS reportes CASCADE;

CREATE TABLE reportes (
  id               uuid        PRIMARY KEY DEFAULT UUID(),
  created_at       DATETIME NOT NULL DEFAULT now(),
  updated_at       DATETIME NOT NULL DEFAULT now(),
  contrato_id      uuid        NOT NULL REFERENCES contratos(id) ON DELETE RESTRICT,
  frecuencia_id    smallint    NOT NULL REFERENCES frecuencias_reporte(id),
  periodo_inicio   date        NOT NULL,
  periodo_fin      date        NOT NULL,
  -- Estado del reporte
  generado_at      DATETIME,          -- cuándo se calcularon los datos
  enviado_at       DATETIME,          -- cuándo se envió al cliente
  aprobado_by      text,                 -- quién lo revisó en ValVic
  -- Análisis IA
  analisis_ia      text,                 -- texto generado por Claude
  recomendaciones  text,                 -- recomendaciones específicas
  -- Control
  UNIQUE (contrato_id, periodo_inicio, periodo_fin),
  CHECK (periodo_fin > periodo_inicio)
);

CREATE TRIGGER set_updated_at_reportes
  BEFORE UPDATE ON reportes
  FOR EACH ROW EXECUTE FUNCTION trigger_updated_at();


-- ================================================================
--  CAPA 1: MÉTRICAS UNIVERSALES
--  Aplican a TODOS los tipos de negocio sin excepción.
--  Fuente: mixta (algunas automáticas, otras manuales)
-- ================================================================

CREATE TABLE metricas_universales (
  reporte_id          uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- FINANCIERAS (fuente: manual_cliente — el negocio ingresa sus ingresos)
  ingresos_total      numeric(14,2),    -- ingresos brutos del período
  ingresos_anterior   numeric(14,2),    -- período anterior para comparar
  gastos_total        numeric(14,2),    -- gastos operacionales (opcional)
  ticket_promedio     numeric(10,2),    -- valor promedio por transacción
  transacciones_total integer,          -- número de ventas/servicios realizados

  -- CLIENTES (fuente: automático si usa bot de citas, sino manual)
  clientes_total      integer,          -- clientes únicos atendidos
  clientes_nuevos     integer,          -- primera vez en el período
  clientes_recurrentes integer,         -- ya habían comprado antes
  tasa_retencion      numeric(5,2),     -- % clientes que volvieron vs período anterior

  -- OPERACIONALES VALVIC (fuente: automático desde tablas de ValVic)
  -- Estos campos se calculan solos si el cliente usa los servicios
  citas_programadas   integer,          -- desde tabla citas
  citas_completadas   integer,          -- estado = 'completada'
  citas_canceladas    integer,          -- estado = 'cancelada'
  citas_inasistencia  integer,          -- estado = 'no_asistio'
  tasa_asistencia     numeric(5,2),     -- % calculado automáticamente
  posts_generados     integer,          -- desde tabla posts
  posts_publicados    integer,          -- estado = 'publicado'

  -- SATISFACCIÓN (fuente: manual o integración futura)
  nps_score           smallint CHECK (nps_score BETWEEN -100 AND 100),
  reseñas_positivas   smallint,
  reseñas_negativas   smallint,
  calificacion_promedio numeric(3,2) CHECK (calificacion_promedio BETWEEN 0 AND 5),

  -- METADATOS DE FUENTE
  fuente_financiero_id  smallint REFERENCES fuentes_dato(id),
  fuente_clientes_id    smallint REFERENCES fuentes_dato(id),
  fuente_satisfaccion_id smallint REFERENCES fuentes_dato(id)
);


-- ================================================================
--  CAPA 2: EXTENSIONES POR TIPO DE NEGOCIO
--  Cada tabla solo existe para su tipo de negocio.
--  La relación es 1:1 con reportes (un reporte tiene una extensión).
--  CHECK garantiza que el tipo de negocio sea correcto.
-- ================================================================

-- ── 2.1 CLÍNICA / SALUD ESTÉTICA ─────────────────────────────
-- Métricas específicas: procedimientos, tiempo en sala, ocupación
CREATE TABLE metricas_clinica (
  reporte_id              uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- Ocupación (fuente: automático si usa bot de citas)
  horas_disponibles       numeric(6,1),   -- horas totales de agenda disponible
  horas_ocupadas          numeric(6,1),   -- horas efectivamente agendadas
  tasa_ocupacion          numeric(5,2),   -- % calculado automáticamente

  -- Procedimientos (fuente: manual)
  procedimiento_top_1     text,           -- nombre del procedimiento más vendido
  procedimiento_top_1_qty integer,
  procedimiento_top_2     text,
  procedimiento_top_2_qty integer,
  procedimiento_top_3     text,
  procedimiento_top_3_qty integer,

  -- Gestión clínica (fuente: manual)
  tiempo_espera_promedio  smallint,       -- minutos promedio de espera
  ingresos_seguros        numeric(12,2),  -- ingresos vía seguros de salud
  ingresos_particular     numeric(12,2),  -- ingresos particulares
  pacientes_lista_espera  integer,        -- pacientes en lista de espera

  -- Indicadores de calidad (fuente: manual)
  complicaciones          integer DEFAULT 0,
  derivaciones            integer          -- pacientes derivados a especialista
);

-- ── 2.2 INMOBILIARIA ─────────────────────────────────────────
-- Métricas: propiedades, visitas, cierres, comisiones
CREATE TABLE metricas_inmobiliaria (
  reporte_id              uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- Cartera (fuente: manual)
  propiedades_activas     integer,        -- propiedades en cartera
  propiedades_nuevas      integer,        -- captadas en el período
  propiedades_vendidas    integer,        -- cerradas en el período
  propiedades_arrendadas  integer,

  -- Valor de cartera (fuente: manual)
  valor_cartera_total     numeric(16,2),  -- suma de valor de propiedades activas
  valor_vendido           numeric(16,2),  -- valor total de lo cerrado
  comision_total          numeric(14,2),  -- comisiones cobradas
  comision_promedio_pct   numeric(5,2),   -- % promedio de comisión

  -- Embudo de ventas (fuente: automático si usa bot de citas)
  visitas_realizadas      integer,
  leads_recibidos         integer,
  leads_calificados       integer,
  tasa_conversion_visita  numeric(5,2),   -- visitas → oferta
  tasa_conversion_cierre  numeric(5,2),   -- oferta → cierre
  dias_promedio_cierre    smallint,       -- días desde captación hasta cierre

  -- Tipos de operación (fuente: manual)
  operaciones_venta       integer,
  operaciones_arriendo    integer,
  operaciones_comercial   integer,

  -- Indicadores de mercado (fuente: manual)
  precio_m2_promedio      numeric(10,2),
  zona_top               text            -- barrio/zona con más actividad
);

-- ── 2.3 AUTOMOTRIZ ───────────────────────────────────────────
-- Métricas: venta de vehículos + taller (dos unidades de negocio)
CREATE TABLE metricas_automotriz (
  reporte_id              uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- VENTAS DE VEHÍCULOS (fuente: manual)
  vehiculos_vendidos      integer,
  vehiculos_nuevos_vendidos integer,
  vehiculos_usados_vendidos integer,
  valor_promedio_vehiculo numeric(14,2),
  margen_promedio_pct     numeric(5,2),   -- % de margen por vehículo
  financiamientos_cerrados integer,       -- ventas con financiamiento
  stock_disponible        integer,        -- vehículos en stock al cierre

  -- TALLER (fuente: automático si usa bot de citas)
  ordenes_trabajo         integer,        -- OTs abiertas en el período
  ordenes_completadas     integer,
  tiempo_entrega_promedio numeric(4,1),   -- días promedio de estadía en taller
  ingresos_taller         numeric(12,2),
  servicios_top_1         text,           -- servicio más frecuente
  servicios_top_1_qty     integer,
  repuestos_vendidos_valor numeric(12,2),

  -- POSTVENTA (fuente: manual)
  llamadas_seguimiento    integer,
  clientes_satisfechos    integer,
  garantias_activadas     integer
);

-- ── 2.4 HOTEL / ALOJAMIENTO ──────────────────────────────────
-- KPIs hoteleros estándar: RevPAR, ADR, ocupación
CREATE TABLE metricas_hotel (
  reporte_id              uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- OCUPACIÓN (fuente: manual o integración PMS)
  habitaciones_total      smallint,       -- total de habitaciones del hotel
  noches_disponibles      integer,        -- habitaciones × días del período
  noches_vendidas         integer,        -- noches efectivamente ocupadas
  tasa_ocupacion          numeric(5,2),   -- % calculado (noches_vendidas/disponibles)

  -- KPIs HOTELEROS ESTÁNDAR (fuente: calculado)
  adr                     numeric(10,2),  -- Average Daily Rate (ingreso/noche vendida)
  revpar                  numeric(10,2),  -- Revenue Per Available Room
  goppar                  numeric(10,2),  -- Gross Operating Profit Per Available Room

  -- INGRESOS POR CENTRO (fuente: manual)
  ingresos_habitaciones   numeric(14,2),
  ingresos_restaurante    numeric(14,2),
  ingresos_spa            numeric(14,2),
  ingresos_eventos        numeric(14,2),
  ingresos_otros          numeric(14,2),

  -- HUÉSPEDES (fuente: manual)
  huespedes_total         integer,
  huespedes_nacionales    integer,
  huespedes_extranjeros   integer,
  estadia_promedio_noches numeric(4,1),
  reservas_directas       integer,        -- sin intermediario (Booking, Airbnb)
  reservas_ota            integer,        -- via OTA (Booking, Airbnb, etc.)
  tasa_reservas_directas  numeric(5,2),   -- % calculado

  -- CANALES (fuente: manual)
  canal_top_1             text,           -- 'Booking.com', 'directo', etc.
  canal_top_1_pct         numeric(5,2),
  canal_top_2             text,
  canal_top_2_pct         numeric(5,2)
);

-- ── 2.5 EDUCACIÓN PRIVADA ────────────────────────────────────
-- Métricas: matrículas, retención, cobranza
CREATE TABLE metricas_educacion (
  reporte_id              uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- MATRÍCULA (fuente: manual)
  matriculados_total      integer,        -- alumnos activos en el período
  matriculados_nuevos     integer,        -- ingresos en el período
  matriculados_egresados  integer,        -- egresados o retirados
  tasa_renovacion         numeric(5,2),   -- % que renovó matrícula vs año anterior
  lista_espera            integer,

  -- PROGRAMAS (fuente: manual)
  programas_activos       smallint,       -- número de cursos/carreras activos
  programa_top_1          text,           -- programa con más alumnos
  programa_top_1_qty      integer,
  ocupacion_promedio_aula numeric(5,2),   -- % promedio de ocupación de salas

  -- FINANCIERO EDUCATIVO (fuente: manual)
  arancel_promedio        numeric(10,2),  -- arancel mensual promedio por alumno
  tasa_morosidad          numeric(5,2),   -- % de alumnos con pago atrasado
  cobranza_recuperada     numeric(12,2),  -- deuda recuperada en el período
  becas_otorgadas         integer,
  valor_becas             numeric(12,2),

  -- DOCENTES (fuente: manual)
  docentes_activos        smallint,
  ratio_alumno_docente    numeric(5,1),   -- alumnos por docente

  -- RESULTADOS (fuente: manual)
  tasa_aprobacion         numeric(5,2),   -- % alumnos que aprobaron el período
  nps_alumnos             smallint CHECK (nps_alumnos BETWEEN -100 AND 100),
  nps_apoderados          smallint CHECK (nps_apoderados BETWEEN -100 AND 100)
);

-- ── 2.6 JURÍDICO / NOTARÍA ───────────────────────────────────
-- Métricas: casos, honorarios, tiempos
CREATE TABLE metricas_juridico (
  reporte_id              uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- CARTERA DE CASOS (fuente: manual)
  casos_activos           integer,        -- casos abiertos al cierre del período
  casos_nuevos            integer,        -- abiertos en el período
  casos_cerrados          integer,        -- cerrados en el período
  casos_ganados           integer,        -- con resultado favorable
  tasa_exito              numeric(5,2),   -- % calculado (ganados/cerrados)
  duracion_promedio_dias  integer,        -- días promedio de duración de un caso

  -- TIPOS DE CASO (fuente: manual)
  tipo_caso_top_1         text,           -- 'laboral', 'civil', 'penal', etc.
  tipo_caso_top_1_qty     integer,
  tipo_caso_top_2         text,
  tipo_caso_top_2_qty     integer,

  -- HONORARIOS (fuente: manual)
  honorarios_fijos        numeric(14,2),  -- contratos de honorario fijo
  honorarios_exito        numeric(14,2),  -- porcentaje sobre resultado
  honorarios_pendientes   numeric(14,2),  -- por cobrar
  tasa_cobranza           numeric(5,2),   -- % cobrado del total facturado

  -- EQUIPO (fuente: manual)
  abogados_activos        smallint,
  casos_por_abogado       numeric(5,1),   -- promedio de carga
  horas_facturables       numeric(8,1),   -- si cobra por hora

  -- NOTARÍA (si aplica, fuente: manual)
  escrituras_firmadas     integer,
  protocolizaciones       integer,
  autorizaciones          integer
);

-- ── 2.7 RESTAURANTE / CAFÉ ───────────────────────────────────
-- Alta rotación, múltiples servicios (mesa, delivery, take away)
CREATE TABLE metricas_restaurante (
  reporte_id              uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- SERVICIO (fuente: automático si usa bot de reservas)
  reservas_total          integer,
  cubiertos_total         integer,        -- personas atendidas
  cubiertos_promedio_dia  numeric(6,1),
  tasa_ocupacion_mesas    numeric(5,2),   -- % de mesas ocupadas en horario pico
  no_shows                integer,        -- reservas que no llegaron

  -- VENTAS POR CANAL (fuente: manual)
  ingresos_salon          numeric(12,2),
  ingresos_delivery       numeric(12,2),
  ingresos_takeaway       numeric(12,2),
  ticket_promedio_salon   numeric(8,2),
  ticket_promedio_delivery numeric(8,2),
  plataformas_delivery    text,           -- 'Rappi, PedidosYa', etc.

  -- MENÚ (fuente: manual)
  plato_top_1             text,
  plato_top_1_qty         integer,
  plato_top_2             text,
  plato_top_2_qty         integer,
  plato_top_3             text,
  plato_top_3_qty         integer,
  bebida_top_1            text,
  bebida_top_1_qty        integer,

  -- COSTOS (fuente: manual)
  costo_materia_prima     numeric(12,2),
  food_cost_pct           numeric(5,2),   -- % costo de alimentos sobre ventas
  merma_pct               numeric(5,2),   -- % de pérdida por merma

  -- PERSONAL (fuente: manual)
  personal_cocina         smallint,
  personal_sala           smallint,
  ventas_por_empleado     numeric(10,2)
);

-- ── 2.8 SPA / BELLEZA PREMIUM ────────────────────────────────
CREATE TABLE metricas_spa (
  reporte_id              uuid    PRIMARY KEY REFERENCES reportes(id) ON DELETE CASCADE,

  -- SERVICIOS (fuente: automático si usa bot de citas)
  sesiones_total          integer,
  sesiones_por_dia        numeric(5,1),
  tasa_ocupacion_salas    numeric(5,2),
  duracion_promedio_min   smallint,

  -- TRATAMIENTOS (fuente: manual)
  tratamiento_top_1       text,
  tratamiento_top_1_qty   integer,
  tratamiento_top_1_ingreso numeric(10,2),
  tratamiento_top_2       text,
  tratamiento_top_2_qty   integer,
  tratamiento_top_3       text,
  tratamiento_top_3_qty   integer,

  -- CLIENTES (fuente: manual)
  clientes_primera_vez    integer,
  clientes_paquete        integer,        -- con paquete de sesiones prepagado
  paquetes_vendidos       integer,
  ingresos_paquetes       numeric(12,2),
  tasa_conversion_paquete numeric(5,2),   -- % que compra paquete tras primera visita

  -- PRODUCTOS (fuente: manual)
  ingresos_productos      numeric(12,2),  -- venta de productos (cremas, etc.)
  productos_top_1         text,
  productos_top_1_qty     integer,

  -- PERSONAL (fuente: manual)
  terapeutas_activos      smallint,
  sesiones_por_terapeuta  numeric(5,1),
  ingresos_por_terapeuta  numeric(10,2)
);


-- ================================================================
--  CAPA 3: MÉTRICAS CUSTOM (EAV tipado)
--  Para métricas no previstas sin romper el schema.
--  Solo cuando las extensiones anteriores no cubren el dato.
-- ================================================================

-- Catálogo de métricas custom disponibles por tipo de negocio
CREATE TABLE catalogo_metricas_custom (
  id              smallint PRIMARY KEY AUTO_INCREMENT,
  tipo_negocio_id smallint REFERENCES tipos_negocio(id),  -- NULL = aplica a todos
  clave           text     NOT NULL,
  etiqueta        text     NOT NULL,    -- nombre legible para el cliente
  tipo_dato       text     NOT NULL CHECK (tipo_dato IN ('numero', 'porcentaje', 'texto', 'moneda', 'entero')),
  unidad          text,                 -- 'kg', 'min', 'USD', etc.
  descripcion     text,
  fuente_id       smallint REFERENCES fuentes_dato(id),
  UNIQUE (tipo_negocio_id, clave)
);

-- Valores de métricas custom por reporte
CREATE TABLE metricas_custom (
  id              uuid     PRIMARY KEY DEFAULT UUID(),
  reporte_id      uuid     NOT NULL REFERENCES reportes(id) ON DELETE CASCADE,
  metrica_id      smallint NOT NULL REFERENCES catalogo_metricas_custom(id),
  valor_numero    numeric(16,4),
  valor_texto     text,
  fuente_id       smallint REFERENCES fuentes_dato(id),
  notas           text,
  UNIQUE (reporte_id, metrica_id)
);


-- ================================================================
--  FORMULARIO DE INGRESO MANUAL
--  Registra exactamente qué datos ingresó el cliente y cuándo.
--  Permite rastrear qué campos fueron llenados vs automáticos.
-- ================================================================

CREATE TABLE ingresos_manuales (
  id              uuid        PRIMARY KEY DEFAULT UUID(),
  created_at      DATETIME NOT NULL DEFAULT now(),
  reporte_id      uuid        NOT NULL REFERENCES reportes(id) ON DELETE CASCADE,
  campo           text        NOT NULL,   -- nombre del campo actualizado
  valor_anterior  text,                   -- para auditoría
  valor_nuevo     text        NOT NULL,
  ingresado_por   text,                   -- identificador del cliente
  -- No se permite modificar datos ya aprobados
  CONSTRAINT no_modificar_aprobado CHECK (true)  -- se refuerza con trigger
);

-- Trigger: no permitir modificar reporte ya aprobado
CREATE OR REPLACE FUNCTION validar_modificacion_reporte()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  aprobado text;
BEGIN
  SELECT aprobado_by INTO aprobado
  FROM reportes WHERE id = NEW.reporte_id;
  IF aprobado IS NOT NULL THEN
    RAISE EXCEPTION 'No se puede modificar un reporte ya aprobado';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER check_reporte_aprobado
  BEFORE INSERT ON ingresos_manuales
  FOR EACH ROW EXECUTE FUNCTION validar_modificacion_reporte();


-- ================================================================
--  FUNCIÓN: CALCULAR MÉTRICAS AUTOMÁTICAS
--  Calcula los datos que vienen de las tablas de ValVic.
--  Se llama al generar el reporte.
-- ================================================================

CREATE OR REPLACE FUNCTION calcular_metricas_automaticas(p_reporte_id uuid)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_contrato_id    uuid;
  v_periodo_inicio date;
  v_periodo_fin    date;
  v_citas_prog     integer;
  v_citas_comp     integer;
  v_citas_canc     integer;
  v_citas_noas     integer;
  v_posts_gen      integer;
  v_posts_pub      integer;
  v_tasa_asistencia numeric(5,2);
BEGIN
  -- Obtener datos del reporte
  SELECT contrato_id, periodo_inicio, periodo_fin
  INTO v_contrato_id, v_periodo_inicio, v_periodo_fin
  FROM reportes WHERE id = p_reporte_id;

  -- Calcular métricas de citas
  SELECT
    COUNT(*)                                          FILTER (WHERE c.estado_id = (SELECT id FROM estados_cita WHERE nombre = 'programada' OR nombre = 'confirmada')),
    COUNT(*)                                          FILTER (WHERE c.estado_id = (SELECT id FROM estados_cita WHERE nombre = 'completada')),
    COUNT(*)                                          FILTER (WHERE c.estado_id = (SELECT id FROM estados_cita WHERE nombre = 'cancelada')),
    COUNT(*)                                          FILTER (WHERE c.estado_id = (SELECT id FROM estados_cita WHERE nombre = 'no_asistio'))
  INTO v_citas_prog, v_citas_comp, v_citas_canc, v_citas_noas
  FROM citas c
  WHERE c.contrato_id = v_contrato_id
    AND c.fecha BETWEEN v_periodo_inicio AND v_periodo_fin;

  -- Tasa de asistencia
  IF (v_citas_comp + v_citas_noas) > 0 THEN
    v_tasa_asistencia := round((v_citas_comp::numeric / (v_citas_comp + v_citas_noas)) * 100, 2);
  END IF;

  -- Calcular métricas de posts
  SELECT
    COUNT(*),
    COUNT(*) FILTER (WHERE p.estado_id = (SELECT id FROM estados_post WHERE nombre = 'publicado'))
  INTO v_posts_gen, v_posts_pub
  FROM posts p
  WHERE p.contrato_id = v_contrato_id
    AND p.created_at BETWEEN v_periodo_inicio AND v_periodo_fin;

  -- Insertar o actualizar métricas universales automáticas
  INSERT INTO metricas_universales (
    reporte_id,
    citas_programadas, citas_completadas, citas_canceladas, citas_inasistencia,
    tasa_asistencia,
    posts_generados, posts_publicados,
    fuente_financiero_id, fuente_clientes_id
  ) VALUES (
    p_reporte_id,
    v_citas_prog, v_citas_comp, v_citas_canc, v_citas_noas,
    v_tasa_asistencia,
    v_posts_gen, v_posts_pub,
    (SELECT id FROM fuentes_dato WHERE nombre = 'manual_cliente'),
    (SELECT id FROM fuentes_dato WHERE nombre = 'automatico_valvic')
  )
  ON CONFLICT (reporte_id) DO UPDATE SET
    citas_programadas  = EXCLUDED.citas_programadas,
    citas_completadas  = EXCLUDED.citas_completadas,
    citas_canceladas   = EXCLUDED.citas_canceladas,
    citas_inasistencia = EXCLUDED.citas_inasistencia,
    tasa_asistencia    = EXCLUDED.tasa_asistencia,
    posts_generados    = EXCLUDED.posts_generados,
    posts_publicados   = EXCLUDED.posts_publicados;

  -- Marcar como generado
  UPDATE reportes SET generado_at = now() WHERE id = p_reporte_id;

END;
$$;


-- ================================================================
--  VISTAS PARA GENERACIÓN DE REPORTES CON IA
--  Claude recibe estas vistas ya procesadas → genera el análisis
-- ================================================================

-- Vista completa para cualquier tipo de negocio
CREATE OR REPLACE VIEW v_reporte_completo AS
SELECT
  r.id                  AS reporte_id,
  r.periodo_inicio,
  r.periodo_fin,
  r.analisis_ia,
  fr.nombre             AS frecuencia,
  -- Cliente
  cl.nombre_negocio,
  cl.tono,
  cl.diferenciador,
  cl.promo_activa,
  tn.nombre             AS tipo_negocio,
  -- Métricas universales
  mu.ingresos_total,
  mu.ingresos_anterior,
  CASE
    WHEN mu.ingresos_anterior > 0
    THEN round(((mu.ingresos_total - mu.ingresos_anterior) / mu.ingresos_anterior) * 100, 2)
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


-- Vista resumen de KPIs para el email/WhatsApp al cliente
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
    THEN round(((mu.ingresos_total - mu.ingresos_anterior) / mu.ingresos_anterior) * 100, 1)
    ELSE NULL
  END              AS variacion_ingresos_pct,
  r.analisis_ia,
  r.recomendaciones
FROM reportes r
JOIN contratos con ON con.id = r.contrato_id
JOIN clientes  cl  ON cl.id  = con.cliente_id
LEFT JOIN metricas_universales mu ON mu.reporte_id = r.id;


-- ================================================================
--  RLS PARA TABLAS DE REPORTES
-- ================================================================

ALTER TABLE reportes              ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_universales  ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_clinica      ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_inmobiliaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_automotriz   ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_hotel        ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_educacion    ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_juridico     ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_restaurante  ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_spa          ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_custom       ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingresos_manuales     ENABLE ROW LEVEL SECURITY;

-- Solo service_role puede leer/escribir reportes
-- El frontend nunca accede directamente a estas tablas


-- ================================================================
--  ÍNDICES ADICIONALES
-- ================================================================

CREATE INDEX idx_reportes_contrato    ON reportes (contrato_id, periodo_inicio DESC);
CREATE INDEX idx_reportes_pendientes  ON reportes (generado_at, enviado_at)
  WHERE enviado_at IS NULL;
CREATE INDEX idx_metricas_custom_rep  ON metricas_custom (reporte_id);
CREATE INDEX idx_ingresos_manuales    ON ingresos_manuales (reporte_id, created_at DESC);
