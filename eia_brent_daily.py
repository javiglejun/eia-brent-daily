import pandas as pd
import requests
from io import BytesIO
from datetime import datetime

URL = "https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls"

# Descargar archivo
r = requests.get(URL)
xls = pd.ExcelFile(BytesIO(r.content))

# Leer hoja
df = pd.read_excel(xls, sheet_name=0, skiprows=2)

# Limpiar columnas
df = df.rename(columns={
    "Week Of": "week",
    "Mon": "Mon",
    "Tue": "Tue",
    "Wed": "Wed",
    "Thu": "Thu",
    "Fri": "Fri"
})

# Convertir a formato largo
df = df.melt(id_vars=["week"], var_name="day", value_name="price")

# Eliminar nulos
df = df.dropna()

# Convertir fechas (simplificado)
df["date"] = pd.to_datetime(df["week"])

# Guardar CSV limpio
df[["date","price"]].to_csv("eia_brent.csv", index=False)

print("CSV actualizado")
