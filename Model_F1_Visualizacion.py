import pyomo
from pyomo.environ import *
from pyomo.opt import SolverFactory
from Funciones import *


# Usar cbc como optimizador
solver = SolverFactory('cbc', executable='Optimizer\\Cbc-releases.2.10.12-windows-2022-msvs-v17-Release-x64\\bin\\cbc.exe')

# Ruta de la instancia JSON
instancia = 'instances\\instance5.json'

# Llamar a la función para importar datos
E, D, T, G, Z, dz, dr, e_g, di, max, min = importar_data(instancia, imprimir=False)

model = ConcreteModel(name='Universidad')
model.X = Var(E, D, T, Z, within=Binary, initialize = 0) # Si el colaborador e en el escritorio d asiste el dia d en la zona z
model.Y = Var(E, T, within=Binary, initialize = 0) # Si el colaborador e asiste el dia t
model.Z = Var(G, T, within=Binary, initialize = 0) # Si el grupo g tiene primario el dia t
model.J = Var(G, T, within=NonNegativeIntegers, initialize = 0) # Cantidad de zonas en las que está presente integrantes de cada grupo
model.P = Var(G, Z, T, within = Binary, initialize = 0) # Si el grupo g tiene presencia (al menos un colaborador) en la zona z

# Variables para penalizacion
model.Penalizacion = Var(E, within=Binary, initialize=0) # 1 si el colaborador asiste 1 dia, 0 si asiste 2
model.Penalizacion2 = Var(G, Z, T, within=Binary, initialize=0) # 1 si del grupo g en la zona z el dia t hay un solo colaborador, 0 EOC

# def satisfaccion_rule(model):
#     return sum(
#         model.X[e,d,t,z] * int(t in di[e])
#         for e in E
#         for d in D
#         for t in T
#         for z in Z
#     )
# model.satisfaccion = Objective(rule=satisfaccion_rule, sense=maximize)

# Funcion objetivo
def distribucion_rule(model):
    return sum(model.J[g, t] for g in G for t in T) + sum(model.Penalizacion[e] for e in E) + sum(model.Penalizacion2[g, z, t] for g in G for z in Z for t in T)  # Minimizar la cantidad de zonas y penalizaciones
model.distribucion_rule = Objective(rule=distribucion_rule, sense=minimize)

#RESTRICCIONES
# Relación [X] con variable auxiliar Y
def dias_presencialidad(model, e, t):
  return sum(model.X[e, d, t, z] for d in D for z in Z) == model.Y[e, t]
model.dias_presencialidad = Constraint(E, T, rule=dias_presencialidad)

# Días de presencialidad en el rango
def dias_min(model, e):
  return sum(model.Y[e, t] for t in T) >= min - model.Penalizacion[e]
model.dias_min = Constraint(E, rule=dias_min)

def dias_max(model, e):
  return sum(model.Y[e, t] for t in T) <= max
model.dias_max = Constraint(E, rule=dias_max)

# Asignar solo un escritorio si va dicho dia
def solo_un_escritorio(model, e, t):
  return sum(model.X[e, d, t, z] for d in D for z in Z) <= 1
model.solo_un_escritorio = Constraint(E, T, rule=solo_un_escritorio)

# Cada colaborador debe estar en un escritorio de cumplas con sus caracteristicas
def colaborador_escritorio(model, e, d, t, z):
  return model.X[e, d, t, z] <= int((d in dr[e]))
model.colaborador_escritorio = Constraint(E, D, T, Z, rule=colaborador_escritorio)

###################################################################################################
# Un escritorio solo se le puede asignar a una persona
def escritorio_unico(model, d, t):
    return sum(model.X[e, d, t, z] for e in E if d in dr[e] for z in Z if d in dz[z]) <= 1
model.escritorio_unico = Constraint(D, T, rule=escritorio_unico)

# No se debe asignar escritorios que no estan en esa zona #############################################
def no_esta_en_zona(model, e, d, t, z):
  return model.X[e, d, t, z] <= int((d in dz[z]))
