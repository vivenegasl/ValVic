# Estado Actual del Proyecto — ValVic (Marzo 2026)

Este documento registra los hitos más recientes y las tareas pendientes para que el próximo agente o desarrollador sepa exactamente dónde continuar.

## Estructura del Proyecto
- `/Landing`: Sitio web de marketing y demos.
- `/Panel`: Aplicativo de clientes (Agenda, Pacientes).
- `/Agentes`: Backend FastAPI y agentes de IA.
  - `/verticals`: Configuraciones YAML de negocio.
- `/Database`: Esquemas SQL (MySQL y legacy Postgres).
- `/docs`: Documentación estratégica y Roadmap.
- `/legacy`: Cementerio de scripts antiguos y backups.
- `/.agent/brain`: Memoria compartida del proyecto.

## 🚀 Logros Recientes (Sesión Actual)
- **Unificación de Marca:** Se cambió globalmente de "Val Vic" a "**ValVic**".
- **Estructura Modular:** Separación de `Landing/` y `Panel/` en la raíz.
- **Consolidación Técnica:** Unificación de esquemas en `/Database` e integración de verticales en `/Agentes`.
- **Identidad Visual:** Transición completa a la temática **Esmeralda Premium**.
- **Luz de seguimiento (`cursor-glow`) reactiva:** Esmeralda en oscuros, Rubí en claros.
- **Estrategia de Onboarding:** Definición del modelo "Embedded Signup" para escalabilidad de clientes finales.
- **Seguridad y Estructura:** Refactorización del Panel para separar CSS y JS externos.
- **Base de Datos:** Conversión exitosa de esquemas PostgreSQL a **MySQL HeatWave**.
- **🆕 Migración Meta WhatsApp Cloud API:** Implementación completa del webhook para Meta directo en `agente_conversacion.py`:
  - `GET /webhook/whatsapp`: verificación de token con `META_VERIFY_TOKEN`.
  - `POST /webhook/whatsapp`: validación HMAC-SHA256 con `META_APP_SECRET`, parseo con Pydantic v2 (`MetaWebhookPayload`).
  - `_enviar_whatsapp()`: migrado de 360dialog a `graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages`.
  - `_enviar_template_whatsapp()`: nueva función para mensajes de tipo `template` (HSM/message openers).
  - Variables agregadas a `.env.example`: `META_ACCESS_TOKEN`, `META_VERIFY_TOKEN`, `META_APP_SECRET`, `META_PHONE_NUMBER_ID`.

- **🆕 Autenticación JWT Completa:** Implementada seguridad Oauth-like en `auth_panel.py` y `agente_conversacion.py`.
  - `POST /api/auth/login` con bcrypt hashing.
  - Cookies con atributos estatus `HttpOnly`, `SameSite=Strict` y `Secure` condicionado (HTTPS).
  - Dependency de FastAPI `requiere_auth` implementado para verificación transparente de claims.
  - `/api/agenda` y `/api/pacientes` operando bajo multi-tenancy usando el `cliente_id` del JWT. 

- **🆕 UI Modificada con Web Components:** El sidebar y el topbar del Panel Citas han sido refactorizados y transformados a Customs Elements nativos (`<sidebar-nav>` y `<topbar-header>`) dotados de Shadow DOM.
  - Cero código de etiquetas HTML y SVG Phosphor duplicadas por página.
  - Sincronización transparente con `checkSession()` y location API de Javascript.

## 🛠️ Tareas Pendientes e Ideas
- [ ] **Optimización SEO:** Revisar meta-tags y descripciones para todas las páginas de `demos/`.
- [ ] **Pruebas de Carga:** Realizar una auditoría de rendimiento en los scripts de `neural.js` para asegurar 60fps en móviles.
- [ ] **Configurar Webhook en Meta Portal:** Registrar la URL `https://<oracle-vm-ip>:8001/webhook/whatsapp` en developers.facebook.com y completar verificación con `META_VERIFY_TOKEN`.
- [ ] **Deprecar 360dialog:** Una vez que el webhook de Meta esté validado en producción, eliminar `DIALOG360_API_KEY` y `DIALOG360_PHONE_ID` del código y `.env`.
- [ ] **notificar_fundador():** Actualizar para enviar alertas al fundador vía Meta Graph API (actualmente solo loggea).

## ⚠️ Bloqueos / Avisos
- El usuario prefiere no usar frameworks bajo ninguna circunstancia.
- La visibilidad del cursor-glow en pantallas blancas es crítica; mantener la opacidad alta si se vuelve a ajustar.
- `META_APP_SECRET` es **obligatorio en producción** para la validación de firma. En desarrollo, si la variable no está configurada, el webhook es permisivo (solo loggea un warning).
