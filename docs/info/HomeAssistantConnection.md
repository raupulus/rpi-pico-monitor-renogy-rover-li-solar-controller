# Módulo: HomeAssistantConnection

Integración con la API REST de Home Assistant en [`src/Models/HomeAssistantConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py).

## Qué hace y qué NO hace
- **Qué hace**:
  - Se comunica directamente con los endpoints REST de Home Assistant (`/api/states/<entity_id>`) mediante tokens de acceso de larga duración.
  - Crea y mantiene una entidad de dispositivo raíz (`sensor.renogy_rover_li_<device_id>_device`) que vincula todas las entidades bajo un único dispositivo en el registro de Home Assistant.
  - Publica entidades independientes para cada métrica del controlador solar y de la Raspberry Pi Pico, inyectando metadatos estándar (`device`, `unique_id`, `device_class`, `state_class`, `unit_of_measurement`, `friendly_name`).
  - Limita la actualización de la entidad de dispositivo raíz a 1 vez por hora (3600 segundos) para no saturar la base de datos de Home Assistant.
  - Sanitiza cadenas de texto para asegurar compatibilidad ASCII estricta y evitar rechazos de JSON por parte del parser de Home Assistant.
  - Implementa `_capitalize_words()` para suplir la falta de `str.title()` en el intérprete MicroPython.
- **Qué NO hace**:
  - No utiliza MQTT ni Home Assistant MQTT Discovery (emplea peticiones HTTP REST directas).
  - No escucha eventos ni comandos desde Home Assistant (comunicación unidireccional de telemetría).

## Modelo de datos
Metadatos del dispositivo inyectados en cada entidad para asegurar su agrupación:

```python
device_info = {
    "identifiers": [f"renogy_rover_li_{self.device_id}"],
    "name": f"Controlador Solar Renogy Rover Li {self.device_id}",
    "manufacturer": "Renogy",
    "model": "Rover Li",
    "sw_version": str(self.device_version),
    "suggested_area": "Exterior"
}
```

Estructura de la petición enviada a `/api/states/<entity_id>`:
```json
{
  "state": 12.4,
  "attributes": {
    "device": { ... },
    "unique_id": "renogy_rover_li_1_solar_battery_voltage",
    "friendly_name": "Solar Battery Voltage",
    "device_class": "voltage",
    "state_class": "measurement",
    "unit_of_measurement": "V",
    "last_update": 1627984567,
    "microcontroller": { ... }
  }
}
```

## Flujos principales
1. **Verificación y Creación del Dispositivo**:
   - `check_connection()`: Realiza un `GET /api/` para verificar que la instancia responda `{"message": "API running."}`.
   - `create_device_entity()`: Realiza `POST /api/states/sensor.renogy_rover_li_<id>_device` con atributos descriptivos globales.
2. **Publicación de Métricas (`update_solar_controller_data`)**:
   - Comprueba si han transcurrido más de 3600s desde la última actualización del dispositivo; si es así, refresca la entidad raíz.
   - Itera sobre el diccionario de datos del controlador solar.
   - Determina automáticamente la clase de dispositivo (`device_class`: voltage, current, power, energy, temperature, battery), la clase de estado (`state_class`: measurement, total_increasing) y la unidad de medida (`V`, `A`, `W`, `Wh`, `kWh`, `°C`, `%`).
   - Envía cada entidad mediante `update_sensor()`.
3. **Publicación de Métricas del Microcontrolador (`update_microcontroller_data`)**:
   - Publica `sensor.microcontroller_temperature`, `binary_sensor.microcontroller_wifi`, `sensor.microcontroller_wifi_signal` y `sensor.microcontroller_battery`.

## Puntos de entrada
| Método | Parámetros | Retorno | Requisitos |
|---|---|---|---|
| `check_connection()` | Ninguno | `bool` | WiFi y token válido |
| `create_device_entity()` | Ninguno | `bool` | API accesible |
| `verify_device_exists()` | Ninguno | `bool` | API accesible |
| `update_sensor(...)` | `entity_id, state, attributes, ...` | `bool` | API accesible |
| `update_solar_controller_data(data)` | `data: dict` | `bool` | API accesible |
| `update_microcontroller_data()` | Ninguno | `bool` | Objeto `controller` válido |

## Dependencias
- **Dependencias entrantes**:
  - Consumido por [`src/main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py) y [`tests/test_device_creation.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/test_device_creation.py).
- **Dependencias salientes**:
  - `urequests`, `ujson`, `time`, [`src/Models/RpiPico.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RpiPico.py).

## Configuración
Variables en `env.py`:
- `UPLOAD_HOME_ASSISTANT` (`bool`): Habilita o deshabilita la subida.
- `HOME_ASSISTANT_URL` (`str`): URL base de la instancia (ej. `http://192.168.1.100:8123`).
- `HOME_ASSISTANT_TOKEN` (`str`): Token de acceso de larga duración.
- `DEVICE_ID` (`int`): Identificador del dispositivo.

## Trampas conocidas
- No utilizar caracteres acentuados o símbolos como `°` directamente en atributos; deben filtrarse con `_sanitize_string()`.
- Home Assistant no agrupará entidades si el valor de `identifiers` en `device` difiere aunque sea en una letra entre las distintas entidades.
- No existe el método `.title()` en cadenas de MicroPython; debe emplearse la función auxiliar `_capitalize_words()`.

## Tests que lo cubren
- [`tests/test_device_creation.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/test_device_creation.py)
- [`tests/verify_entity_grouping.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/verify_entity_grouping.py)

## Pendiente real
- Ninguno.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