model.no_esta_en_zona = Constraint(E, D, T, Z, rule=no_esta_en_zona)
#######################################################################################################

# Cada grupo tiene grupo primario una vez
def grupo_primario(model, g):
  return sum(model.Z[g, t] for t in T) == 1
model.grupo_primario = Constraint(G, rule=grupo_primario)

# Los integrantes de cada grupo deben asistir al primario
def asistencia_en_reunion(model, e, t, g):
  if e in e_g[g]:
    return model.Y[e, t] >= model.Z[g, t]
  else:
    return Constraint.Skip
model.asistencia_en_reunion = Constraint(E, T, G, rule=asistencia_en_reunion)

# No debe estar una persona "Sola" (Sola = no hay más colaboradores de su mismo equipo) en una zona
def sola(model, z, g, t):
  return sum(model.X[e, d, t, z] for e in e_g[g] for d in dz[z]) >=  (model.P[g, z, t] * 2) - model.Penalizacion2[g, z, t]
model.sola = Constraint(Z, G, T, rule=sola)

def sola2(model, z, g, t):
  return sum(model.X[e, d, t, z] for e in e_g[g] for d in dz[z]) <=  model.P[g, z, t] * 10000000000
model.sola2 = Constraint(Z, G, T, rule=sola2)

# Relacionar las variables J y P
def relacion_J_P(model, g, t):
  return model.J[g, t] == sum(model.P[g, z, t] for z in Z)
model.relacion_J_P = Constraint(G, T, rule=relacion_J_P)

# Establecer límite de tiempo en segundos
solver.options['seconds'] = 3600

# Establecer tolerancia de optimalidad
solver.options['ratio'] = 0.01  # 1% de tolerancia de optimalidad
# Criterios de parada: tiempo máximo (en segundos) y tolerancia de optimalidad
solver.solve(
    model,
    tee=True,  # Muestra el log del solver
)

#########################################################################################

nombre_instancia = instancia.split('\\')[-1].split('.json')[0]

import pickle
# Exportar modelo en pickle
with open(f'Model_outputs\\model_{nombre_instancia}.pkl', 'wb') as f:
    pickle.dump(model, f)

# Guardar la hora actual
from datetime import datetime
hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Guardar la hora de finalización
with open(f'Model_outputs\\hora_finalizacion_{nombre_instancia}.txt', 'w') as f:
    f.write(hora_actual)


# del model
model = cargar_modelo(nombre_instancia)
#########################################################################################

import pandas as pd

print(value(model.distribucion_rule))

df_resumen = resumen(E, D, T, Z, model, di, e_g)

df_reuniones = reuniones(G, T, model, e_g, D, Z)

df_programacion_primario = programacion_primario(model, G, T, e_g, D, Z)

df_programacion = programacion(model, E, D, T, Z, e_g)

preferencias(model, E, T, di)

# Imprimir valores de penalizacion
print("Penalizaciones asociadas a que van un solo dia de la semana:")
for e in E:
    if model.Penalizacion[e].value > 0:
        print(f"Colaborador: {e} | grupo: {next((k for k, lista in e_g.items() if e in lista), None)}")

print("\nPenalizaciones asociadas a que un grupo tiene un solo colaborador en una zona:")
# Imprimir valores de penalizacion2
for g in G:
    for z in Z:
        for t in T:
            if model.Penalizacion2[g, z, t].value > 0:
                print(f"Grupo {g} en zona {z} el día {t} tiene penalización un colaborador solo")


# df_programacion['Empleado']
# df_programacion['Escritorio']

# for i in range(len(df_programacion['Escritorio'])):
#    if list(df_programacion['Escritorio'])[i] not in dr[list(df_programacion['Empleado'])[i]]:
#        print(f"Error: El escritorio {list(df_programacion['Escritorio'])[i]} no es válido para el empleado {list(df_programacion['Empleado'])[i]}")

#########################################################################################
#visualización 

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
