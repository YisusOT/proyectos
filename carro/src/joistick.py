import network
import espnow
import machine
from machine import Pin, ADC
import struct
import time
receiver_mac = b'\xAC\x15\x18\xD4\x43\xA4' 

JOY_X_PIN = 35
JOY_Y_PIN = 34

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect() 
try:
    sta.config(channel=1)
except Exception as e:
    print("Nota: No se pudo forzar el canal WiFi, usando default.")

e = espnow.ESPNow()
e.active(True)

try:
    e.add_peer(receiver_mac)
    print("Peer añadido correctamente")
except OSError:
    print("Error: El peer ya existe o dirección inválida")


adc_x = ADC(Pin(JOY_X_PIN))
adc_y = ADC(Pin(JOY_Y_PIN))

adc_x.atten(ADC.ATTN_11DB)
adc_y.atten(ADC.ATTN_11DB)

print("Transmisor listo. Enviando datos...")

def map_value(x, in_min, in_max, out_min, out_max):
    
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


while True:
    raw_x = adc_x.read_u16()
    raw_y = adc_y.read_u16()

    
    val_x = map_value(raw_x, 0, 65535, 1000, -1000)
    val_y = map_value(raw_y, 0, 65535, 1000, -1000)
    msg_data = struct.pack('<hh', val_x, val_y)

    try:
        e.send(receiver_mac, msg_data)
        
        
    except OSError as err:
        if err.args[0] == 12:
            pass 
        else:
            print("Error enviando:", err)

    time.sleep_ms(50)