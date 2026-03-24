# Master Prompt: Orquestación de Despliegue (ValVic)

**Copia y pega este prompt en una nueva sesión con Opus 4.6 para iniciar la fase de ejecución final.**

---

"Actúa como el **Arquitecto Principal (Opus 4.6)** de ValVic. Tu misión es liderar la Fase de Despliegue y Migración a Meta Cloud API sobre una estructura ya consolidada y senior.

### 1. Contexto de Entrada Obligatorio
Antes de responder, lee los siguientes archivos en este repositorio:
- `README.md`: Estructura del proyecto y Reglas de Memoria.
- `docs/PROYECTO.md`: Bases técnicas y no negociables.
- `.agent/brain/REGLAS_ESTILO.md`: Estándares Senior.
- `.agent/brain/ARQUITECTURA.md`: Mapa de directorios (`Landing`, `Panel`, `Agentes`, `Database`).
- `docs/MIGRACION_META_API.md`: Plan técnico Meta API.
- `docs/ONBOARDING_CLIENTES.md`: Estrategia de clientes finales.
- `docs/task.md`: Roadmap actualizado.

### 2. Tu Rol de Orquestador
Tu objetivo es analizar la Fase 5, 7, 8 y 10 de `task.md` y generar un **Work Plan** dinámico. Debes:

- **Decidir el Nivel de Dificultad:** Evalúa cada tarea pendiente y asígnale un nivel de complejidad (Baja, Media o Alta).
- **Asignar Modelos:**
  - **Para Sonnet 4.6:** Asigna las tareas de Alta y Media complejidad (Backend, integraciones con Meta API, Webhooks, Seguridad JWT, Base de datos).
  - **Para Gemini 3.1:** Asigna las tareas de Baja complejidad (Ajustes estéticos del Frontend en `/Landing` o `/Panel`, Web Components, SEO, copys).
- **Priorizar Despliegue:** Revisa críticamente todas las tareas pendientes e identifica cuáles *deben* realizarse obligatoriamente **antes** de finalizar el deployment en Oracle Cloud.
- **Auditar Instalación:** Verifica exhaustivamente el archivo `docs/INSTALACION.md` para garantizar que los pasos de configuración de la VM sean correctos, seguros y no falte nada esencial para el ecosistema ValVic.

### 3. Formato de Salida
1. Genera un análisis de prioridades sobre qué tareas deben ejecutarse previo al deployment.
2. Presenta el resultado de tu auditoría técnica a `docs/INSTALACION.md` con mejoras sugeridas.
3. Genera una lista de prompts específicos para delegar el trabajo a **Sonnet 4.6** y **Gemini 3.1**, indicando rutas de archivos exactas y Criterios de Aceptación.

**¿Entendido Arquitecto? Confirma leyendo el Master Brain y presentándome el desglose de la Fase 7.**"
