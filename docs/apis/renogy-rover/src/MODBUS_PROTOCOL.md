# Documentación del Protocolo Modbus para Controlador Solar Renogy Rover Li

Este documento proporciona información detallada sobre la implementación del protocolo Modbus para comunicarse con el controlador solar Renogy Rover Li a través de RS232. Incluye direcciones de registros, tipos de datos y ejemplos de cómo leer e interpretar datos del controlador.

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Detalles de Conexión RS232](#detalles-de-conexión-rs232)
3. [Implementación del Protocolo Modbus](#implementación-del-protocolo-modbus)
4. [Mapa de Registros Modbus](#mapa-de-registros-modbus)
   - [Información del Sistema](#información-del-sistema)
   - [Información de la Batería](#información-de-la-batería)
   - [Información del Panel Solar](#información-del-panel-solar)
   - [Información de la Carga](#información-de-la-carga)
   - [Datos Históricos Diarios](#datos-históricos-diarios)
   - [Datos Históricos Acumulativos](#datos-históricos-acumulativos)
   - [Información de Estado](#información-de-estado)
   - [Parámetros de Configuración](#parámetros-de-configuración)
5. [Interpretación de Datos](#interpretación-de-datos)
6. [Ejemplos de Comandos y Respuestas](#ejemplos-de-comandos-y-respuestas)

## Introducción

El controlador solar Renogy Rover Li utiliza el protocolo Modbus RTU sobre RS232 para la comunicación. Este protocolo permite leer varios parámetros del controlador, como el voltaje de la batería, la potencia del panel solar, la corriente de carga y los datos históricos.

La implementación en este proyecto utiliza una Raspberry Pi Pico con MicroPython para comunicarse con el controlador a través de un conversor TTL a RS232.

## Detalles de Conexión RS232

### Conexión de Hardware

Para conectar la Raspberry Pi Pico al controlador Renogy Rover Li:

1. Conecta la Raspberry Pi Pico a un conversor TTL a RS232:
   ```
   Raspberry Pi Pico | Conversor TTL a RS232
   ------------------------------------
   TX (GPIO0/Pin1)  | RX
   RX (GPIO1/Pin2)  | TX
   GND              | GND
   ```

2. Conecta el conversor RS232 al puerto RS232 del controlador Renogy Rover Li.

### Parámetros de Comunicación

- Velocidad de baudios: 9600
- Bits de datos: 8
- Paridad: Ninguna
- Bits de parada: 1
- Control de flujo: Ninguno

## Implementación del Protocolo Modbus

### Formato de Mensaje Modbus RTU

El formato de mensaje Modbus RTU para leer registros es:

```
[slave_id, function_code, reg_addr_hi, reg_addr_lo, reg_count_hi, reg_count_lo, crc_lo, crc_hi]
```

Donde:
- `slave_id`: El ID del dispositivo esclavo (predeterminado: 1 para Renogy Rover Li)
- `function_code`: El código de función Modbus (3 para leer registros de retención)
- `reg_addr_hi`, `reg_addr_lo`: Bytes alto y bajo de la dirección del registro
- `reg_count_hi`, `reg_count_lo`: Bytes alto y bajo del número de registros a leer
- `crc_lo`, `crc_hi`: Bytes bajo y alto de la suma de verificación CRC-16

### Formato de Respuesta Modbus RTU

El formato de respuesta para una lectura exitosa es:

```
[slave_id, function_code, byte_count, data..., crc_lo, crc_hi]
```

Donde:
- `slave_id`: El ID del dispositivo esclavo (igual que en la solicitud)
- `function_code`: El código de función Modbus (igual que en la solicitud)
- `byte_count`: El número de bytes de datos que siguen
- `data...`: Los bytes de datos (2 bytes por registro)
- `crc_lo`, `crc_hi`: Bytes bajo y alto de la suma de verificación CRC-16

### Formato de Respuesta de Error

Si ocurre un error, el formato de respuesta es:

```
[slave_id, function_code + 0x80, exception_code, crc_lo, crc_hi]
```

Donde:
- `slave_id`: El ID del dispositivo esclavo (igual que en la solicitud)
- `function_code + 0x80`: El código de función con el bit alto activado (indica un error)
- `exception_code`: El código de excepción Modbus
- `crc_lo`, `crc_hi`: Bytes bajo y alto de la suma de verificación CRC-16

### Cálculo CRC-16

La suma de verificación CRC-16 se calcula utilizando el siguiente algoritmo:

```python
def calculate_crc(data):
    crc = 0xFFFF
    
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    
    # Devolver CRC en formato little-endian (byte bajo primero)
    return bytes([crc & 0xFF, crc >> 8])
```

## Mapa de Registros Modbus

Las siguientes tablas listan todos los registros disponibles en el controlador Renogy Rover Li, organizados por categoría funcional.

### Información del Sistema

| Parámetro | Dirección de Registro | Bytes | Tipo de Datos | Descripción |
|-----------|----------------------|-------|---------------|-------------|
| Modelo | 0x0012 | 8 | string | Nombre del modelo del controlador |
| Voltaje del Sistema | 0x000A | 2 | float | Voltaje máximo soportado por el sistema (V) - Byte alto del primer registro |
| Corriente del Sistema | 0x000A | 2 | float | Corriente de carga nominal (A) - Byte bajo del primer registro |
| Versión de Hardware | 0x0014 | 4 | string | Versión de hardware en formato V{mayor}.{menor}.{parche} |
| Versión de Software | 0x0014 | 4 | string | Versión de software en formato V{mayor}.{menor}.{parche} |
| Número de Serie | 0x0018 | 4 | string | Número de serie del controlador |

### Información de la Batería

| Parámetro | Dirección de Registro | Bytes | Tipo de Datos | Descripción |
|-----------|----------------------|-------|---------------|-------------|
| Porcentaje de Batería | 0x0100 | 2 | float | Capacidad actual de la batería (0-100%) |
| Voltaje de la Batería | 0x0101 | 2 | float | Voltaje de la batería * 0.1 (V) |
| Temperatura de la Batería | 0x0103 | 2 | float | Temperatura de la batería (°C) - Byte bajo del registro, bit 7 es bit de signo |
| Tipo de Batería | 0xE004 | 2 | int | Tipo de batería (1=abierta, 2=sellada, 3=gel, 4=litio, 5=personalizada) |
| Capacidad Nominal de la Batería | 0xE002 | 2 | int | Capacidad nominal de la batería (Ah) |

### Información del Panel Solar

| Parámetro | Dirección de Registro | Bytes | Tipo de Datos | Descripción |
|-----------|----------------------|-------|---------------|-------------|
| Voltaje Solar | 0x0107 | 2 | float | Voltaje del panel solar * 0.1 (V) |
| Corriente Solar | 0x0108 | 2 | float | Corriente del panel solar * 0.01 (A) |
| Potencia Solar | 0x0109 | 2 | float | Potencia de carga solar (W) |

### Información de la Carga

| Parámetro | Dirección de Registro | Bytes | Tipo de Datos | Descripción |
|-----------|----------------------|-------|---------------|-------------|
| Voltaje de la Carga | 0x0104 | 2 | float | Voltaje de la carga * 0.1 (V) |
| Corriente de la Carga | 0x0105 | 2 | float | Corriente de la carga * 0.01 (A) |
| Potencia de la Carga | 0x0106 | 2 | float | Potencia de la carga (W) |

### Datos Históricos Diarios

| Parámetro | Dirección de Registro | Bytes | Tipo de Datos | Descripción |
|-----------|----------------------|-------|---------------|-------------|
| Voltaje Mínimo de Batería Hoy | 0x010B | 2 | float | Voltaje mínimo de la batería hoy * 0.1 (V) |
| Voltaje Máximo de Batería Hoy | 0x010C | 2 | float | Voltaje máximo de la batería hoy * 0.1 (V) |
| Corriente Máxima de Carga Hoy | 0x010D | 2 | float | Corriente máxima de carga hoy * 0.01 (A) |
| Corriente Máxima de Descarga Hoy | 0x010E | 2 | float | Corriente máxima de descarga hoy * 0.01 (A) |
| Potencia Máxima de Carga Hoy | 0x010F | 2 | int | Potencia máxima de carga hoy (W) |
| Potencia Máxima de Descarga Hoy | 0x0110 | 2 | int | Potencia máxima de descarga hoy (W) |
| Amperios-Hora de Carga Hoy | 0x0111 | 2 | int | Amperios-hora de carga hoy (Ah) |
| Amperios-Hora de Descarga Hoy | 0x0112 | 2 | int | Amperios-hora de descarga hoy (Ah) |
| Generación de Energía Hoy | 0x0113 | 2 | int | Generación de energía hoy (Wh) |
| Consumo de Energía Hoy | 0x0114 | 2 | int | Consumo de energía hoy (Wh) |

### Datos Históricos Acumulativos

| Parámetro | Dirección de Registro | Bytes | Tipo de Datos | Descripción |
|-----------|----------------------|-------|---------------|-------------|
| Total de Días en Funcionamiento | 0x0115 | 2 | int | Número total de días en funcionamiento |
| Total de Sobredescargas de Batería | 0x0116 | 2 | int | Número total de sobredescargas de la batería |
| Total de Cargas Completas de Batería | 0x0117 | 2 | int | Número total de cargas completas de la batería |
| Total de Amperios-Hora de Carga | 0x0118 | 4 | int | Total de amperios-hora de carga (Ah) |
| Total de Amperios-Hora de Descarga | 0x011A | 4 | int | Total de amperios-hora de descarga (Ah) |
| Generación de Energía Acumulativa | 0x011C | 4 | int | Generación de energía acumulativa (kWh/10000) |
| Consumo de Energía Acumulativo | 0x011E | 4 | int | Consumo de energía acumulativo (kWh/10000) |

### Información de Estado

| Parámetro | Dirección de Registro | Bytes | Tipo de Datos | Descripción |
|-----------|----------------------|-------|---------------|-------------|
| Temperatura del Controlador | 0x0103 | 2 | float | Temperatura del controlador (°C) - Byte alto del registro, bit 7 es bit de signo |
| Estado de Luz de Calle | 0x0120 | 2 | bool | Estado de la luz de calle (encendido/apagado) |
| Brillo de Luz de Calle | 0x0120 | 2 | int | Brillo de la luz de calle (0-100%) |
| Estado de Carga | 0x0120 | 2 | int | Estado de carga (0=desactivado, 1=activado, 2=mppt, 3=ecualización, 4=impulso, 5=flotación, 6=limitación de corriente) |

## Interpretación de Datos

### Lectura de Valores Enteros

Los valores enteros se devuelven directamente del registro. Por ejemplo, el número total de días en funcionamiento (registro 0x0115) se devuelve como un valor entero.

### Lectura de Valores de Punto Flotante

Algunos valores necesitan ser escalados para obtener el valor real:

- Valores de voltaje (marcados con * 0.1): Divide el valor del registro por 10
  ```python
  # Asumiendo que has leído el registro 0x0101 y obtuviste un valor de 261
  raw_value = 261  # Este es el valor crudo del registro
  battery_voltage = raw_value / 10  # = 26.1V
  ```

- Valores de corriente (marcados con * 0.01): Divide el valor del registro por 100
  ```python
  # Asumiendo que has leído el registro 0x0108 y obtuviste un valor de 125
  raw_value = 125  # Este es el valor crudo del registro
  solar_current = raw_value / 100  # = 1.25A
  ```

### Lectura de Valores de Temperatura

Los valores de temperatura tienen un formato especial donde el bit 7 es el bit de signo:

```python
# Para temperatura de la batería (registro 0x0103, byte bajo)
# Asumiendo que has leído el registro 0x0103 y obtuviste un valor de 0x2A19
raw_register = 0x2A19  # Este es el valor crudo del registro

# Extraer el byte bajo para la temperatura de la batería
battery_temp_bits = raw_register & 0x00FF  # = 0x19 = 25
temp_value = battery_temp_bits & 0x7F      # Remover bit de signo = 0x19 = 25
sign = (battery_temp_bits >> 7) & 1        # Extraer bit de signo = 0 (positivo)

if sign == 1:
    temperature = -(temp_value)  # Temperatura negativa
else:
    temperature = temp_value     # Temperatura positiva = 25°C
```

### Lectura de Valores de Cadena

Los valores de cadena (como números de versión) necesitan un manejo especial:

```python
# Para versión de software (registro 0x0014)
# Asumiendo que has leído los registros 0x0014-0x0015 y obtuviste valores [0x0301, 0x0200]
raw_registers = [0x0301, 0x0200]  # Estos son los valores crudos de los registros

major = raw_registers[0] & 0x00FF  # = 0x01 = 1
minor = raw_registers[1] >> 8      # = 0x02 = 2
patch = raw_registers[1] & 0x00FF  # = 0x00 = 0

version = f"V{major}.{minor}.{patch}"  # = "V1.2.0"
```

### Lectura de Valores de Múltiples Registros

Algunos valores abarcan múltiples registros (4 bytes). Para estos, necesitas combinar los registros:

```python
# Para total de amperios-hora de carga (registros 0x0118-0x0119)
# Asumiendo que has leído los registros 0x0118-0x0119 y obtuviste valores [0x0001, 0x86A0]
raw_registers = [0x0001, 0x86A0]  # Estos son los valores crudos de los registros

total_charging_ah = (raw_registers[0] << 16) + raw_registers[1]  # = 0x00010000 + 0x86A0 = 100000 Ah
```

## Ejemplos de Comandos y Respuestas

### Ejemplo 1: Lectura del Voltaje de la Batería

Para leer el voltaje de la batería (registro 0x0101):

**Comando:**
```
ID Esclavo: 0x01
Código de Función: 0x03
Dirección de Registro: 0x0101
Cantidad de Registros: 0x0001
CRC: Calculado basado en lo anterior
```

**Representación hexadecimal:**
```
01 03 01 01 00 01 [CRC_LO] [CRC_HI]
```

**Respuesta (ejemplo):**
```
ID Esclavo: 0x01
Código de Función: 0x03
Cantidad de Bytes: 0x02
Datos: 0x0105 (261 decimal)
CRC: Calculado basado en lo anterior
```

**Interpretación:**
```
Voltaje de la Batería = 0x0105 / 10 = 26.1V
```

### Ejemplo 2: Lectura de la Potencia Solar

Para leer la potencia solar (registro 0x0109):

**Comando:**
```
ID Esclavo: 0x01
Código de Función: 0x03
Dirección de Registro: 0x0109
Cantidad de Registros: 0x0001
CRC: Calculado basado en lo anterior
```

**Representación hexadecimal:**
```
01 03 01 09 00 01 [CRC_LO] [CRC_HI]
```

**Respuesta (ejemplo):**
```
ID Esclavo: 0x01
Código de Función: 0x03
Cantidad de Bytes: 0x02
Datos: 0x00C8 (200 decimal)
CRC: Calculado basado en lo anterior
```

**Interpretación:**
```
Potencia Solar = 200W
```

### Ejemplo 3: Lectura de la Temperatura del Controlador

Para leer la temperatura del controlador (registro 0x0103):

**Comando:**
```
ID Esclavo: 0x01
Código de Función: 0x03
Dirección de Registro: 0x0103
Cantidad de Registros: 0x0001
CRC: Calculado basado en lo anterior
```

**Representación hexadecimal:**
```
01 03 01 03 00 01 [CRC_LO] [CRC_HI]
```

**Respuesta (ejemplo):**
```
ID Esclavo: 0x01
Código de Función: 0x03
Cantidad de Bytes: 0x02
Datos: 0x2A19 (10777 decimal)
CRC: Calculado basado en lo anterior
```

**Interpretación:**
```
Temperatura del Controlador (byte alto): 0x2A = 42°C
Temperatura de la Batería (byte bajo): 0x19 = 25°C
```

### Ejemplo 4: Lectura de Múltiples Registros

Para leer voltaje y corriente del sistema (registro 0x000A):

**Comando:**
```
ID Esclavo: 0x01
Código de Función: 0x03
Dirección de Registro: 0x000A
Cantidad de Registros: 0x0001
CRC: Calculado basado en lo anterior
```

**Representación hexadecimal:**
```
01 03 00 0A 00 01 [CRC_LO] [CRC_HI]
```

**Respuesta (ejemplo):**
```
ID Esclavo: 0x01
Código de Función: 0x03
Cantidad de Bytes: 0x02
Datos: 0x1214 (4628 decimal)
CRC: Calculado basado en lo anterior
```

**Interpretación:**
```
Voltaje del Sistema (byte alto): 0x12 = 18V
Corriente del Sistema (byte bajo): 0x14 = 20A
```

---

Esta documentación proporciona una referencia completa para comunicarse con el controlador solar Renogy Rover Li utilizando el protocolo Modbus RTU sobre RS232. Incluye todas las direcciones de registros, tipos de datos y ejemplos necesarios para leer e interpretar datos del controlador.