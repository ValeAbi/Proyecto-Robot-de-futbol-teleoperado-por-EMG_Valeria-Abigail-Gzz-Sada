import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

# ==========================================
# 1. DEFINICIÓN DE VARIABLES (ANTECEDENTES)
# ==========================================
# Universo de discurso: EMG de 0 a 4095 (12 bits)
emg_izq = ctrl.Antecedent(np.arange(0, 4096, 1), 'EMG_Izquierdo')
emg_der = ctrl.Antecedent(np.arange(0, 4096, 1), 'EMG_Derecho')

# Universo de discurso: Motor PWM de 0 a 100% (luego lo pasas a 65535)
motor_izq = ctrl.Consequent(np.arange(0, 101, 1), 'Motor_Izquierdo')
motor_der = ctrl.Consequent(np.arange(0, 101, 1), 'Motor_Derecho')

# ==========================================
# 2. FUNCIONES DE MEMBRESÍA (5 NIVELES)
# ==========================================
# Para lograr 25 reglas (5x5), definimos 5 estados de fuerza:
# 1. Reposo (Ruido)
# 2. Muy Leve
# 3. Normal
# 4. Fuerte
# 5. Hulk (Saturación)

# --- ENTRADAS (EMG) ---
names_emg = ['Reposo', 'MuyBaja', 'Media', 'Alta', 'Hulk']

# Usamos automf para generar 5 niveles equidistantes o personalizados
# Aquí los personalizo para que coincidan con tu hardware real
for sensor in [emg_izq, emg_der]:
    sensor['Reposo']  = fuzz.trapmf(sensor.universe, [0, 0, 800, 1200])
    sensor['MuyBaja'] = fuzz.trimf(sensor.universe, [1000, 1500, 2000])
    sensor['Media']   = fuzz.trimf(sensor.universe, [1800, 2500, 3200])
    sensor['Alta']    = fuzz.trimf(sensor.universe, [3000, 3500, 4000])
    sensor['Hulk']    = fuzz.trapmf(sensor.universe, [3800, 4096, 4096, 4100])

# --- SALIDAS (MOTORES) ---
names_motor = ['Paro', 'Lento', 'Crucero', 'Rapido', 'Turbo']
for motor in [motor_izq, motor_der]:
    motor['Paro']    = fuzz.trapmf(motor.universe, [0, 0, 10, 20])
    motor['Lento']   = fuzz.trimf(motor.universe, [15, 30, 45])
    motor['Crucero'] = fuzz.trimf(motor.universe, [40, 55, 70])
    motor['Rapido']  = fuzz.trimf(motor.universe, [65, 80, 95])
    motor['Turbo']   = fuzz.trapmf(motor.universe, [90, 100, 100, 100])

# Visualizar las funciones de membresía (Opcional, descomentar para ver)
emg_izq.view()
motor_izq.view()

# ==========================================
# 3. BASE DE REGLAS (25 REGLAS)
# ==========================================
# Lógica de Tanque: 
# Si EMG Izq es ALTA -> Motor Izq es RÁPIDO.
# Si EMG Der es BAJA -> Motor Der es LENTO (Esto provoca un giro).

reglas = []

# Matriz de decisión 5x5
# Recorremos cada nivel del sensor izquierdo y derecho
# Niveles: Reposo(0), MuyBaja(1), Media(2), Alta(3), Hulk(4)
# Salidas correspondientes a la lógica de movimiento directo

# Mapeo simple: La salida sigue a la entrada directa (Control Proporcional Difuso)
mis_niveles_emg = [emg_izq['Reposo'], emg_izq['MuyBaja'], emg_izq['Media'], emg_izq['Alta'], emg_izq['Hulk']]
mis_niveles_der = [emg_der['Reposo'], emg_der['MuyBaja'], emg_der['Media'], emg_der['Alta'], emg_der['Hulk']]

salidas_motor = ['Paro', 'Lento', 'Crucero', 'Rapido', 'Turbo']

