from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
import serial
import time
import os
import threading
import json
import subprocess
import socket

base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))
app.secret_key = "seguridad_muro_verde_ipn"

# --- MEMORIA DE CONFIGURACIÓN Y POSICIÓN ---
ARCHIVO_CONFIG = os.path.join(base_dir, 'config_cnc.json')
ARCHIVO_POSICION = os.path.join(base_dir, 'posicion_cnc.json')

def cargar_config():
    if os.path.exists(ARCHIVO_CONFIG):
        with open(ARCHIVO_CONFIG, 'r') as f:
            return json.load(f)
    return {"v_max": 4000, "a_max": 500}

def guardar_config(conf):
    with open(ARCHIVO_CONFIG, 'w') as f:
        json.dump(conf, f)

def cargar_posicion():
    if os.path.exists(ARCHIVO_POSICION):
        try:
            with open(ARCHIVO_POSICION, 'r') as f:
                data = json.load(f)
                if "x_pasos" in data: return data 
        except: pass
    return {"x_pasos": 0, "y_pasos": 0, "estado": "IDLE"}

def guardar_posicion(estado):
    try:
        temp_file = ARCHIVO_POSICION + '.tmp'
        with open(temp_file, 'w') as f:
            json.dump(estado, f)
        os.replace(temp_file, ARCHIVO_POSICION)
    except: pass

config_actual = cargar_config()
estado_cnc = cargar_posicion()

# --- CONFIGURACIÓN SERIAL (PICO) ---
PUERTO = '/dev/ttyACM0'  
BAUDIOS = 115200
conexion_serial = None

try:
    conexion_serial = serial.Serial(PUERTO, BAUDIOS, timeout=0) 
    time.sleep(1)
    conexion_serial.reset_input_buffer()
    estado_conexion = "Conectado"
    
    cmd_sync = f"G92 X{estado_cnc['x_pasos']} Y{estado_cnc['y_pasos']}\n"
    conexion_serial.write(cmd_sync.encode('utf-8'))
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
                            if "POS" in linea:
                                try:
                                    idx = linea.find("POS")
                                    partes = linea[idx:].split()
                                    if len(partes) >= 3:
                                        estado_cnc["x_pasos"] = int(partes[1])
                                        estado_cnc["y_pasos"] = int(partes[2])
                                        estado_cnc["estado"] = "MOVING"
                                except Exception: pass 
                            
                            if "OK" in linea:
                                estado_cnc["estado"] = "IDLE"
                                guardar_posicion(estado_cnc)
            except Exception: 
                pass
        time.sleep(0.01)

threading.Thread(target=escuchar_pico, daemon=True).start()

# --- EXTRACCIÓN DE DATOS DEL SISTEMA Y RED ---
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "127.0.0.1"

