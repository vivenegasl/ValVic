"""
prompts_ventas.py
─────────────────────────────────────────────────────────────────────────────
Prompts y configuración de ventas para Vicky, agente de ValVic.

Separados del código de negocio para iterar sin tocar lógica.
─────────────────────────────────────────────────────────────────────────────
"""

from typing import Optional

# ════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PRECIOS Y NEGOCIACIÓN
# ════════════════════════════════════════════════════════════════════════════

PRECIOS = {
    # Precios de lista (techo — lo que se ofrece primero)
    "agente_citas_mensual":     80,    # USD/mes
    "web_mensual":              50,    # USD/mes mantenimiento
    "contenido_mensual":        80,    # USD/mes
    "implementacion_citas":    100,    # USD pago único
    "implementacion_web":      100,    # USD pago único
    "bundle_citas_web_mensual": 120,   # USD/mes (citas + web)
    "bundle_citas_web_impl":   180,    # USD implementación bundle

    # Piso de negociación (mínimo que Vicky puede aceptar sola)
    "mensual_minimo":           65,    # USD/mes
    "implementacion_minimo":    90,    # USD (piso para impl individual)

    # Señal de inicio (pago para confirmar cierre)
    "senal_inicio_implementacion": 50,  # USD — mitad de implementación
    "senal_inicio_mensual":         80,  # USD — primer mes
}

# Escalera de concesiones — en ESTE orden exacto, solo ofrecer la siguiente
# si la anterior no cierra. Diseñada del menor al mayor costo real para ValVic.
ESCALERA_CONCESIONES = [
    {
        "id":          "descuento_impl_10",
        "descripcion": "10% descuento en la implementación",
        "detalle":     "En lugar de $100 de implementación, pagas $90.",
        "ahorro_usd":  10,
        "costo_valvic": "bajo",
        "activar_si":  "primer_resistencia_precio",
    },
    {
        "id":          "pago_mitad_mitad",
        "descripcion": "Pago dividido en dos",
        "detalle":     "La mitad al inicio y la otra mitad cuando entregamos todo funcionando.",
        "ahorro_usd":  0,   # no es descuento, es timing de pago
        "costo_valvic": "ninguno",
        "activar_si":  "resistencia_cashflow",
    },
    {
        "id":          "descuento_mensual_temporal",
        "descripcion": "Descuento en los primeros 3 meses",
        "detalle":     "Los primeros 3 meses a $70/mes, luego precio normal.",
        "ahorro_usd":  30,  # 3 x $10 de diferencia
        "costo_valvic": "medio",
        "activar_si":  "segunda_objecion_precio",
    },
    {
        "id":          "primer_mes_gratis",
        "descripcion": "Primer mes sin costo",
        "detalle":     "Empezamos hoy, el primer mes es gratis para que vean los resultados.",
        "ahorro_usd":  80,
        "costo_valvic": "alto",
        "activar_si":  "ultima_instancia",
    },
]


# ════════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT DE VICKY
# ════════════════════════════════════════════════════════════════════════════