idx = 1
for i, estado_izq in enumerate(mis_niveles_emg):
    for j, estado_der in enumerate(mis_niveles_der):
        
        # El motor izquierdo reacciona a la fuerza izquierda
        out_izq = motor_izq[salidas_motor[i]]
        
        # El motor derecho reacciona a la fuerza derecha
        out_der = motor_der[salidas_motor[j]]
        
        # Creamos la regla
        regla = ctrl.Rule(estado_izq & estado_der, (out_izq, out_der))
        reglas.append(regla)
        print(f"Regla {idx}: Si Izq={names_emg[i]} y Der={names_emg[j]} -> M_Izq={salidas_motor[i]}, M_Der={salidas_motor[j]}")
        idx += 1

# ==========================================
# 4. SISTEMA DE CONTROL Y SIMULACIÓN
# ==========================================
sistema_control = ctrl.ControlSystem(reglas)
simulacion = ctrl.ControlSystemSimulation(sistema_control)

# ==========================================
# 5. PRUEBA DE CASOS (SIMULACIÓN NUMÉRICA)
# ==========================================
print("\n--- PRUEBA DE ESCRITORIO ---")
# Caso 1: Avanzar Recto (Ambos fuerza media)
simulacion.input['EMG_Izquierdo'] = 2500
simulacion.input['EMG_Derecho'] = 2500
simulacion.compute()
print(f"Entrada(2500, 2500) -> Motor Izq: {simulacion.output['Motor_Izquierdo']:.2f}%, Motor Der: {simulacion.output['Motor_Derecho']:.2f}%")

# Caso 2: Girar a la Derecha (Izquierda fuerte, Derecha relajada)
simulacion.input['EMG_Izquierdo'] = 3800 # Hulk
simulacion.input['EMG_Derecho'] = 1000   # Reposo
simulacion.compute()
print(f"Entrada(3800, 1000) -> Motor Izq: {simulacion.output['Motor_Izquierdo']:.2f}%, Motor Der: {simulacion.output['Motor_Derecho']:.2f}%")

# ==========================================
# 6. GENERACIÓN DE GRÁFICAS 3D (Surface Plot)
# ==========================================
# Generamos datos para la superficie
x_vals = np.linspace(0, 4096, 50) # Rango EMG Izq
y_vals = np.linspace(0, 4096, 50) # Rango EMG Der
X, Y = np.meshgrid(x_vals, y_vals)
Z_izq = np.zeros_like(X)
Z_der = np.zeros_like(X)

print("\nGenerando superficie de control 3D (esto puede tardar unos segundos)...")

for i in range(50):
    for j in range(50):
        simulacion.input['EMG_Izquierdo'] = X[i, j]
        simulacion.input['EMG_Derecho'] = Y[i, j]
        simulacion.compute()
        Z_izq[i, j] = simulacion.output['Motor_Izquierdo']
        Z_der[i, j] = simulacion.output['Motor_Derecho']

# Plotting
fig = plt.figure(figsize=(14, 6))

# Subplot 1: Motor Izquierdo
ax1 = fig.add_subplot(1, 2, 1, projection='3d')
surf1 = ax1.plot_surface(X, Y, Z_izq, cmap='viridis', linewidth=0, antialiased=True)
ax1.set_title('Superficie de Control: Motor Izquierdo')
ax1.set_xlabel('EMG Izquierdo')
ax1.set_ylabel('EMG Derecho')
ax1.set_zlabel('Velocidad Motor Izq (%)')

# Subplot 2: Motor Derecho
ax2 = fig.add_subplot(1, 2, 2, projection='3d')
surf2 = ax2.plot_surface(X, Y, Z_der, cmap='plasma', linewidth=0, antialiased=True)
ax2.set_title('Superficie de Control: Motor Derecho')
ax2.set_xlabel('EMG Izquierdo')
ax2.set_ylabel('EMG Derecho')
ax2.set_zlabel('Velocidad Motor Der (%)')

plt.show()