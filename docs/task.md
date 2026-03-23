# ValVic — Tareas Pendientes
> Última actualización: 22 marzo 2026

## Fase 0 — Revisión Inicial ✅
- [x] Leer y analizar `prompts_ventas.py`, `prospector.py`, YAMLs, SQL, requirements, setup
- [x] Actualizar review con hallazgos de los archivos nuevos

## Fase 1 — Bugs Críticos (Web)
- [x] Eliminar `onclick` inline del HTML → event delegation en `nav.js`
- [x] Eliminar styles inline del HTML → mover a `styles.css`
- [x] Corregir CSP en `.htaccess` — quitar `'unsafe-inline'` scripts

## Fase 1B — Bugs Críticos (Backend)
- [ ] Arreglar `subagente_db.py` — lectura MySQL (métodos async con aiomysql)
- [ ] Eliminar `config.py` legacy con credenciales hardcodeadas (en `Estructuras/`)

## Fase 2 — Actualización Web (según PROYECTO.md)
- [x] Precios web service: implementación=$120
- [x] Formulario: agregar verticales al dropdown (10 opciones incluyendo Dental, Veterinaria, Spa, etc.)
- [x] Footer: © 2026
- [x] Meta description: actualizada con foco en citas/dental/spa/veterinaria
- [x] FAQ: agregar las 4 preguntas (implementación, sistema actual, satisfacción, tipo negocio)


## Fase 3 — Entorno de Desarrollo ✅
- [x] Crear entorno virtual `.venv` en la raíz del proyecto
- [x] Instalar dependencias de `requirements.txt` (fastapi, anthropic, httpx, pydantic, uvicorn, etc.)
- [x] Resolver errores de importación del IDE (fastapi, pydantic, etc.)

## Fase 4 — Conversión SQL PostgreSQL → MySQL
- [ ] Convertir `valvic_schema_principal.sql` (gen_random_uuid→UUID, IDENTITY→AUTO_INCREMENT, timestamptz→DATETIME, etc.)
- [ ] Convertir `valvic_schema_reportes.sql`

## Fase 5 — Infraestructura Oracle (BLOQUEANTE: requiere 2FA con teléfono)
- [ ] Activar Oracle VM
- [ ] Crear usuario MySQL `valvic_app` en HeatWave
- [ ] Ejecutar `schema_prospeccion_mysql.sql` en MySQL
- [ ] Ejecutar schemas principales (post-conversión MySQL)
- [ ] Correr `setup_oracle.sh` en la VM
- [ ] Configurar SSL en api.valvic.cl con certbot
- [ ] Iniciar servicio `valvic-vicky` con systemd

## Fase 6 — Pruebas Locales (sin Oracle)
- [ ] Configurar `ANTHROPIC_API_KEY` en `.env`
- [ ] `python prospector.py --vertical dental --ciudad Santiago --cantidad 10 --test`
- [ ] `python agente_conversacion.py --simular --telefono "+56912345678"`

## Fase 7 — Post-Oracle (cuando Oracle esté activo)
- [ ] Configurar webhook 360dialog → `https://api.valvic.cl/webhook/whatsapp`
- [ ] Primer lote real: `python prospector.py --vertical dental --ciudad Santiago --cantidad 50`
- [ ] Migrar `generador.py` de Sheets a MySQL
- [ ] Migrar `notificaciones.py` de CallMeBot a 360dialog
- [ ] Mover archivos legacy a carpeta `legacy/` (generador, sheets, notificaciones, main, clientes, config)
- [ ] Panel web del negocio (`/panel/agenda`, `/panel/horarios`)
- [ ] Página del paciente (`valvic.cl/cita/TOKEN`)
- [ ] Integraciones Google My Business + Meta Graph
- [ ] Motor de reportes completo
- [ ] Agente de seguimiento (2do mensaje a 3 días sin respuesta)
- [ ] Sistema de cobro (Flow/Khipu) integrado en cierre de Vicky

## Fase 8 — Mejoras Técnicas
- [ ] Timeout en llamadas Claude API (ya tiene en clasificador, falta en generar_respuesta_vicky)
- [ ] `asyncio.get_running_loop()` en vez de `get_event_loop()` en `agente_conversacion.py`
- [ ] Crear páginas de aterrizaje SEO por vertical (`/clinica-dental`, `/veterinaria`, `/spa`)
- [ ] Actualizar JSON-LD con `serviceArea` (Santiago, Valparaíso, Concepción)
