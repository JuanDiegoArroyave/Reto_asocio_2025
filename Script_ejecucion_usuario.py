from Funciones_modelos import *

preferencias_satisfechas, porcentaje = resolver_modelo_F2('instance1', 300)

df_programacion = resolver_modelo_F1('instance1', (porcentaje/100), porcentaje, preferencias_satisfechas, 300)

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# Asegurarse de que los días están estandarizados
df_programacion["Día"] = df_programacion["Día"].str.strip().str.capitalize()

# Crear carpeta para guardar los gráficos
carpeta_graficos = "graficos_programacion"
os.makedirs(carpeta_graficos, exist_ok=True)

# Definir orden deseado de los días
orden_dias = ["L", "Ma", "Mi", "J", "V"]

# Inicializar el escritor de Excel
excel_filename = "programacion_completa.xls"
excel_writer = pd.ExcelWriter("programacion_completa.xlsx", engine="openpyxl")

# Recorrer los días en el orden deseado
for dia in orden_dias:
    df_dia = df_programacion[df_programacion["Día"] == dia]

    if df_dia.empty:
        continue  # Saltar si no hay datos para ese día

    # --- Guardar hoja en Excel ---
    df_dia.to_excel(excel_writer, sheet_name=dia, index=False)

    # --- Crear gráfico ---
    pivot_table = df_dia.pivot_table(index="Empleado", columns="Escritorio", values="Zona", aggfunc='first')

    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_table.isna(), cbar=False, cmap="Greys", linewidths=0.5, linecolor='gray')

    # Anotar zonas dentro del heatmap
    for i, row in enumerate(pivot_table.index):
        for j, col in enumerate(pivot_table.columns):
            value = pivot_table.loc[row, col]
            if pd.notna(value):
                plt.text(j + 0.5, i + 0.5, value, ha='center', va='center', fontsize=8)

    plt.title(f"Asignaciones - Día: {dia}")
    plt.xlabel("Escritorio")
    plt.ylabel("Empleado")
    plt.tight_layout()

    # Guardar imagen en carpeta
    ruta_guardado = os.path.join(carpeta_graficos, f"programacion_dia_{dia}.png")
    plt.savefig(ruta_guardado)
    plt.close()

# Guardar el archivo Excel
excel_writer.close()