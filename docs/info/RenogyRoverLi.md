# Módulo: RenogyRoverLi

Modelo de dominio y decodificador de protocolo para el controlador solar Renogy Rover Li en [`src/Models/RenogyRoverLi.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py).

## Qué hace y qué NO hace
- **Qué hace**:
  - Mapea las direcciones de registros Modbus holding (`0x03`) del controlador según su especificación.
  - Almacena en caché valores estáticos del dispositivo (`hardware_version`, `software_version`, `serial_number`, `system_voltage`, `battery_type`, `nominal_battery_capacity`) durante la inicialización.
  - Aplica factores de conversión de escala (voltios divididos por 10, amperios divididos por 100, potencias enteras en vatios).
  - Decodifica registros empaquetados de temperatura (byte alto controlador, byte bajo batería) gestionando el bit de signo 7.
  - Decodifica registros de 32 bits combinando dos registros consecutivos de 16 bits (Ah y kWh acumulados).
  - Traduce códigos numéricos de estado a etiquetas legibles (`charging_status_label`).
  - Proporciona una estimación calculada del estado y brillo de la luz de calle en base al voltaje de placas solares.
- **Qué NO hace**:
  - No interactúa directamente con el puerto UART físico ni calcula CRC (delegado a [`SerialConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/SerialConnection.py)).
  - No realiza llamadas de red ni interactúa con Home Assistant o APIs HTTP.

## Modelo de datos
El método `get_all_datas()` devuelve un diccionario con las siguientes claves verificadas:

```python
{
    # Información del sistema
    "hardware": str,                 # ej. "V1.2.3"
    "version": str,                  # ej. "V1.0.0"
    "serial_number": str,            # ej. "12345678"
    "system_voltage_current": float, # ej. 12.0
    "system_intensity_current": float,# ej. 20.0
    "battery_type": str,             # "open", "sealed", "gel", "lithium", "custom"
    "nominal_battery_capacity": int, # ej. 100 Ah

    # Batería
    "battery_percentage": float,     # 0.0 a 100.0 %
    "battery_voltage": float,        # Voltios
    "battery_temperature": float,    # °C
    "charging_status": int,          # 0..6
    "charging_status_label": str,    # "deactivated", "mppt", "float", etc.

    # Panel solar
    "solar_voltage": float,          # Voltios
    "solar_current": float,          # Amperios
    "solar_power": float,            # Vatios

    # Carga (Load)
    "load_voltage": float,           # Voltios
    "load_current": float,           # Amperios
    "load_power": float,             # Vatios

    # Día en curso (Today)
    "today_battery_min_voltage": float,
    "today_battery_max_voltage": float,
    "today_max_charging_current": float,
    "today_max_discharging_current": float,
    "today_max_charging_power": int,
    "today_max_discharging_power": int,
    "today_charging_amp_hours": int,
    "today_discharging_amp_hours": int,
    "today_power_generation": int,   # Wh
    "today_power_consumption": int,  # Wh

    # Histórico general acumulado
    "historical_total_days_operating": int,
    "historical_total_number_battery_over_discharges": int,
    "historical_total_number_battery_full_charges": int,
    "historical_total_charging_amp_hours": int,
    "historical_total_discharging_amp_hours": int,
    "historical_cumulative_power_generation": float,   # kWh
    "historical_cumulative_power_consumption": float,  # kWh

    # Campos calculados / auxiliares
    "controller_temperature": float, # °C
    "street_light_status": bool,     # True / False
    "street_light_brightness": int   # 0 a 100 %
}
```

## Flujos principales
1. **Inicialización**:
   - Recibe la instancia de `SerialConnection`.
   - Llama a `_initialize_static_data()`, que lee y guarda en caché las direcciones `0x000A` (voltaje/corriente nominal), `0x0014` (software version), `0x0018` (hardware y número de serie), `0xE002` (capacidad) y `0xE004` (tipo de batería).
2. **Consulta completa de telemetría**:
   - `get_all_datas()` invoca ordenadamente `get_system_info_datas()`, `get_battery_info_datas()`, `get_solar_info_datas()`, `get_load_info_datas()`, `get_historical_today_info_datas()` y `get_historical_info_datas()`.
   - Combina todos los resultados en un diccionario unificado con `dict.update()`.

## Puntos de entrada
| Método | Parámetros | Retorno | Requisitos |
|---|---|---|---|
| `__init__(connection, debug)` | `connection: SerialConnection, debug: bool` | Instancia | Instancia UART activa |
| `get_all_datas()` | Ninguno | `dict` | Enlace serie operativo |
| `get_system_info_datas()` | Ninguno | `dict` | Lee de caché |
| `get_battery_info_datas()` | Ninguno | `dict` | Consulta registros `0x0100`, `0x0101`, `0x0103`, `0x0120` |
| `get_solar_info_datas()` | Ninguno | `dict` | Consulta registros `0x0107`, `0x0108`, `0x0109` |
| `get_load_info_datas()` | Ninguno | `dict` | Consulta registros `0x0104`, `0x0105`, `0x0106` |
| `get_historical_today_info_datas()` | Ninguno | `dict` | Consulta registros `0x010B`..`0x0114` |
| `get_historical_info_datas()` | Ninguno | `dict` | Consulta registros `0x0115`..`0x011E` |

## Dependencias
- **Dependencias entrantes**:
  - Consumido por [`src/main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py).
- **Dependencias salientes**:
  - Inyecta y consume [`src/Models/SerialConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/SerialConnection.py).

## Configuración
Hereda el flag `DEBUG` para emitir logs detallados de los valores crudos leídos de los registros.

## Trampas conocidas
- **Luz de calle**: El registro `0x0120` no refleja fielmente el brillo ni encendido de farola en algunos firmwares; se estima calculando la tensión del panel solar entre 12.3V y 41.5V.
- Si la conexión serie falla durante el arranque, los datos cacheados pueden quedar como cadenas vacías o valores nulos.

## Tests que lo cubren
- Verificación funcional dentro del bucle de telemetría en `src/main.py`.

## Pendiente real
- Ninguno.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
