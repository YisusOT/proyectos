## UNIVERSIDAD POLITECNICA DE VICTORIA  (UPV)

### MATERIA: 

METODOLOGIAS DE LA PROGRAMACION.

### PROFESOR:
M.C CARLOS ANTONIO TOVAR GARCIA 

### PROYECTO: 

CARRO CONTROLADO A CONTROL REMOTO

### INTEGRANTES:

- Jhonatan Israel Herrera Ibarra
- Jose Humberto Garcia Gamez
- Jesus Ignacio Olvera Trejo
- Jhordan Alexander Mariano Ramirez
- Rodrigo Martin Gomez de los Reyes 
- Edson Saeed Urbina Guerrero

## Materiales que utilizamos

- 2 ESP-32
- proto
- Puente en H
- 4 Moto-reductores
- Base del carrito
- Joystik

## Código 1: Lector de Dirección MAC
¿Qué hace?
Este código funciona como una herramienta de configuración. Su única misión es decirte cuál es el número de identificación único (Dirección MAC) de la tarjeta ESP32 que va a ser el Receptor (el carro).

¿Por qué es necesario?
El protocolo ESP-NOW no usa nombres de red; usa direcciones MAC directas. El Transmisor (el control) necesita esta MAC para saber exactamente a qué dispositivo debe enviar los comandos. Es como obtener el número de teléfono exacto de la persona a la que quieres llamar.

Lo más importante:
El código te da la dirección en tres formatos. Tienes que tomar el formato de MicroPython (ej. receiver_mac = b'\xAC\x15...') y pegarlo en el Código 2.

```py
import network
import ubinascii

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

mac_bytes = wlan.config('mac')

print("\n" + "="*40)
print("--- LECTURA DE DIRECCION MAC ---")
print("="*40)

mac_readable = ubinascii.hexlify(mac_bytes, ':').decode().upper()
print(f"\nMAC Normal: {mac_readable}")

c_format = ", ".join(["0x{:02X}".format(b) for b in mac_bytes])
print("\nCOPIA ESTO PARA ARDUINO (C++):")
print(f"uint8_t receiverAddress[] = {{ {c_format} }};")

print("\nCOPIA ESTO PARA MICROPYTHON:")
print(f"receiver_mac = {mac_bytes}")

print("="*40 + "\n")

```


## Código 2: Transmisor (El Mando de Control)

¿Qué hace?
Este es el software que convierte los movimientos de tu joystick en instrucciones de movimiento y las envía por el aire al carro.



```py
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

```



### Entradas y Salidas

| Fuente                  | Tipo        | Rango                         | Descripción                                      |
| ----------------------- | ----------- | ----------------------------- | ------------------------------------------------ |
| **Joystick X (Pin 35)** | Analógica   | 0 – 65535                     | Lectura ADC del eje X del joystick.              |
| **Joystick Y (Pin 34)** | Analógica   | 0 – 65535                     | Lectura ADC del eje Y del joystick.              |
| **MAC del receptor**    | Byte string | `b'\xAC\x15\x18\xD4\x43\xA4'` | Dirección del dispositivo receptor para ESP-NOW. |
| **Tiempo de espera**    | Constante   | 50 ms                         | Intervalo entre envíos (frecuencia de ~20 Hz).   |

| Destino              | Tipo              | Ejemplo de contenido                                     |Descripción                                 |
| -------------------- | ----------------- | -------------------------------------------------------- |------------------------------------------- |
| **ESP-NOW (Peer)**   | Binario (`bytes`) | `b'\xE8\x03\x18\xFC'`                                    | Contiene los valores mapeados del joystick empaquetados.         |
| **Consola / Serial** | Texto             | `"Peer añadido correctamente"` o `"Error enviando: ..."` | Mensajes de depuración sobre el estado del envío o de la conexión. |



## Código 3: Receptor (El Cerebro del Carro)

¿Qué hace?
Este es el software que vive dentro del carro. Recibe la orden del mando y la traduce en la velocidad y dirección adecuadas para cada motor.

```py
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
    

```

-----

### Entradas

