# ValVic — Playbook y Estrategia Comercial
> Documento vivo para el equipo de ventas, fundadores e IA's comerciales.
> Todo cambio de precios o estrategia de negociación debe actualizarse aquí.

## SERVICIOS Y PRECIOS

| Servicio | Implementación | Mensual | Piso mensual |
|---|---|---|---|
| Agente de citas IA | $100 | $80 | $65 |
| Sitio web profesional | $100 | $50 | $40 |
| Bundle citas + web | $180 | $120-135 | $80 |
| Generador de contenido IA | $100 | $80 | $65 |
| Centro de reportes IA | $100 | $55 | $45 |

**Benchmark mercado:** Nexden desde $20 USD/mes (self-service), AgendaPro desde $29 USD/mes.
ValVic es done-for-you + WhatsApp nativo → justifica 2-3x el precio de la competencia.

---

## AGENTES POR VERTICAL

| Vertical | Agente | Producto principal | Mensual lista | Piso |
|---|---|---|---|---|
| Clínicas dentales | Daniela | Citas | $90 | $70 |
| Centros de estética | Camila | Citas | $95 | $70 |
| Veterinarias | Vicky | Citas | $80 | $65 |
| Spas / salones | Sofía | Citas | $80 | $65 |
| Psicólogos / coaches | Valentina | Citas | $80 | $65 |
| Gimnasios | Andrea | Citas | $75 | $65 |
| Inmobiliarias | Valeria | Web | $70 | $55 |
| Mueblerías | Valeria | Web | $50 | $40 |

---

## ESCALERA DE CONCESIONES (Cierre Autónomo)
*(Orden obligatorio — solo ofrecer la siguiente si falla la anterior)*

1. **10% descuento implementación** → primera resistencia de precio.
2. **Pago 50/50** (ahora / al entregar) → objeción de flujo de caja.
3. **Descuento temporal 3 meses** → segunda objeción de precio.
4. **Primer mes gratis** → opción nuclear, última instancia.

---

## ESTRATEGIA DE PROSPECCIÓN

**Canal principal:** prospección WhatsApp + cierre automático por el Agente.
**Cierre exitoso:** pago de señal de inicio ($50 USD implementación).
**Escalado a humano:** 3 objeciones sin resolver | cliente lo pide explícitamente | exige precio < piso orgánico.

**Prioridad comercial (por probabilidad rápida de cierre):**
1. Clínicas dentales — ROI matemático inmediato ($120-250 USD por cita perdida).
2. Centros de estética — ticket alto, mismo argumento.
3. Spas / salones — dolor de tiempo brutal (6-8h/semana en WA manual).
4. Psicólogos / coaches — no-show sensible, ticket alto.
5. Veterinarias — llamadas perdidas durante la consulta clínica.

---

## COSTOS ESTIMADOS EN PRODUCCIÓN

| Componente | Uso | Costo Base |
|---|---|---|
| Oracle VM + MySQL | Always Free | $0 |
| Claude API (10 clientes) | ~50k tokens/mes | ~$15-25 USD/mes |
| 360dialog WhatsApp API | Plan Básico | ~$5.50 USD/mes |
| Hostinger Business | Web clientes | Incluido (ya pagado) |
| Google Places API | 200/búsquedas semana | $0 (dentro de cuota) |

**Costos de Meta (Prospección):** Meta cobra ~$0.05 por cada cliente contactado *en frío* por la API. Gastar $100 USD/mes en prospección garantiza impactar a 2.000 clínicas directamente en su bandeja de entrada. Un solo cierre (setup $180) cubre la publicidad del mes.

---

## CAMBIOS PENDIENTES WEB (Copywriting)

La web debe vender el dolor, no la tecnología.
- **Hero section:** "Tu clínica pierde citas cada semana. Las recuperamos automáticamente." 
- **Sección de Servicios:** Mostrar los precios abiertamente (desde $80 USD/mes).
- **Sección de Rubros:** Grid con los 8 verticales y el problema específico de cada uno (ej. dental = "cada cita vacía son $150 USD").
- **Meta description:** "Automatiza las citas de tu clínica dental, spa o veterinaria con IA. Implementación en 5 días. Desde $80 USD/mes."
