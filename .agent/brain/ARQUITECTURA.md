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

## 🔌 Flujos Técnicos
1. **Petición Cliente:** Entra por `360dialog` -> Procesa en `FastAPI` (Oracle) -> Responde vía `Claude`.
2. **Dashboard UI:** El usuario accede a `/panel/login.html` -> Valida credenciales -> Carga `agenda.html` inyectando datos corporativos desde MySQL.
3. **Estilo:** Carga dinámica de variables CSS en el `:root` de `panel.css` permite cambios de tema instantáneos (ej: de Azul a Esmeralda).
