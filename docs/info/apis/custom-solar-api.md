# Integración con API Solar Propia (API V2 — Energía)

Documento técnico sobre el contrato y protocolo de comunicación HTTP REST con el backend propio para el envío y consulta de telemetría energética solar.

## 1. Contrato de Transporte y Arquitectura

- **Base URL**: `/api/v2` (ej. `https://api.example.com` o `http://192.168.1.10:8000`).
- **Endpoint de Subida**: `POST /api/v2/energy/solar-readings`
- **Endpoint de Consulta**: `GET /api/v2/energy/solar-readings`
- **Autenticación**: Laravel Sanctum, cabecera `Authorization: Bearer <API_TOKEN>`.
  - **Ability requerida para subida**: `energy:write``.
  - **Ability requerida para consulta**: `energy:read`.
  - El token puede estar restringido al dispositivo (`device:{hardware_device_id}`). Un dispositivo ajeno provocará HTTP `422`.
- **Headers Requeridos**:
  - `Authorization: Bearer <API_TOKEN>`
  - `Content-Type: application/json`
  - `Accept: application/json`
- **Rate Limit**: 60 peticiones/min por token (`api-store`).

> ⚠️ **Migración a API V2 (2026-09-06)**: Los antiguos endpoints bajo `/hardware` (`/hardware/solar-readings`, `/hardware/v1/solarcharge/store`) que requerían `hardware:write` han sido deprecados y responden 404. El cliente debe utilizar las rutas `/energy/*` con tokens emitidos con la ability `energy:write`.

---

## 2. Envelope de Respuesta Estándar

Todas las respuestas del servidor utilizan la estructura unificada `ApiResponseTrait`:

### Éxito (HTTP 200 / 201)
```json
{
  "success": true,
  "message": "Lectura del controlador solar almacenada",
  "data": {
    "id": 88,
    "hardware_device_id": 1,
    "hardware_energy_id": 4,
    "date": "2026-09-06",
    "read_at": "2026-09-06T18:45:00.000000Z",
    "controller": { ... },
    "battery": { ... },
    "generation": { ... },
    "load": { ... },
    "day": { ... },
    "total": { ... }
  },
  "warnings": [
    "Aviso opcional si ocurrió alguna anomalía no crítica (ej. corriente negativa o reinicio de días)"
  ]
}
```
*Nota*: `warnings` no aparece si no hay avisos.

### Error (HTTP 401, 403, 422, 429, 500)
```json
{
  "success": false,
  "message": "Descripción del error",
  "errors": {
    "campo": ["Detalle de validación"]
  }
}
```

---

## 3. Estructura del Cuerpo (`POST /energy/solar-readings`)

El payload enviado por [`Api.send_to_api()`](../Api.md) estructura los datos nativos de telemetría y el estado de salud del hardware:

```json
{
  "hardware_device_id": 1,
  "hardware": "V1.0.0",
  "version": "V1.2.4",
  "serial_number": "12345678",
  "battery_type": "lithium",
  "battery_voltage": 13.2,
  "battery_current": null,
  "battery_power": null,
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
      "wifi_ssid": "your_wifi_ssid"
    }
  }
}
```

### Detalle de `hardware_device_info`
Permite reportar la salud del microcontrolador en la misma petición sin necesidad de la ability `hardware:write` ni llamadas extra:
- `temp`: Temperatura interna de CPU del RP2040 (°C).
- `voltage`: Voltaje de batería externa de respaldo medida en pin ADC (V).
- `battery_level`: Porcentaje de batería externa (0–100%).
- `ram`: Porcentaje de uso de memoria RAM en MicroPython.
- `uptime`: Segundos transcurridos desde el encendido de la Raspberry Pi Pico W.
- `ip_local`: Dirección IP asignada en la red local.
- `extra`: Diccionario con diagnósticos adicionales de red (`wifi_rssi`, `wifi_ssid`).

---

## 4. Comportamiento y Tolerancia a Fallos

1. **Liberación de Sockets**:
   - Cada petición HTTP cierra explícitamente el socket (`response.close()`) en un bloque `finally`, seguido de `gc.collect()`, evitando saturación de sockets en el stack LWIP de MicroPython (`OSError: ENOMEM`).
2. **Reintentos con Retroceso Exponencial**:
   - En caso de errores transitorios de red o timeouts (hasta 3 reintentos con factor de backoff de 0.5s: 0.5s, 1.0s, 2.0s).
   - Errores definitivos de cliente (HTTP 401, 403, 422) abortan inmediatamente los reintentos para no saturar el servidor ni el rate limit.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