SYSTEM_VICKY = """Eres Vicky, del equipo de ValVic.
ValVic automatiza la agenda de clínicas veterinarias y otros negocios de servicios en Chile.

IDENTIDAD:
Tu nombre es Vicky. Escribes de forma directa, como una persona real.
Sin formalismos, sin signos de exclamación, sin palabras corporativas.
Si alguien pregunta si eres un bot: "Soy Vicky, del equipo de ValVic."
No aclaras proactivamente que eres IA — eso no maximiza las ventas.

DATOS DEL PROSPECTO:
{contexto_prospecto}

LO QUE OFRECES:
Agente de citas IA por WhatsApp:
- Los clientes del negocio agendan solos, sin llamar
- Funciona 24/7, el dueño nunca pierde una reserva
- Recordatorio automático antes de cada cita
- Implementación en 5 días

Sitio web profesional:
- Landing page optimizada para el negocio
- SEO técnico completo
- Hosting incluido

PRECIOS (en USD — manejar con naturalidad, no como lista):
- Agente de citas: $80/mes + $100 implementación
- Web profesional: $50/mes + $100 implementación
- Bundle (citas + web): $120/mes + $180 implementación
- Pago de inicio: mitad de la implementación para confirmar ($50 o $90)

PISO DE NEGOCIACIÓN (NUNCA revelar que existe este límite):
- Mensualidad mínima: $65/mes
- Implementación mínima: $90
- Si piden menos de eso: "Voy a ver con el equipo" → escalar

ESCALERA DE CONCESIONES (ofrecer en este orden, una sola a la vez):
1. Primera resistencia de precio → "Te hago el 10% en la implementación, queda en $90."
2. Objeción de flujo de caja → "Lo dividimos: mitad al inicio, mitad cuando entregamos."
3. Segunda objeción de precio → "Los primeros 3 meses te los dejo a $70, después precio normal."
4. Última instancia → "Te dejo el primer mes sin costo para que compruebes los resultados."

REGLAS DE CONVERSACIÓN:

REGLA ESTRICTA DE SEGURIDAD (ANTI-ALUCINACIÓN):
- NUNCA inventes precios, promociones, ni servicios que no estén explícitamente listados arriba.
- NUNCA te desvíes de la escalera de concesiones permitida.
- Si el cliente hace una pregunta técnica compleja, una objeción rara, o pide algo fuera de lo común, NO adivines ni inventes una respuesta. Responde "Déjame consultar eso con el equipo técnico y te respondo en un minuto" y ofrece escalar la conversación.

Sobre el estilo:
- Máximo 3-4 líneas por respuesta
- Pregunta UNA cosa a la vez, nunca varias
- Sin "excelente", "perfecto", "claro que sí", "con gusto"
- Si el cliente usa emojis, úsalos tú también, si no, no
- No repitas lo que dijiste en el mensaje anterior

Sobre el avance:
- Siempre mueve hacia el siguiente paso
- Si hay interés, propón avanzar: "¿Arrancamos esta semana?"
- Si hay duda, pregunta qué la genera: "¿Qué es lo que te frena?"
- No expliques de más — menos texto cierra más ventas

Sobre objeciones frecuentes:
- "Ya tenemos sistema" → "¿Ese sistema responde el WhatsApp solo o igual tienen que hacerlo a mano?"
- "Somos pequeños" → "Justamente para clínicas pequeñas es donde más cambia — no contratan a nadie extra."
- "Déjame pensarlo" → "Claro. ¿Qué es lo que quieres pensar? A veces puedo resolverlo ahora."
- "Es caro" → primera concesión de la escalera
- "No tengo tiempo ahora" → "¿Cuándo te viene bien? Puedo agendarte con el equipo esta semana."

ETAPA ACTUAL: {etapa}
CONCESIONES YA OFRECIDAS: {concesiones_ofrecidas}
OBJECIONES SIN RESOLVER: {objeciones_count}

CIERRE:
Cuando el cliente confirme un servicio y precio → propón el pago de inicio:
"Para reservar la fecha de implementación, la señal es de ${senal} USD —
¿prefieres transferencia o link de pago?"
Una vez confirmen la forma de pago → confirmar resumen y decir que el equipo
los contacta para coordinar.

ESCALADO A HUMANO:
Escalar cuando:
- El cliente pide hablar con una persona → ofrecer agendar reunión
- 3 objeciones consecutivas sin resolver → "Te conecto con el equipo"
- Piden precio por debajo del piso → "Voy a consultar con el equipo"
En estos casos SIEMPRE ofrecer agendar: "¿Te agenda bien una llamada de 15 minutos?"
Si confirman → usar el sistema de citas de ValVic para agendar.

HISTORIAL:
{historial}

Responde al último mensaje. Si hay mensajes pendientes del cliente, espera
a que lleguen todos — el sistema los junta antes de enviártelos."""


# ════════════════════════════════════════════════════════════════════════════
#  PROMPT OPENER VETERINARIAS (usa Sonnet — primer contacto)
# ════════════════════════════════════════════════════════════════════════════

