# Arquitectura de ValVic

Mapa rápido para entender la ubicación de los archivos y la lógica del sistema.

## 📂 Directorios Clave

### 1. `/Landing` (Sitio Público)
- Contiene la web de marketing, activos públicos y demos.
- `index.html`: Landing page principal reactiva.

### 2. `/Panel` (App de Clientes)
- Panel administrativo independiente.
- `/css` y `/js`: Recursos exclusivos del dashboard y lógica Vanilla JS.
- `/js/components`: Arquitectura web basada en **Web Components nativos** con Shadow DOM (`<sidebar-nav>`, `<topbar-header>`).
- `login.html`, `agenda.html`: Interfaces funcionales modulares sin HTML duplicado.

### 3. `/Agentes` (Backend IA)
- `agente_conversacion.py`: Lógica de interacción Claude/Vicky.
- `/verticals`: Configuraciones YAML de negocio (Dental, Vet, etc.).
- `subagente_db.py`: Interfaz MySQL HeatWave.

### 4. `/Database` (Persistencia)
- `/legacy_postgres`: Copia de respaldo de esquemas PostgreSQL.
- `*_mysql.sql`: Esquemas de producción para Oracle Cloud.

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
2. **Dashboard UI:** El usuario accede a `/panel/login.html` -> Consume `/api/auth/login` -> Se genera Cookie JWT (`HttpOnly`, `SameSite=Strict`) -> Carga `agenda.html` consumiendo rutas protegidas (`/api/agenda`, `/api/pacientes`) validadas vía `Depends(requiere_auth)`.
3. **Onboarding:** El cliente vincula su número vía **Meta Embedded Signup** -> ValVic recibe `PhoneID` -> El sistema gestiona múltiples instancias de Vicky.
4. **Estilo:** Carga dinámica de variables CSS en el `:root` de `panel.css`.
