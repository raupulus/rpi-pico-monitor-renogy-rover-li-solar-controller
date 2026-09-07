# Decisiones Técnicas y Arquitectura

Registro de decisiones deliberadas de arquitectura y diseño tomadas en el proyecto, con su contexto, motivación y consecuencias prácticas.

## 1. Uso de UART por Hardware en Lugar de Bit-Banging
- **Contexto**: El microcontrolador RP2040 dispone de dos periféricos UART dedicados (`UART0` y `UART1`).
- **Decisión**: Se utiliza `machine.UART(0)` mapeado a pines físicos GPIO 0 (TX) y GPIO 1 (RX) a 9600 baudios, 8N1.
- **Motivo**: La temporización de Modbus RTU exige intervalos de guarda entre caracteres de 3.5 tiempos de carácter. El bit-banging por software en MicroPython genera jitter que corrompe tramas aleatoriamente.
- **Consecuencia**: No reasignar pines UART a pines que no correspondan con los bloques hardware del RP2040.

## 2. Caché de Registros Estáticos durante el Arranque
- **Contexto**: Registros como número de serie, modelo, versión de firmware y tensiones nominales no varían durante el funcionamiento del sistema.
- **Decisión**: [`RenogyRoverLi.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py) consulta estos registros una única vez en `_initialize_static_data()` y los almacena en memoria de clase.
- **Motivo**: Reduce el número de transacciones Modbus por ciclo en más de 8 consultas redundantes, acortando el tiempo total de polling.
- **Consecuencia**: Si el controlador solar se reinicia o cambia de configuración mientras el monitor sigue encendido, los datos estáticos no se refrescan hasta el próximo reinicio de la Pico.

## 3. Estimación de Luz de Farola por Tensión de Paneles
- **Contexto**: La especificación Modbus documenta el registro `0x0120` para indicar el brillo y estado de la salida de alumbrado público, pero diversos firmwares devuelven valores incongruentes o estáticos.
- **Decisión**: Se calcula una estimación analógica proporcional basada en la tensión del panel solar entre 12.3 V (0%) y 41.5 V (100%).
- **Motivo**: Proporciona una métrica consistente y continua independientemente de la versión de firmware del controlador Renogy.

## 4. Agrupación Lógica en Home Assistant vía Diccionario `device`
- **Contexto**: Home Assistant creaba entidades dispersas sin vincularlas a un único aparato físico dentro de su registro.
- **Decisión**: [`HomeAssistantConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py) inyecta el mismo diccionario `device` con identificador único determinista (`renogy_rover_li_<DEVICE_ID>`) en todos los payloads enviados a `/api/states/`.
- **Motivo**: Permite que Home Assistant reconozca automáticamente todos los sensores como pertenecientes a un único dispositivo "Controlador Solar Renogy Rover Li", permitiendo asignación a áreas y tarjetas unificadas en Lovelace.
- **Consecuencia**: Los identificadores deben coincidir estrictamente en cada sensor.

## 5. Cierre Forzado de Sockets HTTP en MicroPython
- **Contexto**: El stack de red LWIP en MicroPython sobre Raspberry Pi Pico W cuenta con un pool muy limitado de descriptores de sockets (típicamente 4 concurrentes).
- **Decisión**: Tanto en [`Api.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py) como en [`HomeAssistantConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py) las peticiones `urequests` envuelven la respuesta en un bloque `finally:` que invoca `response.close()` y posteriormente llama a `gc.collect()`.
- **Motivo**: Evitar fugas de descriptores de socket que provocan fallos irrecuperables de memoria (`OSError: ENOMEM`) tras horas o días de ejecución continua.

