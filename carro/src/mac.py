import network
import ubinascii

# 1. Activar la interfaz Station (STA)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# 2. Obtener la dirección MAC en crudo (bytes)
mac_bytes = wlan.config('mac')

print("\n" + "="*40)
print("--- LECTURA DE DIRECCION MAC ---")
print("="*40)

# --- Formato 1: Legible Humano ---
# Convertimos los bytes a hex y los separamos con dos puntos
mac_readable = ubinascii.hexlify(mac_bytes, ':').decode().upper()
print(f"\nMAC Normal: {mac_readable}")

# --- Formato 2: Para código C++ / Arduino ---
# Creamos el array { 0xAC, 0x15... }
c_format = ", ".join(["0x{:02X}".format(b) for b in mac_bytes])
print("\nCOPIA ESTO PARA ARDUINO (C++):")
print(f"uint8_t receiverAddress[] = {{ {c_format} }};")

# --- Formato 3: Para código MicroPython ---
# Este es el que necesitas para el script de 'Transmisor' que te di antes
print("\nCOPIA ESTO PARA MICROPYTHON:")
print(f"receiver_mac = {mac_bytes}")

print("="*40 + "\n")