def get_ssid():
    try:
        ssid = subprocess.check_output(['iwgetid', '-r']).decode('utf-8').strip()
        if ssid: return ssid
    except: pass
    try:
        ssid_raw = subprocess.check_output(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi']).decode('utf-8')
        ssid_list = [line.split(':')[1] for line in ssid_raw.split('\n') if line.startswith('yes')]
        if ssid_list: return ssid_list[0]
    except: pass
    return "Desconectado"

prev_cpu_stats = {"cpu0": (0,0), "cpu1": (0,0), "cpu2": (0,0), "cpu3": (0,0)}

def obtener_telemetria_pi():
    global prev_cpu_stats
    
    # 1. Uptime (Tiempo Activo)
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        dias = int(uptime_seconds // 86400)
        horas = int((uptime_seconds % 86400) // 3600)
        minutos = int((uptime_seconds % 3600) // 60)
        
        if dias > 0: uptime_str = f"{dias} días, {horas} hrs, {minutos} min"
        elif horas > 0: uptime_str = f"{horas} hrs, {minutos} min"
        else: uptime_str = f"{minutos} min"
    except:
        uptime_str = "--"

    # 2. Temperatura
    try:
        temp_raw = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('utf-8')
        temp = float(temp_raw.replace("temp=", "").replace("'C\n", ""))
    except: temp = 0.0

    # 3. CPU Loads
    cpu_loads = []
    try:
        with open('/proc/stat', 'r') as f:
            lines = f.readlines()
            
        for i in range(4):
            core_name = f"cpu{i}"
            linea_cpu = next((l for l in lines if l.startswith(f"{core_name} ")), None)
            
            if linea_cpu:
                datos = list(map(int, linea_cpu.split()[1:]))
                tiempo_inactivo = datos[3] + datos[4]
                tiempo_total = sum(datos)
                
                prev_inactivo, prev_total = prev_cpu_stats[core_name]
                delta_inactivo = tiempo_inactivo - prev_inactivo
                delta_total = tiempo_total - prev_total
                
                if delta_total == 0:
                    cpu_loads.append(0.0)
                else:
                    carga = (1.0 - (delta_inactivo / delta_total)) * 100.0
                    cpu_loads.append(round(carga, 1))
                
                prev_cpu_stats[core_name] = (tiempo_inactivo, tiempo_total)
            else:
                cpu_loads.append(0.0)
    except:
        cpu_loads = [0.0, 0.0, 0.0, 0.0]

    # 4. RAM
    try:
        mem = subprocess.check_output(['free', '-m']).decode('utf-8').splitlines()[1].split()
        ram_total, ram_usada = int(mem[1]), int(mem[2])
        ram_porc = round((ram_usada / ram_total) * 100, 1)
    except: ram_total, ram_usada, ram_porc = 0, 0, 0.0

    # 5. Disco
    try:
        disco = subprocess.check_output(['df', '-h', '/']).decode('utf-8').splitlines()[1].split()
        disco_total, disco_usado, disco_porc = disco[1], disco[2], disco[4]
    except: disco_total, disco_usado, disco_porc = "0G", "0G", "0%"

    return {
        "uptime": uptime_str,
        "temp": temp, "cpu_loads": cpu_loads,
        "ram_total": ram_total, "ram_usada": ram_usada, "ram_porc": ram_porc,
        "disco_total": disco_total, "disco_usado": disco_usado, "disco_porc": disco_porc
    }

# --- RUTAS ---
@app.route('/')
def index(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('usuario') == 'admin' and request.form.get('password') == '1234':
            session['logeado'] = True
            return redirect(url_for('panel'))
        return "Error", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logeado', None)
    return redirect(url_for('login'))

@app.route('/panel')
def panel():
    if not session.get('logeado'): return redirect(url_for('login'))
    return render_template('control_riego.html', estado=estado_conexion)

@app.route('/red_wifi')
def red_wifi():
    if not session.get('logeado'): return redirect(url_for('login'))
    return render_template('panel.html', ssid=get_ssid(), ip=get_ip_address())

@app.route('/sistema')
def sistema():
    if not session.get('logeado'): return redirect(url_for('login'))
    return render_template('sistema.html')

# --- API ---
@app.route('/api/telemetria')
def api_telemetria():
    if not session.get('logeado'): return jsonify({"error": "Auth"}), 401
    resp = jsonify(obtener_telemetria_pi())
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/api/estado')
def api_estado():
    resp = jsonify(estado_cnc)
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    global config_actual
    if not session.get('logeado'): return jsonify({"error": "Auth"}), 401
    if request.method == 'POST':
        datos = request.json
        config_actual['v_max'] = int(datos.get('v_max', 4000))
        config_actual['a_max'] = int(datos.get('a_max', 500))
        guardar_config(config_actual)
        return jsonify({"status": "ok", "config": config_actual})
    return jsonify(config_actual)

@app.route('/api/comando', methods=['POST'])
def api_comando():
    if not session.get('logeado'): return jsonify({"error": "Auth"}), 401
    cmd = request.json.get('gcode', '').upper()
    if conexion_serial and conexion_serial.is_open:
        conexion_serial.write(f"{cmd}\n".encode('utf-8'))
        if cmd != "M112": estado_cnc["estado"] = "MOVING"
    return jsonify({"status": "ok"})

@app.route('/logo.png')
def serve_logo():
    return send_file("/home/muroverde/MuroVerde/Master_Control/static/Escudo_ipn.png", mimetype='image/png')

if __name__ == '__main__':
    os.system("sudo fuser -k 5000/tcp > /dev/null 2>&1")
    time.sleep(1)
    app.run(host='0.0.0.0', port=5000, use_reloader=False, threaded=True)