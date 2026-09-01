import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

# ==========================================
# 1. DEFINICIÓN DE VARIABLES
# ==========================================
emg_izq = ctrl.Antecedent(np.arange(0, 4096, 1), 'EMG_Izquierdo')
emg_der = ctrl.Antecedent(np.arange(0, 4096, 1), 'EMG_Derecho')
motor_izq = ctrl.Consequent(np.arange(0, 101, 1), 'Motor_Izquierdo')
motor_der = ctrl.Consequent(np.arange(0, 101, 1), 'Motor_Derecho')

# ==========================================
# 2. FUNCIONES DE MEMBRESÍA
# ==========================================
# Sensores
for sensor in [emg_izq, emg_der]:
    sensor['Reposo']  = fuzz.trapmf(sensor.universe, [0, 0, 800, 1200])
    sensor['MuyBaja'] = fuzz.trimf(sensor.universe, [1000, 1500, 2000])
    sensor['Media']   = fuzz.trimf(sensor.universe, [1800, 2500, 3200])
    sensor['Alta']    = fuzz.trimf(sensor.universe, [3000, 3500, 4000])
    sensor['Hulk']    = fuzz.trapmf(sensor.universe, [3800, 4096, 4096, 4100])

# Motores
salidas_motor = ['Paro', 'Lento', 'Crucero', 'Rapido', 'Turbo']
for motor in [motor_izq, motor_der]:
    motor['Paro']    = fuzz.trapmf(motor.universe, [0, 0, 10, 20])
    motor['Lento']   = fuzz.trimf(motor.universe, [15, 30, 45])
    motor['Crucero'] = fuzz.trimf(motor.universe, [40, 55, 70])
    motor['Rapido']  = fuzz.trimf(motor.universe, [65, 80, 95])
    motor['Turbo']   = fuzz.trapmf(motor.universe, [90, 100, 100, 100])

# ==========================================
# 3. BASE DE REGLAS
# ==========================================
reglas = []
mis_niveles_emg = [emg_izq['Reposo'], emg_izq['MuyBaja'], emg_izq['Media'], emg_izq['Alta'], emg_izq['Hulk']]
mis_niveles_der = [emg_der['Reposo'], emg_der['MuyBaja'], emg_der['Media'], emg_der['Alta'], emg_der['Hulk']]
nombres_salida = ['Paro', 'Lento', 'Crucero', 'Rapido', 'Turbo']

for i, estado_izq in enumerate(mis_niveles_emg):
    for j, estado_der in enumerate(mis_niveles_der):
        out_izq = motor_izq[nombres_salida[i]]
        out_der = motor_der[nombres_salida[j]]
        regla = ctrl.Rule(estado_izq & estado_der, (out_izq, out_der))
        reglas.append(regla)

sistema_control = ctrl.ControlSystem(reglas)
simulacion = ctrl.ControlSystemSimulation(sistema_control)

# ==========================================
# 4. CONFIGURAR LA PRUEBA (Simulación)
# ==========================================
# CAMBIA ESTOS VALORES para obtener la gráfica que necesitas copiar
val_izq = 3800  # Ejemplo: Hulk
val_der = 1500  # Ejemplo: MuyBaja

simulacion.input['EMG_Izquierdo'] = val_izq
simulacion.input['EMG_Derecho'] = val_der

# Calculamos
simulacion.compute()
print(f"Resultados -> MI: {simulacion.output['Motor_Izquierdo']:.2f}%, MD: {simulacion.output['Motor_Derecho']:.2f}%")

# ==========================================
# 5. GENERAR GRÁFICAS 2D (Resultado)
# ==========================================
# Esta es la parte que genera la imagen que subiste, pero con el resultado relleno

# Gráfica Motor Izquierdo
motor_izq.view(sim=simulacion)
fig1 = plt.gcf()
fig1.canvas.manager.set_window_title(f'Resultado Motor IZQ (Entrada: {val_izq})')

# Gráfica Motor Derecho
motor_der.view(sim=simulacion)
fig2 = plt.gcf()
fig2.canvas.manager.set_window_title(f'Resultado Motor DER (Entrada: {val_der})')

# Bloquear para que no se cierren
plt.show(block=True)