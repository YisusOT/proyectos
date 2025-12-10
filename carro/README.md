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

-----

## INTRODUCCION

Nuestro proyecto se trato de armar un carrito a control remoto con la base de ESP-32 y programarlo con Micropython.

#### ¿Que es una ESP-32?

El ESP-32 es un microcontrolador de sistema en chip (SoC) de bajo costo y bajo consumo.
Se conecta inalambricamente facilitando su conexion en red, y en otros dispositivos inteligentes.

#### ¿que es el codigo MAC y para que sirve?
- Es un identificador único que viene asignado a cada dispositivo con red
- indetificacion de dispositivos en la red
- enviar datos a otros dispositivos o equipo específicos
- direct communication (como un ESP32 a ESP32)
- ¿Por qué es necesario?
El protocolo ESP-NOW no usa nombres de red; usa direcciones MAC directas. El Transmisor (el control) necesita esta MAC para saber exactamente a qué dispositivo debe enviar los comandos. Es como obtener el número de teléfono exacto de la persona a la que quieres llamar.
​Lo más importante:
El código te da la dirección en tres formatos. Tienes que tomar el formato de MicroPython (ej. receiver_mac = b'\xAC\x15...') y pegarlo en el Código 2.Transmisor (El Mando de Control)
​¿Qué hace?
Este es el software que convierte los movimientos de tu joystick en instrucciones de movimiento y las envía por el aire al carro.
Sección del Código Función para el Carro RC
receiver_mac = ... Le dice al control: "Quiero hablar con ESTE carro en específico".
Activación de ESP-NOW Prepara la radio del ESP32 para hablar en modo directo, sin necesidad de conectarse a un router Wi-Fi.
Lectura del Joystick (ADC) Lee los ejes X y Y del joystick. La clave es el ajuste de atenuación (ADC.ATTN_11DB) que asegura que se lean todos los movimientos del joystick.
map_value() Procesa la intención. Convierte la lectura cruda (0 a 65535) en un valor de control simple y fácil de usar, generalmente de -1000 a 1000 (donde -1000 es toda la potencia hacia atrás y 1000 es toda la potencia hacia adelante/girar).
struct.pack('<hh', val_x, val_y) Empaqueta la orden. Agarra los dos valores de control (-1000 a 1000) y los comprime en un paquete binario de solo 4 bytes. Esto garantiza que la comunicación sea rapidísima y la latencia baja.
e.send() Envía ese paquete corto de datos al carro cada 50 milisegundos.
En resumen: El Código 2 toma tu control, lo digitaliza, lo comprime y lo grita al Código 3:Receptor (El Cerebro del Carro)
​¿Qué hace?
Este es el software que vive dentro del carro. Recibe la orden del mando y la traduce en la velocidad y dirección adecuadas para cada motor.Sección del Código Función para el Carro RC
Configuración de Pines Configura los 4 pines de dirección y los 2 pines de velocidad (PWM) que se conectan al driver de motores (Puente H).
Activación de ESP-NOW Enciende la radio y se pone en modo escucha, esperando órdenes de su "peer" (el mando).
e.recv() y struct.unpack() Escucha y Desempaca. Espera que llegue un paquete, lo abre y recupera los dos valores de control originales (X y Y, de -1000 a 1000).
drive_motors(x, y) La Lógica de Manejo (Tank Drive Mixing): Esta es la sección más importante. Utiliza un algoritmo para calcular qué tan rápido y en qué dirección debe ir la rueda izquierda y la rueda derecha, basándose en la palanca X y Y.
set_motor() Physical Control. It takes the final value of each motor and does two things: 1) If the value is positive or negative, it activates the correct steering pins (forward/backward). 2) It uses the magnitude of the value to set the duty cycle of the PWM (the power) going to the motor.

En resumen: El Código 3 escucha el paquete, calcula las velocidades para girar y moverse, y luego le manda esa electricidad a los motores para que el carro se mueva.


