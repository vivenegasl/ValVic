# config.py — LEGACY (modo Sheets, pendiente migrar a MySQL)
# ⚠️  Este archivo era la configuración del sistema de contenido basado en Google Sheets.
#     Está en desuso. Migrar a variables de entorno (.env) antes de usar en producción.
#     Ver: .env.example en la raíz del proyecto.
#
# Las credenciales reales NUNCA deben hardcodearse aquí.
# Usar: os.environ.get('NOMBRE_VARIABLE') o python-dotenv

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys — leer desde variables de entorno
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CALLMEBOT_KEY     = os.environ.get('CALLMEBOT_KEY', '')   # Legacy — usar 360dialog en lo nuevo

# Google Sheets — credenciales del service account
GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')

# Gmail SMTP — solo para notificaciones legacy
GMAIL_USER     = os.environ.get('GMAIL_USER', '')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', '')

# Configuración de contenido
POSTS_POR_RED = {
    'instagram': 4,
    'facebook':  3,
    'tiktok':    2,
}
