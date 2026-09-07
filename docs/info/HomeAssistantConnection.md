# Módulo: HomeAssistantConnection

Integración con la API REST de Home Assistant en [`src/Models/HomeAssistantConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/HomeAssistantConnection.py).

## Qué hace y qué NO hace
- **Qué hace**:
  - Se comunica directamente con los endpoints REST de Home Assistant (`/api/states/<entity_id>`) mediante tokens de acceso de larga duración.
  - Crea y mantiene una entidad de dispositivo raíz (`sensor.renogy_rover_li_<device_id>_device`) que vincula todas las entidades bajo un único dispositivo en el registro de Home Assistant.
  - Publica entidades independientes para cada métrica del controlador solar y de la Raspberry Pi Pico, inyectando metadatos estándar (`device`, `unique_id`, `device_class`, `state_class`, `unit_of_measurement`, `friendly_name`).
  - **Optimización por Delta (Vía A)**: Aplica filtrado por variación para reducir entre un 75% y 90% las peticiones HTTP sin romper ninguna entidad ni tarjeta de dashboard existente:
    - Entidades estáticas (`hardware`, `version`, `serial_number`, `battery_type`, `nominal_battery_capacity`, etc.): Se envían al iniciar y luego sólo una vez cada hora (`STATIC_INTERVAL = 3600s`).
    - Sensores analógicos: Emplean umbrales de banda muerta (`DEADBANDS`) (0.05V en batería, 0.1V en paneles, 0.05A en corriente, 1.0W en potencia, 0.5°C en temperatura) para descartar fluctuaciones por ruido de lectura.
    - Latido forzado (`HEARTBEAT_INTERVAL = 600s`): Si un sensor no ha cambiado en 10 minutos, se fuerza su reenvío para evitar que Home Assistant considere la entidad estancada o inactiva.
    - Caché de verificación: `check_connection()` y `verify_device_exists()` cachean las respuestas positivas para no lanzar llamadas `GET` redundantes cada minuto.
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
  \"state\": 12.4,
  \"attributes\": {
    \"device\": { ... },
    \"unique_id\": \"renogy_rover_li_1_solar_battery_voltage\",
    \"friendly_name\": \"Solar Battery Voltage\",
    \"device_class\": \"voltage\",
    \"state_class\": \"measurement\",
    \"unit_of_measurement\": \"V\",
    \"last_update\": 1627984567,
    \"microcontroller\": { ... }
  }
}
```

## Flujos principales
1. **Verificación y Creación del Dispositivo**:
   - `check_connection()`: Realiza `GET /api/` para verificar la disponibilidad; cachea el resultado positivo durante 5 minutos para evitar peticiones redundantes.
   - `create_device_entity()`: Realiza `POST /api/states/sensor.renogy_rover_li_<id>_device` con atributos descriptivos globales cada 3600s.
   - `verify_device_exists()`: Verifica existencia del sensor raíz una sola vez y cachea el estado positivo.
2. **Publicación de Métricas (`update_solar_controller_data`)**:
   - Itera sobre el diccionario de datos del controlador solar.
   - Evalúa `_should_send_update()` contra la caché `_last_sent_states` y `_last_sent_times`.
   - Si no ha variado por encima del umbral o no ha vencido el latido, omite la petición HTTP.
   - Si requiere envío, determina la clase de dispositivo (`device_class`), clase de estado (`state_class`), unidad de medida y envía vía `update_sensor()`.
3. **Publicación de Métricas del Microcontrolador (`update_microcontroller_sensors`)**:
   - Publica bajo el mismo filtrado por delta: `sensor.microcontroller_temperature`, `binary_sensor.microcontroller_wifi`, `sensor.microcontroller_wifi_signal` y `sensor.microcontroller_battery`.

## Puntos de entrada
| Método | Parámetros | Retorno | Requisitos |
|---|---|---|---|
| `check_connection()` | Ninguno | `bool` | WiFi y token válido (con caché 5 min) |
| `create_device_entity()` | Ninguno | `bool` | API accesible (con intervalo 3600s) |
| `verify_device_exists()` | Ninguno | `bool` | API accesible (con caché permanente) |
| `update_sensor(...)` | `entity_id, state, attributes, ...` | `bool` | API accesible |
| `update_solar_controller_data(data)` | `data: dict` | `bool` | API accesible (filtrado por delta) |
| `update_microcontroller_sensors()` | Ninguno | `bool` | Objeto `controller` válido (filtrado por delta) |

## Dependencias
- **Dependencias entrantes**:
  - Consumido por [`src/main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py) y [`tests/test_battery_calculation.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/test_battery_calculation.py).
- **Dependencias salientes**:
  - `urequests`, `ujson`, `time`, `gc`, [`src/Models/RpiPico.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RpiPico.py).

## Configuración
Variables opcionales en `env.py`:
- `UPLOAD_HOME_ASSISTANT` (`bool`): Habilita o deshabilita la subida.
- `HOME_ASSISTANT_URL` (`str`): URL base de la instancia (ej. `http://192.168.1.100:8123`).
- `HOME_ASSISTANT_TOKEN` (`str`): Token de acceso de larga duración.
- `DEVICE_ID` (`int`): Identificador del dispositivo.
- `HA_DELTA_FILTERING` (`bool`, por defecto `True`): Activa el filtrado por variación y latidos.
- `HA_HEARTBEAT_INTERVAL` (`int`, por defecto `600`): Segundos máximos antes de forzar el reenvío de un sensor dinámico.
- `HA_STATIC_INTERVAL` (`int`, por defecto `3600`): Segundos máximos antes de forzar el reenvío de un sensor estático.

## Trampas conocidas
- No utilizar caracteres acentuados o símbolos como `°` directamente en atributos; deben filtrarse con `_sanitize_string()`.
- Home Assistant no agrupará entidades si el valor de `identifiers` en `device` difiere aunque sea en una letra entre las distintas entidades.
- No existe el método `.title()` en cadenas de MicroPython; debe emplearse la función auxiliar `_capitalize_words()`.
- Cada petición HTTP genera un socket TCP efímero; es crítico no desactivar el filtrado por delta en entornos de ciclo corto para evitar agotar la memoria del chip CYW43439.

## Tests que lo cubren
- [`tests/test_battery_calculation.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/test_battery_calculation.py) (incluye pruebas de filtrado por delta, deadbands y caché).
- [`tests/test_device_creation.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/test_device_creation.py).
- [`tests/verify_entity_grouping.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/tests/verify_entity_grouping.py).

## Pendiente real
- Ninguno.

---
> Raúl Caro Pastorino · <public@raupulus.dev> · [raupulus.dev](https://raupulus.dev)
