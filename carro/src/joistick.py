import network
import espnow
import machine
from machine import Pin, ADC
import struct
import time

# --- CONFIGURACIÓN DE USUARIO ---

# IMPORTANTE: Reemplaza esto con la MAC de tu receptor (la misma que tenías en C++)
# El formato debe ser b'...' con los valores en hexadecimal.
receiver_mac = b'\xAC\x15\x18\xD4\x43\xA4' 

# Pines del Joystick
JOY_X_PIN = 35
JOY_Y_PIN = 34

# --- Inicialización de WiFi y ESP-NOW ---

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect() # Desconectamos para usar ESP-NOW puro

# Intentamos forzar el canal 1 (igual que en tu código C++)
try:
    sta.config(channel=1)
except Exception as e:
    # Algunos firmwares no permiten cambiar canal si no están conectados, 
    # pero para ESP-NOW suele funcionar por defecto.
    print("Nota: No se pudo forzar el canal WiFi, usando default.")

e = espnow.ESPNow()
e.active(True)

# Añadimos al receptor (Peer)
try:
    e.add_peer(receiver_mac)
    print("Peer añadido correctamente")
except OSError:
    print("Error: El peer ya existe o dirección inválida")

# --- Configuración de Joystick (ADC) ---

adc_x = ADC(Pin(JOY_X_PIN))
adc_y = ADC(Pin(JOY_Y_PIN))

# Configurar atenuación para leer rango completo 0-3.3v
# Sin esto, el ESP32 solo lee hasta ~1.0v y se satura.
adc_x.atten(ADC.ATTN_11DB)
adc_y.atten(ADC.ATTN_11DB)

print("Transmisor listo. Enviando datos...")

# --- Funciones Auxiliares ---

def map_value(x, in_min, in_max, out_min, out_max):
    """
    Mapea un valor de un rango a otro.
    """
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# --- Bucle Principal ---

while True:
    # 1. Leer valores crudos (0 a 65535 en MicroPython)
    raw_x = adc_x.read_u16()
    raw_y = adc_y.read_u16()

    # 2. Mapear valores
    # En Arduino tu map era: map(rawX, 0, 4095, 1000, -1000);
    # Aquí la entrada es 0-65535.
    # Nota: Mantenemos la lógica de inversión (1000 a -1000) si tu joystick está invertido.
    
    val_x = map_value(raw_x, 0, 65535, 1000, -1000)
    val_y = map_value(raw_y, 0, 65535, 1000, -1000)

    # 3. Empaquetar datos
    # '<hh' significa: Little Endian, dos enteros cortos (short) con signo (2 bytes c/u)
    # Esto genera exactamente la misma estructura binaria que tu struct de C++
    msg_data = struct.pack('<hh', val_x, val_y)

    # 4. Enviar
    try:
        # True al final indica que esperamos confirmación (ACK) si se desea, 
        # pero e.send devuelve None o lanza excepción.
        e.send(receiver_mac, msg_data)
        
        # Opcional: Imprimir para depurar
        # print(f"Enviado -> X: {val_x} Y: {val_y}")
        
    except OSError as err:
        # Normalmente error 12 (ENOMEM) si se envía muy rápido o el buffer está lleno
        if err.args[0] == 12:
            pass # Buffer lleno, ignoramos este paquete
        else:
            print("Error enviando:", err)

    # 5. Esperar 50ms (aprox 20Hz)
    time.sleep_ms(50)