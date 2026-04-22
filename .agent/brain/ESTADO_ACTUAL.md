# Estado Actual del Proyecto — ValVic (24 Marzo 2026)

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
- **🆕 Migración completa de 360dialog a Meta Cloud API (Fase Final):**
  - `agente_conversacion.py`: Webhook GET/POST, HMAC-SHA256, `_enviar_whatsapp()`, `_enviar_template_whatsapp()` → todo Meta Graph API v20.0.
  - `prospector.py`: Función `procesar_envio()` migrada de `waba.360dialog.io` a `graph.facebook.com/v20.0`. Usa `META_TEMPLATE_NAME`.
  - `notificar_fundador()`: Convertida a `async`, ahora envía alertas WhatsApp al fundador vía Meta (cierre, escalado, reunión).
  - `.env.example`: Limpiado de todas las variables 360dialog. Agregada `META_TEMPLATE_NAME`.
  - `configuracion.html`: UI actualizada de "360dialog" a "Meta WhatsApp Cloud API".
  - `PROYECTO.md`: Tabla de decisiones y APIs actualizadas.
  - Depuración total: 0 referencias a 360dialog en código activo.

- **🆕 Autenticación JWT Completa:** Implementada seguridad Oauth-like en `auth_panel.py` y `agente_conversacion.py`.
  - `POST /api/auth/login` con bcrypt hashing.
  - Cookies con atributos estatus `HttpOnly`, `SameSite=Strict` y `Secure` condicionado (HTTPS).
  - Dependency de FastAPI `requiere_auth` implementado para verificación transparente de claims.
  - `/api/agenda` y `/api/pacientes` operando bajo multi-tenancy usando el `cliente_id` del JWT. 

- **🆕 UI Modificada con Web Components:** El sidebar y el topbar del Panel Citas han sido refactorizados y transformados a Customs Elements nativos (`<sidebar-nav>` y `<topbar-header>`) dotados de Shadow DOM.
  - Cero código de etiquetas HTML y SVG Phosphor duplicadas por página.
  - Sincronización transparente con `checkSession()` y location API de Javascript.

- **🆕 Auditoría `setup_oracle.sh` corregida:**
  - ExecStart systemd: `Agentes.agente_conversacion:app` (antes apuntaba a raíz).
  - Cron jobs: Rutas corregidas a `Agentes/prospector.py`, `Agentes/actualizar_openers.py`, `Agentes/backup_mysql.py`.
  - Certbot: Agregado `agenda.valvic.cl` al comando SSL.
  - Nota explícita de que `Landing/` se aloja en Hostinger, no en la VM.

## 🛠️ Tareas Pendientes e Ideas
- [ ] **Optimización SEO:** Revisar meta-tags y descripciones para todas las páginas de `demos/`.
- [ ] **Pruebas de Carga:** Auditoría de rendimiento en `neural.js` para 60fps en móviles.
- [ ] **Configurar Webhook en Meta Portal:** Registrar `https://api.valvic.cl/webhook/whatsapp` en developers.facebook.com.
- [ ] **Activar Oracle VM:** Requiere 2FA presencial del fundador.
- [ ] **Crear App en Meta Developer Portal:** Requiere acceso humano.
- [ ] **Ejecutar schemas MySQL en HeatWave:** Post-VM.

## ⚠️ Bloqueos / Avisos
- El usuario prefiere no usar frameworks bajo ninguna circunstancia.
- La visibilidad del cursor-glow en pantallas blancas es crítica; mantener la opacidad alta si se vuelve a ajustar.
- `META_APP_SECRET` es **obligatorio en producción** para la validación de firma. En desarrollo, si la variable no está configurada, el webhook es permisivo (solo loggea un warning).
