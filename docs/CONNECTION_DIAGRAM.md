# Connection Diagram for Raspberry Pi Pico to Renogy Rover Li Solar Controller

This document provides detailed instructions for connecting a Raspberry Pi Pico to a Renogy Rover Li solar controller using a TTL to RS232 converter.

## Hardware Requirements

- Raspberry Pi Pico (or Raspberry Pi Pico W for wireless connectivity)
- TTL to RS232 converter module (e.g., MAX3232 based converter)
- Jumper wires
- Renogy Rover Li solar controller
- Optional: External battery for portable operation

## Pin Connections

### Raspberry Pi Pico to TTL-RS232 Converter

| Raspberry Pi Pico | TTL-RS232 Converter |
|-------------------|---------------------|
| GPIO0 (Pin 1) - TX | RX                 |
| GPIO1 (Pin 2) - RX | TX                 |
| 3.3V (Pin 36)     | VCC (if 3.3V compatible) |
| GND (Pin 38)      | GND                 |

**Note:** If your TTL-RS232 converter requires 5V, use the VSYS (Pin 39) or 5V output pin instead of 3.3V.

### TTL-RS232 Converter to Renogy Rover Li

The Renogy Rover Li solar controller has an RJ12 port for RS232 communication. You'll need to connect the RS232 side of your converter to this port.

| TTL-RS232 Converter (RS232 side) | Renogy Rover Li RJ12 Port |
|----------------------------------|---------------------------|
| TX                               | RX (Pin 3 on RJ12)        |
| RX                               | TX (Pin 4 on RJ12)        |
| GND                              | GND (Pin 5 on RJ12)       |

**Note:** The RJ12 pinout may vary. Please consult your Renogy Rover Li manual to confirm the correct pins.

## Visual Diagram

```
+----------------+     +------------------+     +-------------------+
|                |     |                  |     |                   |
| Raspberry Pi   |     | TTL to RS232     |     | Renogy Rover Li   |
| Pico           |     | Converter        |     | Solar Controller  |
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

## Optional: External Battery Connection

If you want to power the Raspberry Pi Pico from an external battery and monitor the battery level:

1. Connect the battery's positive terminal to the VSYS pin (Pin 39) on the Raspberry Pi Pico
2. Connect the battery's negative terminal to a GND pin on the Raspberry Pi Pico
3. To monitor the battery level, use a voltage divider and connect it to an ADC pin:

```
Battery+ ---+
            |
            R1 (e.g., 100kΩ)
            |
            +--- To ADC pin (e.g., GPIO26/ADC0)
            |
            R2 (e.g., 10kΩ)
            |
Battery- ---+
```

Configure the battery monitoring in your env.py file:

```python
BATTERY_ADC_PIN = 26  # ADC pin number for battery monitoring
BATTERY_MIN_VOLTAGE = 2.5  # Minimum battery voltage
BATTERY_MAX_VOLTAGE = 4.2  # Maximum battery voltage
```

## Software Configuration

After making the physical connections, you need to configure the software:

1. Copy the `.env.example.py` file to `env.py`
2. Update the values in `env.py` to match your configuration
3. Make sure the UART pins are correctly set:

```python
SERIAL_TX_PIN = 0  # GPIO pin number for TX (UART0 TX is GPIO0)
SERIAL_RX_PIN = 1  # GPIO pin number for RX (UART0 RX is GPIO1)
```

## Troubleshooting

If you're having trouble with the connection:

1. **Check the wiring**: Make sure all connections are secure and correctly wired.
2. **Check power**: Ensure the TTL to RS232 converter is receiving power.
3. **Check ground**: Make sure all devices share a common ground.
4. **Check TX/RX**: Sometimes TX and RX connections need to be swapped.
5. **Check baud rate**: The default baud rate for the Renogy Rover Li is 9600. Make sure your software is configured to use this rate.
6. **Check debug output**: Enable DEBUG mode in your env.py file to see more detailed output.

## LED Indicators

### Onboard LED

The Raspberry Pi Pico's onboard LED is used to indicate the status of the application:

- **LED on**: Program is running
- **LED blink once**: Successful data collection cycle
- **LED rapid blink (5 times)**: Error occurred

### External LEDs (Optional)

You can connect external LEDs to provide more detailed status information:

1. **Power LED**: Indicates the system is powered on
2. **Upload LED**: Indicates when data is being uploaded to API/Home Assistant
3. **Cycle LED**: Indicates when the cycle is working (reading data from the solar controller)

#### External LED Connections

| LED Type | Raspberry Pi Pico | External Components |
|----------|------------------|---------------------|
| Power LED | GPIO15 (default) | LED → 220Ω resistor → GND |
| Upload LED | GPIO14 (default) | LED → 220Ω resistor → GND |
| Cycle LED | GPIO13 (default) | LED → 220Ω resistor → GND |

**Note:** The GPIO pins can be configured in your `env.py` file:

```python
# Configuración de LEDs externos (opcional)
LED_POWER_PIN = 15  # Número de pin GPIO para LED de encendido
LED_UPLOAD_PIN = 14  # Número de pin GPIO para LED de subida a API/Home Assistant
LED_CYCLE_PIN = 13  # Número de pin GPIO para LED de trabajo del ciclo
```

#### External LED Circuit Diagram

```
Raspberry Pi Pico GPIO Pin --+
                             |
                             | 
                             ⎍ LED
                             |
                             |
                        220Ω ⎍ Resistor
                             |
                             |
                            GND
```

These LEDs provide visual feedback about the system's operation, which can help diagnose issues without needing to connect to the serial console.