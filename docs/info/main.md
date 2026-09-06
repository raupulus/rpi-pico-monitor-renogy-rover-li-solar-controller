# Módulo: main

Orquestador principal y bucle continuo de telemetría del monitor solar en [`src/main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py).

## Qué hace y qué NO hace
- **Qué hace**:
  - Carga la configuración desde `env.py` (o recurre a valores por defecto seguros).
  - Inicializa los subsistemas de hardware ([`RpiPico`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RpiPico.py)), serie ([`SerialConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/SerialConnection.py)), controlador solar ([`RenogyRoverLi`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py)) y clientes HTTP ([`Api`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py) y [`HomeAssistantConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py)).
  - Sincroniza la hora del RTC con servidores NTP a través de `ntptime`.
  - Comprueba activamente la conexión WiFi en cada ciclo con `ensure_wifi_connected(timeout=WIFI_CONNECT_TIMEOUT)`.
  - Reintenta reconexiones limpias de forma no bloqueante si el router se apaga o la señal cae.
  - Mantiene un contador de ciclos offline (`offline_cycles`) y ejecuta reinicio preventivo por software (`machine.reset()`) si se supera `MAX_OFFLINE_CYCLES` para purgar el chip CYW43439 ante congelamiento prolongado.
  - Sincroniza automáticamente la hora NTP en cuanto el enlace WiFi se restablece tras una desconexión.
  - Omite intentos de subida HTTP (API y Home Assistant) cuando no hay WiFi, evitando bloqueos por timeout y fugas de sockets.
  - Ejecuta el bucle continuo `loop()`: lee métricas del controlador y de la placa, las envía a los endpoints configurados y gestiona pausas.
  - Ejecuta `gc.collect()` tras cada ciclo para limpiar memoria y evitar fragmentación del heap.
  - Controla la señalización visual de LEDs (ciclo, subida, error, encendido).
- **Qué NO hace**:
  - No calcula CRC ni manipula tramas UART directamente (delegado a [`SerialConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/SerialConnection.py)).
  - No interpreta registros Modbus en crudo (delegado a [`RenogyRoverLi`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py)).
  - No formatea entidades para Home Assistant (delegado a [`HomeAssistantConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py)).

## Modelo de datos
Gestiona el diccionario unificado de métricas devuelto por [`RenogyRoverLi.get_all_datas()`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py#L427-L442):
- Diccionario plano que incluye claves de batería, placas solares, carga, registros diarios e históricos acumulados.

## Flujos principales
1. **Arranque e Inicialización**:
   - `main()` instancia `RpiPico` e intenta conectar a WiFi con timeout acotado.
   - Enciende el LED de Power y sincroniza reloj NTP (`sync_time()`).
   - Inicializa el driver UART en los pines `SERIAL_TX_PIN` y `SERIAL_RX_PIN`.
   - Inicializa el modelo `RenogyRoverLi`, que precarga la información estática del dispositivo.
   - Inicializa clientes de API y Home Assistant si están habilitados en `env.py`.
2. **Ciclo de Telemetría**:
   - **Comprobación WiFi**: Llama a `rpi_pico.ensure_wifi_connected(timeout=WIFI_CONNECT_TIMEOUT)`. Si falla, incrementa `offline_cycles`; si supera `MAX_OFFLINE_CYCLES`, reinicia con `machine.reset()`. Si se recupera, sincroniza NTP y resetea el contador.
   - **Lectura Modbus**: Enciende `led_cycle`, lee métricas del controlador solar y apaga `led_cycle`.
   - **Subida a API**: Si `UPLOAD_API = True` y `wifi_is_connected()`: activa `led_upload`, envía a la API externa mediante `api.send_to_api(params)` y apaga `led_upload`.
   - **Subida a Home Assistant**: Si `UPLOAD_HOME_ASSISTANT = True` y `wifi_is_connected()`: activa `led_upload`, verifica dispositivo y actualiza sensores mediante `home_assistant.update_solar_controller_data(params)` y `update_microcontroller_sensors()`, apagando `led_upload`.
   - **Finalización**: Emite parpadeo simple de confirmación en LED integrado, recolecta basura con `collect_garbage()` y duerme `SLEEP_TIME` segundos mediante `sleep_pause()`.
3. **Manejo de Excepciones**:
   - Parpadea 5 veces de forma rápida el LED integrado ante error y duerme `SLEEP_TIME` segundos antes de reintentar.
   - Si se produce un fallo crítico fuera del bucle protegido en `main()`, espera 10 segundos y reinicia el microcontrolador con `machine.reset()`.

## Puntos de entrada
| Función | Parámetros | Retorno | Requisitos |
|---|---|---|---|
| `main()` | Ninguno | Ninguno (bucle infinito) | Archivo `env.py` accesible |
| `loop()` | Ninguno | Ninguno (bucle continuo) | Microcontrolador inicializado |
| `sync_time()` | Ninguno | `bool` | Conexión WiFi activa |
| `collect_garbage()` | Ninguno | `None` | Ninguno |
| `sleep_pause(seconds)` | `seconds: int` | `None` | Ninguno |

## Dependencias
- **Dependencias entrantes**: Ninguna (es el punto de entrada ejecutado automáticamente por MicroPython al arrancar el archivo `main.py`).
- **Dependencias salientes**:
  - `machine`, `time`, `gc`, `ntptime`
  - [`Models.RpiPico`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RpiPico.py)
  - [`Models.SerialConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/SerialConnection.py)
  - [`Models.RenogyRoverLi`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py)
  - [`Models.Api`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py)
  - [`Models.HomeAssistantConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py)

## Configuración
Variables en `env.py`:
- `DEBUG` (`bool`): Habilita trazas detalladas por consola serie.
- `SLEEP_TIME` (`int`): Tiempo de espera entre lecturas (segundos, por defecto 60).
- `WIFI_CONNECT_TIMEOUT` (`int`): Timeout máximo de asociación WiFi por intento (por defecto 15s).
- `MAX_OFFLINE_CYCLES` (`int`): Ciclos offline consecutivos antes de reinicio preventivo por software (por defecto 15).
- `UPLOAD_API` (`bool`): Activa subida a API REST propia.
- `UPLOAD_HOME_ASSISTANT` (`bool`): Activa subida a Home Assistant.
- `SERIAL_TX_PIN` (`int`), `SERIAL_RX_PIN` (`int`): Pines UART0.

## Trampas conocidas
- No usar `machine.light_sleep()` en `sleep_pause()`; congela el stack WiFi en Pico W.
- No omitir la verificación de WiFi antes de peticiones HTTP: intentar abrir sockets cuando la ruta está caída causa saturación de bloques TCP PCB en lwIP y agotamiento de memoria (`ENOMEM`).

## Tests que lo cubren
- Verificación en banco conectando a consola REPL y observando el ciclo completo.

## Pendiente real
- Ninguno.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
