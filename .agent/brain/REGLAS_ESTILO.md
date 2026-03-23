# Reglas de Estilo y Desarrollo — ValVic

Estas reglas son de cumplimiento obligatorio para mantener la consistencia del proyecto a través de diferentes modelos de IA y desarrolladores.

## 0. Estándares Senior (Mandatorio)
- **Calidad de Ingeniería:** El código debe ser modular, escalable y seguir principios **DRY** (Don't Repeat Yourself).
- **Incompatibilidad de Frameworks:** NUNCA proponer React, Vue, LangChain o n8n. ValVic es 100% Vanilla y Python nativo.
- **Solución Modular Proactiva (REGLA DE ORO):** Si una restricción (como usar Vanilla HTML/JS) induce a repetir código (ej. menús laterales), el agente DEBE proponer proactivamente soluciones modulares compatibles (ej. inyección por Web Components o JS Fetch) para mantener el estándar.
- **Regla de Memoria Viva (MANDATORIA):** Tras cada hito, aprendizaje técnico o cambio estratégico, el agente DEBE actualizar proactivamente `ESTADO_ACTUAL.md` y `ARQUITECTURA.md` en el Master Brain (`.agent/brain/`). No esperes a que el usuario lo pida.
- **Manejo de Errores:** Logging estricto y bloques `try/except` en toda interacción con APIs externas (360dialog, Claude, etc.).

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

## 5. Requisitos de Datos y Seguridad
- **PKs UUID:** Siempre usar UUID string para IDs expuestos en base de datos.
- **Pydantic v2:** Uso obligatorio para de-serialización y validación de esquemas en Python.
- **Cookies Seguras:** Autenticación vía JWT usando cookies `HttpOnly` y `Secure`.

## 6. Proceso de Desarrollo (Metamodelo SPARC)
Antes de programar cualquier nueva funcionalidad o agente, se debe seguir este flujo:
1. **Especificación:** Definir límites de autonomía y breaks de emergencia.
2. **Tools:** Definir lista exacta de funciones de acceso.
3. **Schemas:** Definir entradas/salidas estrictas vía Pydantic.
4. **Error Handling:** Definir política de reintentos (backoff exponencial).
5. **Testing:** Simulación CLI antes de despliegue en producción.
