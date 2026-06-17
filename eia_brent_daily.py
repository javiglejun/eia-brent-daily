import pandas as pd
import requests
from io import BytesIO

URL = "https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls"

# 1) Descargar el fichero
response = requests.get(URL, timeout=60)
response.raise_for_status()

excel_file = BytesIO(response.content)

# 2) Leer la hoja correcta usando la fila 2 como cabecera real
df = pd.read_excel(
    excel_file,
    sheet_name="Data 1",
    header=2,
    engine="xlrd"
)

# 3) Renombrar columnas a nombres simples
df.columns = [str(col).strip() for col in df.columns]

df = df.rename(columns={
    "Date": "date",
    "Europe Brent Spot Price FOB (Dollars per Barrel)": "price"
})

# 4) Quedarse solo con las columnas útiles
df = df[["date", "price"]].copy()

# 5) Limpiar nulos
df = df.dropna(subset=["date", "price"])

# 6) Asegurar tipos
df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
df["price"] = pd.to_numeric(df["price"], errors="coerce")

df = df.dropna(subset=["date", "price"])

# 7) Ordenar por fecha
df = df.sort_values("date").reset_index(drop=True)

# 8) Guardar a CSV
df.to_csv("eia_brent.csv", index=False, encoding="utf-8")

print("CSV actualizado correctamente")
print(df.tail())
