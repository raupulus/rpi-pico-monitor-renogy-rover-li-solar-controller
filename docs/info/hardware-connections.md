# Esquema de Conexiones de Hardware

Instrucciones detalladas de conexionado físico entre la Raspberry Pi Pico, el conversor RS232, el controlador Renogy Rover Li, los LEDs y los sensores auxiliares.

## 1. Conexión Raspberry Pi Pico a Conversor TTL-RS232 (MAX3232)

| Pin Raspberry Pi Pico | Función Pico | Pin Conversor TTL-RS232 | Notas |
|---|---|---|---|
| Pin 1 | GPIO0 (UART0 TX) | RX (TTL) | Señal transmitida por la Pico hacia el conversor |
| Pin 2 | GPIO1 (UART0 RX) | TX (TTL) | Señal recibida por la Pico desde el conversor |
| Pin 36 | 3V3(OUT) | VCC | Alimentación lógica (si el conversor admite 3.3V) |
| Pin 38 | GND | GND | Referencia de masa común |
| Pin 39 (Opcional) | VSYS (5V) | VCC | Utilizar si el módulo MAX3232 requiere estrictamente 5V |

## 2. Conexión Conversor RS232 a Puerto RJ12 Renogy Rover Li

El puerto de comunicaciones del Renogy Rover Li es una toma RJ12 hembra de 6 contactos (6P6C):

| Lado RS232 (Conversor) | Puerto RJ12 Renogy Rover Li | Función |
|---|---|---|
| TX (RS232) | Pin 3 (RX del controlador) | Envío de peticiones Modbus hacia el controlador |
| RX (RS232) | Pin 4 (TX del controlador) | Recepción de respuestas Modbus desde el controlador |
| GND (RS232) | Pin 5 (GND del controlador) | Masa de señal aislada |

```
+------------------+     +--------------------+     +-------------------+
|                  |     |                    |     |                   |
| Raspberry Pi     |     | Conversor TTL      |     | Renogy Rover Li   |
| Pico W           |     | a RS232 (MAX3232)  |     | Controlador Solar |
|                  |     |                    |     |                   |
| GPIO0 (Pin 1 TX) +---->| RX (TTL)  RS232 TX +---->| Pin 3 (RJ12 RX)   |
|                  |     |                    |     |                   |
| GPIO1 (Pin 2 RX) <-----+ TX (TTL)  RS232 RX <-----+ Pin 4 (RJ12 TX)   |
|                  |     |                    |     |                   |
| GND (Pin 38)     +-----+ GND       RS232 GND+-----+ Pin 5 (RJ12 GND)  |
|                  |     |                    |     |                   |
| 3.3V (Pin 36)    +---->| VCC                |     |                   |
+------------------+     +--------------------+     +-------------------+
```

## 3. Conexión de LEDs Indicadores Externos (Opcional)

Cada LED externo se conecta con una resistencia en serie limitadora de corriente (220 Ω a 330 Ω) para proteger las salidas GPIO del RP2040:

| LED | GPIO Pico | Pin Físico | Conexión del Circuito |
|---|---|---|---|
| **Power (Alimentación)** | GPIO15 | Pin 20 | GPIO15 → Ánodo LED → Cátodo LED → Resistencia 220Ω → GND |
| **Upload (Envío de datos)** | GPIO14 | Pin 19 | GPIO14 → Ánodo LED → Cátodo LED → Resistencia 220Ω → GND |
| **Cycle (Lectura de ciclo)** | GPIO13 | Pin 17 | GPIO13 → Ánodo LED → Cátodo LED → Resistencia 220Ω → GND |

```
GPIO Pico (13, 14 o 15) ────┤ Anodo (Largo) [LED] Cátodo (Corto) ├───[ 220Ω ]───┤ GND
```

## 4. Conexión de Monitoreo de Batería Externa (Opcional)

Si la Raspberry Pi Pico se alimenta mediante una celda o batería externa (Li-Ion / LiFePO4 de 3.7V - 4.2V conectada a VSYS) y se desea medir su porcentaje:

```
Batería (+) ───[ R1: 100 kΩ ]───┬───[ R2: 10 kΩ ]───┤ Batería (-) / GND
                                │
                                └─── A GPIO26 (ADC0 / Pin 31)
```

En `env.py` se definen los parámetros:
```python
BATTERY_ADC_PIN = 26
BATTERY_MIN_VOLTAGE = 2.5
BATTERY_MAX_VOLTAGE = 4.2
```

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
