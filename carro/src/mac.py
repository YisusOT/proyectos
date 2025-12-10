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