import pandas as pd
import requests
from io import BytesIO
import re

URL = "https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls"

# ----------------------------
# 1. Descargar el fichero
# ----------------------------
response = requests.get(URL, timeout=60)
response.raise_for_status()

excel_file = BytesIO(response.content)

# ----------------------------
# 2. Leer sin asumir cabecera
# ----------------------------
raw = pd.read_excel(excel_file, sheet_name=0, header=None, engine="xlrd")

# ----------------------------
# 3. Buscar la fila donde está la cabecera real
# ----------------------------
header_row = None

for i in range(min(30, len(raw))):
    row_values = [str(x).strip() for x in raw.iloc[i].tolist()]
    row_text = " | ".join(row_values)

    if "Week Of" in row_text and any(day in row_text for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]):
        header_row = i
        break

if header_row is None:
    raise Exception("No se ha encontrado la fila de cabecera con 'Week Of', 'Mon', 'Tue', etc.")

# ----------------------------
# 4. Volver a leer usando esa fila como cabecera
# ----------------------------
df = pd.read_excel(excel_file, sheet_name=0, header=header_row, engine="xlrd")

# Limpiar nombres de columnas
df.columns = [str(col).strip() for col in df.columns]

# ----------------------------
# 5. Detectar la columna de semana
# ----------------------------
week_col = None
for col in df.columns:
    if "Week Of" in str(col):
        week_col = col
        break

if week_col is None:
    raise Exception(f"No se encontró columna 'Week Of'. Columnas detectadas: {list(df.columns)}")

# ----------------------------
# 6. Detectar columnas de días
# ----------------------------
day_cols = []
for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
    for col in df.columns:
        if day == str(col).strip():
            day_cols.append(col)

if not day_cols:
    raise Exception(f"No se encontraron columnas Mon/Tue/Wed/Thu/Fri. Columnas detectadas: {list(df.columns)}")

# ----------------------------
# 7. Quedarse solo con las columnas útiles
# ----------------------------
df = df[[week_col] + day_cols].copy()

# Renombrar
rename_dict = {week_col: "week"}
for col in day_cols:
    rename_dict[col] = str(col).strip()

df = df.rename(columns=rename_dict)

# Eliminar filas vacías
df = df.dropna(subset=["week"], how="all")

# ----------------------------
# 8. Pasar a formato largo
# ----------------------------
df_long = df.melt(
    id_vars=["week"],
    value_vars=[c for c in ["Mon", "Tue", "Wed", "Thu", "Fri"] if c in df.columns],
    var_name="day",
    value_name="price"
)

# Eliminar nulos
df_long = df_long.dropna(subset=["price"])

# ----------------------------
# 9. Convertir la fecha de la semana
# ----------------------------
def parse_week_date(value):
    """
    Intenta extraer una fecha tipo '1987 May-18 to May-22'
    y se queda con el primer día.
    """
    text = str(value).strip()

    match = re.match(r"(\d{4})\s+([A-Za-z]{3})-(\d{1,2})", text)
    if match:
        year, month, day = match.groups()
        return pd.to_datetime(f"{year}-{month}-{day}", format="%Y-%b-%d", errors="coerce")

    return pd.NaT

df_long["week_start"] = df_long["week"].apply(parse_week_date)

# Offset según día
offset_map = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4
}

df_long["date"] = df_long.apply(
    lambda row: row["week_start"] + pd.Timedelta(days=offset_map.get(row["day"], 0))
    if pd.notnull(row["week_start"]) else pd.NaT,
    axis=1
)

# ----------------------------
# 10. Limpiar y guardar
# ----------------------------
df_final = df_long[["date", "price"]].copy()
df_final = df_final.dropna(subset=["date", "price"])
df_final["date"] = pd.to_datetime(df_final["date"]).dt.date

df_final.to_csv("eia_brent.csv", index=False)

print("CSV actualizado correctamente")
print(df_final.tail())
