# API local y protocolo serial

Esta referencia se obtuvo del código V2 recibido. No documenta firmware verificado ni añade endpoints nuevos.

## Navegación

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/` | Redirección al acceso. |
| GET / POST | `/login` | Formulario; recibe `usuario` y `password`. Acceso inválido: 401. |
| GET | `/logout` | Elimina la marca de sesión y redirige al acceso. |
| GET | `/panel` | Dashboard CNC, requiere sesión. |
| GET | `/red_wifi` | Datos de red, requiere sesión. |
| GET | `/sistema` | Telemetría, requiere sesión. |
| GET | `/logo.png` | PNG desde la ruta absoluta de la Pi. |

## Endpoints JSON

| Método | Ruta | Sesión requerida | Contenido |
| --- | --- | --- | --- |
| GET | `/api/estado` | No en el respaldo | `x_pasos`, `y_pasos`, `estado`. |
| GET | `/api/telemetria` | Sí | `uptime`, `temp`, `cpu_loads`, `ram_total`, `ram_usada`, `ram_porc`, `disco_total`, `disco_usado`, `disco_porc`. |
| GET | `/api/config` | Sí | Configuración actual: `v_max`, `a_max`. |
| POST | `/api/config` | Sí | Recibe `v_max` y `a_max`; devuelve `status` y `config`. |
| POST | `/api/comando` | Sí | Recibe `gcode`; responde con `status: "ok"`. |

Las rutas JSON protegidas responden `401` y `{"error":"Auth"}` si no hay sesión. Los POST esperan `Content-Type: application/json`. No hay validación completa de tipos, rangos o límites mecánicos.

Ejemplo de estado (ilustrativo):

```json
{"x_pasos": 0, "y_pasos": 0, "estado": "IDLE"}
```

**La respuesta HTTP `ok` no confirma ejecución física:** V2 también la devuelve si no existe conexión serial. El estado del servidor y los mensajes de la Pico son señales distintas.

## Mensajes seriales observados

Puerto configurado: `/dev/ttyACM0`. Velocidad: 115200 baudios. Mensajes de texto terminados en `\n`.

| Mensaje | Uso en el servidor o interfaz |
| --- | --- |
| `G1 X… Y… F… A…` | Solicitud de movimiento; coordenadas enviadas en pasos. `F` y `A` proceden de la configuración. |
| `G92 X… Y…` | Sincronización de coordenadas al conectar o solicitud de fijar cero desde la interfaz. |
| `M112` | Botón de paro de emergencia. Su efecto real depende del firmware. |
| `M17` | Botón para trabar motores. |
| `M18` | Botón para liberar motores. |
| `POS <x> <y>` | Mensaje recibido: dos enteros que V2 interpreta como posición en pasos. |
| `OK` | Mensaje recibido: cambia a `IDLE` y persiste el estado. |

No se presupone compatibilidad con cualquier controlador G-Code: el parámetro `A`, las unidades de `F` y la semántica precisa de cada comando dependen del firmware ausente. La interfaz genera el formato de la tabla, pero la API reenvía cualquier cadena recibida en `gcode`.