-----
## Materiales que utilizamos

- ESP-32
- proto
- Puente en H
- Moto-reductores
- Base del carrito
- Joystik

-----

## Proceso de desarrollo:

- Comprar los materiales
- Montar el proyecto
- Integrar los componentes electronicos
- Crear el codigo en Micropython para el carro y el control remoto.
- Testear el codigo
- Probar el carrito

-----

## CODIGO DE MICROPYTHON

```py
import network
import espnow
import machine
from machine import Pin, PWM
import struct
import time
# --- Configuración de Pines ---
# Motor A
ENA_PIN = 14
IN1_PIN = 27
IN2_PIN = 26
# Motor B
ENB_PIN = 32
IN3_PIN = 25
IN4_PIN = 33

# --- Inicialización de Hardware ---

# Configuración PWM (Frecuencia 1000Hz es estándar para motores DC)
pwm_a = PWM(Pin(ENA_PIN), freq=1000)
pwm_b = PWM(Pin(ENB_PIN), freq=1000)

# Configuración Pines de Dirección
in1 = Pin(IN1_PIN, Pin.OUT)
in2 = Pin(IN2_PIN, Pin.OUT)
in3 = Pin(IN3_PIN, Pin.OUT)
in4 = Pin(IN4_PIN, Pin.OUT)

# Inicializamos motores detenidos
pwm_a.duty_u16(0)
pwm_b.duty_u16(0)

# --- Configuración ESP-NOW ---
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect() # Nos aseguramos de no estar conectados a un router

e = espnow.ESPNow()
e.active(True)

print("MicroPython ESP-NOW Receptor Listo")
print("Esperando datos de Joystick...")

# --- Funciones Auxiliares ---

def map_value(x, in_min, in_max, out_min, out_max):
    """
    Equivalente a la función map() de Arduino.
    """
    val = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return int(val)

def set_motor(pwm_obj, pin1, pin2, speed_u16, direction):
    """
    Controla un motor individual.
    speed_u16: valor de 0 a 65535
    direction: 1 (adelante), -1 (atrás), 0 (parar)
    """
    if direction > 0: # Adelante
        pin1.value(1)
        pin2.value(0)
        pwm_obj.duty_u16(speed_u16)
    elif direction < 0: # Atrás
        pin1.value(0)
        pin2.value(1)
        pwm_obj.duty_u16(speed_u16)
    else: # Parar
        pin1.value(0)
        pin2.value(0)
        pwm_obj.duty_u16(0)

def drive_motors(x, y):
    # Zona muerta (Deadzone)
    deadzone = 100
    if abs(x) < deadzone: x = 0
    if abs(y) < deadzone: y = 0
    
    # Mezcla tipo tanque (Tank drive mixing)
    motor_a_val = y + x
    motor_b_val = y - x
    
    # Constrain (limitar valores entre -1000 y 1000 como en tu código original)
    motor_a_val = max(min(motor_a_val, 1000), -1000)
    motor_b_val = max(min(motor_b_val, 1000), -1000)
    
    # --- Motor A ---
    dir_a = 0
    if motor_a_val > 0: dir_a = 1
    elif motor_a_val < 0: dir_a = -1
    
    # Mapear de 0-1000 a 0-65535 (Resolución PWM de MicroPython)
    speed_a = map_value(abs(motor_a_val), 0, 1000, 0, 65535)
    set_motor(pwm_a, in1, in2, speed_a, dir_a)

    # --- Motor B ---
    dir_b = 0
    if motor_b_val > 0: dir_b = 1
    elif motor_b_val < 0: dir_b = -1
    
    speed_b = map_value(abs(motor_b_val), 0, 1000, 0, 65535)
    set_motor(pwm_b, in3, in4, speed_b, dir_b)
    
    # Debug opcional
    # print(f"X: {x}, Y: {y} | MotA: {motor_a_val} ({speed_a}), MotB: {motor_b_val} ({speed_b})")

# --- Bucle Principal ---

while True:
    # e.recv() devuelve una tupla: (mac_address, message)
    # Si no hay mensaje, devuelve (None, None) o espera según timeout
    host, msg = e.recv()
    
    if msg:
        try:
            # Desempaquetamos los datos.
            # '<hh': Little Endian, dos short (int16)
            # Esto debe coincidir con tu struct de C++ {int16_t x; int16_t y;}
            x, y = struct.unpack('<hh', msg)
            
            # Ver datos crudos (opcional)
            print(f"Recibido -> Joystick X: {x} Y: {y}")
            
            drive_motors(x, y)
            
        except ValueError:
            print("Error al decodificar paquete")
    
    # Pequeña pausa para no saturar el CPU si no llegan mensajes (opcional)
    # time.sleep_ms(10)

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


-----

## Validaciones

- Ambas coordenadas deben de estar en rango de +1000 a -1000
- Verifica que msg existe antes de intentar procesarlo.
- Valida que el paquete recibido:
  - Tenga el tamaño correcto (4 bytes)
  - Tiene el formato correcto (dos enteros Int16)

-----

## Codigo del Joystick

```py
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