| **Variable**  | **Tipo**    | **Fuente**             | **Descripción**                                         |
| ------------- | ----------- | ---------------------- | ------------------------------------------------------- |
| `msg`         | bytes       | ESP-NOW                | Paquete recibido que contiene los valores del joystick. |
| `x`           | int16       | struct.unpack de `msg` | Valor del eje X del joystick recibido por ESP-NOW.      |
| `y`           | int16       | struct.unpack de `msg` | Valor del eje Y del joystick recibido por ESP-NOW.      |
| `host`        | MAC (bytes) | ESP-NOW                | Dirección MAC del emisor del mensaje (no se usa).       |
| `motor_a_val` | int         | Procesamiento interno  | Valor calculado para la mezcla de motores (y + x).      |
| `motor_b_val` | int         | Procesamiento interno  | Valor calculado para la mezcla de motores (y - x).      |
| `dir_a`       | int         | Procesamiento interno  | Dirección del motor A (1 adelante, -1 atrás, 0 parar).  |
| `dir_b`       | int         | Procesamiento interno  | Dirección del motor B.                                  |
| `speed_a`     | int         | map_value()            | Velocidad PWM del motor A (0–65535).                    |
| `speed_b`     | int         | map_value()            | Velocidad PWM del motor B (0–65535).                    |

### Salidas de los motores

| Variable  | Función / Salida                                                                   |
| --------- | ---------------------------------------------------------------------------------- |
| `pwm_a`   | Objeto PWM que controla la velocidad del **Motor A** (ENA_PIN) mediante `duty_u16` |
| `pwm_b`   | Objeto PWM que controla la velocidad del **Motor B** (ENB_PIN) mediante `duty_u16` |
| `in1`     | Pin de dirección del **Motor A** (IN1_PIN)                                         |
| `in2`     | Pin de dirección del **Motor A** (IN2_PIN)                                         |
| `in3`     | Pin de dirección del **Motor B** (IN3_PIN)                                         |
| `in4`     | Pin de dirección del **Motor B** (IN4_PIN)                                         |
| `speed_a` | Valor de velocidad calculado para Motor A (0-65535)                                |
| `speed_b` | Valor de velocidad calculado para Motor B (0-65535)                                |
| `dir_a`   | Dirección de Motor A: 1 = adelante, -1 = atrás, 0 = detener                        |
| `dir_b`   | Dirección de Motor B: 1 = adelante, -1 = atrás, 0 = detener                        |

### Variables de salida de depuracion

| Variable      | Uso de salida                                  |
| ------------- | ---------------------------------------------- |
| `x`           | Valor X recibido del joystick (int16)          |
| `y`           | Valor Y recibido del joystick (int16)          |
| `motor_a_val` | Valor calculado de mezcla para Motor A (±1000) |
| `motor_b_val` | Valor calculado de mezcla para Motor B (±1000) |



## Validaciones

- Ambas coordenadas deben de estar en rango de +1000 a -1000
- Verifica que msg existe antes de intentar procesarlo.
- Valida que el paquete recibido:
  - Tenga el tamaño correcto (4 bytes)
  - Tiene el formato correcto (dos enteros Int16)

El Código 3 escucha el paquete, calcula las velocidades para girar y moverse, y luego le manda esa electricidad a los motores para que el carro se mueva.

## Resultados
El proyecto fue un exito, cumplio con nuestras expectativas, al momento de mover el Joystick el carro reaccionaba y se movia a la direccion que dirigia la palanca.

Su funcionammiento se basa en que cuando se mueve dos palanquitas que alteran el eje X y Y al momento de mover el Joisitck esas palanquitas envian una señal al carro el cual interpreta esos dos ejes en una potencia de voltaje a los respectivos motores permitiendo asi su movimiento.


## Contratiempos y observaciones:
- Vimos que la conexion en paralelo consumia mucha energia y cuando lo pasamos a conexion en serie, consumia menos.

- Descargamos mal Micropython por culpa no poner atencion a la momento de explicacion de la instalacion.


### Conclusiones:

Para concluir con nuestro reporte, aprendimos como funcionan los carritos a control remoto además de como se comportan cada motor y para que circunstancias podremos combinarlas para crear algo nuevo, fue una buena manera de introducción al software de micro python, y podremos seguir utilizando este software para futuros proyectos.

Además, aprendí a usar ESP32,
Subir el repositorio a github, también aprendí sobre el desafío que representa diseñar un buen diseño práctico y funcional para el carro, debido a que no puede ser demasiado detallado sin ocupar peso innecesario que podría perjudicar a los motores.