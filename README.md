# ValVic — Repositorio Principal
Sistema multi-agente en Python puro y FastAPI para automatizar la prospección, negociación y agendamiento de negocios de servicios en Chile a través de WhatsApp.

## CÓMO EJECUTAR EL PROSPECTOR 

*(Requiere que `.env` esté correctamente configurado con las claves)*

```bash
# Ver verticales disponibles en la carpeta yml
python Agentes/prospector.py --listar-verticales

# Prospectar (Simulación CLI)
python Agentes/prospector.py --vertical dental --ciudad Santiago --cantidad 5 --test

# Enviar en Firme en Producción
python Agentes/prospector.py --vertical psicologos --ciudad Santiago --enviar

# Revisar mensajes generados o estado de prospectos
python Agentes/prospector.py --vertical dental --solo-revisar
```

---

## INVENTARIO DE ARCHIVOS PRINCIPALES

### Sistema Central (Marzo 2026)
| Archivo | Función |
|---|---|
| `Agentes/prospector.py` | Orquestador multi-vertical. Busca, califica e inyecta prospectos. |
| `Agentes/subagente_db.py` | Capa base de datos ORM con AIOMySQL persistente. |
| `Agentes/prompts_ventas.py` | Prompt dinámico de cierres, pre-respuestas y escaleras de negociación. |
| `Agentes/agente_conversacion.py` | "Vicky" y otros agentes - Toma decisión asíncrona inbound de WA. |
| `verticals/` | Carpeta .yaml donde se define cada arquetipo sin tocar código. |
| `schema_prospeccion_mysql.sql` | Estructura de BD en sintaxis nativa de MySQL HeatWave. |

---

## MAPA ORGÁNICO DE AGENTES

### Capa 1 — Operación crítica
- **Agente de Citas:** Atiende WA de pacientes, agenda en MySQL usando NLP natural.
- **Agente Recordatorios:** Dispara alertas via cron a 24h y 1h.
- **Agente Reportes:** Envía KPIs semanales y análisis de ROI al dueño de la clínica.

### Capa 2 — Crecimiento y Generación (Motor ValVic)
- **Prospector Multi-vertical (Activo):** Búsqueda API de clínicas, generación paralela del mensaje rompehielo y dispatch por 360dialog.
- **Vicky (Activo):** Agente Sales/SDR. Rebate objeciones asíncronamente en WhatsApp con Debounce de tiempos.
- **Seguimiento Autómata:** Reintenta el lead al día 3 garantizando que nunca se olvida un chat.

### Capa Transversal IA (Optimización)
- **Routing:** Enrutador clasificador de bajo costo en `claude-haiku`.
- **Generativo:** Motor persuasivo complejo usando `claude-sonnet`.
- **Caching:** Ahorros de hasta 90% con Prompt Caching en directrices estáticas de YAML y system prompts en las operaciones paralelas masivas.
