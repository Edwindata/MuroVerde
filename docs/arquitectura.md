# Arquitectura y datos

## Componentes

| Componente | Responsabilidad |
| --- | --- |
| `Master_Control_V2.py` | Servir HTML y API con Flask; gestionar sesión, conexión serial y archivos JSON. |
| `templates/control_riego.html` | Mostrar la cuadrícula CNC, convertir milímetros a pasos y enviar comandos. |
| `templates/sistema.html` | Consultar y mostrar temperatura, CPU, memoria, disco y tiempo activo. |
| `templates/panel.html` | Mostrar SSID e IP. El cambio de Wi-Fi es un aviso de función en desarrollo. |
| `templates/login.html` | Formulario de acceso. |
| Pico | Ejecutar el protocolo de movimiento. Su implementación no está incluida. |

Flask escucha en `0.0.0.0:5000`, con hilos habilitados y sin recargador. La conexión serial y el hilo lector se crean al cargar el módulo, por lo que importar el script también tiene efectos sobre el hardware.

## Flujo de movimiento

1. El usuario selecciona una celda o utiliza un control manual.
2. El navegador envía un JSON con `gcode` a `/api/comando`.
3. El servidor convierte el comando a mayúsculas y lo escribe por serial, terminado en salto de línea.
4. Un hilo revisa la recepción aproximadamente cada 10 ms, conserva fragmentos incompletos y procesa líneas completas.
5. Los mensajes con `POS` actualizan coordenadas y marcan `MOVING`; los que contienen `OK` marcan `IDLE` y guardan la posición.
6. El navegador consulta `/api/estado` cada 300 ms y actualiza coordenadas y colores.

La interfaz utiliza `comandoEnVuelo` para retrasar cambios visuales de estado hasta 500 ms después de que termina la petición del comando. Es una medida de presentación; no constituye una confirmación de movimiento ni garantiza ausencia de parpadeos.

## Geometría incluida

La cuadrícula tiene 12 columnas y 7 filas. El frontend define un área de 3102 × 3051 mm y 157.48 pasos por milímetro en ambos ejes. Estos valores están escritos en el HTML y deben contrastarse con la máquina real; no fueron calibrados durante esta integración.

## Persistencia

| Archivo local | Contenido | Momento de escritura |
| --- | --- | --- |
| `config_cnc.json` | `v_max`, `a_max` | Al guardar desde `/api/config`. |
| `posicion_cnc.json` | `x_pasos`, `y_pasos`, `estado` | Al detectar `OK` en la lectura serial. |

El archivo de posición se escribe primero como `.tmp` y después se reemplaza. Esto reduce la posibilidad de un JSON parcial, pero no garantiza conservar la última posición física ante un corte. Al conectar, V2 transmite las coordenadas recuperadas mediante `G92`.

## Telemetría

La pantalla consulta la API cada 2 segundos. Se leen `/proc/uptime`, `/proc/stat` y las salidas de `vcgencmd measure_temp`, `free -m` y `df -h /`. El código calcula uso de cuatro núcleos a partir de diferencias entre lecturas; la primera muestra no representa necesariamente el intervalo de dos segundos. Para red se utilizan `iwgetid` y, como alternativa, `nmcli`.
