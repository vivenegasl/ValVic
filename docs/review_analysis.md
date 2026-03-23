# ValVic — Revisión Completa de Archivos y Plan de Acción

> Revisé **30+ archivos** en 4 directorios. A continuación: hallazgos por componente, problemas detectados, y un plan de acción priorizado para lograr los requerimientos del PROYECTO.md.

---

## 📊 Resumen del Estado Actual

| Componente | Archivos | Estado |
|---|---|---|
| **Agentes** (prospección/ventas) | 3 Python | ✅ Construidos, funcionales |
| **Estructuras** (legado + schemas) | 6 Python + 2 SQL | ⚠️ Legado sin migrar, SQL en PostgreSQL |
| **ValVic Web** (landing) | HTML + 4 CSS + 10 JS + 3 demos | ✅ Producción, buen SEO |
| **Logos** | 9 imágenes | ✅ Todos los formatos cubiertos |

---

## 🟢 Agentes — Lo que está bien y lo que falta

### [agente_conversacion.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/agente_conversacion.py) (876 líneas)
**Bien hecho:**
- Debounce adaptativo bien implementado (5s → 10s burst)
- Pipeline claro: clasificar → generar → detectar cierre → actualizar estado
- Prompt caching en system prompt (ahorra tokens)
- Modo simulación con CLI completo
- Escalado a humano con 3 objeciones

**Problemas encontrados:**

