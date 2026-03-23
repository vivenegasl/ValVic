"""
sheets.py
Guarda los posts generados en el Google Sheet del cliente.
Crea la hoja si no existe y da formato automáticamente.
"""

import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS_FILE, SHEET_TAB_NAME

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Fecha generación", "Cliente", "Red social", "Día",
    "Fecha publicación", "Texto completo", "Hashtags", "Estado"
]

# Colores por red para formatear la hoja
COLOR_REDES = {
    "instagram": {"red": 0.886, "green": 0.188, "blue": 0.424},
    "facebook":  {"red": 0.094, "green": 0.463, "blue": 0.949},
    "linkedin":  {"red": 0.039, "green": 0.400, "blue": 0.761},
}


def conectar():
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
    )
    return gspread.authorize(creds)


def guardar_posts(sheet_id: str, posts: list[dict]) -> bool:
    """
    Agrega los posts al Sheet del cliente.
    Crea los encabezados y formato si es la primera vez.
    """
    try:
        gc    = conectar()
        sh    = gc.open_by_key(sheet_id)

        # Obtener o crear la hoja
        try:
            ws = sh.worksheet(SHEET_TAB_NAME)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=SHEET_TAB_NAME, rows=500, cols=10)
            _formatear_hoja(ws)

        # Si está vacía, agregar encabezados
        if ws.row_count == 0 or not ws.get_all_values():
            ws.append_row(HEADERS)
            _formatear_encabezados(ws)

        # Agregar los posts
        for post in posts:
            row = [
                post.get("fecha_generacion", ""),
                post.get("cliente", ""),
                post.get("red", "").capitalize(),
                post.get("dia", ""),
                post.get("fecha_publicacion", ""),
                post.get("texto_completo", ""),
                post.get("hashtags_str", ""),
                "⏳ Pendiente revisión",
            ]
            ws.append_row(row)

        print(f"  ✅ {len(posts)} posts guardados en Google Sheets")
        return True

    except Exception as e:
        print(f"  ❌ Error guardando en Sheets: {e}")
        return False


def _formatear_encabezados(ws):
    """Aplica formato visual a la fila de encabezados."""
    try:
        ws.format("A1:H1", {
            "backgroundColor": {"red": 0.051, "green": 0.071, "blue": 0.157},
            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1},
                           "bold": True, "fontSize": 11},
            "horizontalAlignment": "CENTER",
        })
        # Ancho de columnas
        requests = [{"updateDimensionProperties": {
            "range": {"sheetId": ws.id, "dimension": "COLUMNS",
                      "startIndex": i, "endIndex": i+1},
            "properties": {"pixelSize": w},
            "fields": "pixelSize"
        }} for i, w in enumerate([140, 120, 110, 90, 110, 380, 200, 140])]
        ws.spreadsheet.batch_update({"requests": requests})
    except Exception:
        pass  # El formato falla silenciosamente, los datos ya están guardados


def _formatear_hoja(ws):
    """Congela la fila de encabezados."""
    try:
        ws.spreadsheet.batch_update({"requests": [{
            "updateSheetProperties": {
                "properties": {"sheetId": ws.id,
                               "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount"
            }
        }]})
    except Exception:
        pass