```

-----

### Entradas y Salidas

| Fuente                  | Tipo        | Rango                         | Descripción                                      |
| ----------------------- | ----------- | ----------------------------- | ------------------------------------------------ |
| **Joystick X (Pin 35)** | Analógica   | 0 – 65535                     | Lectura ADC del eje X del joystick.              |
| **Joystick Y (Pin 34)** | Analógica   | 0 – 65535                     | Lectura ADC del eje Y del joystick.              |
| **MAC del receptor**    | Byte string | `b'\xAC\x15\x18\xD4\x43\xA4'` | Dirección del dispositivo receptor para ESP-NOW. |
| **Tiempo de espera**    | Constante   | 50 ms                         | Intervalo entre envíos (frecuencia de ~20 Hz).   |

| Destino              | Tipo              | Ejemplo de contenido                                     | Descripción                                                        |
| -------------------- | ----------------- | -------------------------------------------------------- | ------------------------------------------------------------------ |
| **ESP-NOW (Peer)**   | Binario (`bytes`) | `b'\xE8\x03\x18\xFC'`                                    | Contiene los valores mapeados del joystick empaquetados.           |
| **Consola / Serial** | Texto             | `"Peer añadido correctamente"` o `"Error enviando: ..."` | Mensajes de depuración sobre el estado del envío o de la conexión. |

-----

## Resultados
El proyecto fue un exito, cumplio con nuestras expectativas, al momento de mover el Joystick el carro reaccionaba y se movia a la direccion que dirigia la palanca.

Su funcionammiento se basa en que cuando se mueve dos palanquitas que alteran el eje X y Y al momento de mover el Joisitck esas palanquitas envian una señal al carro el cual interpreta esos dos ejes en una potencia de voltaje a los respectivos motores permitiendo asi su movimiento.

-----

## Contratiempos y observaciones:
- Vimos que la conexion en paralelo consumia mucha energia y cuando lo pasamos a conexion en serie, consumia menos.

- Descargamos mal Micropython por culpa no poner atencion a la momento de explicacion de la instalacion.

-----

### Conclusiones:

Para concluir con nuestro reporte, aprendimos como funcionan los carritos a control remoto además de como se comportan cada motor y para que circunstancias podremos combinarlas para crear algo nuevo, fue una buena manera de introducción al software de micro python, y podremos seguir utilizando este software para futuros proyectos.

Además, aprendí a usar ESP32,
Subir el repositorio a github, también aprendí sobre el desafío que representa diseñar un buen diseño práctico y funcional para el carro, debido a que no puede ser demasiado detallado sin ocupar peso innecesario que podría perjudicar a los motores.