| # | Problema | Severidad | Línea |
|---|---|---|---|
| 1 | `onclick="toggleMobile()"` en el nav del HTML viola CSP (será problema de la web, no del agente) — pero aquí el clasificador hardcodea "veterinaria" en el prompt (L286) | 🔴 Alta | 286 |
| 2 | `prompts_ventas.py` referenciado pero **no existe** en la carpeta Agentes | 🔴 Alta | 35-42 |
| 3 | Usa `asyncio.get_event_loop()` deprecado en Python 3.12+ | 🟡 Media | 109 |
| 4 | `background.add_task(lambda ...)` en webhook — si el lambda captura la variable incorrectamente puede causar bugs de closure | 🟡 Media | 705-707 |
| 5 | No hay timeout en las llamadas a Claude API (clasificar/detectar cierre) | 🟡 Media | 301-308 |
| 6 | SQL injection potencial en [actualizar_conv()](file:///c:/Users/vlind/Desktop/Valvic/Agentes/agente_conversacion.py#243-252) — construye query con f-string | 🟡 Media | 250 |
| 7 | Hardcoded `prospectos_vet.db` como nombre (no sigue convención multi-vertical) | 🟠 Baja | 65 |

### [subagente_db.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py) (540 líneas)
**Bien hecho:**
- Modelos Pydantic v2 completos ([ProspectoNuevo](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py#58-71), [ProspectoCalificado](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py#73-81), [ResultadoDB](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py#83-89))
- Backend auto-switch SQLite/MySQL según variables de entorno
- Deduplicación por `place_id`
- Método [resumen()](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py#453-467) con barra visual útil para debugging

**Problemas encontrados:**

| # | Problema | Severidad | Línea |
|---|---|---|---|
| 1 | Los métodos de lectura ([obtener_por_estado](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py#422-425), [obtener_no_contactados](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py#426-436), etc.) **siempre usan SQLite**, incluso cuando `USAR_MYSQL=True` | 🔴 Alta | 422-445 |
| 2 | Monkey-patch de métodos multi-vertical al final del archivo — antipatrón, debería ser métodos de clase | 🟡 Media | 536-539 |
| 3 | No hay columna [vertical](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py#520-534) en el `CREATE TABLE` del SQLite pero los queries multi-vertical la filtran | 🟡 Media | 99-120 vs 477 |
| 4 | `asyncio.run()` dentro de métodos sync puede causar error si se llama desde un contexto async existente | 🟡 Media | 359-360 |

### [actualizar_openers.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/actualizar_openers.py) (140 líneas)
**Bien hecho:**
- Semáforo para limitar paralelismo con Sonnet
- Preview mode (`--preview`) sin escribir en DB
- Manejo de errores en cada llamada a Claude

**Problemas encontrados:**

| # | Problema | Severidad | Línea |
|---|---|---|---|
| 1 | Importa `PROMPT_OPENER_VETERINARIAS` de `prompts_ventas.py` — archivo que **no existe** en el repo | 🔴 Alta | 27 |
| 2 | Hardcoded a veterinarias, no es multi-vertical todavía | 🟡 Media | 45 |

---

## 🟡 Estructuras (Legado) — Estado y Plan de Migración

### Archivos legacy y su destino

| Archivo | Estado actual | Acción necesaria |
|---|---|---|
| [config.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/config.py) | ⚠️ API key hardcodeada como string | Eliminar — usar `.env` exclusivamente |
| [clientes.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/clientes.py) | Config de clientes en dict | Migrar a MySQL tabla `clientes` |
| [generador.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/generador.py) | Funcional con Sheets | Migrar a MySQL |
| [sheets.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/sheets.py) | Funcional con gspread | Reemplazar por MySQL |
| [notificaciones.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/notificaciones.py) | CallMeBot + Gmail SMTP | Migrar a 360dialog + OCI Email |
| [main.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/main.py) | Orquestador | Migrar a cron job |

**⚠️ Problema crítico en [config.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/config.py):** API key de Anthropic está como string placeholder `"TU_ANTHROPIC_API_KEY"` — esto viola la regla de "nunca hardcodear credenciales". Si alguien pone la key real ahí y lo commitea, se compromete.

### SQL Schemas

| Archivo | Problema | Acción |
|---|---|---|
| [valvic_schema_principal.sql](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/valvic_schema_principal.sql) (593 líneas) | 🔴 **100% PostgreSQL** — `gen_random_uuid()`, `timestamptz`, `GENERATED ALWAYS AS IDENTITY`, RLS, `pg_trgm`, PL/pgSQL triggers | Convertir completo a MySQL |
| [valvic_schema_reportes.sql](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/valvic_schema_reportes.sql) (681 líneas) | 🔴 **100% PostgreSQL** — mismas incompatibilidades + DROP CASCADE, FILTER clause, ON CONFLICT | Convertir completo a MySQL |

**Detalle de incompatibilidades PostgreSQL → MySQL:**

```diff
- gen_random_uuid()              → UUID() o generación desde Python
- GENERATED ALWAYS AS IDENTITY   → AUTO_INCREMENT
- timestamptz                    → DATETIME
- ON CONFLICT DO UPDATE          → ON DUPLICATE KEY UPDATE
- CREATE EXTENSION               → No aplica
- PL/pgSQL triggers              → Reescribir en MySQL DELIMITER syntax
- FILTER (WHERE ...)             → CASE WHEN ... THEN 1 END con SUM
- Row Level Security             → No existe en MySQL — implementar en aplicación
- Partial indexes (WHERE)        → No soportados — usar índices normales
- regex operator (~)             → REGEXP
- ILIKE                          → LOWER() LIKE LOWER()
```

---

## 🔵 ValVic Web — Análisis Detallado

### [index.html](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/index.html) (406 líneas)
**Muy bien:**
- SEO técnico completo (title, meta description, canonical, OG, Twitter Cards)
- JSON-LD de Organization y Services
- CSP en meta tag
- Preconnect y dns-prefetch para Google Fonts
- Estructura semántica con `aria-label`

**Problemas encontrados:**

| # | Problema | Severidad |
|---|---|---|
| 1 | `onclick="toggleMobile()"` inline en L80 — viola la regla CSP de "nunca inline" | 🔴 Alta |
| 2 | `onclick="closeMobile()"` inline en L83-86 — misma violación | 🔴 Alta |
| 3 | El `style="border-radius:6px;"` inline en L70 y L366 — viola CSP para styles | 🟡 Media |
| 4 | Footer dice `© 2025` pero estamos en 2026 | 🟡 Media |
| 5 | Formulario no tiene los 8 verticales del YAML — faltan veterinarias, psicólogos, estética, inmobiliarias, mueblerías | 🟡 Media |
| 6 | Precios en la web ($135 Esencial, $350 Completo) **no coinciden** con los del PROYECTO.md ($80-135/mes) | 🔴 Alta |
| 7 | No existe sección de rubros/verticales como pide el PROYECTO.md | 🔴 Alta |
| 8 | Hero genérico — no enfocado en el problema vendible como pide PROYECTO.md | 🟡 Media |
| 9 | No hay FAQ como pide el PROYECTO.md | 🟡 Media |
| 10 | CSP en [.htaccess](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/.htaccess) tiene `'unsafe-inline'` para scripts Y styles, contradice la regla del proyecto | 🔴 Alta |

### [styles.css](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/css/styles.css) (310 líneas)
- **Muy bien**: CSS variables bien organizadas, responsive, dark/light alternado, animaciones suaves
- **Problema**: Está minificado en una sola línea — dificulta mantenimiento

### JavaScript (10 archivos)
- [config.js](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/config.js) ✅ — constantes limpias
- [utils.js](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/utils.js) ✅ — funciones puras bien documentadas con sanitización XSS
- [nav.js](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/nav.js) ✅ — IIFE, clean
- [form.js](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/form.js) ✅ — rate limiting, sanitización, error handling
- [animations.js](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/animations.js) ✅ — IntersectionObserver, contadores
- [neural.js](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/neural.js) ✅ — canvas con partículas interactivas, bien optimizado
- [mockup.js](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/mockup.js) ✅ — chat animado con rotación de conversaciones
- Demo JS (3 archivos): ~72KB total — simulan la funcionalidad de cada servicio

### [tests/index.html](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/tests/index.html) — 27 tests
- Mini test runner propio (describe/it/expect)
- Cubre: [sanitize()](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/utils.js#6-16), [validarForm()](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/utils.js#17-37), [checkRateLimit()](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/utils.js#38-52), [buildPayload()](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/utils.js#53-69)
- ✅ Todos los edge cases cubiertos: XSS, validación, rate limiting

### [.htaccess](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/.htaccess) — Bueno pero contradictorio
- ✅ HTTPS forzado, www → sin www, cache, gzip, server signature off
- 🔴 CSP incluye `'unsafe-inline'` para scripts y styles — contradice PROYECTO.md que dice "nunca unsafe-inline para scripts"

---

## 🔴 Archivos Faltantes (referenciados pero no existen)

| Archivo | Referenciado en | Prioridad |
|---|---|---|
| `prompts_ventas.py` | [agente_conversacion.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/agente_conversacion.py), [actualizar_openers.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/actualizar_openers.py) | 🔴 **Crítico** — sin este archivo los agentes no funcionan |
| `prospector.py` | PROYECTO.md | 🔴 **Crítico** — el prospector multi-vertical |
| `verticals/*.yaml` (8 archivos) | PROYECTO.md | 🔴 **Crítico** — configuración por rubro |
| `schema_prospeccion_mysql.sql` | PROYECTO.md | 🟡 **Necesario** — schema MySQL listo |
| `requirements.txt` | PROYECTO.md | 🟡 **Necesario** |
| `.env.example` | PROYECTO.md | 🟡 **Necesario** |
| `setup_oracle.sh` | PROYECTO.md | 🟡 **Necesario** |
| `INSTALACION.md` | PROYECTO.md | 🟠 **Deseable** |
| 3 SKILLs .md | PROYECTO.md | 🟠 **Deseable** |

> **Estos archivos están listados como "construidos" en PROYECTO.md pero no están en la carpeta del proyecto.** Es probable que estén en otro lugar o en otro repositorio. Necesito confirmación del usuario.

---

## 🎯 Plan de Acción Priorizado

### Fase 0 — Archivos Faltantes (BLOQUEANTE)
1. ☐ **Localizar o regenerar `prompts_ventas.py`** — sin este archivo, ningún agente funciona
2. ☐ **Localizar `prospector.py`** y los 8 YAMLs de verticales
3. ☐ **Localizar `schema_prospeccion_mysql.sql`**, `requirements.txt`, `.env.example`

### Fase 1 — Bugs Críticos (antes de cualquier cosa)
4. ☐ Eliminar `onclick` inline del HTML → mover a event delegation en [nav.js](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/js/nav.js)
5. ☐ Eliminar styles inline del HTML → mover a [styles.css](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/css/styles.css)
6. ☐ Corregir CSP en [.htaccess](file:///c:/Users/vlind/Desktop/Valvic/ValVic%20Web/.htaccess) — quitar `'unsafe-inline'` para scripts
7. ☐ Arreglar [subagente_db.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py) — los métodos de lectura deben usar MySQL cuando corresponde
8. ☐ Arreglar [agente_conversacion.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/agente_conversacion.py) L286 — clasificador hardcodeado a "veterinaria", debe ser dinámico por vertical
9. ☐ Eliminar [config.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/config.py) de Estructuras (credenciales hardcodeadas)

### Fase 2 — Actualización de la Web (coherencia con PROYECTO.md)
10. ☐ **Hero section**: Cambiar texto genérico → enfoque en citas perdidas
11. ☐ **Sección de rubros**: Agregar grid con los 8 verticales activos
12. ☐ **Precios**: Alinear con los precios del PROYECTO.md ($80/mes citas, $50/mes web, $120/mes bundle)
13. ☐ **Formulario**: Agregar los 8 verticales al dropdown
14. ☐ **FAQ**: Agregar las 4 preguntas frecuentes definidas
15. ☐ **Footer**: Actualizar © 2025 → 2026
16. ☐ **Meta description**: Actualizar con el texto nuevo del PROYECTO.md

### Fase 3 — Conversión SQL (cuando Oracle esté activo)
17. ☐ Convertir [valvic_schema_principal.sql](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/valvic_schema_principal.sql) de PostgreSQL a MySQL
18. ☐ Convertir [valvic_schema_reportes.sql](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/valvic_schema_reportes.sql) de PostgreSQL a MySQL
19. ☐ Eliminar RLS y reemplazar con lógica de aplicación
20. ☐ Reescribir triggers en sintaxis MySQL

### Fase 4 — Migración del Legado
21. ☐ Migrar [generador.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/generador.py) de Sheets a MySQL
22. ☐ Migrar [notificaciones.py](file:///c:/Users/vlind/Desktop/Valvic/Estructuras/notificaciones.py) de CallMeBot a 360dialog
23. ☐ Mover archivos legacy a carpeta `legacy/` con README explicativo

### Fase 5 — Mejoras técnicas
24. ☐ Agregar timeout a llamadas Claude API en [agente_conversacion.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/agente_conversacion.py)
25. ☐ Refactorizar monkey-patch en [subagente_db.py](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py) a métodos de clase
26. ☐ Agregar columna [vertical](file:///c:/Users/vlind/Desktop/Valvic/Agentes/subagente_db.py#520-534) al CREATE TABLE de SQLite
27. ☐ Agregar manejo de `asyncio.get_running_loop()` en vez de `get_event_loop()`
