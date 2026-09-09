from flask import Flask, request, jsonify, render_template_string
import serial
import time
import os
import threading
import subprocess

app = Flask(__name__)

# --- 1. CONFIGURACIÓN SERIAL ---
PUERTO = '/dev/pico_muroverde'
BAUDIOS = 115200

# Variables globales compartidas
conexion_serial = None
estado_conexion = "Simulación"
estado_cnc = {
    "x_pasos": 0,
    "y_pasos": 0,
    "estado": "IDLE"
}

def inicializar_serial():
    global conexion_serial, estado_conexion
    try:
        # Timeout de 0.1 para que el hilo de lectura no se quede trabado
        conexion_serial = serial.Serial(PUERTO, BAUDIOS, timeout=0.1) 
        time.sleep(1)
        conexion_serial.reset_input_buffer()
        estado_conexion = "Conectado"
        print("🟢 Conexión serial establecida con la Pico")
        return True
    except Exception:
        estado_conexion = "Simulación"
        return False

inicializar_serial()

# --- HILO DE TELEMETRÍA (DRENAJE DE CABLE) ---
def escuchar_pico():
    global estado_cnc, conexion_serial
    buffer_serial = ""
    while True:
        if conexion_serial and conexion_serial.is_open:
            try:
                # Leemos todo lo que haya en el buffer para evitar lag
                if conexion_serial.in_waiting > 0:
                    datos = conexion_serial.read(conexion_serial.in_waiting).decode('utf-8', errors='ignore')
                    buffer_serial += datos
                    
                    if '\n' in buffer_serial:
                        lineas = buffer_serial.split('\n')
                        buffer_serial = lineas.pop() # El último pedazo se queda para la siguiente vuelta
                        
                        for linea in lineas:
                            linea = linea.strip()
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
            except serial.SerialException:
                print("🔴 Error Serial. Reintentando...")
                conexion_serial.close()
                time.sleep(2)
                inicializar_serial()
            except Exception: pass
        else:
            time.sleep(1)
        time.sleep(0.01)

threading.Thread(target=escuchar_pico, daemon=True).start()

