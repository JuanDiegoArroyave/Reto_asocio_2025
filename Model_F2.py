from Funciones import *
import pyomo
from pyomo.environ import *
from pyomo.opt import SolverFactory

# Usar cbc como optimizador
solver = SolverFactory('cbc', executable='Optimizer\\Cbc-releases.2.10.12-windows-2022-msvs-v17-Release-x64\\bin\\cbc.exe')

# Ruta de la instancia JSON
instancia = 'instances\\instance10.json'

# Llamar a la función para importar datos
E, D, T, G, Z, dz, dr, e_g, di, max, min = importar_data(instancia, imprimir=False)

model = ConcreteModel(name='Colaboradores')
model.X = Var(E, D, T, Z, within=Binary, initialize = 0) # Si el colaborador e en el escritorio d asiste el dia d en la zona z
model.Y = Var(E, T, within=Binary, initialize = 0) # Si el colaborador e asiste el dia t
model.Z = Var(G, T, within=Binary, initialize = 0) # Si el grupo g tiene primario el dia t

# Funcion objetivo: Maximizar la satisfacción de los empleados
def satisfaccion_rule(model):
    return sum(
        model.X[e,d,t,z] * int(t in di[e])
        for e in E
        for d in D
        for t in T
        for z in Z
    )
model.satisfaccion = Objective(rule=satisfaccion_rule, sense=maximize)

#RESTRICCIONES
# Relación [X] con variable auxiliar Y
def dias_presencialidad(model, e, t):
  return sum(model.X[e, d, t, z] for d in D for z in Z) == model.Y[e, t]
model.dias_presencialidad = Constraint(E, T, rule=dias_presencialidad)

# Días de presencialidad en el rango
def dias_min(model, e):
  return sum(model.Y[e, t] for t in T) >= min
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

# Un escritorio solo se le puede asignar a una persona
def escritorio_unico(model, d, t):
    return sum(model.X[e, d, t, z] for e in E if d in dr[e] for z in Z if d in dz[z]) <= 1
model.escritorio_unico = Constraint(D, T, rule=escritorio_unico)

# No se debe asignar escritorios que no estan en esa zona #############################################
def no_esta_en_zona(model, e, d, t, z):
  return model.X[e, d, t, z] <= int((d in dz[z]))
model.no_esta_en_zona = Constraint(E, D, T, Z, rule=no_esta_en_zona)

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

# Establecer límite de tiempo en segundos
solver.options['seconds'] = 300

# Establecer tolerancia de optimalidad
solver.options['ratio'] = 0.01  # 1% de tolerancia de optimalidad
# Criterios de parada: tiempo máximo (en segundos) y tolerancia de optimalidad
solver.solve(
    model,
    tee=True,  # Muestra el log del solver
)

# Imprimir resultados de la FO
print(f"Valor de la función objetivo (Satisfacción): {model.satisfaccion()}")

df_resumen = resumen(E, D, T, Z, model, di, e_g)

df_reuniones = reuniones(G, T, model, e_g, D, Z)

df_programacion_primario = programacion_primario(model, G, T, e_g, D, Z)

df_programacion = programacion(model, E, D, T, Z, e_g)

preferencias(model, E, T, di)
