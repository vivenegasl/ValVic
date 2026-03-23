# Arquitectura de ValVic

Mapa rápido para entender la ubicación de los archivos y la lógica del sistema.

## 📂 Directorios Clave

### 1. `/ValVic Web` (Frontend Hostinger)
- `/css`: Estilos globales y específicos (`styles.css`, `panel.css`).
- `/js`: Lógica de navegación, animaciones y formularios (`nav.js`, `animations.js`, `neural.js`).
- `/panel`: Secciones privadas del cliente (`agenda.html`, `pacientes.html`, `configuracion.html`).
- `/demos`: Páginas interactivas de demostración de servicios IA.
- `index.html`: Landing page principal reactiva.

### 2. `/Agentes` (Backend Python/FastAPI)
- `agente_conversacion.py`: Lógica principal de interacción con Claude.
- `auth_panel.py`: Manejo de sesiones y seguridad JWT.
- `subagente_db.py`: Interfaz de comunicación con MySQL.

### 3. `/sql` & `/Estructuras`
- Contiene los esquemas de bases de datos tanto para MySQL como legacy (PostgreSQL).

### 4. `/.agent/brain/` (Memoria Compartida)
- Lugar donde reside el contexto para IAs (este directorio).

## 🏢 Infraestructura de ValVic
- **Hostinger Business:** Alojamiento del Frontend estático (HTML/JS/CSS).
- **Oracle Cloud (Free Tier):** Instancia VM Ampere (4 CPU, 24GB RAM) alojando la base de datos MySQL HeatWave y la API FastAPI.
- **Automatización:** Crontab de Linux ejecutando scripts de Python nativo (Sin n8n/Make).

## 🔌 APIs Externas Autorizadas
- **Claude (Anthropic):** Modelos `sonnet` para lógica compleja y `haiku` para clasificación masiva.
- **Google Places API v1:** Búsqueda avanzada de prospectos (vía `searchText` con FieldMasks).
- **360dialog:** Canal oficial BSP para la API de WhatsApp Business.

## 🔗 Flujos Técnicos
1. **Petición Cliente:** Entra por `360dialog`/`Meta API` -> Procesa en `FastAPI` (Oracle) -> Responde vía `Claude`.
2. **Dashboard UI:** El usuario accede a `/panel/login.html` -> Valida credenciales -> Carga `agenda.html`.
3. **Onboarding:** El cliente vincula su número vía **Meta Embedded Signup** -> ValVic recibe `PhoneID` -> El sistema gestiona múltiples instancias de Vicky.
4. **Estilo:** Carga dinámica de variables CSS en el `:root` de `panel.css`.
