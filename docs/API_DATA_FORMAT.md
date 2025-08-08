# Documentación del Formato de Datos para API y Home Assistant

Este documento describe los formatos de datos utilizados al enviar información a la API y Home Assistant desde la Raspberry Pi Pico que monitoriza el controlador solar Renogy Rover Li.

## Formato de Datos de la API

Al enviar datos a la API, se utiliza la siguiente estructura JSON:

```json
{
    "solar_voltage": 18.6,
    "battery_voltage": 12.4,
    "controller_temperature": 35.2,
    "battery_percentage": 85,
    "solar_current": 2.5,
    "solar_power": 46.5,
  "hardware_device_id": 1,
  "microcontroller": {
    "temperature": 28.5,
    "wifi_connected": true,
    "wifi_signal_strength": -65,
    "battery_percentage": 85.2,
    "battery_voltage": 3.8
  }
}
```

Nota: El ejemplo anterior es una versión simplificada.

### Campos de Datos del Microcontrolador

El objeto `microcontroller` contiene información sobre la Raspberry Pi Pico:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `temperature` | float | Temperatura de la CPU en grados Celsius |
| `wifi_connected` | boolean | Si el WiFi está conectado |
| `wifi_signal_strength` | integer | Intensidad de la señal WiFi en dBm (solo si está conectado) |
| `battery_percentage` | float | Porcentaje de carga de la batería (solo si está configurado el monitoreo de batería externa) |
| `battery_voltage` | float | Voltaje de la batería en voltios (solo si está configurado el monitoreo de batería externa) |

### Campos de Datos del Controlador Solar

El objeto `data` contiene información del controlador solar Renogy Rover Li. Se incluyen los siguientes campos:

#### Información del Sistema

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `system_voltage` | float | Voltaje del sistema (V) |
| `system_current` | float | Corriente del sistema (A) |
| `hardware_version` | string | Versión de hardware del controlador |
| `software_version` | string | Versión de software del controlador |
| `serial_number` | string | Número de serie del controlador |

#### Información de la Batería

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `battery_percentage` | float | Estado de carga de la batería (%) |
| `battery_voltage` | float | Voltaje de la batería (V) |
| `battery_temperature` | float | Temperatura de la batería (°C) |
| `battery_type` | string | Tipo de batería |
| `battery_capacity` | float | Capacidad nominal de la batería (Ah) |

#### Información del Panel Solar

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `solar_voltage` | float | Voltaje del panel solar (V) |
| `solar_current` | float | Corriente del panel solar (A) |
| `solar_power` | float | Potencia del panel solar (W) |

#### Información de la Carga

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `load_voltage` | float | Voltaje de la carga (V) |
| `load_current` | float | Corriente de la carga (A) |
| `load_power` | float | Potencia de la carga (W) |

#### Información del Controlador

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `controller_temperature` | float | Temperatura del controlador (°C) |
| `charging_status` | integer | Código de estado de carga |
| `charging_status_label` | string | Descripción del estado de carga |

#### Estadísticas Diarias

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `today_battery_min_voltage` | float | Voltaje mínimo de la batería hoy (V) |
| `today_battery_max_voltage` | float | Voltaje máximo de la batería hoy (V) |
| `today_max_charging_current` | float | Corriente máxima de carga hoy (A) |
| `today_max_discharging_current` | float | Corriente máxima de descarga hoy (A) |
| `today_max_charging_power` | float | Potencia máxima de carga hoy (W) |
| `today_max_discharging_power` | float | Potencia máxima de descarga hoy (W) |
| `today_charging_amp_hours` | float | Amperios-hora de carga hoy (Ah) |
| `today_discharging_amp_hours` | float | Amperios-hora de descarga hoy (Ah) |
| `today_power_generation` | float | Generación de energía hoy (Wh) |
| `today_power_consumption` | float | Consumo de energía hoy (Wh) |

