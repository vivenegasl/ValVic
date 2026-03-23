"""
notificaciones.py
Envía WhatsApp (CallMeBot) y email (Gmail SMTP) al cliente
con el resumen de los posts generados.
"""

import smtplib
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import CALLMEBOT_API_KEY, GMAIL_USER, GMAIL_APP_PASS


# ══════════════════════════════════════════════════════════════
#  WHATSAPP vía CallMeBot (gratis, sin API oficial)
# ══════════════════════════════════════════════════════════════
def enviar_whatsapp(telefono: str, posts: list[dict], cliente_nombre: str) -> bool:
    """
    Envía un resumen por WhatsApp al número del cliente.
    Formato: +56912345678
    """
    if not CALLMEBOT_API_KEY or CALLMEBOT_API_KEY == "TU_CALLMEBOT_API_KEY":
        print("  ⚠️  CallMeBot no configurado — omitiendo WhatsApp")
        return False

    # Construir mensaje resumido
    redes = list({p["red"] for p in posts})
    iconos = {"instagram": "📸", "facebook": "👤", "linkedin": "💼"}
    redes_str = " · ".join([f"{iconos.get(r,'📱')} {r.capitalize()}" for r in redes])

    mensaje = (
        f"✅ *Contenido de la semana listo* — {cliente_nombre}\n\n"
        f"📅 Se generaron *{len(posts)} posts* para:\n{redes_str}\n\n"
        f"Revísalos en tu Google Sheet y aprueba los que quieras publicar.\n\n"
        f"_Generado automáticamente por ValVic IA_ 🤖"
    )

    try:
        url = (
            f"https://api.callmebot.com/whatsapp.php?"
            f"phone={urllib.parse.quote(telefono)}"
            f"&text={urllib.parse.quote(mensaje)}"
            f"&apikey={CALLMEBOT_API_KEY}"
        )
        with urllib.request.urlopen(url, timeout=10) as resp:
            if resp.status == 200:
                print(f"  ✅ WhatsApp enviado a {telefono}")
                return True
    except Exception as e:
        print(f"  ❌ Error WhatsApp: {e}")
    return False


# ══════════════════════════════════════════════════════════════
#  EMAIL vía Gmail SMTP
# ══════════════════════════════════════════════════════════════
def enviar_email(email_destino: str, posts: list[dict], cliente_nombre: str) -> bool:
    """Envía un email con los posts formateados en HTML."""
    if not GMAIL_APP_PASS or GMAIL_APP_PASS == "TU_CONTRASEÑA_DE_APP":
        print("  ⚠️  Gmail no configurado — omitiendo email")
        return False

    try:
        html = _construir_html(posts, cliente_nombre)
        msg  = MIMEMultipart("alternative")
        msg["Subject"] = f"✅ Contenido de la semana listo — {cliente_nombre}"
        msg["From"]    = GMAIL_USER
        msg["To"]      = email_destino
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASS)
            server.sendmail(GMAIL_USER, email_destino, msg.as_string())

        print(f"  ✅ Email enviado a {email_destino}")
        return True

    except Exception as e:
        print(f"  ❌ Error email: {e}")
        return False


def _construir_html(posts: list[dict], nombre: str) -> str:
    """Genera el HTML del email con los posts."""
    colores = {"instagram": "#E1306C", "facebook": "#1877F2", "linkedin": "#0A66C2"}
    iconos  = {"instagram": "📸", "facebook": "👤", "linkedin": "💼"}

    cards = ""
    for p in posts:
        color = colores.get(p.get("red",""), "#333")
        icono = iconos.get(p.get("red",""), "📱")
        texto = p.get("texto_completo","").replace("\n","<br>")
        cards += f"""
        <div style="background:white;border-radius:12px;border:1px solid #E8E4DD;
                    margin-bottom:16px;overflow:hidden;">
          <div style="background:{color};padding:10px 16px;display:flex;
                      align-items:center;gap:8px;">
            <span style="font-size:16px;">{icono}</span>
            <span style="color:white;font-weight:600;font-size:14px;">
              {p.get('red','').capitalize()}
            </span>
            <span style="color:rgba(255,255,255,.7);font-size:12px;margin-left:auto;">
              {p.get('dia','')} {p.get('fecha_publicacion','')}
            </span>
          </div>
          <div style="padding:14px 16px;font-size:14px;color:#333;line-height:1.6;">
            {texto}
          </div>
        </div>"""

    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"></head>
    <body style="font-family:'DM Sans',Arial,sans-serif;background:#F7F4EF;
                 padding:32px;margin:0;">
      <div style="max-width:600px;margin:0 auto;">
        <div style="background:#0F1420;border-radius:16px;padding:24px;
                    margin-bottom:24px;text-align:center;">
          <h1 style="color:white;font-size:22px;margin:0 0 8px;">
            Val<span style="color:#4B79FF;">Vic</span>
          </h1>
          <p style="color:rgba(255,255,255,.5);font-size:13px;margin:0;">
            Contenido de la semana — {nombre}
          </p>
        </div>
        <div style="background:#F7F4EF;border-radius:10px;padding:16px;
                    margin-bottom:24px;text-align:center;">
          <p style="color:#4A4A56;font-size:14px;margin:0;">
            Se generaron <strong>{len(posts)} posts</strong> para esta semana.
            Revísalos, apruébalos y publícalos cuando quieras.
          </p>
        </div>
        {cards}
        <p style="text-align:center;font-size:12px;color:#9A9AA8;margin-top:24px;">
          Generado automáticamente por ValVic IA 🤖<br>
          <a href="https://valvic.cl" style="color:#4B79FF;">valvic.cl</a>
        </p>
      </div>
    </body></html>"""
