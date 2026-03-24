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

## 🛠️ Tareas Pendientes e Ideas
- [ ] **Optimización SEO:** Revisar meta-tags y descripciones para todas las páginas de `demos/`.
- [ ] **Autenticación Panel:** Implementar la lógica de JWT en `Agentes/auth_panel.py` conectando con el login.
- [ ] **Web Components:** Evaluar convertir el sidebar y topbar del panel en Web Components nativos para evitar duplicidad de HTML.
- [ ] **Pruebas de Carga:** Realizar una auditoría de rendimiento en los scripts de `neural.js` para asegurar 60fps en móviles.

## ⚠️ Bloqueos / Avisos
- El usuario prefiere no usar frameworks bajo ninguna circunstancia.
- La visibilidad del cursor-glow en pantallas blancas es crítica; mantener la opacidad alta si se vuelve a ajustar.
