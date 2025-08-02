# API and Home Assistant Data Format Documentation

This document describes the data formats used when sending data to the API and Home Assistant from the Raspberry Pi Pico monitoring the Renogy Rover Li solar controller.

## API Data Format

When sending data to the API, the following JSON structure is used:

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

Note: The above is a simplified example.

### Microcontroller Data Fields

The `microcontroller` object contains information about the Raspberry Pi Pico:

| Field | Type | Description |
|-------|------|-------------|
| `temperature` | float | CPU temperature in degrees Celsius |
| `wifi_connected` | boolean | Whether WiFi is connected |
| `wifi_signal_strength` | integer | WiFi signal strength in dBm (only if connected) |
| `battery_percentage` | float | Battery charge percentage (only if external battery monitoring is configured) |
| `battery_voltage` | float | Battery voltage in volts (only if external battery monitoring is configured) |

### Solar Controller Data Fields

The `data` object contains information from the Renogy Rover Li solar controller. The following fields are included:

#### System Information

| Field | Type | Description |
|-------|------|-------------|
| `system_voltage` | float | System voltage (V) |
| `system_current` | float | System current (A) |
| `hardware_version` | string | Hardware version of the controller |
| `software_version` | string | Software version of the controller |
| `serial_number` | string | Serial number of the controller |

#### Battery Information

| Field | Type | Description |
|-------|------|-------------|
| `battery_percentage` | float | Battery state of charge (%) |
| `battery_voltage` | float | Battery voltage (V) |
| `battery_temperature` | float | Battery temperature (°C) |
| `battery_type` | string | Type of battery |
| `battery_capacity` | float | Nominal battery capacity (Ah) |

#### Solar Panel Information

| Field | Type | Description |
|-------|------|-------------|
| `solar_voltage` | float | Solar panel voltage (V) |
| `solar_current` | float | Solar panel current (A) |
| `solar_power` | float | Solar panel power (W) |

#### Load Information

| Field | Type | Description |
|-------|------|-------------|
| `load_voltage` | float | Load voltage (V) |
| `load_current` | float | Load current (A) |
| `load_power` | float | Load power (W) |

#### Controller Information

| Field | Type | Description |
|-------|------|-------------|
| `controller_temperature` | float | Controller temperature (°C) |
| `charging_status` | integer | Charging status code |
| `charging_status_label` | string | Charging status description |

#### Daily Statistics

| Field | Type | Description |
|-------|------|-------------|
| `today_battery_min_voltage` | float | Minimum battery voltage today (V) |
| `today_battery_max_voltage` | float | Maximum battery voltage today (V) |
| `today_max_charging_current` | float | Maximum charging current today (A) |
| `today_max_discharging_current` | float | Maximum discharging current today (A) |
| `today_max_charging_power` | float | Maximum charging power today (W) |
| `today_max_discharging_power` | float | Maximum discharging power today (W) |
| `today_charging_amp_hours` | float | Charging amp hours today (Ah) |
| `today_discharging_amp_hours` | float | Discharging amp hours today (Ah) |
| `today_power_generation` | float | Power generation today (Wh) |
| `today_power_consumption` | float | Power consumption today (Wh) |

#### Historical Statistics

| Field | Type | Description |
|-------|------|-------------|
| `historical_total_days_operating` | integer | Total days operating |
| `historical_total_battery_over_discharges` | integer | Total number of battery over-discharges |
| `historical_total_battery_full_charges` | integer | Total number of battery full charges |
| `historical_total_charging_amp_hours` | float | Total charging amp hours (Ah) |
| `historical_total_discharging_amp_hours` | float | Total discharging amp hours (Ah) |
| `historical_cumulative_power_generation` | float | Cumulative power generation (kWh) |
| `historical_cumulative_power_consumption` | float | Cumulative power consumption (kWh) |

## Home Assistant Integration

When sending data to Home Assistant, each data point is sent as a separate sensor entity. The entity IDs follow this format:

```
sensor.solar_{field_name}
```

For example, the battery voltage would be sent as `sensor.solar_battery_voltage`.

### Sensor Attributes

Each sensor includes the following attributes:

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

### Microcontroller Sensors

In addition to the solar controller data, the following sensors are created for the microcontroller:

| Entity ID | Description |
|-----------|-------------|
| `sensor.microcontroller_temperature` | CPU temperature |
| `binary_sensor.microcontroller_wifi` | WiFi connection status |
| `sensor.microcontroller_wifi_signal` | WiFi signal strength |
| `sensor.microcontroller_battery` | Battery percentage |

## Example API Request

Here's an example of a complete API request:

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

## Notes on Data Availability

- Not all fields may be available in every request. The availability depends on the capabilities of the specific Renogy Rover Li model and the current state of the system.
- Some fields may be null if the data is not available or could not be read from the controller.
- The microcontroller battery information will only be included if an external battery is connected and configured for monitoring.