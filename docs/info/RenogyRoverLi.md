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
  - Obtiene la corriente de carga entregada a la batería por el regulador (`battery_charging_current` en `0x0102`).
  - Calcula el balance neto de corriente de batería (`battery_current` = $I_{chg} - I_{load}$) y de potencia neta (`battery_power` = $V_{bat} \times I_{net}$).
  - Lee el estado del interruptor de salida Load (`load_switch_status` en `0x010A`).
  - Lee el registro de fallos (`0x0121`) y decodifica la máscara de alarmas activas en una lista de identificadores (`faults`).
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
    "battery_charging_current": float,# Corriente de carga hacia batería (A)
    "battery_current": float,        # Corriente neta (A, positiva = carga, negativa = descarga a load)
    "battery_power": float,          # Potencia neta (W, positiva = carga, negativa = descarga a load)

    # Panel solar
    "solar_voltage": float,          # Voltios
    "solar_current": float,          # Amperios
    "solar_power": float,            # Vatios

    # Carga (Load)
    "load_voltage": float,           # Voltios
    "load_current": float,           # Amperios
    "load_power": float,             # Vatios
    "load_switch_status": int,       # 0 = OFF, 1 = ON

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

    # Diagnóstico y campos calculados
    "controller_temperature": float, # °C
    "street_light_status": bool,     # True / False
    "street_light_brightness": int,  # 0 a 100 %
    "fault_code": int,               # Código numérico de alarma (0x0121)
    "faults": list                   # Lista de cadenas con alarmas activas
}
```

## Flujos principales
1. **Inicialización y Caché Estática**:
   - Inicializa el enlace UART serie mediante `SerialConnection`.
   - Invoca `_initialize_static_data()`, que lee una sola vez y guarda en memoria RAM los valores de fábrica: versión de software (`0x0014`), versión de hardware y número de serie (`0x0018`), voltaje y corriente nominal del sistema (`0x000A`), tipo de batería (`0xE004`) y capacidad nominal (`0xE002`).
2. **Lectura Optimizada por Bloques (`get_all_datas_fast`)**:
   - **Trama 1 (Tiempo real y diario)**: Lee de forma contigua los registros `0x0100` a `0x0114` (21 registros) en una única transacción Modbus RTU. Decodifica instantáneamente voltajes, corrientes, potencias de carga/solar, temperaturas y máximos/mínimos diarios.
   - **Trama 2 (Estado y fallos)**: Lee en bloque los registros `0x0120` y `0x0121` (2 registros) para decodificar el estado de carga y códigos de alarma.
   - **Caché de históricos de por vida**: Mantiene en caché las métricas acumuladas de por vida (`0x0115` a `0x011F`, 11 registros), refrescándolas únicamente una vez cada 10 minutos (`historical_interval=600s`).
   - **Cálculos en memoria RAM**: Realiza derivados instantáneos sin peticiones serie extra (`battery_current = battery_charging_current - load_current`, `battery_power`, `street_light_brightness` y lista de `faults`).
   - **Mecanismo de Resiliencia / Fallback**: Si cualquier lectura en bloque falla o se corrompe por ruido, invoca de forma transparente `get_all_datas()` estándar registro a registro.
3. **Consulta Clásica Registro a Registro (`get_all_datas`)**:
   - Mantiene intacta la compatibilidad con todas las lecturas individuales invocando secuencialmente cada método getter.

## Puntos de entrada
| Método | Parámetros | Retorno | Requisitos |
|---|---|---|---|
| `__init__(device_id, tx_pin, rx_pin, debug, historical_interval)` | Pines UART, debug e intervalo de históricos | Instancia | Pines GPIO válidos |
| `get_all_datas_fast(refresh_historical)` | `refresh_historical: bool = False` | `dict` | Enlace serie operativo (optimizado por bloques) |
| `get_all_datas()` | Ninguno | `dict` | Enlace serie operativo (modo clásico) |
| `get_all_controller_info_datas()` | Ninguno | `dict` | Lee de caché |
| `get_all_battery_info_datas()` | Ninguno | `dict` | Consulta registros `0x0100`, `0x0101`, `0x0102`, `0x0103`, `0x0120` |
| `get_battery_charging_current()` | Ninguno | `float \| None` | Consulta registro `0x0102` |
| `get_battery_current()` | Ninguno | `float \| None` | Calcula $I_{chg} - I_{load}$ |
| `get_battery_power()` | Ninguno | `float \| None` | Calcula $V_{bat} \times I_{net}$ |
| `get_all_solar_panel_info_datas()` | Ninguno | `dict` | Consulta registros `0x0107`, `0x0108`, `0x0109` |
| `get_all_load_info_datas()` | Ninguno | `dict` | Consulta registros `0x0104`, `0x0105`, `0x0106`, `0x010A` |
| `get_load_switch_status()` | Ninguno | `int \| None` | Consulta registro `0x010A` |
| `get_fault_code()` | Ninguno | `int` | Consulta registro `0x0121` |
| `get_faults()` | Ninguno | `list` | Decodifica bits de `0x0121` |
| `get_today_historical_info_datas()` | Ninguno | `dict` | Consulta registros `0x010B`..`0x0114` |
| `get_historical_info_datas(force)` | `force: bool = False` | `dict` | Lee con caché temporal de 10 min |

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
- [`tests/test_battery_calculation.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/test_battery_calculation.py): Valida la decodificación por bloques Modbus, balance neto de batería ($I_{net}$, $P_{net}$), caché estática de intensidad nominal, intervalo de caché histórica de por vida y fallback automático ante errores serie.

## Pendiente real
- Ninguno.

---
> Raúl Caro Pastorino · <public@raupulus.dev> · [raupulus.dev](https://raupulus.dev)
