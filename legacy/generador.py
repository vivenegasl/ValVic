"""
generador.py
Llama a Claude API y genera los posts de la semana para un cliente.
Incluye historial para evitar repetir contenido ya generado.
"""

import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from config import ANTHROPIC_API_KEY, POSTS_POR_RED, GOOGLE_CREDENTIALS_FILE
import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Días sugeridos de publicación por red
DIAS_RED = {
    "instagram": ["Lunes", "Jueves"],
    "facebook":  ["Martes", "Viernes"],
    "linkedin":  ["Miércoles", "Viernes"],
}

COLORES_RED = {
    "instagram": "#E1306C",
    "facebook":  "#1877F2",
    "linkedin":  "#0A66C2",
}

# Cuántos posts del historial enviar a Claude para evitar repetición
MAX_HISTORIAL = 20


def obtener_historial(sheet_id: str) -> list[str]:
    """
    Lee los últimos MAX_HISTORIAL posts del Sheet del cliente
    y devuelve solo el campo 'texto_completo' para que Claude los evite.
    """
    try:
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
        )
        gc   = gspread.authorize(creds)
        sh   = gc.open_by_key(sheet_id)
        ws   = sh.worksheet("Contenido")
        rows = ws.get_all_values()

        if len(rows) <= 1:  # solo encabezados o vacío
            return []

        # Columna 6 (índice 5) = texto_completo
        textos = [row[5] for row in rows[1:] if len(row) > 5 and row[5]]
        ultimos = textos[-MAX_HISTORIAL:]
        print(f"  📚 Historial: {len(ultimos)} posts anteriores cargados")
        return ultimos

    except Exception as e:
        print(f"  ⚠️  No se pudo cargar historial: {e}")
        return []


def generar_posts(cliente: dict) -> list[dict]:
    """
    Llama a Claude y devuelve una lista de posts listos para guardar.
    Usa el historial del cliente para evitar repetir ideas.
    """
    redes    = cliente["redes"]
    nombre   = cliente["nombre"]
    tipo     = cliente["tipo"]
    dif      = cliente["diferenciador"]
    tono     = cliente["tono"]
    promo    = cliente["promo"]
    promo_str = f"\nPromoción activa esta semana: {promo}" if promo else ""

    # Cargar historial del cliente
    historial = obtener_historial(cliente["sheet_id"])
    historial_str = ""
    if historial:
        muestra = historial[-10:]  # últimos 10 como contexto
        historial_str = "\n\nCONTENIDO YA PUBLICADO — NO REPETIR estas ideas:\n"
        for i, h in enumerate(muestra, 1):
            # Solo primeras 120 chars para no inflar el prompt
            historial_str += f"{i}. {h[:120]}...\n"

    # Calcular fechas de publicación
    hoy   = datetime.now()
    lunes = hoy + timedelta(days=(7 - hoy.weekday()))
    fechas = {
        "Lunes":     lunes.strftime("%d/%m"),
        "Martes":    (lunes + timedelta(1)).strftime("%d/%m"),
        "Miércoles": (lunes + timedelta(2)).strftime("%d/%m"),
        "Jueves":    (lunes + timedelta(3)).strftime("%d/%m"),
        "Viernes":   (lunes + timedelta(4)).strftime("%d/%m"),
    }

    prompt = f"""Eres el community manager de {nombre}.

CONTEXTO DEL NEGOCIO:
- Nombre: {nombre}
- Tipo: {tipo}
- Diferenciador: {dif}
- Tono de comunicación: {tono}{promo_str}{historial_str}

TAREA:
Genera {POSTS_POR_RED} posts para cada una de estas redes: {', '.join(redes)}.
Total de posts: {len(redes) * POSTS_POR_RED}

REGLAS IMPORTANTES:
- Cada post debe tener una IDEA DISTINTA a los anteriores y entre sí
- No repitas frases, estructuras ni conceptos del historial anterior
- Varía el formato: preguntas, datos curiosos, historias, consejos, promociones
- Adapta el estilo a cada red (Instagram visual, LinkedIn profesional, Facebook conversacional)
- Incluye emoji relevantes sin exagerar
- Hashtags específicos (5-7 por post)
- Tono: {tono}
- Si hay promoción, inclúyela en al menos 1 post

RESPONDE ÚNICAMENTE con JSON válido, sin texto adicional:
[
  {{
    "red": "instagram",
    "dia": "Lunes",
    "emoji": "✨",
    "texto": "texto completo del post",
    "hashtags": ["#tag1", "#tag2"]
  }}
]"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = response.content[0].text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        posts = json.loads(texto)

        # Enriquecer con metadatos
        for post in posts:
            post["fecha_publicacion"] = fechas.get(post.get("dia", "Lunes"), "")
            post["fecha_generacion"]  = datetime.now().strftime("%d/%m/%Y %H:%M")
            post["cliente"]           = nombre
            post["color_red"]         = COLORES_RED.get(post["red"], "#333")
            post["hashtags_str"]      = " ".join(post.get("hashtags", []))
            post["texto_completo"]    = f"{post['emoji']} {post['texto']}\n\n{post['hashtags_str']}"

        print(f"  ✅ {len(posts)} posts generados para {nombre}")
        return posts

    except (json.JSONDecodeError, Exception) as e:
        print(f"  ❌ Error generando posts para {nombre}: {e}")
        return []

