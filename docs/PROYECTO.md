# ValVic — Constitución Técnica y Arquitectura
> [!IMPORTANT]
> **REGLA DE MEMORIA VIVA:** Al inicio de cada sesión, el agente DEBE leer `/.agent/brain/`. Al finalizar cada hito o antes de terminar la sesión, el agente DEBE actualizar proactivamente el Master Brain (`ESTADO_ACTUAL.md`, `ARQUITECTURA.md`).

> Archivo de referencia OBLIGATORIO para Claude y otras IAs.
> Última actualización: Marzo 2026.

---

## REGLAS CRÍTICAS — LEER ANTES DE CUALQUIER RESPUESTA

Estas restricciones son NO NEGOCIABLES. Si una propuesta técnica viola cualquiera de estas reglas, recházala sin importar cuán elegante parezca la solución alternativa.

**Lectura Obligatoria y Estándar Senior (NUEVA REGLA):**
- **Contexto Mandatorio:** Es OBLIGATORIO Y ESTRICTO que cualquier asistente de IA (Claude, Gemini, etc.) lea el contenido completo de este archivo (`PROYECTO.md`) como su primer paso de contexto en cualquier sesión, sin excepciones.
- **Calidad Senior:** Todo código debe soportar la revisión de un equipo de ingenieros Senior. Esto exige: arquitectura limpia, principios DRY (Don't Repeat Yourself), código altamente modular y manejo seguro de errores. Si una restricción (como usar Vanilla HTML/JS) induce a repetir código (ej. menús laterales), el agente DEBE proponer proactivamente soluciones modulares compatibles (ej. inyección por Web Components o JS Fetch) para mantener el estándar.

**Stack — nunca proponer alternativas a:**
- **Base de datos:** MySQL HeatWave en Oracle. NUNCA PostgreSQL, Supabase, o PlanetScale.
- **Backend:** Python 3 + FastAPI. NUNCA Node.js como runtime principal, NUNCA frameworks de agentes abstractos (LangChain, CrewAI, etc.).
- **Frontend:** HTML/CSS/JS puro. NUNCA React, Vue, Next.js, Svelte.
- **Automatización:** Python directo con crontab. NUNCA n8n, Make, Zapier.
- **Infraestructura:** Oracle Cloud Free Tier. NUNCA AWS, GCP, Azure, Railway.

**Código e Integridad — aplicar siempre:**
- **PKs UUID:** En toda tabla expuesta al exterior — nunca auto-increment.
- **Estados BBDD:** Como FK a tabla de estados — NUNCA TEXT libre ("activo", etc).
- **Pydantic v2:** Para todos los modelos de datos en Python Python.
- **Credenciales:** Variables de entorno estricto en `.env` — nunca hardcodeadas.
- **Manejo de Errores:** Try/except en toda llamada a API externa con logging estricto.

**Seguridad (NUEVO):**
- **Autenticación:** Todo panel (`/panel`) requiere validación vía JWT usando cookies `HttpOnly` y `Secure`.
- **Webhooks:** Todo Request a `/webhook/whatsapp` DEBE validar el header/firma criptográfica de 360dialog para prevenir inyecciones.
- **Backups:** Un script en `cron` diario (3 AM) debe hacer `mysqldump` y enviarlo de forma encriptada a Oracle Object Storage.

**Regla de Negocio sobre Modelos de Agentes:**
- **Intervención Humana:** Ningún agente enviará el PRIMER mensaje de contacto en frío sin aprobación humana (comando `ENVIAR`). Sin embargo, el seguimiento automático y la respuesta a leads tibios dentro de las 24 horas es 100% autónoma.
- **Exclusividad de Datos:** El contexto que recibe cada agente debe ser el *mínimo* estricto necesario para operar.

---

## DECISIONES DE ARQUITECTURA TÉCNICA

| Decisión | Por qué esta |
|---|---|
| MySQL en Oracle Cloud | Always Free permanente; 50GB; control total sobre la instancia. |
| Python + FastAPI | SDK Anthropic es Python-primero; I/O bound puro; ideal para Dev Solitario. |
| HTML/CSS/JS puro | Políticas CSP estrictas; cero dependencias; despliegue drag-and-drop en Hostinger. |
| Python directo para crons | Sin vendor lock-in; permite lógica compleja e inyección de DB gratis. |
| 360dialog para WhatsApp | Uso Oficial BSP. Baileys viola ToS y arriesga baneo permanente. |
| Pydantic v2 | Validación estricta en runtime y de-serialización. |
| Config vertical YAML | Agregar un rubro nuevo exige CERO cambios de código. Todo se lee dinámicamente. |

---

## STACK TECNOLÓGICO Y ENTORNOS

### 1. Frontend (Clientes) — Hostinger Business
- HTML/CSS/JS modular, cero CSS inline (csp-ready).
- Fuentes: Fraunces (titulares), DM Sans (cuerpo).
- Dominio: valvic.cl | email: contacto@valvic.cl

### 2. Backend API — Oracle VM Ampere
- 4 CPU, 24GB RAM, Ubuntu 22.04 LTS.
- Base de datos: MySQL HeatWave 50GB.
- API: FastAPI (Python 3.11+).

### 3. APIs Externas Autorizadas
- **Claude:** `claude-sonnet` (texto persuasivo) y `claude-haiku-3-5` (clasificación batch).
- **Google Places API v1 (Nueva):** Endpoint `places:searchText` con FieldMasks en JSON para buscar prospectos. (NO la antigua versión legacy /textsearch).
- **WhatsApp API:** 360dialog Oficial (requiere uso de tipo `template` para los message openers).

---

## BASE DE DATOS Y ESTÁNDARES SQL

**Incompatibilidades clave PostgreSQL → MySQL HeatWave (a tener en cuenta al migrar esquemas):**
- `gen_random_uuid()` → Debes usar `UUID()` de MySQL.
- `GENERATED ALWAYS AS IDENTITY` → Debes usar `AUTO_INCREMENT`.
- `timestamptz` → Debes usar `DATETIME`.
- `ON CONFLICT DO UPDATE` → Debes usar `ON DUPLICATE KEY UPDATE`.

---

## PROCESO DE DESARROLLO DE AGENTES (SPARC API)

Antes de programar un agente, escribir y documentar el flujo dictado por el Metamodelo SPARC:
1. **Especificación:** ¿Qué decisiones toma solos? ¿Qué detona un break de emergencia?
2. **Tools:** Lista exacta de funciones a las que tiene acceso. 
3. **Pydantic Schemas:** Definir un In/Out strict output.
4. **Manejo de Errores:** ¿Reintenta backoff exponencial o aborta?
5. **Testing:** Proceso en aislamiento (simulación `--test` CLI) antes de exponerlo a 360dialog.

---
> **Nota para IAs:** Los estados de las tareas pendientes residen en `task.md`. Los precios y la estrategia de ventas comercial residen en `VENTAS.md`. El inventario de archivos en `README.md`. No dupliques esa información aquí.
