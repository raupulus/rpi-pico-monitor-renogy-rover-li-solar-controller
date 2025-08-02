# Guía Completa de Configuración de Home Assistant

Esta guía proporciona instrucciones paso a paso para configurar Home Assistant con el proyecto de monitorización del controlador solar Renogy Rover Li. Siguiendo estas instrucciones, podrás visualizar todos los datos del controlador solar en tu panel de Home Assistant, correctamente agrupados bajo un único dispositivo.

## Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Generación de Token de Acceso](#generación-de-token-de-acceso)
3. [Configuración del Proyecto](#configuración-del-proyecto)
4. [Configuración de Home Assistant](#configuración-de-home-assistant)
5. [Verificación de la Integración](#verificación-de-la-integración)
6. [Creación de Paneles](#creación-de-paneles)
7. [Solución de Problemas](#solución-de-problemas)

## Requisitos Previos

- Una instalación funcional de Home Assistant
- La Raspberry Pi Pico con el firmware del proyecto instalado
- Acceso a la configuración de Home Assistant

## Generación de Token de Acceso

Para que la Raspberry Pi Pico pueda comunicarse con Home Assistant, necesitas generar un token de acceso de larga duración:

1. Accede a tu instancia de Home Assistant en el navegador
2. Haz clic en tu nombre de usuario en la esquina inferior izquierda
3. Desplázate hacia abajo hasta "Tokens de acceso de larga duración"
4. Haz clic en "Crear token"
5. Asigna un nombre descriptivo como "Raspberry Pi Pico Solar Controller"
6. Haz clic en "OK"
7. **IMPORTANTE**: Copia el token generado y guárdalo en un lugar seguro. Este token solo se muestra una vez.

## Configuración del Proyecto

Configura el proyecto para conectarse a Home Assistant:

1. Edita el archivo `env.py` en la Raspberry Pi Pico
2. Configura las siguientes variables:

```python
# Configuración de Home Assistant
UPLOAD_HOME_ASSISTANT = True  # Activa la subida a Home Assistant
HOME_ASSISTANT_URL = "http://192.168.1.100:8123"  # URL de tu instancia de Home Assistant
HOME_ASSISTANT_TOKEN = "tu_token_de_acceso"  # Token generado anteriormente
DEVICE_ID = 1  # ID único para este dispositivo
```

Asegúrate de reemplazar:
- `http://192.168.1.100:8123` con la URL real de tu instancia de Home Assistant
- `tu_token_de_acceso` con el token que generaste en el paso anterior

## Configuración de Home Assistant

### Paso 1: Habilitar la Inclusión de Paquetes

Primero, debes configurar Home Assistant para que utilice el sistema de paquetes, que permite organizar la configuración en archivos separados:

1. Edita el archivo `configuration.yaml` en tu instalación de Home Assistant
2. Añade o modifica la sección `homeassistant` para incluir los paquetes:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

3. Guarda el archivo

### Paso 2: Crear el Directorio de Paquetes

1. Crea un directorio llamado `packages` en el mismo nivel que tu archivo `configuration.yaml`
2. Si estás usando Home Assistant OS o Home Assistant Container, puedes hacerlo desde la interfaz de Supervisor > Herramientas del Sistema > Explorador de Archivos

### Paso 3: Crear el Archivo de Configuración del Controlador Solar

1. Crea un archivo llamado `solar_controller.yaml` en el directorio `packages`
2. Copia y pega el siguiente contenido:

```yaml
# Configuración del Controlador Solar Renogy Rover Li
# Este archivo configura la integración con el controlador solar

# Personalización de entidades
homeassistant:
  customize:
    # Entidad del dispositivo principal
    sensor.renogy_rover_li_1_device:
      friendly_name: "Controlador Solar Renogy Rover Li"
      icon: mdi:solar-power

# Grupo para el panel
group:
  solar_controller:
    name: "Controlador Solar"
    entities:
      - sensor.solar_battery_voltage
      - sensor.solar_battery_percentage
      - sensor.solar_solar_power
      - sensor.solar_solar_voltage
      - sensor.solar_controller_temperature
      - sensor.solar_battery_temperature
      - sensor.solar_today_power_generation
      - sensor.solar_today_power_consumption

# Configuración de estadísticas globales para energía solar
utility_meter:
  # Medidores para generación de energía
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
  
  # Medidores para consumo de energía
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

# Tarjeta para el panel
lovelace:
  resources:
    - url: /hacsfiles/mini-graph-card/mini-graph-card-bundle.js
      type: module
  dashboards:
    solar-dashboard:
      mode: yaml
      title: Solar Dashboard
      icon: mdi:solar-power
      show_in_sidebar: true
      filename: solar-dashboard.yaml
```

3. Guarda el archivo

### Paso 4: Crear el Panel de Control

1. Crea un archivo llamado `solar-dashboard.yaml` en el directorio raíz de configuración de Home Assistant
2. Copia y pega el siguiente contenido:

```yaml
title: Solar Dashboard
views:
  - title: Solar Controller
    path: solar
    icon: mdi:solar-power
    badges: []
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
        title: "Tendencias"
        hours_to_show: 24
        entities:
          - entity: sensor.solar_solar_power
          - entity: sensor.solar_battery_voltage
      
      - type: entities
        title: "Estadísticas Diarias"
        entities:
          - entity: sensor.solar_today_power_generation
          - entity: sensor.solar_today_power_consumption
          - entity: sensor.solar_today_battery_min_voltage
          - entity: sensor.solar_today_battery_max_voltage
      
      - type: entities
        title: "Estadísticas Globales"
        entities:
          - entity: sensor.solar_historical_total_days_operating
          - entity: sensor.solar_historical_total_number_battery_full_charges
          - entity: sensor.solar_historical_total_number_battery_over_discharges
          - entity: sensor.solar_historical_total_charging_amp_hours
          - entity: sensor.solar_historical_total_discharging_amp_hours
          - entity: sensor.solar_historical_cumulative_power_generation
          - entity: sensor.solar_historical_cumulative_power_consumption
      
      - type: entities
        title: "Estado del Microcontrolador"
        entities:
          - entity: sensor.microcontroller_temperature
          - entity: binary_sensor.microcontroller_wifi
          - entity: sensor.microcontroller_wifi_signal
```

3. Guarda el archivo

### Paso 5: Reiniciar Home Assistant

1. Ve a Configuración > Sistema > Reiniciar
2. Haz clic en "REINICIAR"
3. Espera a que Home Assistant se reinicie completamente

## Verificación de la Integración

Para verificar que la integración funciona correctamente:

1. Reinicia la Raspberry Pi Pico para que comience a enviar datos a Home Assistant
2. Espera unos minutos para que se envíen los datos
3. En Home Assistant, ve a Configuración > Dispositivos
4. Busca "Controlador Solar Renogy Rover Li" en la lista de dispositivos
5. Haz clic en él para ver todas las entidades asociadas
6. Verifica que todas las entidades esperadas estén presentes y agrupadas bajo este dispositivo

También puedes ejecutar el script de verificación incluido en el proyecto:

1. En la Raspberry Pi Pico, ejecuta:

```python

from tests import verify_entity_grouping
```
2. Sigue las instrucciones en pantalla para verificar la agrupación de entidades

## Creación de Paneles

Si quieres personalizar el panel de control, puedes hacerlo de dos maneras:

### Método 1: Usando la Interfaz de Usuario

1. Ve a Configuración > Paneles
2. Haz clic en "+" para añadir una nueva tarjeta
3. Selecciona el tipo de tarjeta que deseas añadir
4. Configura la tarjeta según tus preferencias
5. Haz clic en "GUARDAR"

### Método 2: Editando el Archivo YAML

1. Edita el archivo `solar-dashboard.yaml` que creaste anteriormente
2. Añade o modifica las tarjetas según tus preferencias
3. Guarda el archivo
4. Recarga la página del panel de control para ver los cambios

## Solución de Problemas

### El dispositivo no aparece en Home Assistant

Si el dispositivo "Controlador Solar Renogy Rover Li" no aparece en Home Assistant:

1. Verifica que `UPLOAD_HOME_ASSISTANT` está establecido en `True` en tu archivo `env.py`
2. Verifica que `HOME_ASSISTANT_URL` y `HOME_ASSISTANT_TOKEN` están correctamente configurados
3. Asegúrate de que la Raspberry Pi Pico está conectada a la red y puede acceder a Home Assistant
4. Activa el modo DEBUG en `env.py` para ver mensajes detallados:
   ```python
   DEBUG = True
   ```
5. Reinicia la Raspberry Pi Pico y observa los mensajes de depuración

### Las entidades no están agrupadas

Si las entidades existen pero no están agrupadas bajo el dispositivo:

1. Verifica que todas las entidades tienen el mismo identificador de dispositivo
2. Ejecuta el script de verificación para identificar entidades problemáticas:
   ```python

from tests import verify_entity_grouping
   ```
3. Si encuentras entidades problemáticas, puedes corregirlas manualmente usando el script de verificación

### Error "Invalid JSON specified"

Si ves errores como "Invalid JSON specified" en los logs:

1. Verifica que no hay caracteres especiales en los nombres de las entidades o atributos
2. Asegúrate de que estás usando la última versión del código, que incluye sanitización de caracteres especiales

### Home Assistant no es accesible

Si la Raspberry Pi Pico no puede conectarse a Home Assistant:

1. Verifica que la URL de Home Assistant es correcta y accesible desde la red de la Raspberry Pi Pico
2. Asegúrate de que no hay firewalls o restricciones de red que bloqueen la conexión
3. Verifica que el token de acceso es válido y tiene los permisos necesarios

### Entidades duplicadas

Si ves entidades duplicadas en Home Assistant:

1. Ve a Configuración > Entidades
2. Selecciona las entidades duplicadas
3. Haz clic en "ELIMINAR"
4. Reinicia la Raspberry Pi Pico para que vuelva a crear las entidades correctamente

## Configuración Simplificada

Esta guía utiliza una configuración simplificada para Home Assistant que se centra en lo esencial:

1. **Entidades Correctas**: Usa los nombres de entidad correctos como `sensor.solar_solar_voltage` y `sensor.solar_solar_power`, que coinciden con cómo se crean en el código.

2. **Estadísticas Globales**: Utiliza los datos históricos generales proporcionados por el método `get_historical_info_datas()` del modelo RenogyRoverLi.

3. **Estadísticas de Generación Solar**: Utiliza un gráfico de estadísticas para visualizar los datos de generación de energía diaria.

4. **Panel Básico**: Proporciona un panel de control básico que muestra la información más importante.

### Notas sobre Nombres de Entidades

Los nombres de entidad como `sensor.solar_solar_voltage` pueden parecer redundantes, pero son correctos. Esto ocurre porque:

1. El prefijo `sensor.` es añadido por Home Assistant para todas las entidades de tipo sensor.
2. El prefijo `solar_` es añadido por el código al crear las entidades.
3. Las claves en el modelo RenogyRoverLi son `solar_voltage`, `solar_power`, etc.

Sin embargo, los nombres amigables mostrados en la interfaz de usuario no tienen esta redundancia, gracias al código que evita nombres como "Solar Solar Voltage".

### Datos Históricos y Estadísticas

La sección "Estadísticas Globales" muestra los datos históricos generales del controlador solar, que son proporcionados por el método `get_historical_info_datas()` del modelo RenogyRoverLi. Estos datos incluyen:

- Días totales de operación
- Número total de cargas completas de la batería
- Número total de descargas excesivas de la batería
- Amperios-hora totales de carga
- Amperios-hora totales de descarga
- Generación de energía acumulada
- Consumo de energía acumulado

La sección "Estadísticas de Generación Solar" muestra un gráfico de estadísticas para la generación de energía diaria, utilizando la entidad `sensor.solar_today_power_generation`. Este gráfico muestra la media, mínimo, máximo y suma de la generación de energía durante el día.

## Prueba de la Configuración

Para probar esta configuración:

1. Aplica los cambios en tu archivo `configuration.yaml` y en el directorio `packages`.
2. Reinicia Home Assistant.
3. Reinicia la Raspberry Pi Pico para que comience a enviar datos.
4. Verifica que las entidades aparecen correctamente agrupadas en Home Assistant.
5. Comprueba que el panel de control muestra la información correctamente.

### Verificación de las Correcciones

Para verificar específicamente las correcciones realizadas:

1. **Estadísticas Globales**: Verifica que la sección "Estadísticas Globales" muestra los datos históricos del controlador solar:
   - Días totales de operación
   - Número total de cargas completas de la batería
   - Número total de descargas excesivas de la batería
   - Amperios-hora totales de carga
   - Amperios-hora totales de descarga
   - Generación de energía acumulada
   - Consumo de energía acumulado

2. **Estadísticas de Generación Solar**: Verifica que la sección "Estadísticas de Generación Solar" muestra un gráfico de estadísticas para la generación de energía diaria, sin mostrar el error "Error de configuración".

Si alguna de estas secciones no se muestra correctamente:
- Verifica que las entidades existen en Home Assistant usando el script de verificación.
- Comprueba que la sintaxis YAML es correcta.
- Asegúrate de que Home Assistant tiene suficientes datos históricos para mostrar estadísticas.

Si encuentras problemas, activa el modo DEBUG en tu archivo `env.py` y revisa los mensajes de depuración para identificar el origen del problema.

## Conclusión

Siguiendo esta guía, deberías tener una integración funcional entre tu Raspberry Pi Pico con el controlador solar Renogy Rover Li y Home Assistant. Todas las entidades deberían estar correctamente agrupadas bajo un único dispositivo, y deberías poder visualizar los datos esenciales en un panel de control.

Si sigues teniendo problemas, no dudes en consultar la documentación adicional o abrir un issue en el repositorio del proyecto.