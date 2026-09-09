import time
import subprocess
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

i2c = busio.I2C(board.SCL, board.SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3c)

disp.fill(0)
disp.show()

width = disp.width
height = disp.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

def obtener_datos():
    try:
        ssid_raw = subprocess.check_output(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi']).decode('utf-8')
        ssid_list = [line.split(':')[1] for line in ssid_raw.split('\n') if line.startswith('yes')]
        ssid = ssid_list[0] if ssid_list else "Desconectado"
    except:
        ssid = "Error"

    try:
        cmd_ip = "ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'"
        ip = subprocess.check_output(cmd_ip, shell=True).decode('utf-8').strip()
        if not ip:
            ip = "Sin IP"
    except:
        ip = "Error IP"

    try:
        temp_raw = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('utf-8')
        temp = temp_raw.replace("temp=", "").strip()
    except:
        temp = "0.0'C"
        
    return ssid, ip, temp

pantalla_actual = 0 

while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    ssid, ip, temp = obtener_datos()
    
    draw.text((10, 0), "--- MURO VERDE ---", font=font, fill=255)
    
    if pantalla_actual == 0:
        draw.text((0, 11), f"IP: {ip}", font=font, fill=255)
        draw.text((0, 22), f"Red: {ssid[:15]}", font=font, fill=255)
        pantalla_actual = 1
    else:
        draw.text((0, 11), f"Temp CPU: {temp}", font=font, fill=255)
        draw.text((0, 22), "Estado: Activo", font=font, fill=255)
        pantalla_actual = 0
    
    disp.image(image)
    disp.show()
    time.sleep(4)