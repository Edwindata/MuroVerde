# Versiones y recursos anteriores

Esta carpeta conserva archivos del respaldo que no son necesarios para ejecutar V2. Se mantienen sin cambios como referencia; su ubicación aquí no los convierte en instalaciones autónomas listas para ejecutar.

| Archivo | Descripción |
| --- | --- |
| `V1.py` | Servidor previo con interfaz HTML integrada, puerto serial `/dev/pico_muroverde` y rutas propias de escaneo/conexión Wi-Fi. |
| `control_motores.py` | Servidor de control en puerto 5001, sin acceso por sesión y con actualización simulada de coordenadas cuando no hay Pico. Espera `templates/control_riego.html`, que ahora está en la carpeta principal. |
| `templates/index.html` | Pantalla anterior de red: utiliza `/api/scan` y `/api/connect`, rutas que V2 no implementa. |
| `static/style.css` | Hoja de estilo utilizada por esa pantalla anterior. |

El punto de entrada actual es [Master_Control_V2.py](../Master_Control/Master_Control_V2.py). No ejecutes varios servidores sobre la misma Pico. Para recuperar una versión anterior habría que revisar sus rutas y dependencias; no se cambió su comportamiento en esta integración.

[Volver al proyecto](../README.md)
