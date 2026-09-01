import network
import socket
import time
from machine import Pin, ADC

# ============================================================================
# 1. CONFIGURACIÓN WIFI (CLIENTE)
# ============================================================================
SSID_CARRO = "EMG_CAR"
PASS_CARRO = "12345678"
DEST_IP    = "192.168.4.1"
DEST_PORT  = 5005

led = Pin(2, Pin.OUT)
led.value(0) # Empezamos apagado

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID_CARRO, PASS_CARRO)

print("--- INICIANDO EMISOR ---")
print("Conectando al WiFi del Carro...")
timeout = 0
while not wlan.isconnected() and timeout < 10:
    led.value(1); time.sleep(0.2); led.value(0); time.sleep(0.2)
    timeout += 1
    print(".", end="")

print("") # Salto de linea
if wlan.isconnected():
    print(f"¡CONECTADO! IP Emisor: {wlan.ifconfig()[0]}")
    led.value(1) # Led fijo = Conectado
else:
    print("ADVERTENCIA: No se pudo conectar. Revisar si el Carro está encendido.")
    # No detenemos el código para permitir probar la lectura de sensores offline

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ============================================================================
# 2. MOTOR DE LÓGICA DIFUSA (CLASE OPTIMIZADA)
# ============================================================================
def trimf(x, a, b, c):
    if x <= a or x >= c: return 0.0
    if x == b: return 1.0
    if x < b: return (x - a) / (b - a)
    return (c - x) / (c - b)

def trapmf(x, a, b, c, d):
    if x <= a or x >= d: return 0.0
    if b <= x <= c: return 1.0
    if x < b: return (x - a) / (b - a)
    return (d - x) / (d - c)

class FuzzyEMG:
    def __init__(self, pin_adc, pin_lo_p, pin_lo_n, nombre):
        # Configuración Sensor
        self.adc = ADC(Pin(pin_adc))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)
        
        # Pines Leads Off (Desconexión)
        self.lo_plus = Pin(pin_lo_p, Pin.IN)
        self.lo_minus = Pin(pin_lo_n, Pin.IN)
        
        self.nombre = nombre
        
        # Variables Fuzzy
        self.min_val = 4095
        self.max_val = 0
        self.lectura_anterior = 0
        self.debug_norm = 0 # Variable nueva para visualizar en Thonny
        
    def leer_sensor(self):
        # Si detecta cable suelto, retorna 0
        if self.lo_plus.value() == 1 or self.lo_minus.value() == 1:
            return 0 
        return self.adc.read()

    def calibrar(self):
        val = self.leer_sensor()
        if val < self.min_val: self.min_val = val
        if val > self.max_val: self.max_val = val
        if self.max_val == self.min_val: self.max_val = self.min_val + 100

    def procesar_fuzzy(self):
        # 1. Leer y Normalizar (0 a 100)
        raw = self.leer_sensor()
        
        # Seguridad desconexión
        if raw == 0 and (self.lo_plus.value() == 1 or self.lo_minus.value() == 1):
            self.debug_norm = 0
            return 0
            
        norm = ((raw - self.min_val) / (self.max_val - self.min_val)) * 100
        norm = max(0, min(100, norm))
        self.debug_norm = norm # Guardamos para el print del plotter
        
        # 2. Calcular Derivada (Velocidad de cambio)
        delta = norm - self.lectura_anterior
        self.lectura_anterior = norm
        
        # 3. Fuzzificar Entradas
        mu_amp = {
            'MB': trapmf(norm, -1, 0, 10, 25),
            'B':  trimf(norm, 10, 30, 50),
            'M':  trimf(norm, 30, 50, 70),
            'A':  trimf(norm, 50, 70, 90),
            'MA': trapmf(norm, 75, 90, 100, 101)
        }
        mu_delta = {
            'NB': trapmf(delta, -100, -50, -30, -15),
            'NS': trimf(delta, -30, -15, 0),
            'Z':  trimf(delta, -15, 0, 15),
            'PS': trimf(delta, 0, 15, 30),
            'PB': trapmf(delta, 15, 30, 50, 100)
        }

        # 4. Inferencia (25 Reglas Compactas)
        reglas = []
        # Fila MB (Muy Bajo)
        reglas.append((min(mu_amp['MB'], mu_delta['NB']), 0)); reglas.append((min(mu_amp['MB'], mu_delta['NS']), 0))
        reglas.append((min(mu_amp['MB'], mu_delta['Z']),  0)); reglas.append((min(mu_amp['MB'], mu_delta['PS']), 10))
        reglas.append((min(mu_amp['MB'], mu_delta['PB']), 20))
        # Fila B (Bajo)
        reglas.append((min(mu_amp['B'], mu_delta['NB']), 0));  reglas.append((min(mu_amp['B'], mu_delta['NS']), 10))
        reglas.append((min(mu_amp['B'], mu_delta['Z']),  25)); reglas.append((min(mu_amp['B'], mu_delta['PS']), 35))
        reglas.append((min(mu_amp['B'], mu_delta['PB']), 45))
        # Fila M (Medio)
        reglas.append((min(mu_amp['M'], mu_delta['NB']), 25)); reglas.append((min(mu_amp['M'], mu_delta['NS']), 35))
        reglas.append((min(mu_amp['M'], mu_delta['Z']),  50)); reglas.append((min(mu_amp['M'], mu_delta['PS']), 60))
        reglas.append((min(mu_amp['M'], mu_delta['PB']), 70))
        # Fila A (Alto)
        reglas.append((min(mu_amp['A'], mu_delta['NB']), 50)); reglas.append((min(mu_amp['A'], mu_delta['NS']), 60))
        reglas.append((min(mu_amp['A'], mu_delta['Z']),  75)); reglas.append((min(mu_amp['A'], mu_delta['PS']), 85))
        reglas.append((min(mu_amp['A'], mu_delta['PB']), 90))
        # Fila MA (Muy Alto)
        reglas.append((min(mu_amp['MA'], mu_delta['NB']), 70)); reglas.append((min(mu_amp['MA'], mu_delta['NS']), 80))
        reglas.append((min(mu_amp['MA'], mu_delta['Z']), 100)); reglas.append((min(mu_amp['MA'], mu_delta['PS']), 100))
        reglas.append((min(mu_amp['MA'], mu_delta['PB']), 100))

        # 5. Defuzzificación (Centroide)
        num = 0; den = 0
        for disparo, val_salida in reglas:
            num += disparo * val_salida
            den += disparo
            
        if den == 0: return 0
        return int(num / den)

