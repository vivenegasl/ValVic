"""
main.py
Punto de entrada principal.
Ejecuta el generador para todos los clientes configurados.

Uso:
  python main.py              → genera para todos los clientes
  python main.py valvic       → genera solo para el cliente con id "valvic"
  python main.py --test       → modo prueba (no envía notificaciones)
"""

import sys
from datetime import datetime
from clientes    import CLIENTES
from generador   import generar_posts
from sheets      import guardar_posts
from notificaciones import enviar_whatsapp, enviar_email


def procesar_cliente(cliente: dict, modo_test: bool = False):
    nombre = cliente["nombre"]
    print(f"\n{'─'*55}")
    print(f"🤖 Generando contenido para: {nombre}")
    print(f"   Redes: {', '.join(cliente['redes'])}")
    print(f"{'─'*55}")

    # 1. Generar posts con Claude
    posts = generar_posts(cliente)
    if not posts:
        print(f"  ⚠️  No se generaron posts para {nombre}")
        return

    # 2. Guardar en Google Sheets
    guardar_posts(cliente["sheet_id"], posts)

    # 3. Notificaciones (omitir en modo test)
    if not modo_test:
        if cliente.get("whatsapp"):
            enviar_whatsapp(cliente["whatsapp"], posts, nombre)
        if cliente.get("email"):
            enviar_email(cliente["email"], posts, nombre)
    else:
        print("  ℹ️  Modo test — notificaciones omitidas")

    print(f"\n  ✅ {nombre} completado — {len(posts)} posts generados")


def main():
    args      = sys.argv[1:]
    modo_test = "--test" in args
    filtro    = next((a for a in args if not a.startswith("--")), None)

    print(f"""
╔══════════════════════════════════════════════════╗
║     ValVic — Generador de Contenido IA          ║
║  {datetime.now().strftime('%A %d/%m/%Y  %H:%M'):<44}║
║  Modo: {'TEST' if modo_test else 'PRODUCCIÓN':<43}║
╚══════════════════════════════════════════════════╝""")

    clientes = CLIENTES
    if filtro:
        clientes = [c for c in CLIENTES if c["id"] == filtro]
        if not clientes:
            print(f"\n❌ No se encontró el cliente con id '{filtro}'")
            print(f"   IDs disponibles: {[c['id'] for c in CLIENTES]}")
            return

    print(f"\n📋 Clientes a procesar: {len(clientes)}")
    for c in clientes:
        procesar_cliente(c, modo_test)

    print(f"\n{'═'*55}")
    print(f"🎉 Proceso completado — {len(clientes)} cliente(s)")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
