"""
UNAHUR → Google Sheets uploader
================================
Lee horarios_data.json y vuelca todo a un Google Sheet.

Setup (una sola vez):
  1. Ir a https://console.cloud.google.com
  2. Crear proyecto → habilitar "Google Sheets API" y "Google Drive API"
  3. Crear credenciales → Cuenta de servicio → descargar JSON → guardar como "credentials.json"
  4. En el Sheet destino, compartir con el email de la cuenta de servicio (editor)
  5. Completar SHEET_ID abajo y ejecutar: python sheets_upload.py
"""

import json
import os
import sys
from dotenv import load_dotenv
import re

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("[ERROR] Instalar dependencias: pip install gspread google-auth")
    sys.exit(1)

load_dotenv()

# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────
CREDENTIALS_FILE = "credentials.json"   # descargado de Google Cloud
SHEET_ID         = os.getenv("SHEET_ID")
WORKSHEET_NAME   = "Horarios UNAHUR 2026"
FILE_DATOS       = "horarios_data.json"

# ──────────────────────────────────────────────
#  AUTENTICACIÓN
# ──────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def conectar_sheets():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"[ERROR] No se encontró {CREDENTIALS_FILE}")
        print("  → Descargarlo desde Google Cloud Console (cuenta de servicio)")
        sys.exit(1)

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc

def limpiar_comision(titulo):
    """Extrae solo el número de comisión del título completo."""
    if not titulo:
        return ""
    # Buscar número después de "comisión", "comision", "COM" (con o sin espacio/guion)
    m = re.search(r'comisi[oó]n[\s\-]*(\d+)', titulo, re.IGNORECASE)
    if m:
        return f"Comisión {int(m.group(1))}"
    # Fallback: buscar "COM" seguido de número
    m = re.search(r'\bCOM[\s\-]*(\d+)', titulo, re.IGNORECASE)
    if m:
        return f"Comisión {int(m.group(1))}"
    # Si no encuentra número, devolver vacío o el título original recortado
    return titulo

# ──────────────────────────────────────────────
#  UPLOAD
# ──────────────────────────────────────────────

def upload(datos, gc):
    try:
        sh = gc.open_by_key(SHEET_ID)
    except Exception as e:
        print(f"[ERROR] No se pudo abrir el Sheet: {e}")
        print("  → Verificar SHEET_ID y que el sheet esté compartido con la cuenta de servicio")
        sys.exit(1)

    # Crear/reemplazar hoja
    try:
        ws = sh.worksheet(WORKSHEET_NAME)
        ws.clear()
        print(f"[SHEETS] Hoja '{WORKSHEET_NAME}' limpiada")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=200, cols=5)
        print(f"[SHEETS] Hoja '{WORKSHEET_NAME}' creada")

    headers = ["Materia", "Código", "Comisión", "Turno", "Horario", "Tipo Clase"]

    rows = [headers]

    for materia in datos:
        nombre     = materia.get("nombre", "")
        codigo     = materia.get("codigo", "")
        comisiones = materia.get("comisiones", [])

        if not comisiones:
            rows.append([nombre, codigo, "(sin comisiones)", "", ""])
            continue

        for com in comisiones:
            if not com.get("comision") and not com.get("horario"):
                continue

            rows.append([
                nombre,
                codigo,
                limpiar_comision(com.get("comision", "")),
                com.get("turno",""),
                com.get("horario",""),
                com.get("tipo_clase", ""),
            ])

    # Batch update (más eficiente que row a row)
    ws.update(rows, value_input_option="RAW")

    # Formato encabezado
    ws.format("A1:F1", {
        "backgroundColor": {"red": 0.122, "green": 0.306, "blue": 0.475},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "horizontalAlignment": "CENTER",
    })

    # Freeze encabezado
    sh.batch_update({"requests": [{
        "updateSheetProperties": {
            "properties": {
                "sheetId": ws.id,
                "gridProperties": {"frozenRowCount": 1}
            },
            "fields": "gridProperties.frozenRowCount"
        }
    }]})

    print(f"[SHEETS] ✓ {len(rows)-1} filas cargadas en '{WORKSHEET_NAME}'")
    print(f"[SHEETS] URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")

# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  UNAHUR → Google Sheets Uploader")
    print("=" * 50)

    if SHEET_ID == "":
        print("[ERROR] Completar SHEET_ID en el script.")
        sys.exit(1)

    if not os.path.exists(FILE_DATOS):
        print(f"[ERROR] No se encontró {FILE_DATOS}. Ejecutar primero scraper.py")
        sys.exit(1)

    with open(FILE_DATOS, "r", encoding="utf-8") as f:
        datos = json.load(f)

    print(f"[INFO] {len(datos)} materias en {FILE_DATOS}")

    gc = conectar_sheets()
    upload(datos, gc)

if __name__ == "__main__":
    main()
