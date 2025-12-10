esptool --port COM3 erase_flash
esptool --port COM3 --baud 460800 write_flash 0x1000 upython-v1.26.1.bin