# ============================================================================
# 3. OBJETOS Y CALIBRACIÓN
# ============================================================================
brazo_izq = FuzzyEMG(36, 4, 14, "Izquierdo") # ADC 36
brazo_der = FuzzyEMG(39, 16, 17, "Derecho")  # ADC 39

print("--- CALIBRACIÓN (5s) ---")
print("INSTRUCCIÓN: Contrae y relaja AMBOS brazos fuertemente.")
start_time = time.time()
while (time.time() - start_time) < 5:
    led.value(not led.value()) # Parpadeo rápido
    brazo_izq.calibrar()
    brazo_der.calibrar()
    time.sleep_ms(10)
    
led.value(1) # Listo
print(f"Rango Izq: {brazo_izq.min_val}-{brazo_izq.max_val}")
print(f"Rango Der: {brazo_der.min_val}-{brazo_der.max_val}")
print("--- TRANSMITIENDO ---")
print("Leyenda Plotter: L_In=Entrada Izq, L_Out=Salida Izq, R_In=Entrada Der, R_Out=Salida Der")

# ============================================================================
# 4. BUCLE PRINCIPAL (CON ESCAPE)
# ============================================================================
try:
    while True:
        # 1. Procesamiento Difuso
        vel_izq = brazo_izq.procesar_fuzzy()
        vel_der = brazo_der.procesar_fuzzy()
        
        # 2. VISUALIZACIÓN MEJORADA (Para Thonny Plotter)
        # Mostramos Entrada (debug_norm) vs Salida (vel) para ver la relación
        # Formato: "Variable:Valor,Variable:Valor..."
        # L_In = Left Input (Fuerza tuya), L_Out = Left Output (Lo que va al motor)
        print(f"L_In:{int(brazo_izq.debug_norm)},L_Out:{vel_izq},R_In:{int(brazo_der.debug_norm)},R_Out:{vel_der}")
        
        # 3. Enviar Datos
        mensaje = "{},{}".format(vel_izq, vel_der)
        
        try:
            sock.sendto(mensaje.encode(), (DEST_IP, DEST_PORT))
        except:
            pass # Ignoramos errores de red puntuales
            
        time.sleep_ms(50) # 20 Hz

except KeyboardInterrupt:
    print("\n--- DETENIDO POR USUARIO (Ctrl+C) ---")
    led.value(0)
    sock.close()