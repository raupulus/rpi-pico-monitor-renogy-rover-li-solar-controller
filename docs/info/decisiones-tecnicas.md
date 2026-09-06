# Decisiones Técnicas

Registro de decisiones deliberadas de arquitectura y diseño tomadas en el proyecto para evitar regresiones o intentos erróneos de «arreglar» comportamientos intencionados.

## 1. Driver Modbus RTU directo sobre UART en lugar de `pymodbus`
- **Contexto**: El proyecto original o implementaciones estándar en Python usan `pymodbus` o `minimalmodbus`.
- **Decisión**: Se implementó una clase ligera [`SerialConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/SerialConnection.py) basada directamente en `machine.UART` y cálculo manual de CRC-16 Modbus (polinomio `0xA001`, formato little-endian).
- **Motivo**: MicroPython en Raspberry Pi Pico (RP2040) cuenta con recursos de memoria RAM muy reducidos (264 KB totales) y carece de soporte directo para las dependencias pesadas de `pymodbus`.
- **Consecuencia**: No se deben introducir dependencias externas de protocolos serie que no sean puras o optimizadas para MicroPython.

## 2. Caché en memoria para registros estáticos del controlador
- **Contexto**: La lectura de múltiples registros por UART a 9600 baudios introduce latencia y congestión en el bus RS232.
- **Decisión**: En [`RenogyRoverLi`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py), los parámetros de hardware, versión de firmware, número de serie, capacidad nominal, tipo de batería y voltaje de trabajo del sistema se leen una sola vez durante la inicialización (`_initialize_static_data`) y se mantienen en variables de clase `_cached_*`.
- **Motivo**: Estos valores no varían durante el ciclo de vida del controlador y consultar el bus serie repetidamente incrementa el riesgo de colisión o timeout.
- **Consecuencia**: Si el controlador solar cambiase de configuración en caliente (por ejemplo, cambio de tipo de batería físico), se requiere reiniciar la Pico para refrescar la caché.

## 3. Uso de `dict.update()` en lugar de desempaquetado con `**`
- **Contexto**: En CPython moderno es común combinar diccionarios con `{**a, **b}`.
- **Decisión**: Toda combinación de payloads de métricas se realiza mediante llamadas explícitas a `dict.update()`.
- **Motivo**: En varias versiones del intérprete MicroPython en RP2040, el desempaquetado de argumentos por diccionario `**` dentro de literales dict genera errores de sintaxis o fallos de asignación en tiempo de ejecución.

## 4. Uso de pausa simple `time.sleep()` frente a `machine.light_sleep()`
- **Contexto**: Para ahorro energético en microcontroladores se evalúa `machine.light_sleep()`.
- **Decisión**: Se mantiene `time.sleep(seconds)` estándar en la función [`sleep_pause()`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py#L104-L118).
- **Motivo**: En pruebas sobre la Raspberry Pi Pico W, `light_sleep` provoca bloqueos del reloj interno, desconexiones irrecuperables del chip WiFi CYW43439 o fallos al reanudar los hilos de interrupción de UART.

## 5. Sanitización ASCII de cadenas para la API REST de Home Assistant
- **Contexto**: Las respuestas JSON hacia Home Assistant pueden contener cadenas con caracteres especiales como `°` (grados), `ñ` o vocales con tildes.
- **Decisión**: Se implementó [`_sanitize_string()`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py#L182-L218) que sustituye estos caracteres por equivalentes ASCII simples antes de componer el payload JSON.
- **Motivo**: `urequests` y el servidor HTTP de Home Assistant rechazan payloads con el error `Invalid JSON specified` si la codificación UTF-8 no se alinea estrictamente byte a byte en la capa de transporte MicroPython.

## 6. Heurística de estado y brillo de luz de calle por tensión solar
- **Contexto**: El registro Modbus `0x0120` debería reflejar el estado de la salida de carga (street light).
- **Decisión**: En [`RenogyRoverLi.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py#L510-L552), `get_street_light_status` y `get_street_light_brightness` calculan los valores interpolando la tensión del panel solar (`solar_voltage`) entre 12.3V y 41.5V (diseñado para strings de paneles de hasta ~40V).
- **Motivo**: El registro físico del controlador Renogy Rover Li suele devolver ceros o lecturas erráticas en este campo específico según pruebas en banco de pruebas.
- **Consecuencia**: No modificar esta lógica sin comprobar previamente con lecturas de osciloscopio o peticiones Modbus directas contra el modelo físico específico de controlador.

## 7. Agrupación bajo dispositivo único en Home Assistant y throttle de la entidad raíz
- **Contexto**: Home Assistant crea sensores sueltos si no se suministra un objeto `device` coherente con `identifiers`.
- **Decisión**: Todas las entidades inyectan en sus atributos el diccionario `device` con identificador `renogy_rover_li_<DEVICE_ID>` y se mantiene una entidad raíz `sensor.renogy_rover_li_<DEVICE_ID>_device` que sólo se refresca cada 3600 segundos (1 hora).
- **Motivo**: Garantizar que todas las entidades aparezcan agrupadas en la interfaz de Home Assistant bajo un único dispositivo físico, sin saturar la base de datos de HA (`recorder`) con actualizaciones repetitivas del sensor de timestamp.

## 8. Recolección periódica explícita de basura (`gc.collect()`)
- **Contexto**: En MicroPython, la creación de sockets TCP HTTP repetidos y tramas serie fragmenta el montículo (heap).
- **Decisión**: Se ejecuta [`collect_garbage()`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py#L120-L131) al finalizar cada iteración del bucle principal.
- **Motivo**: Evitar fallos de `MemoryError` inesperados tras horas o días de funcionamiento continuo.

## 9. Adopción de API V2 Full REST y telemetría de salud en `hardware_device_info`
- **Contexto**: La API de telemetría del ecosistema evolucionó de endpoints heterogéneos bajo `/hardware` a una arquitectura Full REST bajo `/api/v2/energy/solar-readings` gobernada por Laravel Sanctum con la ability `energy:write`.
- **Decisión**: [`Api.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py) adopta los nombres de campo oficiales del contrato V2 (`voltage`, `amperage`, `power`, `temperature` para el controlador, etc.) y encapsula el estado vital del microcontrolador dentro del bloque anidado `hardware_device_info` (temperatura de CPU, porcentaje de RAM, uptime en segundos, IP local y RSSI).
- **Motivo**: El backend procesa el estado de salud del hardware receptor dentro de la misma transacción atómica de energía, evitando requerir la ability `hardware:write` y suprimiendo una segunda petición HTTP periódica desde la Pico.
- **Consecuencia**: Todo token de autenticación debe poseer la ability `energy:write`. Rutas anteriores devuelven HTTP 404 y carecen de soporte.

## 10. Reconexión WiFi no bloqueante, reciclado de radio CYW43439 y watchdog de software
- **Contexto**: Tras días de operación continua, cortes temporales de red WiFi o reinicios del router doméstico provocaban que la Raspberry Pi Pico W quedara colgada indefinidamente.
- **Decisión**:
  1. Se eliminó el bucle bloqueante infinito `while not wifi.isconnected()` y los escaneos repetitivos `wifi.scan()` en [`RpiPico.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RpiPico.py).
  2. Cada intento de reconexión limpia recicla la interfaz WLAN (`wlan.disconnect()`, `wlan.active(False)`, `wlan.active(True)`) y re-desactiva el ahorro de energía (`wlan.config(pm=0xa11140)`).
  3. En cada ciclo de [`main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py), se llama a `rpi_pico.ensure_wifi_connected(timeout=WIFI_CONNECT_TIMEOUT)`. Si el enlace está caído, se omiten las peticiones HTTP (API y Home Assistant) para no generar llamadas a sockets abocadas al fracaso.
  4. Si la desconexión persiste más de `MAX_OFFLINE_CYCLES` ciclos consecutivos (aprox. 15-25 minutos), se invoca `machine.reset()` para forzar un reinicio limpio del microcontrolador y su coprocesador de radio.
- **Motivo**: El driver MicroPython del chip Infineon CYW43439 puede entrar en estados no recuperables ante caídas prolongadas de enlace; un intento directo con timeout y un watchdog por software garantizan funcionamiento 100% autónomo y desatendido.
- **Consecuencia**: No volver a introducir llamadas bloqueantes infinitas a la red ni intentar peticiones HTTP sin verificar previamente `wifi_is_connected()`.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
