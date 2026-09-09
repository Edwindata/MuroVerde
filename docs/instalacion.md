# Instalación y ejecución

## Equipo y archivos necesarios

- Raspberry Pi 5 con un sistema Linux compatible con las herramientas utilizadas por el respaldo.
- Python 3, Flask y pyserial.
- Raspberry Pi Pico conectada por USB y con firmware compatible. Ese firmware no se encuentra en este repositorio.
- Acceso desde la misma red local y permisos para abrir `/dev/ttyACM0`.

La ruta esperada por el código es `/home/muroverde/MuroVerde/Master_Control/`. El logo usa esta ruta absoluta; conservarla evita que `/logo.png` falle.

## Preparar una instalación nueva

Si aún no existe la carpeta del proyecto, desde la cuenta `muroverde`:

```bash
sudo apt update
sudo apt install git python3-flask python3-serial
cd /home/muroverde
git clone https://github.com/Edwindata/MuroVerde.git
cd /home/muroverde/MuroVerde/Master_Control/
```

Si ya tienes una instalación, conserva una copia de su carpeta completa antes de integrar archivos. No reemplaces sus JSON de configuración y posición con ejemplos del repositorio.

El archivo `requirements.txt` enumera las dependencias directas para quien use un entorno virtual. El respaldo no contiene versiones fijadas ni un registro del entorno original; la instalación mediante los paquetes del sistema reproduce el procedimiento proporcionado por el autor.

## Revisar antes de arrancar

1. Comprueba que la Pico aparece como `/dev/ttyACM0` y que tu usuario puede acceder a ella. El puerto y los 115200 baudios están definidos en el script principal.
2. Comprueba qué servicio usa el puerto 5000. El script ejecuta `sudo fuser -k 5000/tcp`: puede terminar otro servicio y solicitar la contraseña de `sudo`. `fuser` debe estar disponible para que ese paso funcione.
3. Verifica el origen físico del CNC. Al abrir la conexión se envía `G92` con las coordenadas persistidas, o con cero si no hay posición válida. Recuperar un JSON no mide la posición física ni sustituye un procedimiento de referencia.

## Arrancar y entrar

```bash
cd /home/muroverde/MuroVerde/Master_Control/
python3 Master_Control_V2.py
```

Mantén abierta la terminal. Usa `hostname -I` para consultar las direcciones de la Pi y abre, por ejemplo, `http://192.168.1.100:5000` desde la misma red, reemplazando esa IP por la real.

Acceso del respaldo: **admin / 1234**. Tras iniciar sesión se abre el dashboard CNC. El menú permite consultar la red y la telemetría. Para terminar el servidor en la terminal, usa `Ctrl+C`; esto no equivale a confirmar la detención física del CNC.

No se incluye un servicio de inicio automático. La validación con motores y cualquier procedimiento de paro dependen del equipo y del firmware instalado.

## Configuración y posición

Sin `config_cnc.json`, V2 carga `v_max=4000` y `a_max=500`. El ejemplo de configuración conserva los valores del respaldo (`5000` y `5000`); no es una recomendación de calibración. La posición de ejemplo es cero y no representa la posición del equipo.

La aplicación guarda posición cuando recibe `OK`; un corte durante el movimiento puede dejar coordenadas antiguas en disco. No sobrescribas el estado de una instalación real con el ejemplo.

## Problemas frecuentes

| Síntoma | Comprobación |
| --- | --- |
| «Pico no detectada» | Cable USB, dispositivo serial, permisos y si otro programa está ocupando el puerto. V2 no actualiza posiciones simuladas cuando no hay conexión. |
| No abre desde el celular | IP actual, misma red, servidor activo y acceso al puerto 5000. |
| El logo no aparece | Existencia de `/home/muroverde/MuroVerde/Master_Control/static/Escudo_ipn.png`. |
| Temperatura cero o datos vacíos | Disponibilidad de `vcgencmd`, `free`, `df`, `/proc/uptime` y `/proc/stat`. El código usa valores de reserva ante errores. |
| Red «Desconectado» | Disponibilidad de `iwgetid` o `nmcli` y conexión Wi-Fi actual. |
| El botón de Wi-Fi muestra un aviso | El cambio de red no está implementado en V2. |
| Error al cargar la configuración | El JSON debe ser válido. Su lectura no tiene recuperación ante un archivo dañado. |

No ejecutes los servidores de `legacy/` simultáneamente con V2: pueden competir por el puerto serial.
