# ValVic — Tareas Pendientes
> Última actualización: 22 marzo 2026

## Fase 0 — Revisión Inicial ✅
- [x] Leer y analizar `prompts_ventas.py`, `prospector.py`, YAMLs, SQL, requirements, setup
- [x] Actualizar review con hallazgos de los archivos nuevos

## Fase 1 — Bugs Críticos (Web)
- [x] Eliminar `onclick` inline del HTML → event delegation en `nav.js`
- [x] Eliminar styles inline del HTML → mover a `styles.css`
- [x] Corregir CSP en `.htaccess` — quitar `'unsafe-inline'` scripts

## Fase 1B — Bugs Críticos (Backend) ✅
- [x] Arreglar `subagente_db.py` — lectura MySQL (métodos async con aiomysql)
- [x] Eliminar `config.py` legacy con credenciales hardcodeadas (en `Estructuras/`)

## Fase 2 — Actualización Web & Branding ✅
- [x] Unificación de marca: "Val Vic" → "**ValVic**" en toda la web.
- [x] Temática visual: Adopción de paleta **Esmeralda Premium** con acentos Rubí.
- [x] Logotipos: Implementación de `favicon-180-transparent.png` (transparencia total).
- [x] Interactividad Landing: Rastro de luz (`cursor-glow`) reactivo (Emerald/Ruby).
- [x] Refactorización Panel: Separación estricta de CSS y JS en `/Panel/css` y `/Panel/js`.
- [x] Independización Arquitectónica: `/Landing` y `/Panel` como módulos raíz.
- [x] Consolidación Estructural: Unificación de `/Database` y `/Agentes/verticals`.
- [x] Corrección Smooth-Scroll en menú de navegación.


## Fase 3 — Entorno de Desarrollo ✅
- [x] Crear entorno virtual `.venv` en la raíz del proyecto
- [x] Instalar dependencias de `requirements.txt` (fastapi, anthropic, httpx, pydantic, uvicorn, etc.)
- [x] Resolver errores de importación del IDE (fastapi, pydantic, etc.)

## Fase 4 — Conversión SQL PostgreSQL → MySQL ✅
- [x] Convertir `valvic_schema_principal.sql` a MySQL HeatWave.
- [x] Convertir `valvic_schema_reportes.sql` a MySQL HeatWave.

## Fase 5 — Infraestructura Oracle (BLOQUEANTE)
- [ ] Activar Oracle VM (requiere 2FA con teléfono).
- [ ] Crear usuario MySQL `valvic_app` en HeatWave.
- [ ] Ejecutar `schema_prospeccion_mysql.sql` en MySQL.
- [ ] Ejecutar schemas principales en MySQL.
- [ ] Correr `setup_oracle.sh` en la VM.
- [ ] Configurar SSL en api.valvic.cl con certbot.
- [ ] Iniciar servicio `valvic-vicky` con systemd (FastAPI).

## Fase 6 — Pruebas Locales & Entorno ✅
- [x] Configurar `ANTHROPIC_API_KEY` en `.env`.
- [ ] Test de flujo conversacional con simulador de Agente.
- [x] Mover archivos legacy a carpeta `legacy/`.
- [x] Estructura del Panel web del negocio (`/panel`).

## Fase 7 — Migración a Meta WhatsApp Cloud API (Sustituye 360dialog)
- [x] Diseñar plan de migración (`docs/MIGRACION_META_API.md`).
- [ ] Crear App en Meta Developer Portal.
- [ ] Configurar Webhook de verificación (GET/POST) en FastAPI.
- [ ] Actualizar `agente_conversacion.py` con endpoints de Graph API v20.0.
- [ ] Pruebas de envío/recepción directo con Meta.
- [ ] Lanzar primer lote real con Meta: `python prospector.py --vertical dental --ciudad Santiago --cantidad 50`.

## Fase 8 — Despliegue y Orquestación (Opus/Sonnet/Gemini)
- [ ] **Planificar con Opus 4.6:** Usar el Master Prompt para desglosar subtareas.
- [ ] **Tareas Complejas (Sonnet):** Lógica de agentes, integración Meta API, Seguridad JWT.
- [ ] **Tareas Baja Complejidad (Gemini 3.1):** SEO por vertical, limpieza HTML, ajustes menores.

## Fase 9 — Post-Lanzamiento & Escalado
- [ ] Motor de reportes completo (consumiendo de MySQL HeatWave).
- [ ] Migrar lógica de `generador.py` (antiguo Sheets) a la nueva DB MySQL.
- [ ] Página de cita del paciente (`valvic.cl/cita/TOKEN`).
- [ ] Integraciones Google My Business y API de Google Reviews.
- [ ] Sistema de cobro (Flow/Khipu) integrado en flujo de Vicky.
- [ ] Agente de seguimiento (2do mensaje autónomo a los 3 días).

## Fase 10 — Onboarding Automatizado (Scalability)
- [ ] Implementar flujo de **Meta Embedded Signup** en el Panel.
- [ ] Backend para gestión de múltiples `PhoneID` por cliente.
- [ ] Dashboard de consumo de mensajes (cuota gratuita Meta).

## Fase 8 — Mejoras Técnicas
- [x] Timeout en llamadas Claude API (ya tiene en clasificador, falta en generar_respuesta_vicky)
- [x] `asyncio.get_running_loop()` en vez de `get_event_loop()` en `agente_conversacion.py`
- [ ] Crear páginas de aterrizaje SEO por vertical (`/clinica-dental`, `/veterinaria`, `/spa`)
- [x] Actualizar JSON-LD con `serviceArea` (Santiago, Valparaíso, Concepción)
