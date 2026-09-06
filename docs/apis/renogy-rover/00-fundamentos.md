# Fundamentos: Protocolo Modbus RTU en Renogy Rover Li

## 1. Parámetros de la Capa Física (RS232)

- **Conector físico**: Conector hembra modular RJ12 (6P6C).
- **Asignación de pines verificada**:
  - Pin 3: RX del controlador (recibe datos transmitidos por el cliente).
  - Pin 4: TX del controlador (emite datos hacia el receptor del cliente).
  - Pin 5: Masa de señal (GND).
- **Configuración serie**:
  - Velocidad de baudios: `9600 bps`
  - Bits de datos: `8`
  - Paridad: `Ninguna` (None)
  - Bits de parada: `1`
  - Control de flujo: `Ninguno`

## 2. Formato de Trama Modbus RTU

### Consulta de Lectura (Función 0x03 — Read Holding Registers)
Trama binaria de 8 bytes:
```
[Slave ID] [Function] [Addr Hi] [Addr Lo] [Count Hi] [Count Lo] [CRC Lo] [CRC Hi]
```
- `Slave ID`: Dirección del dispositivo esclavo (`0x01` predeterminado en Renogy).
- `Function`: Código de función Modbus (`0x03`).
- `Addr Hi / Lo`: Dirección inicial del registro a consultar (16 bits, big-endian).
- `Count Hi / Lo`: Número de registros de 16 bits a leer (16 bits, big-endian).
- `CRC Lo / Hi`: Suma de comprobación CRC-16 (little-endian: byte bajo primero).

### Respuesta Exitosa
```
[Slave ID] [Function] [Byte Count] [Data ...] [CRC Lo] [CRC Hi]
```
- `Byte Count`: Número total de bytes de datos devueltos ($N = 2 \times \text{registros solicitados}$).
- `Data`: $N$ bytes conteniendo el valor de los registros en formato big-endian.
- `CRC Lo / Hi`: Verificación CRC-16 de toda la trama previa.

### Respuesta de Excepción
```
[Slave ID] [Function + 0x80] [Exception Code] [CRC Lo] [CRC Hi]
```
- Si el código de función es `0x83`, indica error en la lectura (ej. dirección no válida o longitud excesiva).

## 3. Algoritmo CRC-16 Modbus

La suma de verificación utiliza el polinomio `0xA001` con inicialización en `0xFFFF`:

```python
def calculate_crc(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return bytes([crc & 0xFF, crc >> 8])
```

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
