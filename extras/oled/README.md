# Monitor OLED opcional

`oled_monitor.py` es un programa independiente conservado del respaldo. Alterna cada 4 segundos entre IP/red y temperatura de CPU. La pantalla está configurada como SSD1306 de 128 × 32 píxeles, por I²C, en la dirección `0x3c`.

Importa `board` y `busio` (Adafruit Blinka), `PIL` (Pillow) y `adafruit_ssd1306` (Adafruit CircuitPython SSD1306). Estas dependencias son adicionales a las del servidor Flask. El respaldo no especifica sus versiones ni el procedimiento de configuración de I²C para la Pi 5.

Para obtener datos utiliza `nmcli`, `ip`, `grep` y `vcgencmd`; asume que la interfaz Wi-Fi se llama `wlan0`. La compatibilidad de librerías, bus y cableado debe comprobarse en el equipo antes de ejecutarlo.

El texto «Estado: Activo» es fijo: no consulta la salud del servidor ni el estado del CNC. V2 no inicia este programa automáticamente. No se incluye un servicio de arranque ni se afirma haber probado el accesorio.

[Volver al proyecto](../../README.md)