## 6. Pausa Simple en Bucle con `time.sleep()` en Lugar de `machine.lightsleep()`
- **Contexto**: MicroPython soporta modos de suspensión ligera para reducir consumo de energía.
- **Decisión**: El bucle principal en [`main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py) utiliza pausas en bloques de 1 segundo con `time.sleep(1)` en lugar de `lightsleep()`.
- **Motivo**: `lightsleep()` interfiere con el reloj interno del chip WiFi CYW43439 y suspende los periféricos UART y temporizadores del sistema, provocando pérdidas de conexión de red inexplicables al despertar.

## 7. Retroceso Exponencial con Límite de Reintentos
- **Contexto**: Caídas transitorias de la red WiFi o microcortes en el servidor Home Assistant / API provocaban cuelgues o bucles infinitos de reconexión.
- **Decisión**: Todas las llamadas de red implementan bucles de hasta 3 reintentos con cálculo de tiempo de espera: $\text{espera} = \text{backoff\_factor} \times 2^{\text{intento}}$.
- **Motivo**: Ofrece resiliencia ante cortes momentáneos sin bloquear indefinidamente la ejecución del bucle de telemetría.

## 8. Sanitización de Textos para Home Assistant
- **Contexto**: Nombres de métricas o atributos que contenían caracteres especiales como `°` provocaban errores de serialización o respuestas HTTP 400 por parte de Home Assistant.
- **Decisión**: Se implementó `_sanitize_string()` y `_sanitize_attributes()` en [`HomeAssistantConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py) para reemplazar caracteres no compatibles por secuencias ASCII seguras.

## 9. Adopción del Contrato API V2 (/energy/solar-readings) y Fusión de Salud Hardware
- **Contexto**: La API remota evolucionó hacia una arquitectura REST pura v2 donde la telemetría energética se desacopla del hardware base.
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

## 11. Balance neto de batería y enriquecimiento de telemetría en `hardware_device_info.extra`
- **Contexto**: Los campos `battery_current` y `battery_power` en la API se subían como `null` al no existir un sensor directo de corriente neta en el bus de batería. Asimismo, se requería incorporar diagnósticos del regulador (corriente de carga directa a batería, interruptor de carga DC y códigos de error/alarma) sin violar el contrato estricto de la API V2.
- **Decisión**:
  1. En [`RenogyRoverLi.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py):
     - Se corrigieron las direcciones en `sectionMap`: `today_max_charging_power` a `0x010F` (antes `0x010D`) y `today_max_discharging_power` a `0x0110` (antes `0x010E`).
     - Se añadieron `battery_charging_current` (`0x0102`), `load_switch_status` (`0x010A`) y `fault_code` (`0x0121`).
     - Se implementaron métodos calculados:
       - Corriente neta: $I_{net} = I_{charging} - I_{load}$ (`get_battery_current()`). Positiva si la batería absorbe carga neta, negativa si se descarga hacia la salida Load.
       - Potencia neta: $P_{net} = V_{battery} \times I_{net}$ (`get_battery_power()`).
       - Fallos activos: `get_faults()` decodifica la máscara de 15 bits de `0x0121` según `FAULT_MESSAGES`.
  2. En [`Api.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py):
     - Se envían `battery_current` y `battery_power` en la raíz del payload.
     - Los campos adicionales que no pertenecen al esquema raíz estándar (`battery_charging_current`, `load_switch_status`, `fault_code`, `faults`) se inyectan en `hardware_device_info.extra`.
  3. En [`HomeAssistantConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py):
     - Se definieron los sensores en `SENSOR_METADATA` para `battery_charging_current` (A), `battery_current` (A), `battery_power` (W), `load_switch_status` y códigos de alarma.
     - Se asegura que listas (como `faults`) se envíen formateadas como cadenas legibles para la API de estados de HA.
- **Motivo**: Ofrece trazabilidad energética completa y diagnóstico en tiempo real cumpliendo estrictamente con el contrato REST de la API V2 sin provocar errores de validación HTTP 422.

## 12. Optimización de tráfico HTTP a Home Assistant mediante filtrado por delta y latidos
- **Contexto**: Cada ciclo de monitorización ejecutaba entre 32 y 36 peticiones HTTP REST individuales consecutivas a Home Assistant (`/api/states/<entity_id>`), más comprobaciones redundantes de conectividad y existencia de dispositivo. En MicroPython esto saturaba los sockets de la Pico W y aumentaba la latencia del bucle en más de 8-12 segundos.
- **Decisión**:
  1. Se implementó un filtrado por variación en [`HomeAssistantConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py):
     - Sensores estáticos (`hardware`, `version`, `serial_number`, `battery_type`, etc.): se inicializan en el primer arranque y luego se refrescan sólo una vez cada hora (`STATIC_INTERVAL = 3600s`).
     - Sensores analógicos: usan umbrales mínimos de cambio (`DEADBANDS`) (0.05V, 0.05A, 1.0W, 0.5°C, 1%) para ignorar ruido en lecturas.
     - Valores discretos (estados, etiquetas, interruptor, alarmas): sólo se envían si su valor varía.
     - Latido periódico forzado (`HEARTBEAT_INTERVAL = 600s`): si un valor no varía durante 10 minutos, se reenvía para mantener activa la entidad en Home Assistant.
     - Caché de verificación: `check_connection()` cachea el estado positivo por 5 minutos y `verify_device_exists()` cachea permanentemente tras el primer 200 OK.
  2. La propuesta de agrupar todo en un único sensor maestro con atributos (Opción 1) se aplazó y documentó en `docs/future/README.md` porque habría roto las tarjetas y widgets existentes en Home Assistant al requerir *Template Sensors*.
