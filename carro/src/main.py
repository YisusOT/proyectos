import network
import espnow
import machine
from machine import Pin, PWM
import struct
import time
# Motor A
ENA_PIN = 14
IN1_PIN = 27
IN2_PIN = 26
# Motor B
ENB_PIN = 32
IN3_PIN = 25
IN4_PIN = 33

pwm_a = PWM(Pin(ENA_PIN), freq=1000)
pwm_b = PWM(Pin(ENB_PIN), freq=1000)

in1 = Pin(IN1_PIN, Pin.OUT)
in2 = Pin(IN2_PIN, Pin.OUT)
in3 = Pin(IN3_PIN, Pin.OUT)
in4 = Pin(IN4_PIN, Pin.OUT)

pwm_a.duty_u16(0)
pwm_b.duty_u16(0)

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()

e = espnow.ESPNow()
e.active(True)

print("MicroPython ESP-NOW Receptor Listo")
print("Esperando datos de Joystick...")

def map_value(x, in_min, in_max, out_min, out_max):

    val = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return int(val)

def set_motor(pwm_obj, pin1, pin2, speed_u16, direction):

    if direction > 0: 
        pin1.value(1)
        pin2.value(0)
        pwm_obj.duty_u16(speed_u16)
    elif direction < 0: 
        pin1.value(0)
        pin2.value(1)
        pwm_obj.duty_u16(speed_u16)
    else:
        pin1.value(0)
        pin2.value(0)
        pwm_obj.duty_u16(0)

def drive_motors(x, y):
    deadzone = 100
    if abs(x) < deadzone: x = 0
    if abs(y) < deadzone: y = 0

    motor_a_val = y + x
    motor_b_val = y - x
    
    motor_a_val = max(min(motor_a_val, 1000), -1000)
    motor_b_val = max(min(motor_b_val, 1000), -1000)
    
    # --- Motor A ---
    dir_a = 0
    if motor_a_val > 0: dir_a = 1
    elif motor_a_val < 0: dir_a = -1
    
    speed_a = map_value(abs(motor_a_val), 0, 1000, 0, 65535)
    set_motor(pwm_a, in1, in2, speed_a, dir_a)

    # --- Motor B ---
    dir_b = 0
    if motor_b_val > 0: dir_b = 1
    elif motor_b_val < 0: dir_b = -1
    
    speed_b = map_value(abs(motor_b_val), 0, 1000, 0, 65535)
    set_motor(pwm_b, in3, in4, speed_b, dir_b)
    

while True:
    host, msg = e.recv()
    
    if msg:
        try:
            x, y = struct.unpack('<hh', msg)
            
            print(f"Recibido -> Joystick X: {x} Y: {y}")
            
            drive_motors(x, y)
            
        except ValueError:
            print("Error al decodificar paquete")