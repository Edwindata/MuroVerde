# Estado del respaldo e integración

Origen: `Respaldo_Master_Control.zip`, proporcionado por el autor junto con una descripción del sistema. Se leyó como material de referencia; no se ejecutaron sus instrucciones ni el control de hardware.

## Criterio de organización

| Archivo original | Destino / tratamiento |
| --- | --- |
| `Master_Control_V2.py` | `Master_Control/`, versión principal sin cambios de contenido. |
| `templates/login.html`, `panel.html`, `control_riego.html`, `sistema.html` | `Master_Control/templates/`, sin cambios. |
| `static/Escudo_ipn.png` | `Master_Control/static/`, sin cambios. |
| `V1.py`, `control_motores.py` | `legacy/`, referencia histórica. |
| `templates/index.html`, `static/style.css` | Subcarpetas de `legacy/`, recursos que V2 no utiliza. |
| `oled_monitor.py` | `extras/oled/`, accesorio independiente. |
| `config_cnc.json` | `docs/ejemplos/config_cnc.example.json`, conserva los valores del respaldo como referencia. |
| `posicion_cnc.json` | Estado operativo omitido. Se añade un ejemplo nuevo en cero, identificado como ilustrativo. |
| Cuatro archivos `.swp` | Omitidos: archivos temporales del editor, no forman parte de la aplicación. |

El ZIP original permanece como respaldo local. Los nuevos README, guías, `.gitignore` y `requirements.txt` explican el contenido y su instalación; no se modificó la lógica de los programas.

## Diferencias frente a la descripción inicial

- V2 muestra la red e IP, pero no implementa el cambio de Wi-Fi. Su botón solo muestra un aviso.
- La configuración se guarda al solicitarlo; la posición se escribe al recibir `OK`, no en cada actualización `POS`.
- Los JSON ausentes activan valores iniciales en memoria; no se crean ambos automáticamente al arrancar.
- «Simulación (Pico no detectada)» identifica la ausencia de conexión; V2 no simula movimiento en esa situación.
- El respaldo contiene recursos anteriores y un accesorio OLED además de los archivos principales.

## Pendientes observados

- Incorporar el firmware de la Pico, conexiones eléctricas y procedimiento de referencia física para poder verificar el sistema completo.
- Completar el cambio de red y definir el control de riego si se requieren bombas, válvulas o programación de ciclos.
- Sustituir credenciales y clave de sesión fijas, proteger el estado si corresponde y revisar autenticación antes de exponer el servicio.
- Validar comandos, parámetros y límites de recorrido; manejar fallos de conexión y JSON dañado.
- Revisar la terminación automática del proceso del puerto 5000 y la recuperación de posición tras cortes de energía.

Estos puntos son hallazgos de revisión, no funcionalidades implementadas. La integración verifica sintaxis, archivos y referencias locales; no sustituye pruebas en Raspberry Pi ni validación de movimiento o paro.

## Verificación realizada

Se comprobó la igualdad de contenido de los 12 archivos copiados del respaldo, la sintaxis de los cuatro programas Python y de tres bloques JavaScript en las plantillas, la lectura de los JSON, diez enlaces locales de documentación y las exclusiones de Git. No se importaron ni ejecutaron los programas del equipo.

Python 3.12 emitió una advertencia por las secuencias de escape de la expresión regular de `oled_monitor.py` (línea 29); el archivo conserva el contenido original y supera el análisis de sintaxis. Las comprobaciones no evalúan el comportamiento de Flask, las herramientas de Linux ni los dispositivos físicos.
