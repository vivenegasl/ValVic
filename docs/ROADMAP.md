# ValVic — Roadmap de Desarrollo
> Documento vivo — última actualización: abril 2026

---

## ✅ Completado

<details>
<summary>Fases 0–4, 6: Revisión inicial, bugs web, backend, branding, SQL, entorno</summary>

- Revisión y auditoría de 30+ archivos del proyecto
- Eliminación de `onclick` inline, styles inline, corrección CSP
- Fix `subagente_db.py` (lectura MySQL con aiomysql)
- Unificación de marca "ValVic", paleta Esmeralda Premium
- Web Components (`<sidebar-nav>`, `<topbar-header>`) con Shadow DOM
- Conversión SQL PostgreSQL → MySQL HeatWave
- Entorno virtual `.venv` y dependencias instaladas
- Migración completa de 360dialog → Meta WhatsApp Cloud API (Graph v20.0)
- Autenticación JWT completa (`auth_panel.py`)
- Script de backup MySQL automatizado (`backup_mysql.py`)
- Timeout en llamadas Claude API, `asyncio.get_running_loop()`
- JSON-LD actualizado con `serviceArea`

</details>

---

## 🔴 Fase 5 — Infraestructura Oracle (BLOQUEANTE)
> *Requiere acción manual del fundador*

- [ ] Activar Oracle VM (requiere 2FA con teléfono)
- [ ] Crear usuario MySQL `valvic_app` en HeatWave
- [ ] Ejecutar schemas MySQL en HeatWave
- [ ] Correr `setup_oracle.sh` en la VM
- [ ] Configurar `.env` con credenciales reales en la VM
- [ ] Configurar SSL en `api.valvic.cl` con certbot
- [ ] Iniciar servicio `valvic-vicky` con systemd (FastAPI)

## 🟡 Fase 7 — Meta WhatsApp Cloud API (parcial)
> *Código migrado, falta configuración en portal de Meta*

- [ ] Crear App en Meta Developer Portal
- [ ] Registrar webhook `https://api.valvic.cl/webhook/whatsapp` en portal Meta
- [ ] Pruebas de envío/recepción directo con Meta
- [ ] Lanzar primer lote real: `python prospector.py --vertical dental --ciudad Santiago --cantidad 50`

---

## 🧠 Fase 11 — Sistema de Reservas Funcional (CORE PRODUCT)
> *Sin esto no hay producto vendible. Es la prioridad #1 post-infraestructura.*

### Bot de Citas (`agente_citas.py`) — **NO EXISTE AÚN**
- [ ] Crear `Agentes/agente_citas.py` — el agente que interactúa con el **paciente final** (no con el prospecto)
- [ ] Recibir mensaje del paciente → detectar intención (agendar, cancelar, reagendar, consultar)
- [ ] Extraer entidades temporales con Claude Haiku ("quiero ir mañana en la tarde", "el jueves a las 3")
- [ ] Cruzar disponibilidad real del profesional con tabla `citas` en MySQL
- [ ] Proponer horario(s) disponible(s) al paciente
- [ ] Confirmar y crear la cita en MySQL (INSERT + estado `pendiente_confirmacion`)
- [ ] Manejar cancelaciones y reagendamientos via WhatsApp
- [ ] Evitar **double-booking** (control de concurrencia: `SELECT ... FOR UPDATE` o lock optimista)

### Configuración de Horarios del Cliente
- [ ] CRUD de horarios de atención por día de la semana en el panel (`configuracion.html`)
- [ ] Tabla MySQL `horarios_atencion` (cliente_id, dia_semana, hora_inicio, hora_fin, activo)
- [ ] Endpoint `POST /api/configuracion/horarios` — guardar horarios
- [ ] Endpoint `GET /api/configuracion/horarios` — cargar horarios existentes
- [ ] Definir duración de consulta por servicio (30 min, 45 min, 1 hora)
- [ ] Bloqueo de días feriados o vacaciones

### Panel de Citas para el Cliente (Vista del Dueño)
- [ ] Conectar `agenda.html` a datos reales del endpoint `/api/agenda` (hoy son placeholders `—`)
- [ ] Mostrar **total de citas acumuladas**, **citas del mes**, **pendientes de confirmar** con datos reales
- [ ] Vista de calendario (semanal/mensual) con las citas agendadas por la IA
- [ ] Detalle de cada cita: paciente, servicio, fecha/hora, estado, canal (WhatsApp/manual)
- [ ] Acciones del dueño: confirmar, cancelar, reagendar desde el panel
- [ ] Filtros funcionales por estado (confirmada, pendiente, reagendada, cancelada)

