from flask import Flask, request, jsonify, render_template, send_file
import serial
import time
import os
import threading

base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))

# --- CONFIGURACIÓN SERIAL ---
PUERTO = '/dev/ttyACM0'  # Puerto por defecto de la Pico en Linux
BAUDIOS = 115200
conexion_serial = None

estado_cnc = {"x_pasos": 0, "y_pasos": 0, "estado": "IDLE"}

try:
    conexion_serial = serial.Serial(PUERTO, BAUDIOS, timeout=0) 
    time.sleep(1)
    conexion_serial.reset_input_buffer()
    estado_conexion = "Conectado"
except Exception as e:
    estado_conexion = "Simulación (Pico no detectada)"

def escuchar_pico():
    global estado_cnc
    buffer_serial = "" 
    while True:
        if conexion_serial and conexion_serial.is_open:
            try:
                if conexion_serial.in_waiting > 0:
                    chunk = conexion_serial.read(conexion_serial.in_waiting).decode('utf-8', errors='ignore')
                    buffer_serial += chunk 
                    if '\n' in buffer_serial:
                        lineas = buffer_serial.split('\n')
                        buffer_serial = lineas.pop() 
                        for linea in lineas:
                            linea = linea.strip()
                            if not linea: continue
                            if linea.startswith("POS"):
                                partes = linea.split()
                                if len(partes) >= 3:
                                    try:
                                        estado_cnc["x_pasos"] = int(partes[1])
                                        estado_cnc["y_pasos"] = int(partes[2])
                                        estado_cnc["estado"] = "MOVING"
                                    except ValueError: pass 
                            elif "OK" in linea:
                                estado_cnc["estado"] = "IDLE"
            except Exception: pass
        time.sleep(0.01)

threading.Thread(target=escuchar_pico, daemon=True).start()

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('control_riego.html', estado=estado_conexion)

@app.route('/api/comando', methods=['POST'])
def api_comando():
    cmd = request.json.get('gcode', '').upper()
    if conexion_serial and conexion_serial.is_open:
        conexion_serial.write(f"{cmd}\n".encode('utf-8'))
        if cmd != "M112": estado_cnc["estado"] = "MOVING"
    else:
        if cmd == "M112": estado_cnc["estado"] = "IDLE"
        else:
            for p in cmd.split():
                if p.startswith('X'): estado_cnc["x_pasos"] = int(p[1:])
                elif p.startswith('Y'): estado_cnc["y_pasos"] = int(p[1:])
            if "X0" in cmd and "Y0" in cmd:
                estado_cnc["x_pasos"] = 0; estado_cnc["y_pasos"] = 0
            estado_cnc["estado"] = "IDLE"
    return jsonify({"status": "enviado"})

@app.route('/api/estado')
def api_estado():
    return jsonify(estado_cnc)

# Ruta VIP para el logo
@app.route('/logo.png')
def serve_logo():
    ruta_exacta = "/home/muroverde/MuroVerde/Master_Control/static/Escudo_ipn.png"
    return send_file(ruta_exacta, mimetype='image/png')

if __name__ == '__main__':
    os.system("fuser -k 5001/tcp > /dev/null 2>&1")
    time.sleep(1)
    try:
        app.run(host='0.0.0.0', port=5001) # Puerto 5001 para no chocar
    finally:
        if conexion_serial and conexion_serial.is_open:
            conexion_serial.close()