- **Motivo**: Reduce entre un 75% y un 90% el volumen de peticiones HTTP por ciclo (~3-6 peticiones frente a ~35) preservando el 100% de la compatibilidad con las tarjetas Lovelace y widgets ya creados sin tocar nada en Home Assistant.

## 13. Optimización de lectura Modbus RTU por bloques y caché de históricos acumulados
- **Contexto**: El ciclo anterior ejecutaba más de 25 peticiones Modbus individuales consecutivas registro por registro por la interfaz UART, aumentando la lentitud del ciclo y la probabilidad de colisiones o tramas corruptas. Además, los contadores de por vida (días operando, sobre-descargas, cargas completas, Ah y kWh acumulados) apenas cambian entre minutos.
- **Decisión**:
  1. Mantener todos los getters individuales existentes en [`RenogyRoverLi.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py) para máxima compatibilidad.
  2. Implementar un método de alta velocidad `get_all_datas_fast(refresh_historical=False)`:
     - Bloque 1: Lee de una sola vez 21 registros contiguos (`0x0100` a `0x0114`) para datos en tiempo real y métricas diarias.
     - Bloque 2: Lee de una sola vez 2 registros contiguos (`0x0120` y `0x0121`) para estado de carga y código de fallos.
     - Bloque 3: Mantiene en caché de RAM los históricos de por vida (`0x0115` a `0x011F`, 11 registros), refrescándolos únicamente cada 10 minutos (`HISTORICAL_DATA_INTERVAL = 600s`).
     - Cálculos derivados en RAM: se calculan al vuelo `battery_current`, `battery_power`, `street_light_brightness` y la lista de `faults` sin peticiones serie extra.
     - Fallback transparente: si la lectura por bloques falla por interferencias en la línea, recurre automáticamente a `get_all_datas()` clásico.
- **Motivo**: Reduce el número de transacciones Modbus por minuto de más de 25 a solo 2 tramas (3 cuando coincide el refresco de históricos), reduciendo el tiempo de polling serie en más de un 80%.

## 14. Tipos estrictamente simples (escalares) en `hardware_device_info.extra`
- **Contexto**: El validador del backend de la API REST V2 valida que todo valor contenido en `hardware_device_info.extra` cumpla con `'string|numeric|boolean'`. Al enviar `faults: []` (array/lista), el servidor rechazaba la petición con `HTTP 422 Unprocessable Entity` ("Los valores de extra deben ser simples").
- **Decisión**: En [`Api.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py), el campo `faults` se transforma a cadena de texto con comas (`", ".join(faults)`) o cadena vacía `""` si no hay alarmas activas. Además, un paso de sanitización final (`clean_extra`) descarta valores `null` y convierte cualquier estructura no primitiva a string.
- **Motivo**: Cumplir la validación estricta de tipos de la API V2 garantizando que ninguna lectura sea rechazada.

## 15. Sincronización horaria diaria NTP
- **Contexto**: `main.py` sincronizaba la hora con el servidor NTP repetidamente o tras cada reconexión WiFi. Los servidores públicos de NTP (pool.ntp.org) pueden bloquear clientes que realicen peticiones con excesiva frecuencia.
- **Decisión**: Se implementó una cadencia de sincronización horaria de 24 horas (`NTP_SYNC_INTERVAL = 86400s`). La hora se sincroniza obligatoriamente al arrancar (`force=True`) y en los ciclos posteriores solo si ha transcurrido un día completo.
- **Motivo**: Proteger los recursos de red y evitar bloqueos por rate-limiting de los servidores NTP públicos.

---
> Raúl Caro Pastorino · <public@raupulus.dev> · [raupulus.dev](https://raupulus.dev)
