# Reglas de Estilo y Desarrollo — ValVic

Estas reglas son de cumplimiento obligatorio para mantener la consistencia del proyecto a través de diferentes modelos de IA y desarrolladores.

## 1. Frontend (Principios de Pureza)
- **Vanilla Only:** Usar exclusivamente HTML5, CSS3 y JavaScript nativo. NUNCA usar frameworks (React, Vue, etc.).
- **Separación de Concernimientos:** No usar estilos inline ni scripts inline (salvo excepciones técnicas debidamente comentadas).
  - Los estilos deben vivir en carpetas `css/` (ej: `panel.css`).
  - La lógica debe vivir en carpetas `js/` (ej: `agenda.js`).
- **CSP Ready:** El código debe ser compatible con políticas CSP estrictas (evitar `eval`, `inline-event-handlers`).

## 2. Diseño y Estética Premium
- **Paleta de Colores (Identidad):**
  - **Primario:** Esmeralda Premium (`#10B981`) para elementos de éxito y marca.
  - **Acento/Contraste:** Rubí (`#E11D48`) para alertas o contrastes dinámicos.
  - **Fondos:** Oscuros (`#080D1A`) para Hero/Footer, y Claros Suaves (`#F7F4EF`) para secciones de contenido.
- **Tipografía:** 
  - `Fraunces` para titulares y logotipos.
  - `DM Sans` para cuerpo de texto e interfaces de usuario.
- **Interactividad:** Siempre priorizar micro-animaciones suaves, efectos de brillo (`glow`) y transiciones elegantes (transiciones de 0.3s o 0.4s).

## 3. Backend e Infraestructura
- **MySQL HeatWave (Oracle):** Siempre optimizar los esquemas para MySQL 8.
- **FastAPI:** Uso estricto de Pydantic v2 para validaciones.
- **Seguridad:** JWT vía Cookies HttpOnly para sesiones del panel.

## 4. Convenciones de Código
- **Nombres en Inglés/Español:** Mantener la consistencia actual (Variables/Funciones en camelCase o snake_case según el lenguaje).
- **Documentación:** Todo archivo nuevo debe comenzar con un encabezado de comentario describiendo su propósito. 