# --- 2. INTERFAZ MAINSAIL COMPLETA ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mainsail - Muro Verde</title>
    <style>
        :root { 
            --bg-body: #1a1c20; --bg-sidebar: #131518; --bg-panel: #21252b; --bg-panel-header: #282c34; --border-color: #31363f;
            --text-main: #abb2bf; --text-title: #ffffff;
            --accent-blue: #2196f3; --accent-blue-hover: #1e88e5;
            --accent-red: #f44336; --accent-red-hover: #d32f2f;
            --accent-orange: #ff9800; --accent-green: #4caf50;
            --btn-bg: #3a3f4b; --btn-hover: #4b5263;
        }

        body { font-family: 'Segoe UI', Roboto, sans-serif; background-color: var(--bg-body); color: var(--text-main); margin: 0; display: flex; height: 100vh; overflow: hidden; }

        .sidebar { width: 250px; background-color: var(--bg-sidebar); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; }
        .brand { padding: 20px; font-size: 20px; font-weight: bold; color: var(--accent-red); display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--border-color); }
        .nav-item { padding: 15px 20px; color: var(--text-title); cursor: pointer; border-left: 3px solid transparent; transition: 0.2s; }
        .nav-item.active { background-color: rgba(33, 150, 243, 0.1); border-left: 3px solid var(--accent-blue); }
        .nav-item:hover:not(.active) { background-color: var(--bg-panel); }

        .main-content { flex: 1; display: flex; flex-direction: column; overflow-y: auto; }
        .topbar { background-color: var(--bg-panel); height: 60px; min-height: 60px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: flex-end; align-items: center; padding: 0 20px; }
        
        .btn-estop { background-color: var(--accent-red); color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: 0.2s; }
        .btn-estop:hover { background-color: var(--accent-red-hover); }
        .btn-estop:active { transform: scale(0.95); }

        .dashboard { padding: 20px; display: grid; grid-template-columns: 350px 1fr; grid-template-rows: auto auto; gap: 20px; align-items: start; }
        
        .panel { background-color: var(--bg-panel); border-radius: 6px; border: 1px solid var(--border-color); overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
        .panel-header { background-color: var(--bg-panel-header); padding: 12px 15px; font-weight: bold; color: var(--text-title); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }
        .panel-content { padding: 15px; }

        button { background-color: var(--btn-bg); color: var(--text-title); border: 1px solid var(--border-color); border-radius: 4px; padding: 8px 12px; cursor: pointer; transition: 0.2s; font-weight: 500; }
        button:hover { background-color: var(--btn-hover); }
        .btn-blue { background-color: var(--accent-blue); color: white; border-color: var(--accent-blue); }

        .jog-pad { display: grid; grid-template-columns: repeat(3, 50px); gap: 5px; justify-content: center; margin: 10px 0; }
        .vacio { background: transparent; border: none; }

        .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }
        .status-box { background-color: var(--bg-body); border: 1px solid var(--border-color); border-radius: 4px; padding: 10px; text-align: center; }
        .status-box .label { font-size: 11px; text-transform: uppercase; color: #7f848e; }
        .status-box .value { font-size: 20px; font-weight: bold; color: var(--text-title); font-family: monospace; }
        
        .hardware-state { display: flex; align-items: center; gap: 8px; font-size: 14px; justify-content: center; padding: 10px; background-color: var(--bg-body); border-radius: 4px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; background-color: #7f848e; }
        .dot.moving { background-color: var(--accent-orange); box-shadow: 0 0 8px var(--accent-orange); }
        .dot.idle { background-color: var(--accent-blue); }

        .consola { background-color: #000; color: #abb2bf; font-family: 'Consolas', monospace; padding: 10px; height: 120px; overflow-y: auto; border-radius: 4px; font-size: 12px; border: 1px solid var(--border-color); }

        .muro-panel { grid-column: 2 / 3; grid-row: 1 / 4; }
        .muro-grid { display: grid; grid-template-columns: repeat(12, 1fr); grid-template-rows: repeat(7, 1fr); width: 100%; aspect-ratio: 3102 / 3051; background: var(--bg-body); padding: 10px; border-radius: 6px; border: 1px solid var(--border-color); box-sizing: border-box; gap: 4px; }
        
        .maceta { background-color: var(--btn-bg); border-radius: 4px; cursor: pointer; transition: 0.2s; box-shadow: inset -1px -1px 3px rgba(0,0,0,0.5); }
        .maceta:hover { background-color: var(--btn-hover); }
        .maceta.activa { background-color: var(--accent-blue); box-shadow: 0 0 10px var(--accent-blue); }
        .maceta.moviendo { background-color: var(--accent-orange); box-shadow: 0 0 10px var(--accent-orange); }

        .config-container { padding: 20px; max-width: 800px; margin: 0 auto; display: none; }
        .wifi-list { background: var(--bg-body); border: 1px solid var(--border-color); border-radius: 4px; max-height: 300px; overflow-y: auto; margin-top: 15px; }
        .wifi-item { padding: 12px 15px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
        .wifi-ssid { font-weight: bold; color: var(--text-title); }
        .wifi-form { display: none; margin-top: 15px; background: var(--bg-body); padding: 15px; border-radius: 4px; border: 1px solid var(--border-color); }
        input[type="password"] { width: 100%; padding: 10px; background: var(--bg-panel); border: 1px solid var(--border-color); color: white; margin-bottom: 10px; }
        .alert { padding: 10px; border-radius: 4px; margin-top: 10px; display: none; }
        .alert.success { background: rgba(76, 175, 80, 0.2); color: var(--accent-green); }
        .alert.error { background: rgba(244, 67, 54, 0.2); color: var(--accent-red); }
    </style>
</head>
<body>

    <aside class="sidebar">
        <div class="brand">Muro Verde OS</div>
        <div class="nav-item active" id="nav-dashboard" onclick="cambiarVista('dashboard')">Dashboard</div>
        <div class="nav-item" id="nav-config" onclick="cambiarVista('config')">Configuración Wi-Fi</div>
    </aside>

    <main class="main-content">
        <header class="topbar">
            <button class="btn-estop" onclick="enviarGCode('M112')">🛑 EMERGENCY STOP</button>
        </header>

        <div class="dashboard" id="vista-dashboard">
            <div class="panel">
                <div class="panel-header"><span>Posición</span><span style="font-size:12px; opacity:0.5;">{{ estado }}</span></div>
                <div class="panel-content">
                    <div class="status-grid">
                        <div class="status-box"><div class="label">X (mm)</div><div class="value" id="coord-x">0.00</div></div>
                        <div class="status-box"><div class="label">Y (mm)</div><div class="value" id="coord-y">0.00</div></div>
                    </div>
                    <div class="hardware-state"><div class="dot" id="indicador-hw"></div><span id="texto-hw">IDLE</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">Control Manual (100mm)</div>
                <div class="panel-content">
                    <button class="btn-blue" style="width:100%; margin-bottom:10px;" onclick="enviarGCode('G1 X0 Y0 F8000 A15000')">🏠 HOME</button>
                    <div class="jog-pad">
                        <button class="vacio"></button><button onclick="jog(0, 100)">Y+</button><button class="vacio"></button>
                        <button onclick="jog(-100, 0)">X-</button><button onclick="enviarGCode('G92 X0 Y0')">G92</button><button onclick="jog(100, 0)">X+</button>
                        <button class="vacio"></button><button onclick="jog(0, -100)">Y-</button><button class="vacio"></button>
                    </div>
                </div>
            </div>

            <div class="panel"><div class="panel-content"><div class="consola" id="log">> Sistema listo.</div></div></div>
            
            <div class="panel muro-panel"><div class="muro-grid" id="grid"></div></div>
        </div>

        <div class="config-container" id="vista-config">
            <div class="panel">
                <div class="panel-header">Gestor de Redes</div>
                <div class="panel-content">
                    <button class="btn-blue" id="btn-scan" onclick="escanearWiFi()">🔄 Escanear Redes (Sudo Rescan)</button>
                    <div class="wifi-list" id="lista-redes"></div>
                    <div class="wifi-form" id="form-wifi">
                        <h4 id="ssid-seleccionado"></h4>
                        <input type="hidden" id="input-ssid">
                        <input type="password" id="input-password" placeholder="Contraseña">
                        <button class="btn-blue" onclick="conectarWiFi()">Conectar</button>
                        <div id="wifi-alert" class="alert"></div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        const PMM = 157.48; // Pasos por mm para varilla 1/4"
        const COL = 12; const FIL = 7;
        let tx = 0; let ty = 0; let macetaObjetivo = null;

        function log(msg) {
            document.getElementById('log').innerHTML += `<br>> ${msg}`;
            document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight;
        }

        function cambiarVista(v) {
            document.getElementById('vista-dashboard').style.display = v === 'dashboard' ? 'grid' : 'none';
            document.getElementById('vista-config').style.display = v === 'config' ? 'block' : 'none';
            document.getElementById('nav-dashboard').className = v === 'dashboard' ? 'nav-item active' : 'nav-item';
            document.getElementById('nav-config').className = v === 'config' ? 'nav-item active' : 'nav-item';
        }

        function jog(ox, oy) {
            tx += ox; ty += oy;
            enviarGCode(`G1 X${Math.round(tx * PMM)} Y${Math.round(ty * PMM)} F8000 A15000`);
        }

        function enviarGCode(g) {
            log(g);
            fetch('/api/comando', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ gcode: g }) });
        }

        // Generar Grid
        for (let i = 0; i < 84; i++) {
            const m = document.createElement('div'); m.className = 'maceta';
            m.onclick = () => {
                document.querySelectorAll('.maceta').forEach(x => x.classList.remove('activa', 'moviendo'));
                macetaObjetivo = m;
                let c = i % 12, r = Math.floor(i / 12);
                // Calculo de centro de maceta segun 3m
                tx = (c * 258) + 129; ty = ((6 - r) * 435) + 217;
                enviarGCode(`G1 X${Math.round(tx * PMM)} Y${Math.round(ty * PMM)} F8000 A15000`);
            };
            document.getElementById('grid').appendChild(m);
        }

        setInterval(() => {
            fetch('/api/estado').then(res => res.json()).then(data => {
                let rx = data.x_pasos / PMM; let ry = data.y_pasos / PMM;
                document.getElementById('coord-x').innerText = rx.toFixed(2);
                document.getElementById('coord-y').innerText = ry.toFixed(2);
                const isM = data.estado === "MOVING";
                document.getElementById('indicador-hw').className = isM ? "dot moving" : "dot idle";
                document.getElementById('texto-hw').innerText = isM ? "MOVING" : "IDLE";
                if(macetaObjetivo) {
                    macetaObjetivo.classList.toggle('moviendo', isM);
                    macetaObjetivo.classList.toggle('activa', !isM);
                }
                if(!isM) { tx = rx; ty = ry; }
            });
        }, 300);

        function escanearWiFi() {
            const l = document.getElementById('lista-redes');
            document.getElementById('btn-scan').innerText = "Escaneando activamente...";
            fetch('/api/wifi/scan').then(r => r.json()).then(data => {
                l.innerHTML = '';
                data.forEach(r => {
                    const d = document.createElement('div'); d.className = 'wifi-item';
                    d.innerHTML = `<span>📶 ${r.ssid}</span><span>${r.signal}%</span>`;
                    d.onclick = () => {
                        document.getElementById('form-wifi').style.display = 'block';
                        document.getElementById('ssid-seleccionado').innerText = "Unirse a: " + r.ssid;
                        document.getElementById('input-ssid').value = r.ssid;
                    };
                    l.appendChild(d);
                });
                document.getElementById('btn-scan').innerText = "🔄 Escanear Redes";
            });
        }

        function conectarWiFi() {
            const ssid = document.getElementById('input-ssid').value;
            const p = document.getElementById('input-password').value;
            const a = document.getElementById('wifi-alert');
            a.style.display = 'block'; a.innerText = "Conectando...";
            fetch('/api/wifi/connect', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ ssid: ssid, password: p }) })
            .then(r => r.json()).then(data => {
                a.innerText = data.success ? "Éxito. Reiniciando conexión..." : "Error: " + data.message;
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_PAGE, estado=estado_conexion)

@app.route('/api/comando', methods=['POST'])
def api_comando():
    cmd = request.json.get('gcode', '').upper()
    if conexion_serial and conexion_serial.is_open:
        conexion_serial.write(f"{cmd}\n".encode('utf-8'))
        conexion_serial.flush()
        if cmd != "M112": estado_cnc["estado"] = "MOVING"
    return jsonify({"status": "ok"})

@app.route('/api/estado')
def api_estado(): return jsonify(estado_cnc)

@app.route('/api/wifi/scan')
def wifi_scan():
    try:
        subprocess.run(['sudo', 'nmcli', 'dev', 'wifi', 'rescan'], capture_output=True)
        time.sleep(3)
        res = subprocess.check_output(['sudo', 'nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi', 'list']).decode('utf-8')
        redes = []
        vistos = set()
        for l in res.split('\n'):
            if l:
                p = l.split(':')
                if len(p) >= 2 and p[0] and p[0] not in vistos:
                    redes.append({"ssid": p[0], "signal": p[1], "security": p[2] if len(p)>2 else ""})
                    vistos.add(p[0])
        return jsonify(redes)
    except: return jsonify([])

@app.route('/api/wifi/connect', methods=['POST'])
def wifi_connect():
    d = request.json
    try:
        subprocess.run(['sudo', 'nmcli', 'dev', 'wifi', 'connect', d['ssid'], 'password', d['password']], timeout=20)
        return jsonify({"success": True})
    except: return jsonify({"success": False, "message": "Fallo en conexión"})

if __name__ == '__main__':
    os.system("fuser -k 5000/tcp > /dev/null 2>&1")
    app.run(host='0.0.0.0', port=5000)