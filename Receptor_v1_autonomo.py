import network
import socket
import machine
import time
from machine import Pin, PWM

# ============================================================================
# 1. CONFIGURACIÓN HARDWARE
# ============================================================================
led = Pin(2, Pin.OUT)

# Motores (Ajusta pines si es necesario)
m1_in1 = PWM(Pin(19), freq=1000)
m1_in2 = PWM(Pin(18), freq=1000)
m2_in1 = PWM(Pin(23), freq=1000)
m2_in2 = PWM(Pin(22), freq=1000)

# AJUSTE DE PISO (Potencia mínima)
MIN_PWM = 450 

# ============================================================================
# 2. FUNCIONES DE MOTORES
# ============================================================================
def parar():
    """Detiene todos los motores inmediatamente"""
    m1_in1.duty(0); m1_in2.duty(0)
    m2_in1.duty(0); m2_in2.duty(0)

def motor_izq(pwm, adelante):
    if adelante:
        m1_in1.duty(pwm); m1_in2.duty(0)
    else:
        m1_in1.duty(0); m1_in2.duty(pwm)

def motor_der(pwm, adelante):
    if adelante:
        m2_in1.duty(pwm); m2_in2.duty(0)
    else:
        m2_in1.duty(0); m2_in2.duty(pwm)

def mapear_pwm(valor_entrada, in_min, in_max):
    """Escala un rango de entrada (ej 15-40) al rango PWM del motor"""
    if valor_entrada < in_min: return MIN_PWM
    if valor_entrada > in_max: return 1023
    
    rango_in = in_max - in_min
    rango_out = 1023 - MIN_PWM
    pwm = int(((valor_entrada - in_min) * rango_out / rango_in) + MIN_PWM)
    return pwm

# ============================================================================
# 3. LÓGICA DE MOVIMIENTO (ZONAS)
# ============================================================================
def procesar_movimiento(izq, der):
    promedio = (izq + der) / 2
    diferencia = izq - der
    
    # --- ZONA MUERTA (Reposo) ---
    if izq < 12 and der < 12:
        parar()
        led.value(0)
        return

    # --- PRIORIDAD 1: GIROS (Asimetría) ---
    if abs(diferencia) > 25:
        fuerza_giro = max(izq, der)
        pwm_giro = mapear_pwm(fuerza_giro, 15, 100)
        
        if diferencia > 0: # Izquierda gana -> Giro Izq
            motor_izq(pwm_giro, False) 
            motor_der(pwm_giro, True)
        else:              # Derecha gana -> Giro Der
            motor_izq(pwm_giro, True)
            motor_der(pwm_giro, False)
        led.value(1)
        return

    # --- PRIORIDAD 2: AVANCE / REVERSA ---
    # REVERSA (Suave 15-40%)
    if 15 <= promedio <= 40:
        pwm = mapear_pwm(promedio, 15, 40)
        motor_izq(pwm, False)
        motor_der(pwm, False)
        # Parpadeo rápido
        if (time.ticks_ms() % 200) < 100: led.value(1)
        else: led.value(0)
        
    # ZONA SEGURIDAD (Hueco 41-49%)
    elif 40 < promedio < 50:
        parar()
        led.value(0)

    # ADELANTE (Fuerte 50-100%)
    elif promedio >= 50:
        pwm = mapear_pwm(promedio, 50, 100)
        motor_izq(pwm, True)
        motor_der(pwm, True)
        led.value(1)

# ============================================================================
# 4. LOOP PRINCIPAL CON ESCAPE (Ctrl+C)
# ============================================================================
# Configuración WiFi
AP_SSID = "EMG_CAR"
AP_PASS = "12345678"
UDP_PORT = 5005

try:
    # Inicio WiFi
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASS, authmode=3)
    
    # Inicio Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    sock.settimeout(0.1)

    print("--- SISTEMA LISTO ---")
    print("Para salir de forma segura, presiona Ctrl+C en Thonny")
    parar()

    # BUCLE INFINITO
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            mensaje = data.decode().strip()
            partes = mensaje.split(',')
            
            if len(partes) == 2:
                f_izq = int(partes[0])
                f_der = int(partes[1])
                procesar_movimiento(f_izq, f_der)
                
        except OSError:
            parar() # Timeout: parar por seguridad
        except ValueError:
            pass

except KeyboardInterrupt:
    # --- AQUÍ ENTRA CUANDO PRESIONAS CTRL+C ---
    parar()
    led.value(0)
    print("\n!!! PROGRAMA DETENIDO POR USUARIO !!!")
    print("Motores apagados correctamente.")