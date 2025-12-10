import time 
import math 
import re # Ya no es necesario, lo elimino
import struct 
import random 

# Pines (ejemplo para Raspberry Pi, si se usaran pines GPIO reales)
print("¡Hola desde mi ESP32 con MicroPython!")
print("Este es un mensaje de prueba.")
ENA = 14
ENB = 32
IN1 = 27
IN2 = 26
IN3 = 25
IN4 = 33

# Simulación de las funciones matemáticas de Arduino
def constrain(val, min_val, max_val):
    """Implementa la función constrain de Arduino."""
    return min(max_val, max(min_val, val))

def map_range(x, in_min, in_max, out_min, out_max):
    """Implementa la función map de Arduino."""
    # Uso // para forzar división entera como hace el map de Arduino
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def set_motor(pwm_pin, dir_pin1, dir_pin2, speed):
    """
    Función conceptual para controlar un motor en Python.
    En un entorno real (ej. Raspberry Pi), aquí usarías librerías como
    RPi.GPIO o pigpio para controlar los pines y el PWM.
    """
    # Imprimimos la acción en lugar de ejecutarla físicamente
    if speed > 0:
        # Forward move
        print(f"Motor: HIGH={dir_pin1}, LOW={dir_pin2}, PWM={speed} (Adelante)")
    elif speed < 0:
        # Backward move
        print(f"Motor: LOW={dir_pin1}, HIGH={dir_pin2}, PWM={-speed} (Atrás)")
    else:
        # Stop motor
        print(f"Motor: LOW={dir_pin1} y {dir_pin2}, PWM=0 (Detenido)")

def drive_motors(x, y):
    """
    Traduce la lógica de control de joystick de Arduino a Python.
    """
    # Deadzone (zona muerta) para evitar jitter
    deadzone = 100
    if abs(x) < deadzone:
        x = 0
    if abs(y) < deadzone:
        y = 0

    # Calcular velocidades de motor [-255..255]
    motorA = y + x
    motorB = y - x

    # Limitar a los rangos de entrada/salida definidos en el sketch original (-1000 a 1000)
    motorA = constrain(motorA, -1000, 1000)
    motorB = constrain(motorB, -1000, 1000)

    # Mapear de -1000..1000 a -255..255 (rango de PWM)
    motorA = map_range(motorA, -1000, 1000, -255, 255)
    motorB = map_range(motorB, -1000, 1000, -255, 255)
    
    # Aseguramos que los valores sean enteros para los pines digitales
    motorA = int(motorA)
    motorB = int(motorB)

    # Llamar a la función de control de motor simulada
    set_motor(ENA, IN1, IN2, motorA)
    set_motor(ENB, IN3, IN4, motorB)


# --- Ejemplo de uso de la lógica en Python ---
print("Simulación de control de motores en Python:")
print("--- Adelante a la derecha (Joystick: X=500, Y=800) ---")
drive_motors(500, 800)

print("\n--- Giro a la izquierda (Joystick: X=-800, Y=0) ---")
drive_motors(-800, 0)

print("\n--- Detenido (Joystick: X=50, Y=10) ---")
drive_motors(50, 10)


# ====================================================================
# ADAPTACIÓN CONCEPTUAL EN PYTHON DEL TRANSMISOR (No usa UUID)
# ====================================================================

# Pines (conceptuales)
JOY_X_PIN = 35
JOY_Y_PIN = 34

# Dirección del receptor (conceptual, ya que ESP-NOW no existe en Python nativo)
receiverAddress = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]


def analog_read_simulated(pin):
    """Simula la lectura ADC 0-4095 de ESP32."""
    return random.randint(0, 4095)

def send_data(x, y):
    """
    Simula la función esp_now_send().
    Usarías librerías de red reales (ej. sockets UDP o MQTT) aquí.
    """
    # Empaquetamos los dos enteros de 16 bits (h - short int)
    data_packet = struct.pack('<hh', x, y)
    
    print(f"Simulando envío de datos a {receiverAddress}: X={x}, Y={y}, Paquete={data_packet}")
    # Aquí iría tu código real de envío de red

def setup():
    print("\n--- INICIANDO TRANSMISOR EN PYTHON ---")
    pass

def loop():
    while True:
        # Leer valores ADC simulados
        rawX = analog_read_simulated(JOY_X_PIN)
        rawY = analog_read_simulated(JOY_Y_PIN)

        # Mapear 0-4095 a -1000 a +1000
        data_x = map_range(rawX, 0, 4095, -1000, 1000)
        data_y = map_range(rawY, 0, 4095, -1000, 1000)
        
        send_data(data_x, data_y)

        # Esperar 50ms
        time.sleep(0.050)

# ====================================================================
# Punto de entrada principal para ejecutar el bucle del transmisor
# ====================================================================
if __name__ == "__main__":
    setup()
    # Descomenta la siguiente línea si quieres ejecutar el loop() del transmisor
    # try:
    #     loop()
    # except KeyboardInterrupt:
    #     print("Transmisión detenida por el usuario.")