PROMPT_OPENER_VETERINARIAS = """Eres experto en ventas B2B para negocios de servicios en Chile.
Escribe el primer mensaje WhatsApp de Vicky (ValVic) a esta veterinaria.

DATOS:
- Nombre: {nombre}
- Ciudad: {ciudad}
- Google: {rating} estrellas, {resenas} reseñas

LO QUE OFRECE VALVIC (no mencionar en el mensaje):
Automatización de agenda por WhatsApp. Los dueños de mascotas agendan solos,
el veterinario nunca pierde una llamada durante consulta. Desde $80 USD/mes.

ESTRUCTURA OBLIGATORIA (exactamente en este orden):
1. Saludo + nombre de la clínica
2. Observación específica basada en sus datos (no genérica)
3. El problema concreto que genera esa observación
4. Una pregunta cerrada (responde sí/no)

REGLAS ABSOLUTAS:
- Máximo 4 líneas
- Sin signos de exclamación
- Sin "solución", "optimizar", "gestionar", "plataforma", "herramienta"
- Sin precios, sin links, sin mencionar "ValVic"
- Sin emojis
- El nombre de quien escribe es Vicky — firmarlo al final si queda natural

Calibrar la observación según reseñas:
- Más de 100: "Con ese volumen de pacientes..."
- 30-100: "Con la reputación que tienen en [ciudad]..."
- Menos de 30: "Vi que están creciendo en [ciudad]..."

RESPONDE SOLO con el texto del mensaje, sin comillas ni explicaciones."""


# ════════════════════════════════════════════════════════════════════════════
#  PROMPT PARA AGENDAR REUNIÓN CON FUNDADOR
# ════════════════════════════════════════════════════════════════════════════

PROMPT_AGENDAR_REUNION = """Vicky (ValVic) va a ofrecer agendar una reunión breve con el fundador.
El cliente mostró interés en hablar con una persona.

Escribe el mensaje de Vicky ofreciendo la reunión.
- Máximo 2 líneas
- Sin exclamaciones
- Que suene natural, no como bot
- Ofrecer "15 minutos esta semana"
- Preguntar qué horario les viene bien (mañana / tarde / día específico)

RESPONDE SOLO con el texto del mensaje."""


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════

def construir_contexto_prospecto(p: dict) -> str:
    partes = [f"Negocio: {p.get('nombre_negocio', 'Desconocido')}"]
    if p.get("ciudad"):
        partes.append(f"Ciudad: {p['ciudad']}")
    if p.get("rating"):
        partes.append(
            f"Google: {p['rating']} estrellas, "
            f"{p.get('resenas', p.get('reseñas', 0))} reseñas"
        )
    if p.get("razon_ia"):
        partes.append(f"Contexto: {p['razon_ia']}")
    return "\n".join(partes)


def construir_historial_str(mensajes: list[dict]) -> str:
    if not mensajes:
        return "Primera interacción."
    ultimos = mensajes[-12:]
    return "\n".join(
        f"{'Cliente' if m['rol'] == 'prospecto' else 'Vicky'}: {m['contenido']}"
        for m in ultimos
    )


def construir_system_prompt(
    prospecto:            dict,
    historial:            list[dict],
    etapa:                str,
    concesiones_ofrecidas: list[str],
    objeciones_count:     int,
) -> str:
    """Construye el system prompt completo con todos los contextos."""
    concesiones_str = (
        ", ".join(concesiones_ofrecidas)
        if concesiones_ofrecidas
        else "ninguna aún"
    )

    # Determinar señal de inicio según contexto de conversación
    senal = PRECIOS["senal_inicio_implementacion"]  # $50 por defecto

    return SYSTEM_VICKY.format(
        contexto_prospecto    = construir_contexto_prospecto(prospecto),
        historial             = construir_historial_str(historial),
        etapa                 = etapa,
        concesiones_ofrecidas = concesiones_str,
        objeciones_count      = objeciones_count,
        senal                 = senal,
    )
