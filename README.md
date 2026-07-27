# UNAHUR Scraper — Horarios de Cursada

## Instalación
Bot para hacer Web Scraping y obtener el listado completo de materias ofertadas del cuatrimestre en curso, junto con sus comisiones y horarios. Esto le permite al estudiante tener un panorama de cuales fueron las materias ofertadas y cuales son los dias y horarios de cursada, para facilitar la organizacion previa a la inscripción para el siguiente cuatrimestre.

## Archivos
```
scraper.py          → scraper principal
sheets_upload.py    → uploader a Google Sheets
materias_estado.json  → generado automáticamente (progreso)
horarios_data.json    → generado automáticamente (datos)
horarios_unahur.xlsx  → generado automáticamente (Excel)
credentials.json    → descargar de Google Cloud (para Sheets)
```

## Instalación
### Crear entorno virtual Python
```bash
python -m venv venv
```

### Activar el entorno virtual
```bash
.\venv\Scripts\Activate.ps1
```

### Instalar dependencias
```bash
pip install -r requeriments.txt
```

## Uso

### Paso 1 — Configurar credenciales
En `.env`:
```python
USUARIO  = "tu_usuario_unahur"
PASSWORD = "tu_password_unahur"
CARRERA_ID= "id_de_carrera"          # 38 = Licenciatura en Informática
SHEET_ID = "id_del_google_sheet"
PERIODO  = "2C 2026"
```

> El `CARRERA_ID` se saca del listado de propuestas en `/inicio_alumno`
> (atributo `data-carrera-id` de cada carrera).
> Desde 2026 la carrera está unificada: solo se scrapea la **Licenciatura en
> Informática** (id `38`); la Tecnicatura en Programación pasó a ser título
> intermedio de la Licenciatura.

### Nombre de la hoja destino
Se arma solo, no está hardcodeado:

```
Oferta  +  <carrera abreviada>  +  PERIODO      →  "Oferta Lic. Informática 2C 2026"
```

La carrera la scrapea `scraper.py` del propio SIU y la deja en
`materias_estado.json`; lo único que se toca a mano por cuatrimestre es
`PERIODO` en el `.env`.

El uploader **crea esa hoja si no existe y no toca el resto de las hojas del
documento**. Si el nombre ya existe, esa hoja se limpia y se reescribe — por eso
conviene cambiar `PERIODO` antes de cada corrida.

Para forzar un nombre puntual, se puede definir `WORKSHEET_NAME` en el `.env`,
que pisa todo lo anterior.

⚠️ Antes de arrancar un cuatrimestre nuevo, borrar `horarios_data.json` y
`materias_estado.json` — si quedan del cuatrimestre anterior, el scraper
considera esas materias ya procesadas y no las vuelve a bajar.

### Paso 2 — Ejecutar el scraper
```bash
python scraper.py
```

**Características clave:**
- Recorre las materias de **abajo hacia arriba** (más importantes primero)
- Guarda un checkpoint en `horarios_data.json` y `materias_estado.json` **después de cada materia**
- Si se interrumpe, al volver a ejecutar **retoma desde donde quedó** (no reprocesa las ya completadas)
- Genera `horarios_unahur.xlsx` al finalizar

### Paso 3 — Subir a Google Sheets (opcional)

#### Setup de Google Cloud (una sola vez):
1. Ir a https://console.cloud.google.com
2. Crear un proyecto nuevo
3. Habilitar APIs: **Google Sheets API** + **Google Drive API**
4. Ir a "Credenciales" → "Crear credenciales" → "Cuenta de servicio"
5. Descargar el JSON de la cuenta de servicio → guardarlo como `credentials.json` en esta carpeta
6. Crear un Google Sheet vacío
7. **Compartirlo** con el email de la cuenta de servicio (está en el JSON, campo `client_email`) como **editor**
8. Copiar el ID del Sheet de la URL: `https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit`

#### En `sheets_upload.py`:
```python
SHEET_ID = "pegar-id-del-sheet-aqui"
```

#### Ejecutar:
```bash
python sheets_upload.py
```

## Estructura del JSON de datos
```json
[
  {
    "nombre": "Taller de lenguajes de marcado y tecnologías web",
    "codigo": "791",
    "url": "https://servicios.unahur.edu.ar/unahur3w/cursada/elegir_materia/...",
    "comisiones": [
      {
        "comision": "Comisión: (791) - Comisión - 1 - PRIMER CUATRIMESTRE 2026",
        "periodo": "PRIMER CUATRIMESTRE 2026",
        "turno": "Mañana",
        "horarios": ["Vie 09:00 a 12:00"],
        "periodicidad": "Semanal",
        "tipo_clase": "Combinada",
        "cupo_info": "Cupo: 55 | Inscriptos: 55",
        "inscripto": false,
        "observaciones": ""
      }
    ],
    "scrapeado_en": "2026-03-20T14:30:00"
  }
]
```

## Resolución de problemas

**"Login fallido"** → Verificar usuario/contraseña. Si el sitio tiene CAPTCHA activo
en ese momento, esperá unos minutos e intentá de nuevo.

**"No se encontró #js-listado-materias"** → La sesión venció. Volver a ejecutar,
el scraper va a hacer login de nuevo y retomar desde donde quedó.

**Materias sin comisiones** → Normal para materias que aún no abrieron inscripción
o son del tipo "COMP_" o "AU_" con otro sistema de inscripción.
