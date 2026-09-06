# Inventario de Componentes de Hardware

Detalle de los componentes físicos, especificaciones eléctricas y funciones en el sistema de monitorización.

## 1. Microcontrolador: Raspberry Pi Pico W

- **SoC**: Raspberry Pi RP2040 (Dual-core ARM Cortex-M0+ a 133 MHz).
- **Memoria**: 264 KB SRAM, 2 MB Flash QSPI externa.
- **Conectividad Inalámbrica**: Chip Infineon CYW43439 (Wi-Fi 802.11b/g/n a 2.4 GHz).
- **Firmware**: MicroPython v1.25+ oficial para Raspberry Pi Pico W.
- **Función en el proyecto**: Ejecución del bucle de telemetría, controlador UART0 para Modbus RTU, cliente HTTP REST hacia Home Assistant y API externa, lectura de telemetría interna y control de LEDs.

## 2. Conversor de Nivel TTL a RS232 (MAX3232)

- **Chipset**: Maxim MAX3232 o equivalente compatible con alimentación a 3.3V.
- **Función**: Adaptación bidireccional de niveles lógicos entre los 3.3V de la Raspberry Pi Pico (UART0) y las tensiones bipolares de la norma EIA/TIA RS232 (±5V a ±15V) requeridas por el controlador solar.
- **Pines del lado TTL (hacia la Pico)**:
  - `VCC`: 3.3V (Pin 36 de la Pico) o 5V (VSYS Pin 39 si el conversor sólo opera a 5V).
  - `GND`: Conexión de masa común (Pin 38 de la Pico).
  - `TX`: Entrada de transmisión TTL (conectada a UART0 TX / GPIO0 / Pin 1).
  - `RX`: Salida de recepción TTL (conectada a UART0 RX / GPIO1 / Pin 2).
- **Pines del lado RS232 (hacia el controlador)**:
  - Terminales de transmisión, recepción y masa (o conector DB9 hembra adaptado a RJ12).

## 3. Controlador de Carga Solar: Renogy Rover Li

- **Familia**: Renogy Rover Li MPPT Series (modelos 20A / 30A / 40A / etc.).
- **Interfaz de Comunicaciones**: Puerto RS232 con conector modular RJ12 (6P6C).
- **Protocolo**: Modbus RTU estándar sobre RS232 a 9600 baudios, 8 bits de datos, 1 bit de parada, sin paridad (8N1). Dirección de esclavo (`slave_id`): 1.
- **Parámetros monitorizados**:
  - Tensión, intensidad y potencia de campo solar (PV).
  - Tensión, estado de carga (SOC %), corriente y temperatura de batería.
  - Tensión, corriente y potencia de salida de consumo (Load).
  - Estadísticas energéticas diarias (Ah y Wh de carga y descarga, tensiones mínimas y máximas).
  - Históricos acumulados (días en servicio, recuentos de carga completa y sobredescarga, kWh totales).

## 4. Conector y Cable RJ12 (6P6C)

Asignación típica de patillas del puerto serie en controladores Renogy Rover Li:

| Pin RJ12 | Señal Renogy | Conexión al Conversor RS232 |
|---|---|---|
| Pin 1 | NC / Reservado | Sin conexión |
| Pin 2 | NC / Reservado | Sin conexión |
| Pin 3 | TX del Controlador | RX del conversor RS232 |
| Pin 4 | RX del Controlador | TX del conversor RS232 |
| Pin 5 | GND (Tierra de señal) | GND del conversor RS232 |
| Pin 6 | NC / Alimentación auxiliar | Sin conexión |

> [!NOTE]
> En la documentación del proyecto se verifica que el Pin 3 actúa como RX del controlador (recibe desde el TX del conversor) y Pin 4 como TX del controlador (transmite hacia el RX del conversor).

## 5. LEDs de Diagnóstico y Resistencias

- **LED Encendido (Power)**: Verde o Rojo, cátodo a GND, ánodo a GPIO15 mediante resistencia limitadora de 220Ω - 330Ω.
- **LED Subida (Upload)**: Azul o Amarillo, cátodo a GND, ánodo a GPIO14 mediante resistencia de 220Ω - 330Ω.
- **LED Ciclo (Cycle)**: Blanco o Naranja, cátodo a GND, ánodo a GPIO13 mediante resistencia de 220Ω - 330Ω.
- **LED Integrado**: Directamente controlado mediante el módulo `machine.Pin("LED")` o GPIO interno del CYW43439.

## 6. Monitoreo de Batería Externa (Opcional)

- **Divisor Resistivo**:
  - $R_1$: Resistencia de 100 kΩ entre polo positivo de batería y GPIO26 (ADC0 / Pin 31).
  - $R_2$: Resistencia de 10 kΩ entre GPIO26 y GND.
- **Rango soportado**: Diseñado para paquetes Li-Ion / LiFePO4 de una o dos celdas con escalado lineal hacia el rango 0–3.3V del convertidor analógico-digital del RP2040.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
