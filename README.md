# Buscador de Productores Asesores de Seguros — SSN Argentina

Aplicación de escritorio Windows para buscar productores asesores de seguros registrados en la Superintendencia de Seguros de la Nación (Argentina).

**Fuente de datos**: [Datos Abiertos SSN](https://datosabiertos.ssn.gob.ar) — Licencia CC BY 4.0

---

## Estructura del proyecto

```
productor de seguros/
├── main.py              # Entry point, orquestación de UI
├── data_manager.py      # Carga CSV, cache local, descarga en background
├── ui_components.py     # Todos los componentes de UI (Flet)
├── utils.py             # Normalización, búsqueda fuzzy, clipboard
├── generate_icon.py     # Script auxiliar para generar el ícono
├── requirements.txt
├── README.md
├── assets/
│   └── icon.png         # Ícono de la app
└── data/                # Directorio de cache (creado automáticamente)
    └── productores-asesores.csv   # CSV cacheado localmente
```

---

## Ejecutar en desarrollo

### 1. Crear entorno virtual (recomendado)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Generar el ícono (primera vez)

```bash
python generate_icon.py
```

> Si tenés `Pillow` instalado, genera un ícono con forma de escudo+lupa.
> Si no, genera un placeholder azul sólido. Podés reemplazar `assets/icon.png` con cualquier PNG 256×256.

### 4. Correr la app

```bash
flet run main.py
```

O alternativamente:

```bash
python main.py
```

---

## Generar el ejecutable Windows (.exe)

### Requisitos previos

```bash
pip install pyinstaller
```

> ⚠️ **Importante**: PyInstaller debe correr en Windows para generar un `.exe` válido.
> Si estás en Linux/Mac, usá una VM Windows o GitHub Actions.

### Comando de empaquetado

```bash
pyinstaller \
  --onefile \
  --windowed \
  --name "Buscador SSN" \
  --icon "assets/icon.ico" \
  --add-data "assets:assets" \
  main.py
```

> **Nota sobre el ícono**: PyInstaller requiere formato `.ico` para Windows.
> Convertí `assets/icon.png` a `assets/icon.ico` con cualquier conversor online
> (ej: https://convertio.co/png-ico/) o con ImageMagick:
> ```bash
> magick convert assets/icon.png -resize 256x256 assets/icon.ico
> ```

### En Windows (cmd o PowerShell):

```cmd
pyinstaller --onefile --windowed --name "Buscador SSN" --icon "assets\icon.ico" --add-data "assets;assets" main.py
```

> ⚠️ En Windows el separador de `--add-data` es `;` (punto y coma), no `:`.

### Resultado

El ejecutable queda en `dist/Buscador SSN.exe`.

Distribuible: un único archivo `.exe`, sin instalador, sin requerir Python en el destino.
Al ejecutarlo por primera vez descarga el CSV desde la SSN y lo guarda en `data/` junto al `.exe`.

---

## Datos del CSV

El CSV oficial tiene las siguientes columnas:

| Columna | Descripción |
|---|---|
| `productor_matricula` | Número de matrícula |
| `productor_tipo_id` | Tipo de documento (siempre CUIT) |
| `productor_id` | Número de CUIT |
| `productor_apellido_nombre` | Nombre y apellido |
| `ramo` | Ramo habilitado (Patrimoniales y Vida / Vida / Artículo 19) |

~53.575 registros. Encoding UTF-8, separador coma.

Si el CSV remoto cambia de estructura, la app muestra un aviso y continúa usando el cache anterior.

---

## Licencia de los datos

Los datos son publicados por la SSN bajo licencia **CC BY 4.0**.
URL del dataset: https://datosabiertos.ssn.gob.ar/dataset/be4927ba-6b6d-4cee-b33e-5319b33b15b8