#### Estadísticas Históricas

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `historical_total_days_operating` | integer | Total de días en funcionamiento |
| `historical_total_battery_over_discharges` | integer | Número total de sobredescargas de la batería |
| `historical_total_battery_full_charges` | integer | Número total de cargas completas de la batería |
| `historical_total_charging_amp_hours` | float | Total de amperios-hora de carga (Ah) |
| `historical_total_discharging_amp_hours` | float | Total de amperios-hora de descarga (Ah) |
| `historical_cumulative_power_generation` | float | Generación acumulativa de energía (kWh) |
| `historical_cumulative_power_consumption` | float | Consumo acumulativo de energía (kWh) |

## Integración con Home Assistant

Al enviar datos a Home Assistant, cada punto de datos se envía como una entidad de sensor separada. Los IDs de entidad siguen este formato:

```
sensor.solar_{nombre_campo}
```

Por ejemplo, el voltaje de la batería se enviaría como `sensor.solar_battery_voltage`.

### Atributos del Sensor

Cada sensor incluye los siguientes atributos:

```json
{
  "microcontroller": {
    "temperature": 28.5,
    "wifi_connected": true,
    "wifi_signal_strength": -65,
    "battery_percentage": 85.2,
    "battery_voltage": 3.8
  },
  "last_update": 1627984567,
  "friendly_name": "Solar Battery Voltage"
}
```

### Sensores del Microcontrolador

Además de los datos del controlador solar, se crean los siguientes sensores para el microcontrolador:

| ID de Entidad | Descripción |
|---------------|-------------|
| `sensor.microcontroller_temperature` | Temperatura de la CPU |
| `binary_sensor.microcontroller_wifi` | Estado de conexión WiFi |
| `sensor.microcontroller_wifi_signal` | Intensidad de la señal WiFi |
| `sensor.microcontroller_battery` | Porcentaje de batería |

## Ejemplo de Solicitud API

Aquí tienes un ejemplo de una solicitud API completa:

```json
{
  "data": {
    "system_voltage": 12.4,
    "system_current": 2.5,
    "battery_percentage": 85,
    "battery_voltage": 12.4,
    "battery_temperature": 25.3,
    "controller_temperature": 35.2,
    "load_voltage": 12.3,
    "load_current": 1.2,
    "load_power": 14.8,
    "solar_voltage": 18.6,
    "solar_current": 2.5,
    "solar_power": 46.5,
    "today_battery_min_voltage": 12.1,
    "today_battery_max_voltage": 14.2,
    "today_max_charging_current": 5.2,
    "today_max_discharging_current": 3.1,
    "today_max_charging_power": 65.3,
    "today_max_discharging_power": 45.2,
    "today_charging_amp_hours": 15.6,
    "today_discharging_amp_hours": 12.3,
    "today_power_generation": 186.5,
    "today_power_consumption": 148.2,
    "historical_total_days_operating": 45,
    "historical_total_battery_over_discharges": 2,
    "historical_total_battery_full_charges": 38,
    "historical_total_charging_amp_hours": 685.2,
    "historical_total_discharging_amp_hours": 542.3,
    "historical_cumulative_power_generation": 8.2,
    "historical_cumulative_power_consumption": 6.5,
    "charging_status": 3,
    "charging_status_label": "MPPT charging"
  },
  "hardware_device_id": 1,
  "microcontroller": {
    "temperature": 28.5,
    "wifi_connected": true,
    "wifi_signal_strength": -65,
    "battery_percentage": 85.2,
    "battery_voltage": 3.8
  }
}
```

## Notas sobre la Disponibilidad de Datos

- No todos los campos pueden estar disponibles en cada solicitud. La disponibilidad depende de las capacidades del modelo específico de Renogy Rover Li y del estado actual del sistema.
- Algunos campos pueden ser null si los datos no están disponibles o no se pudieron leer del controlador.
- La información de la batería del microcontrolador solo se incluirá si hay una batería externa conectada y configurada para monitoreo.