# Módulo: RpiPico

Capa de abstracción de hardware para la Raspberry Pi Pico / Pico W en [`src/Models/RpiPico.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RpiPico.py).

## Qué hace y qué NO hace
- **Qué hace**:
  - Inicializa y gestiona la interfaz Wi-Fi en modo estación (STA) usando el chip Infineon CYW43439 de la Pico W.
  - Implementa conexión y reconexión WiFi no bloqueante (`ensure_wifi_connected` / `wifi_connect`) con timeout configurable para no colgar el bucle de telemetría.
  - Recicla y resetea limpiamente el driver WLAN (`wlan.disconnect()`, `wlan.active(False)`, `wlan.active(True)`) desactivando el ahorro de energía (`pm=0xa11140`) para evitar cuelgues del chip de radio tras días de uso o reinicios de router.
  - Conecta a redes WiFi alternativas (`WIFI_ALTERNATIVES`) si la red principal falla.
  - Monitoriza la intensidad de la señal WiFi (RSSI en dBm) mediante `wlan.status('rssi')`.
  - Mide la temperatura interna de la CPU mediante el canal 4 del ADC interno del RP2040 aplicando la fórmula de calibración oficial.
  - Lee y calcula la tensión y porcentaje de batería externa conectada a través de un divisor de tensión en un pin ADC configurable.
  - Inicializa y controla los LEDs de estado (LED integrado en placa, LED de alimentación, LED de ciclo y LED de subida de datos).
  - Provee inicializadores auxiliares para buses hardware I2C y SPI.
  - Protege todos los getters de red (`get_wireless_ip`, `get_wireless_rssi`, etc.) contra excepciones si la red cae.
- **Qué NO hace**:
  - No gestiona el puerto UART de comunicaciones serie (delegado a [`RenogyRoverLi`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py)).
  - No realiza peticiones HTTP a servidores externos (delegado a [`Api`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py) y [`HomeAssistantConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py)).

## Modelo de datos
El método `wireless_info()` devuelve dos listas estructuradas para cliente y punto de acceso:
- `info_client`: `Connected`, `Hostname`, `MAC`, `TXPOWER`, `IP`.
- `info_ap`: `SSID`, `RSSI`, `Channel`.

`read_external_battery()` actualiza y devuelve el diccionario interno de batería:
```python
{
    "pin": int,
    "voltage_current": float,
    "voltage_percentage": float,
    "voltage_min": float,
    "voltage_max": float,
    "voltage_percentage_min": float,
    "voltage_percentage_max": float
}
```

## Flujos principales
1. **Inicialización**:
   - Comprueba si existen credenciales WiFi en `env.py` y llama a `wifi_connect(timeout=15)`.
   - Inicializa el LED integrado (`Pin("LED", Pin.OUT)`).
   - Inicializa los pines GPIO para LEDs externos (`led_power`, `led_upload`, `led_cycle`) si están definidos en `env.py`.
   - Si `led_power` está configurado, se enciende.
2. **Conexión y Reconexión Wi-Fi**:
   - `ensure_wifi_connected(timeout=15)` verifica si `wifi_is_connected()`. Si no lo está, inicia `wifi_connect()`.
   - `wifi_connect()` recicla la interfaz WLAN apagándola y reactivándola con `pm=0xa11140` (modo sin ahorro de energía, esencial para estabilidad de red).
   - Intenta conectar al SSID principal sin escaneos agresivos durante el `timeout` establecido.
   - Si el enlace falla o no conecta, prueba en orden las redes de `WIFI_ALTERNATIVES`.
   - Si ninguna conecta, retorna `False` inmediatamente sin bucles infinitos, permitiendo que el sistema siga leyendo telemetría solar offline.
3. **Lectura de Temperatura**:
   - Lee el sensor interno en canal ADC 4:
     $$\text{Voltaje} = \text{Lectura cruda (16 bits)} \times \frac{3.3}{65535}$$
     $$\text{Temperatura (°C)} = 27 - \frac{\text{Voltaje} - 0.706}{0.001721}$$

## Puntos de entrada
| Método | Parámetros | Retorno | Requisitos |
|---|---|---|---|
| `wifi_connect(ssid, password, timeout)` | Opcionales | `bool` | Credenciales configuradas |
| `ensure_wifi_connected(timeout)` | `timeout: int = 15` | `bool` | Ninguno (no bloqueante) |
| `wifi_is_connected()` | Ninguno | `bool` | Interfaz WLAN iniciada |
| `wifi_status()` | Ninguno | `int` | Constantes `CYW43` |
| `wifi_disconnect()` | Ninguno | `None` | Ninguno |
| `get_wireless_ip()` | Ninguno | `str` | IP asignada o `"0.0.0.0"` |
| `get_wireless_rssi()` | Ninguno | `int` | Señal en dBm o 0 |
| `get_cpu_temperature()` | Ninguno | `float` | ADC disponible |
| `led_power_on()`, `led_power_off()` | Ninguno | `None` | Pin configurado |
| `led_upload_on()`, `led_upload_off()` | Ninguno | `None` | Pin configurado |
| `led_cycle_on()`, `led_cycle_off()` | Ninguno | `None` | Pin configurado |

## Dependencias
- **Dependencias entrantes**:
  - Consumido por [`src/main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py), [`src/Models/Api.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py), [`src/Models/HomeAssistantConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py) y tests.
- **Dependencias salientes**:
  - `machine.Pin`, `machine.ADC`, `machine.I2C`, `machine.SPI`, `machine.deepsleep`, `network.WLAN`, `time`.

## Configuración
Variables en `env.py`:
- `WIFI_SSID`, `WIFI_PASSWORD`, `WIFI_COUNTRY`: Red principal.
- `WIFI_ALTERNATIVES`: Lista de diccionarios `[{"ssid": "...", "password": "..."}, ...]`.
- `WIFI_CONNECT_TIMEOUT`: Timeout máximo de asociación WiFi en segundos (por defecto 15s).
- `MAX_OFFLINE_CYCLES`: Ciclos consecutivos sin conexión antes de reiniciar por hardware (por defecto 15).
- `BATTERY_ADC_PIN`, `BATTERY_MIN_VOLTAGE`, `BATTERY_MAX_VOLTAGE`: Monitorización de batería externa.
- `LED_POWER_PIN`, `LED_UPLOAD_PIN`, `LED_CYCLE_PIN`: Pines para LEDs externos.

## Trampas conocidas
- En Raspberry Pi Pico W, el pin del LED integrado no es un GPIO del RP2040 sino una salida del chip inalámbrico CYW43439 (`Pin("LED")`).
- Nunca usar bucles infinitos `while not wifi.isconnected()` ni escaneos repetitivos `wifi.scan()` durante fallos de red: bloquean la CPU y saturan la pila SPI del chip CYW43 provocando que se congele.
- El ahorro de energía (`pm`) del CYW43 debe desactivarse explícitamente (`0xa11140`); con powersave activo, la Pico W experimenta pérdida de balizas WiFi y desconexiones frecuentes.

## Tests que lo cubren
- `tests/test_device_creation.py` y bucle de arranque en `src/main.py`.

## Pendiente real
- Ninguno.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
