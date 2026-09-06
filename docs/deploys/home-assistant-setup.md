# Guía de Despliegue: Configuración en Home Assistant

Pasos para configurar la recepción de métricas, paquetes de sensores y paneles en Home Assistant.

## 1. Generación de Token de Acceso
1. En la interfaz web de Home Assistant, pulsa sobre tu perfil de usuario (abajo a la izquierda).
2. Desplázate hasta **Tokens de acceso de larga duración** (Long-Lived Access Tokens).
3. Pulsa **Crear token** y nómbralo (ej. `pico-solar-controller`).
4. Copia el token generado y pégalo en `src/env.py` en la variable `HOME_ASSISTANT_TOKEN`.

## 2. Configuración de Paquetes (Packages) en YAML
Para organizar los medidores de utilidad y paneles sin ensuciar `configuration.yaml`:

1. Comprueba que `configuration.yaml` incluya paquetes:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. En la carpeta de configuración de Home Assistant, crea el subdirectorio `packages/` si no existe.
3. Crea el archivo `packages/solar_controller.yaml`:
   ```yaml
   homeassistant:
     customize:
       sensor.renogy_rover_li_1_device:
         friendly_name: "Controlador Solar Renogy Rover Li"
         icon: mdi:solar-power

   # Medidores para cálculo de balances energéticos
   utility_meter:
     solar_energy_daily:
       source: sensor.solar_today_power_generation
       cycle: daily
       name: Generación Solar Diaria
     solar_energy_weekly:
       source: sensor.solar_today_power_generation
       cycle: weekly
       name: Generación Solar Semanal
     solar_energy_monthly:
       source: sensor.solar_today_power_generation
       cycle: monthly
       name: Generación Solar Mensual

     solar_consumption_daily:
       source: sensor.solar_today_power_consumption
       cycle: daily
       name: Consumo Solar Diario
     solar_consumption_weekly:
       source: sensor.solar_today_power_consumption
       cycle: weekly
       name: Consumo Solar Semanal
     solar_consumption_monthly:
       source: sensor.solar_today_power_consumption
       cycle: monthly
       name: Consumo Solar Mensual
   ```

## 3. Configuración del Panel Lovelace
En tu panel de Lovelace (interfaz gráfica o archivo de dashboard `solar-dashboard.yaml`), añade tarjetas de entidades:

```yaml
title: Solar Dashboard
views:
  - title: Solar Controller
    path: solar
    icon: mdi:solar-power
    cards:
      - type: entities
        title: "Estado Actual"
        entities:
          - entity: sensor.solar_battery_voltage
          - entity: sensor.solar_battery_percentage
          - entity: sensor.solar_solar_voltage
          - entity: sensor.solar_solar_power
          - entity: sensor.solar_controller_temperature
          - entity: sensor.solar_charging_status_label

      - type: gauge
        title: "Batería"
        entity: sensor.solar_battery_percentage
        min: 0
        max: 100
        severity:
          green: 50
          yellow: 20
          red: 0

      - type: history-graph
        title: "Tendencias 24h"
        hours_to_show: 24
        entities:
          - entity: sensor.solar_solar_power
          - entity: sensor.solar_battery_voltage

      - type: entities
        title: "Microcontrolador Pico W"
        entities:
          - entity: sensor.microcontroller_temperature
          - entity: binary_sensor.microcontroller_wifi
          - entity: sensor.microcontroller_wifi_signal
```

## 4. Verificación de Agrupación de Dispositivos
1. Dirígete a **Ajustes > Dispositivos y Servicios > Dispositivos**.
2. Deberá aparecer **Controlador Solar Renogy Rover Li 1**.
3. Al hacer clic, todas las entidades (`sensor.solar_*` y `sensor.microcontroller_*`) deben figurar asociadas al mismo dispositivo físico.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
