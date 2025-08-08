# Diagrama de Conexiones para Raspberry Pi Pico a Controlador Solar Renogy Rover Li

Este documento proporciona instrucciones detalladas para conectar una Raspberry Pi Pico a un controlador solar Renogy Rover Li utilizando un conversor TTL a RS232.

## Requisitos de Hardware

- Raspberry Pi Pico (o Raspberry Pi Pico W para conectividad inalámbrica)
- Módulo conversor TTL a RS232 (ej., conversor basado en MAX3232)
- Cables jumper
- Controlador solar Renogy Rover Li
- Opcional: Batería externa para operación portátil

## Conexiones de Pines

### Raspberry Pi Pico a Conversor TTL-RS232

| Raspberry Pi Pico | Conversor TTL-RS232 |
|-------------------|---------------------|
| GPIO0 (Pin 1) - TX | RX                 |
| GPIO1 (Pin 2) - RX | TX                 |
| 3.3V (Pin 36)     | VCC (si es compatible con 3.3V) |
| GND (Pin 38)      | GND                 |

**Nota:** Si tu conversor TTL-RS232 requiere 5V, usa el pin VSYS (Pin 39) o el pin de salida 5V en lugar de 3.3V.

### Conversor TTL-RS232 a Renogy Rover Li

El controlador solar Renogy Rover Li tiene un puerto RJ12 para comunicación RS232. Necesitarás conectar el lado RS232 de tu conversor a este puerto.

| Conversor TTL-RS232 (lado RS232) | Puerto RJ12 Renogy Rover Li |
|----------------------------------|----------------------------|
| TX                               | RX (Pin 3 en RJ12)        |
| RX                               | TX (Pin 4 en RJ12)        |
| GND                              | GND (Pin 5 en RJ12)       |

**Nota:** El pinout RJ12 puede variar. Por favor consulta el manual de tu Renogy Rover Li para confirmar los pines correctos.

## Diagrama Visual

```
+----------------+     +------------------+     +-------------------+
|                |     |                  |     |                   |
| Raspberry Pi   |     | Conversor TTL    |     | Renogy Rover Li   |
| Pico           |     | a RS232          |     | Controlador Solar |
|                |     |                  |     |                   |
| GPIO0 (TX) ----+---->| RX       RS232 TX+---->| RX               |
|                |     |                  |     |                   |
| GPIO1 (RX) <---+-----| TX       RS232 RX|<----| TX               |
|                |     |                  |     |                   |
| GND ----------+----->| GND         GND +---->| GND               |
|                |     |                  |     |                   |
| 3.3V/5V -------+---->| VCC              |     |                   |
|                |     |                  |     |                   |
+----------------+     +------------------+     +-------------------+
```

## Opcional: Conexión de Batería Externa

Si quieres alimentar la Raspberry Pi Pico desde una batería externa y monitorear el nivel de batería:

1. Conecta el terminal positivo de la batería al pin VSYS (Pin 39) en la Raspberry Pi Pico
2. Conecta el terminal negativo de la batería a un pin GND en la Raspberry Pi Pico
3. Para monitorear el nivel de batería, usa un divisor de voltaje y conéctalo a un pin ADC:

```
Batería+ ---+
            |
            R1 (ej., 100kΩ)
            |
            +--- Al pin ADC (ej., GPIO26/ADC0)
            |
            R2 (ej., 10kΩ)
            |
Batería- ---+
```

Configura el monitoreo de batería en tu archivo env.py:

```python
BATTERY_ADC_PIN = 26  # Número de pin ADC para monitoreo de batería
BATTERY_MIN_VOLTAGE = 2.5  # Voltaje mínimo de la batería
BATTERY_MAX_VOLTAGE = 4.2  # Voltaje máximo de la batería
```

## Configuración del Software

Después de realizar las conexiones físicas, necesitas configurar el software:

1. Copia el archivo `.env.example.py` a `env.py`
2. Actualiza los valores en `env.py` para que coincidan con tu configuración
3. Asegúrate de que los pines UART estén configurados correctamente:

```python
SERIAL_TX_PIN = 0  # Número de pin GPIO para TX (UART0 TX es GPIO0)
SERIAL_RX_PIN = 1  # Número de pin GPIO para RX (UART0 RX es GPIO1)
```

## Solución de Problemas

Si tienes problemas con la conexión:

1. **Verifica el cableado**: Asegúrate de que todas las conexiones estén seguras y correctamente conectadas.
2. **Verifica la alimentación**: Asegúrate de que el conversor TTL a RS232 esté recibiendo energía.
3. **Verifica la tierra**: Asegúrate de que todos los dispositivos compartan una tierra común.
4. **Verifica TX/RX**: A veces las conexiones TX y RX necesitan ser intercambiadas.
5. **Verifica la velocidad de baudios**: La velocidad de baudios predeterminada para el Renogy Rover Li es 9600. Asegúrate de que tu software esté configurado para usar esta velocidad.
6. **Verifica la salida de depuración**: Habilita el modo DEBUG en tu archivo env.py para ver una salida más detallada.

## Indicadores LED

### LED Integrado

El LED integrado de la Raspberry Pi Pico se usa para indicar el estado de la aplicación:

- **LED encendido**: El programa está ejecutándose
- **LED parpadea una vez**: Ciclo de recolección de datos exitoso
- **LED parpadea rápidamente (5 veces)**: Ocurrió un error

### LEDs Externos (Opcional)

Puedes conectar LEDs externos para proporcionar información de estado más detallada:

1. **LED de Encendido**: Indica que el sistema está encendido
2. **LED de Subida**: Indica cuando se están subiendo datos a la API/Home Assistant
3. **LED de Ciclo**: Indica cuando el ciclo está funcionando (leyendo datos del controlador solar)

#### Conexiones de LEDs Externos

| Tipo de LED | Raspberry Pi Pico | Componentes Externos |
|-------------|------------------|---------------------|
| LED de Encendido | GPIO15 (predeterminado) | LED → Resistencia 220Ω → GND |
| LED de Subida | GPIO14 (predeterminado) | LED → Resistencia 220Ω → GND |
| LED de Ciclo | GPIO13 (predeterminado) | LED → Resistencia 220Ω → GND |

**Nota:** Los pines GPIO se pueden configurar en tu archivo `env.py`:

```python
# Configuración de LEDs externos (opcional)
LED_POWER_PIN = 15  # Número de pin GPIO para LED de encendido
LED_UPLOAD_PIN = 14  # Número de pin GPIO para LED de subida a API/Home Assistant
LED_CYCLE_PIN = 13  # Número de pin GPIO para LED de trabajo del ciclo
```

#### Diagrama del Circuito de LED Externo

```
Pin GPIO Raspberry Pi Pico --+
                             |
                             | 
                             ⎍ LED
                             |
                             |
                        220Ω ⎍ Resistencia
                             |
                             |
                            GND
```

Estos LEDs proporcionan retroalimentación visual sobre el funcionamiento del sistema, lo que puede ayudar a diagnosticar problemas sin necesidad de conectar a la consola serial.