### Recordatorios Automáticos
- [ ] CronJob que lee tabla `citas` diariamente
- [ ] Enviar recordatorio WhatsApp al paciente 24h antes de la cita
- [ ] Permitir al paciente confirmar o cancelar respondiendo al recordatorio
- [ ] Registrar no-shows (cita sin confirmar + hora pasada)

---

## 🔐 Fase 12 — Autenticación y Acceso del Cliente
> *El login actual es JWT con bcrypt en auth_panel.py — funciona, pero evaluar mejoras*

### Login actual (funcional)
- [ ] Verificar que el flujo login.html → `/api/auth/login` → JWT cookie funcione end-to-end en producción
- [ ] Implementar "Olvidé mi contraseña" (enviar link de reset por email o WhatsApp)
- [ ] Pantalla de registro: ¿el cliente se registra solo o lo registra ValVic manualmente?

### Mejora opcional: Login social (evaluar necesidad)
- [ ] ¿Ofrecer "Iniciar sesión con Google"? → Solo si simplifica el onboarding para clientes que no quieren otra contraseña
- [ ] Si se implementa: usar OAuth 2.0 directo (sin Firebase/Auth0 — regla de oro: sin plataformas externas)
- [ ] Mapear cuenta Google → `cliente_id` existente en MySQL

> **Nota:** El login JWT actual es suficiente para el MVP. Login social es un nice-to-have que puede esperar al post-lanzamiento.

---

## 📊 Fase 13 — Dashboard y Métricas del Cliente
> *El dueño del negocio necesita ver que la IA le genera valor*

- [ ] **Resumen del mes**: total citas, citas por IA vs manuales, tasa de confirmación, no-shows
- [ ] **Gráfico de tendencia**: citas por semana/mes (últimos 3 meses) — Canvas + JS puro
- [ ] **Horarios más demandados**: ¿Lunes 10am es el más pedido? Mostrar heatmap simple
- [ ] **Pacientes nuevos vs recurrentes**: cuántos pacientes distintos agendaron este mes
- [ ] **Tasa de conversión del bot**: mensajes recibidos vs citas efectivamente agendadas
- [ ] **Exportar datos**: botón para descargar CSV de citas del mes

---

## 💬 Fase 14 — Experiencia del Paciente
> *El paciente final también debe tener una buena experiencia fuera de WhatsApp*

- [ ] Página de confirmación de cita: `valvic.cl/cita/{TOKEN}` — el paciente ve su cita y puede confirmar/cancelar desde la web
- [ ] Email de confirmación (opcional, si el paciente dio su correo)
- [ ] Link de reagendamiento en el recordatorio de 24h
- [ ] Formulario de datos pre-cita (nombre, motivo, alergias — según vertical)

---

## 🟢 Fase 8 — Marketing & SEO

- [ ] Crear páginas de aterrizaje SEO por vertical (`/clinica-dental`, `/veterinaria`, `/spa`)
- [ ] Hero actualizado: "Tu clínica pierde citas cada semana. Las recuperamos automáticamente."
- [ ] Precios visibles en la web (alineados con `VENTAS.md`)
- [ ] Sección de verticales con grid visual
- [ ] FAQ section

## 🔵 Fase 9 — Post-Lanzamiento & Escalado

- [ ] Motor de reportes completo (MySQL HeatWave)
- [ ] Migrar lógica de `generador.py` (antiguo Sheets) a MySQL
- [ ] Integraciones Google My Business y API de Google Reviews
- [ ] Sistema de cobro (Flow/Khipu) integrado en flujo de Vicky
- [ ] Agente de seguimiento (2do mensaje autónomo a los 3 días)
- [ ] Sincronización bidireccional con Google Calendar (servicio Premium)

## 🟣 Fase 10 — Onboarding Automatizado (Scalability)

- [ ] Implementar flujo de **Meta Embedded Signup** en el Panel
- [ ] Backend para gestión de múltiples `PhoneID` por cliente
- [ ] Dashboard de consumo de mensajes (cuota gratuita Meta)
- [ ] Wizard de onboarding: el cliente configura horarios, servicios y nombre del agente en 5 pasos

---

## Orden de Prioridad para Producto Funcional

```
Fase 5 (Oracle) ──► Fase 7 (Meta) ──► Fase 11 (Reservas) ──► Fase 12 (Auth)
                                              │
                                              ├──► Fase 13 (Dashboard)
                                              └──► Fase 14 (Paciente)
                                                        │
                                              Fase 8 (SEO) ──► Fase 9 (Escalado) ──► Fase 10 (Multi-tenant)
```

> 💡 **Fase 11 es el corazón del producto.** Sin un sistema de reservas que funcione de punta a punta (paciente escribe → IA agenda → dueño lo ve en su panel), no hay nada que vender.
