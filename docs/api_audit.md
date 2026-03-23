# Auditoría de Conexiones API y Optimización de Tokens

He revisado a fondo el código de los agentes (`prospector.py`, `agente_conversacion.py`, `subagente_db.py` y `prompts_ventas.py`). Aquí tienes el reporte detallado respondiendo a tus dudas:

## 1. Conexión con Google Places API y Reseñas
**Estado: Perfectamente implementado ✅**
- En `prospector.py` (líneas 117-156), el agente hace peticiones HTTP directas a la API de Places `textsearch/json`.
- **Reseñas extraídas:** Captura correctamente el `rating` (estrellas) de la llave `"rating"` y el número total de reseñas de `"user_ratings_total"` guardándolo como `resenas`.
- **Uso inteligente del dato:** Luego, en el prompt que se envía a la IA calificadora (`_calificar_uno`), le inyecta literalmente el texto: `- Google: {rating} estrellas con {resenas} resenas`. Y le da la instrucción explícita a Haiku: *"8-10 puntos: Alto volumen ({resenas} sugiere demanda real)"*. 
- **Veredicto:** La ingesta de datos de Google Places y el uso del "social proof" (reseñas) para calificar la calidad del prospecto está excelente.

## 2. Conexiones con Anthropic (Claude)
**Estado: Conexiones nativas y correctas ✅**
- Estás usando la librería oficial `anthropic` en su versión más actual.
- Haces uso brillante del cliente asíncrono (`AsyncAnthropic`) en `prospector.py` para paralelizar la calificación de múltiples negocios a la vez usando un semáforo de 8 hilos (`asyncio.Semaphore(MAX_PARALELO)`).
- En `agente_conversacion.py` usas el cliente síncrono estándar, lo cual está bien para la etapa inicial donde el webhook los procesa con BackgroundTasks.

## 3. Optimización de Tokens (Maximizando Descuentos)
**Estado: Muy bueno, pero con una oportunidad de mejora crítica ⚠️**

**Lo que estás haciendo perfecto:**
- **Prompt Caching en Conversación:** En `agente_conversacion.py` (Línea 484), estás usando `"cache_control": {"type": "ephemeral"}` en el `system prompt`. Esto es una maravilla. Como el historial de chat de ventas crece en cada turno y las directrices (escalera de concesiones, precios) son largas, procesarlas te está saliendo un **90% más barato** a partir del segundo mensaje enviado por el cliente en menos de 5 minutos.
- **Routing de Modelos:** Usas `claude-haiku-4-5` para las tareas de volumen (calificar prospectos, detectar cierre, detectar intención) y solo mandas llamar al caro `claude-sonnet` para la generación de la respuesta persuasiva final. Esto te ahora miles de dólares a escala.

**La OPORTUNIDAD DE MEJORA para tener más descuento (Token Caching en Prospector):**
En `prospector.py` (línea 317) envías TODO el prompt a Haiku como un solo bloque de `user`.
Como estás procesando lotes de 50 o 100 negocios en paralelo, podrías tener un **90% de descuento en el prospector de Haiku** si separas el prompt en dos partes:
1. **System Prompt (con caché):** Poner aquí todas las reglas del agente, el TIPO DE NEGOCIO, PROBLEMA PRINCIPAL, y cómo evaluar. Le pones `cache_control: ephemeral`.
2. **User Prompt (sin caché):** Poner aquí solo el bloque `NEGOCIO A EVALUAR` (Nombre, Reseñas, Teléfono de un negocio específico).

Como estás lanzando 8 llamadas en paralelo a Anthropic casi al mismo tiempo, las primeras 2 llamadas escribirán la caché del sistema (reglas del vertical de negocio), y las siguientes 48 llamadas de ese lote leerán la caché pagando un **10% del input original**.

### ¿Quieres que implemente esta optimización asíncrona de caché en el `prospector.py` ahora mismo?
