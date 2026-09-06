# Módulo: SerialConnection

Driver de enlace serie y cliente Modbus RTU directo sobre `machine.UART` en [`src/Models/SerialConnection.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/SerialConnection.py).

## Qué hace y qué NO hace
- **Qué hace**:
  - Inicializa el periférico hardware UART0 de MicroPython con parámetros 9600 baudios, 8 bits de datos, sin paridad y 1 bit de parada (8N1).
  - Calcula la suma de comprobación de redundancia cíclica CRC-16 Modbus (polinomio estándar `0xA001`, valor inicial `0xFFFF`, formato little-endian).
  - Ensambla y transmite tramas de consulta Modbus RTU para la función estándar `0x03` (Read Holding Registers) dirigidas al esclavo 1.
  - Vacía el búfer de recepción antes de emitir tramas para evitar lecturas de bytes espurios.
  - Valida la respuesta recibida: longitud mínima, código de excepción Modbus (`function_code + 0x80`), identificador de esclavo coincidente, conteo de bytes y verificación íntegra de CRC.
  - Decodifica los registros de 16 bits (big-endian en los datos devueltos).
  - Gestiona reintentos automáticos (por defecto 5 intentos con pausas de 100 ms).
- **Qué NO hace**:
  - No decodifica el significado de los registros ni aplica factores de conversión (responsabilidad de [`RenogyRoverLi`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py)).
  - No implementa escritura de registros (funciones `0x06` o `0x10`).

## Modelo de datos
- Parámetros de conexión:
  - `tx_pin` (`int`): Pin GPIO de transmisión (por defecto 0).
  - `rx_pin` (`int`): Pin GPIO de recepción (por defecto 1).
  - `baudrate` (`int`): Velocidad en baudios (por defecto 9600).
  - `timeout` (`float`): Tiempo de espera en segundos (por defecto 3.0).
  - `retries` (`int`): Reintentos antes de desistir (por defecto 5).
- Valores devueltos por `read_register`:
  - Lista de enteros de 16 bits `[reg_val_1, reg_val_2, ...]` o `None` en caso de error/timeout.

## Flujos principales
1. **Conexión / Inicialización**:
   - `connect()` instancia `machine.UART(0, baudrate=9600, tx=Pin(tx_pin), rx=Pin(rx_pin), bits=8, parity=None, stop=1, timeout=timeout_ms)`.
2. **Petición Modbus**:
   - Genera trama: `[0x01, 0x03, addr_hi, addr_lo, count_hi, count_lo]`.
   - Añade 2 bytes de CRC.
   - Limpia buffer con `self.uart.read()`.
   - Envía trama con `self.uart.write(message)`.
   - Pausa 100 ms y lee respuesta.
   - Comprueba integridad y extrae palabras de 16 bits `(high << 8) + low`.

## Puntos de entrada
| Método | Parámetros | Retorno | Requisitos |
|---|---|---|---|
| `__init__(debug, tx_pin, rx_pin, baudrate, timeout, retries)` | Parámetros de puerto serie | Instancia | Pines válidos en RP2040 |
| `connect()` | Ninguno | `bool` | Hardware UART disponible |
| `close()` | Ninguno | `bool` | Desinicializa UART |
| `read_register(register, bits=2, type_data=None)` | `register: int, bits: int, type_data: str` | `list[int] \| None` | Puerto serie abierto |
| `read_registers(registers, bits=2)` | `registers: list[int], bits: int` | `dict` | Puerto serie abierto |

## Dependencias
- **Dependencias entrantes**:
  - [`src/main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py) y [`src/Models/RenogyRoverLi.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py).
- **Dependencias salientes**:
  - `machine.UART`, `machine.Pin`, `time`.

## Configuración
Variables en `env.py`:
- `SERIAL_TX_PIN`: Pin GPIO asignado a UART0 TX (por defecto 0).
- `SERIAL_RX_PIN`: Pin GPIO asignado a UART0 RX (por defecto 1).

## Trampas conocidas
- El argumento `bits` en `read_register` representa la **cantidad de registros de 16 bits** a solicitar (por defecto 2 registros = 4 bytes).
- Los conversores MAX3232 de baja calidad pueden meter ruido si la masa (GND) no está compartida sólidamente entre la Pico y el controlador solar.
- Es imprescindible la pequeña pausa de 100 ms tras el envío para que el microcontrolador del Renogy complete el procesamiento de la petición y responda.

## Tests que lo cubren
- Invocado por las pruebas de ciclo en `src/main.py`.

## Pendiente real
- Evaluar si el método `close()` requiere invocar explícitamente `uart.deinit()`.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
