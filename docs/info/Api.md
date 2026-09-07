# Módulo: Api

Cliente HTTP REST para el envío de telemetría hacia la API V2 (módulo `/energy/solar-readings`) en [`src/Models/Api.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/Api.py).

## Qué hace y qué NO hace
- **Qué hace**:
  - Construye el payload JSON unificado según el contrato API V2 mapeando las métricas leídas del Renogy Rover Li hacia los nombres nativos del modelo de energía.
  - Envía la corriente neta (`battery_current`) y potencia neta (`battery_power`) de la batería calculadas en base a la corriente entregada por el regulador y el consumo en bornes Load.
  - Inyecta en el bloque `hardware_device_info` la salud del microcontrolador (temperatura de CPU, uso de RAM, uptime, IP local, RSSI y batería externa ADC si existe).
  - Incluye campos diagnósticos del regulador (`battery_charging_current`, `load_switch_status`, `fault_code`, `faults`) dentro de `hardware_device_info.extra` para respetar estrictamente el esquema raíz del contrato API V2.
  - Gestiona la autenticación mediante cabecera Bearer Token (`Authorization: Bearer <API_TOKEN>`) validada por Laravel Sanctum con la ability `energy:write`.
  - Normaliza la combinación de `API_URL` y `API_PATH` para evitar duplicación de prefijos (`/api` o `/api/v2`).
  - Implementa lógica de reintentos con retroceso exponencial ante errores temporales de red o timeouts.
  - Aborta reintentos inmediatamente ante errores de validación o permisos (HTTP 401, 403, 422).
  - Procesa el envelope `ApiResponseTrait` (`success`, `message`, `data`, `warnings`, `errors`) e informa advertencias en modo debug.
  - Garantiza el cierre explícito de sockets TCP (`response.close()`) y recolección de basura tras cada petición HTTP.
  - Provee método `get_data_from_api()` para consultar lecturas almacenadas (`GET /api/v2/energy/solar-readings`).
- **Qué NO hace**:
  - No interactúa con Home Assistant (delegado a [`HomeAssistantConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py)).
  - No almacena las lecturas localmente en memoria flash en caso de caída prolongada de red.

## Modelo de datos
Estructura del payload JSON enviado por `send_to_api`:

```json
{
  "hardware_device_id": 1,
  "hardware": "V1.0.0",
  "version": "V1.2.4",
  "serial_number": "12345678",
  "battery_type": "lithium",
  "battery_voltage": 13.2,
  "battery_current": 4.1,
  "battery_power": 54.12,
  "battery_percentage": 95,
  "battery_temperature": 24.5,
  "temperature": 32.1,
  "voltage": 19.4,
  "amperage": 3.8,
  "power": 73.7,
  "charging_status": 2,
  "charging_status_label": "mppt",
  "light_status": false,
  "light_brightness": 0,
  "load_voltage": 12.8,
  "load_current": 1.1,
  "load_power": 14.1,
  "day_battery_voltage_min": 12.9,
  "day_battery_voltage_max": 13.6,
  "day_charging_current_max": 5.2,
  "day_discharging_current_max": 2.1,
  "day_charging_power_max": 95,
  "day_discharging_power_max": 28,
  "day_charging_amp_hours": 18,
  "day_discharging_amp_hours": 8,
  "day_power_generation_wh": 240,
  "day_power_consumption_wh": 105,
  "total_operating_days": 184,
  "total_battery_over_discharges": 0,
  "total_battery_full_charges": 142,
  "total_charging_amp_hours": 3210,
  "total_discharging_amp_hours": 1540,
  "total_power_generation_wh": 42100,
  "total_power_consumption_wh": 19800,
  "system_voltage": 12,
  "system_intensity": 20,
  "nominal_battery_capacity": 100,
  "hardware_device_info": {
    "temp": 28.5,
    "voltage": 3.92,
    "battery_level": 82,
    "cpu": null,
    "disk": null,
    "ram": 34.2,
    "uptime": 86400,
    "ip_local": "192.168.1.100",
    "extra": {
      "wifi_rssi": -65,
      "wifi_ssid": "your_wifi_ssid",
      "battery_charging_current": 5.2,
      "load_switch_status": 1,
      "fault_code": 0,
      "faults": ""
    }
  }
}
```

