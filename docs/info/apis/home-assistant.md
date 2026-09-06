# Integración con Home Assistant REST API

Documento de referencia sobre cómo este proyecto envía métricas y mantiene la topología de dispositivos en Home Assistant.

## 1. Estrategia de Conexión

El proyecto interactúa directamente con los endpoints oficiales de Home Assistant a través de su API REST HTTP:

- **Autenticación**: Cabecera `Authorization: Bearer <HOME_ASSISTANT_TOKEN>`.
- **Endpoint Principal**: `POST /api/states/<entity_id>`
- **Verificación de Conectividad**: `GET /api/` (espera estado HTTP 200 y mensaje de bienvenida).

## 2. Modelo de Agrupación por Dispositivo

Para evitar que Home Assistant disperse las métricas como sensores independientes no asociados a un hardware, todas las entidades enviadas por [`HomeAssistantConnection`](../HomeAssistantConnection.md) incluyen dentro de su diccionario `attributes` la estructura `device`:

```json
{
  "state": "12.4",
  "attributes": {
    "device": {
      "identifiers": ["renogy_rover_li_1"],
      "name": "Controlador Solar Renogy Rover Li 1",
      "manufacturer": "Renogy",
      "model": "Rover Li",
      "sw_version": "V1.0.0",
      "suggested_area": "Exterior"
    },
    "unique_id": "renogy_rover_li_1_solar_battery_voltage",
    "friendly_name": "Solar Battery Voltage",
    "device_class": "voltage",
    "state_class": "measurement",
    "unit_of_measurement": "V"
  }
}
```

### Entidad de Dispositivo Raíz
Se crea una entidad raíz: `sensor.renogy_rover_li_<DEVICE_ID>_device`.
- Esta entidad aglutina la versión de software, hardware, número de serie y la marca de tiempo de última actualización.
- Para evitar sobrecargar la base de datos de Home Assistant (`recorder`), su actualización está limitada a intervalos de 3600 segundos (1 hora).

## 3. Entidades Publicadas

### Entidades del Controlador Solar (`sensor.solar_*`)
- Tensión, intensidad y potencia de batería: `sensor.solar_battery_voltage`, `sensor.solar_battery_percentage`, `sensor.solar_battery_temperature`.
- Estado de carga: `sensor.solar_charging_status`, `sensor.solar_charging_status_label`.
- Paneles solares: `sensor.solar_solar_voltage`, `sensor.solar_solar_current`, `sensor.solar_solar_power`.
- Carga de salida (Load): `sensor.solar_load_voltage`, `sensor.solar_load_current`, `sensor.solar_load_power`.
- Estadísticas del día: `sensor.solar_today_power_generation`, `sensor.solar_today_power_consumption`, `sensor.solar_today_battery_min_voltage`, `sensor.solar_today_battery_max_voltage`, etc.
- Históricos generales: `sensor.solar_historical_total_days_operating`, `sensor.solar_historical_cumulative_power_generation`, etc.

### Entidades del Microcontrolador (`sensor.microcontroller_*`)
- `sensor.microcontroller_temperature`: Temperatura de CPU (°C).
- `binary_sensor.microcontroller_wifi`: Estado de conexión de red (on/off).
- `sensor.microcontroller_wifi_signal`: Nivel de señal RSSI (dBm).
- `sensor.microcontroller_battery`: Nivel de batería externa en porcentaje (%) si está habilitada.

## 4. Pruebas y Diagnóstico
- [`tests/test_device_creation.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/test_device_creation.py): Comprueba la conectividad y la creación inicial de la entidad del dispositivo.
- [`tests/verify_entity_grouping.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/verify_entity_grouping.py): Audita y repara atributos de agrupación en caliente.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