## Flujos principales
1. **Envío de Telemetría (`send_to_api`)**:
   - Construye la URL normalizada mediante `_build_url()`.
   - Mapea las claves del diccionario `data` (provenientes del controlador solar) a la nomenclatura oficial de la API V2.
   - Extrae el estado del microcontrolador y campos adicionales en `extra` mediante `_get_hardware_device_info(data)`.
   - Inicia bucle de reintentos:
     - Realiza `urequests.post(url, headers=headers, json=payload)`.
     - Si el código de respuesta es 200 o 201, procesa el envelope JSON, imprime `warnings` si existen (en debug) y retorna `True`.
     - Si es un error definitivo (HTTP 401, 403, 422), aborta los reintentos y retorna `False`.
     - Si falla la conexión o hay error 5xx, calcula el tiempo de retroceso exponencial y reintenta.
     - En el bloque `finally`: cierra siempre `response.close()` y ejecuta `gc.collect()`.

## Puntos de entrada
| Método | Parámetros | Retorno | Requisitos |
|---|---|---|---|
| `__init__(controller, url, path, token, device_id, ...)` | Instancia RpiPico, endpoints, token y device_id | Instancia | URL válida |
| `send_to_api(data)` | `data: dict` | `bool` | WiFi activa, token con `energy:write` |
| `get_data_from_api(path)` | `path: str \| None` | `dict \| False` | WiFi activa, token con `energy:read` |
| `upload(data, method)` | `data: dict, method: str` | `bool` | Alias retrocompatible de `send_to_api` |

## Dependencias
- **Dependencias entrantes**:
  - Consumido por [`src/main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py).
- **Dependencias salientes**:
  - `urequests`, `ujson`, `time`, `gc`, [`src/Models/RpiPico.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RpiPico.py).

## Configuración
Variables en `env.py`:
- `UPLOAD_API` (`bool`): Activa o desactiva las peticiones hacia esta API.
- `API_URL` (`str`): Dirección base del servidor (ej. `https://api.example.com`).
- `API_PATH` (`str`): Endpoint relativo (por defecto `/api/v2/energy/solar-readings`).
- `API_TOKEN` (`str`): Token Bearer Sanctum con ability `energy:write`.
- `DEVICE_ID` (`int`): Identificador numérico del dispositivo (`hardware_device_id`).

## Trampas conocidas
- **Ability del token**: Un token con la antigua ability `hardware:write` responderá con HTTP 403. Se requiere un token con `energy:write`.
- **Fuga de sockets**: Es crítico invocar `response.close()` en el bloque `finally`, ya que el pool de sockets en el stack LWIP de MicroPython se agota rápidamente (`OSError: ENOMEM`).
- **Campos opcionales**: El contrato espera valores `null` para campos no medidos; nunca forzar valores numéricos a `0` si no han sido medidos.
- **Campos adicionales en `extra`**: Métricas adicionales que no figuran en el esquema raíz del contrato API V2 deben ubicarse en `hardware_device_info.extra` para evitar errores `422 Unprocessable Entity`.
- **Valores simples en `extra`**: El validador de la API V2 exige que todos los valores dentro de `hardware_device_info.extra` sean estrictamente tipos simples (número, texto o booleano). Arrays o listas como `faults: []` producen error HTTP 422 ("Los valores de extra deben ser simples"); por ello, listas deben serializarse como texto (ej. `", ".join(faults)` o `""`), y valores `null` deben omitirse.

## Tests que lo cubren
- [`tests/test_battery_calculation.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/test_battery_calculation.py): Valida la estructura del payload API V2, la inyección de telemetría no perteneciente al contrato en `extra` y la sanitización a tipos simples (número, texto o booleano) sin listas ni valores nulos.

## Pendiente real
- Ninguno.

---
> Raúl Caro Pastorino · <public@raupulus.dev> · [raupulus.dev](https://raupulus.dev)
