# Modbus Protocol Documentation for Renogy Rover Li Solar Controller

This document provides detailed information about the Modbus protocol implementation for communicating with the Renogy Rover Li solar controller via RS232. It includes register addresses, data types, and examples of how to read and interpret data from the controller.

## Table of Contents

1. [Introduction](#introduction)
2. [RS232 Connection Details](#rs232-connection-details)
3. [Modbus Protocol Implementation](#modbus-protocol-implementation)
4. [Modbus Register Map](#modbus-register-map)
   - [System Information](#system-information)
   - [Battery Information](#battery-information)
   - [Solar Panel Information](#solar-panel-information)
   - [Load Information](#load-information)
   - [Daily Historical Data](#daily-historical-data)
   - [Cumulative Historical Data](#cumulative-historical-data)
   - [Status Information](#status-information)
   - [Configuration Parameters](#configuration-parameters)
5. [Data Interpretation](#data-interpretation)
6. [Example Commands and Responses](#example-commands-and-responses)

## Introduction

The Renogy Rover Li solar controller uses the Modbus RTU protocol over RS232 for communication. This protocol allows reading various parameters from the controller, such as battery voltage, solar panel power, load current, and historical data.

The implementation in this project uses a Raspberry Pi Pico with MicroPython to communicate with the controller through a TTL to RS232 converter.

## RS232 Connection Details

### Hardware Connection

To connect the Raspberry Pi Pico to the Renogy Rover Li controller:

1. Connect the Raspberry Pi Pico to a TTL to RS232 converter:
   ```
   Raspberry Pi Pico | TTL to RS232 Converter
   ---------------------------------
   TX (GPIO0/Pin1)  | RX
   RX (GPIO1/Pin2)  | TX
   GND              | GND
   ```

2. Connect the RS232 converter to the Renogy Rover Li controller's RS232 port.

### Communication Parameters

- Baud rate: 9600
- Data bits: 8
- Parity: None
- Stop bits: 1
- Flow control: None

## Modbus Protocol Implementation

### Modbus RTU Message Format

The Modbus RTU message format for reading registers is:

```
[slave_id, function_code, reg_addr_hi, reg_addr_lo, reg_count_hi, reg_count_lo, crc_lo, crc_hi]
```

Where:
- `slave_id`: The ID of the slave device (default: 1 for Renogy Rover Li)
- `function_code`: The Modbus function code (3 for reading holding registers)
- `reg_addr_hi`, `reg_addr_lo`: High and low bytes of the register address
- `reg_count_hi`, `reg_count_lo`: High and low bytes of the number of registers to read
- `crc_lo`, `crc_hi`: Low and high bytes of the CRC-16 checksum

### Modbus RTU Response Format

The response format for a successful read is:

```
[slave_id, function_code, byte_count, data..., crc_lo, crc_hi]
```

Where:
- `slave_id`: The ID of the slave device (same as in the request)
- `function_code`: The Modbus function code (same as in the request)
- `byte_count`: The number of data bytes that follow
- `data...`: The data bytes (2 bytes per register)
- `crc_lo`, `crc_hi`: Low and high bytes of the CRC-16 checksum

### Error Response Format

If an error occurs, the response format is:

```
[slave_id, function_code + 0x80, exception_code, crc_lo, crc_hi]
```

Where:
- `slave_id`: The ID of the slave device (same as in the request)
- `function_code + 0x80`: The function code with the high bit set (indicates an error)
- `exception_code`: The Modbus exception code
- `crc_lo`, `crc_hi`: Low and high bytes of the CRC-16 checksum

### CRC-16 Calculation

The CRC-16 checksum is calculated using the following algorithm:

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
    
    # Return CRC in little-endian format (low byte first)
    return bytes([crc & 0xFF, crc >> 8])
```

## Modbus Register Map

The following tables list all the registers available in the Renogy Rover Li controller, organized by functional category.

### System Information

| Parameter | Register Address | Bytes | Data Type | Description |
|-----------|-----------------|-------|-----------|-------------|
| Model | 0x0012 | 8 | string | Model name of the controller |
| System Voltage | 0x000A | 2 | float | Maximum voltage supported by the system (V) - High byte of first register |
| System Current | 0x000A | 2 | float | Rated charging current (A) - Low byte of first register |
| Hardware Version | 0x0014 | 4 | string | Hardware version in format V{major}.{minor}.{patch} |
| Software Version | 0x0014 | 4 | string | Software version in format V{major}.{minor}.{patch} |
| Serial Number | 0x0018 | 4 | string | Serial number of the controller |

### Battery Information

| Parameter | Register Address | Bytes | Data Type | Description |
|-----------|-----------------|-------|-----------|-------------|
| Battery Percentage | 0x0100 | 2 | float | Current battery capacity (0-100%) |
| Battery Voltage | 0x0101 | 2 | float | Battery voltage * 0.1 (V) |
| Battery Temperature | 0x0103 | 2 | float | Battery temperature (°C) - Low byte of register, bit 7 is sign bit |
| Battery Type | 0xE004 | 2 | int | Battery type (1=open, 2=sealed, 3=gel, 4=lithium, 5=self-customized) |
| Nominal Battery Capacity | 0xE002 | 2 | int | Nominal battery capacity (Ah) |

### Solar Panel Information

| Parameter | Register Address | Bytes | Data Type | Description |
|-----------|-----------------|-------|-----------|-------------|
| Solar Voltage | 0x0107 | 2 | float | Solar panel voltage * 0.1 (V) |
| Solar Current | 0x0108 | 2 | float | Solar panel current * 0.01 (A) |
| Solar Power | 0x0109 | 2 | float | Solar charging power (W) |

### Load Information

| Parameter | Register Address | Bytes | Data Type | Description |
|-----------|-----------------|-------|-----------|-------------|
| Load Voltage | 0x0104 | 2 | float | Load voltage * 0.1 (V) |
| Load Current | 0x0105 | 2 | float | Load current * 0.01 (A) |
| Load Power | 0x0106 | 2 | float | Load power (W) |

### Daily Historical Data

| Parameter | Register Address | Bytes | Data Type | Description |
|-----------|-----------------|-------|-----------|-------------|
| Battery Min Voltage Today | 0x010B | 2 | float | Minimum battery voltage today * 0.1 (V) |
| Battery Max Voltage Today | 0x010C | 2 | float | Maximum battery voltage today * 0.1 (V) |
| Max Charging Current Today | 0x010D | 2 | float | Maximum charging current today * 0.01 (A) |
| Max Discharging Current Today | 0x010E | 2 | float | Maximum discharging current today * 0.01 (A) |
| Max Charging Power Today | 0x010F | 2 | int | Maximum charging power today (W) |
| Max Discharging Power Today | 0x0110 | 2 | int | Maximum discharging power today (W) |
| Charging Amp Hours Today | 0x0111 | 2 | int | Charging amp-hours today (Ah) |
| Discharging Amp Hours Today | 0x0112 | 2 | int | Discharging amp-hours today (Ah) |
| Power Generation Today | 0x0113 | 2 | int | Power generation today (Wh) |
| Power Consumption Today | 0x0114 | 2 | int | Power consumption today (Wh) |

### Cumulative Historical Data

| Parameter | Register Address | Bytes | Data Type | Description |
|-----------|-----------------|-------|-----------|-------------|
| Total Days Operating | 0x0115 | 2 | int | Total number of operating days |
| Total Battery Over-Discharges | 0x0116 | 2 | int | Total number of battery over-discharges |
| Total Battery Full Charges | 0x0117 | 2 | int | Total number of battery full charges |
| Total Charging Amp Hours | 0x0118 | 4 | int | Total charging amp-hours (Ah) |
| Total Discharging Amp Hours | 0x011A | 4 | int | Total discharging amp-hours (Ah) |
| Cumulative Power Generation | 0x011C | 4 | int | Cumulative power generation (kWh/10000) |
| Cumulative Power Consumption | 0x011E | 4 | int | Cumulative power consumption (kWh/10000) |

### Status Information

| Parameter | Register Address | Bytes | Data Type | Description |
|-----------|-----------------|-------|-----------|-------------|
| Controller Temperature | 0x0103 | 2 | float | Controller temperature (°C) - High byte of register, bit 7 is sign bit |
| Street Light Status | 0x0120 | 2 | bool | Street light status (on/off) |
| Street Light Brightness | 0x0120 | 2 | int | Street light brightness (0-100%) |
| Charging Status | 0x0120 | 2 | int | Charging status (0=deactivated, 1=activated, 2=mppt, 3=equalizing, 4=boost, 5=floating, 6=current limiting) |

## Data Interpretation

### Reading Integer Values

Integer values are returned directly from the register. For example, the total number of operating days (register 0x0115) is returned as an integer value.

### Reading Float Values

Some values need to be scaled to get the actual value:

- Voltage values (marked with * 0.1): Divide the register value by 10
  ```python
  # Assuming you've read register 0x0101 and got a value of 261
  raw_value = 261  # This is the raw value from the register
  battery_voltage = raw_value / 10  # = 26.1V
  ```

- Current values (marked with * 0.01): Divide the register value by 100
  ```python
  # Assuming you've read register 0x0108 and got a value of 125
  raw_value = 125  # This is the raw value from the register
  solar_current = raw_value / 100  # = 1.25A
  ```

### Reading Temperature Values

Temperature values have a special format where bit 7 is the sign bit:

```python
# For battery temperature (register 0x0103, low byte)
# Assuming you've read register 0x0103 and got a value of 0x2A19
raw_register = 0x2A19  # This is the raw value from the register

# Extract the low byte for battery temperature
battery_temp_bits = raw_register & 0x00FF  # = 0x19 = 25
temp_value = battery_temp_bits & 0x7F      # Remove sign bit = 0x19 = 25
sign = (battery_temp_bits >> 7) & 1        # Extract sign bit = 0 (positive)

if sign == 1:
    temperature = -(temp_value)  # Negative temperature
else:
    temperature = temp_value     # Positive temperature = 25°C
```

### Reading String Values

String values (like version numbers) need special handling:

```python
# For software version (register 0x0014)
# Assuming you've read registers 0x0014-0x0015 and got values [0x0301, 0x0200]
raw_registers = [0x0301, 0x0200]  # These are the raw values from the registers

major = raw_registers[0] & 0x00FF  # = 0x01 = 1
minor = raw_registers[1] >> 8      # = 0x02 = 2
patch = raw_registers[1] & 0x00FF  # = 0x00 = 0

version = f"V{major}.{minor}.{patch}"  # = "V1.2.0"
```

### Reading Multi-Register Values

Some values span multiple registers (4 bytes). For these, you need to combine the registers:

```python
# For total charging amp-hours (registers 0x0118-0x0119)
# Assuming you've read registers 0x0118-0x0119 and got values [0x0001, 0x86A0]
raw_registers = [0x0001, 0x86A0]  # These are the raw values from the registers

total_charging_ah = (raw_registers[0] << 16) + raw_registers[1]  # = 0x00010000 + 0x86A0 = 100000 Ah
```

## Example Commands and Responses

### Example 1: Reading Battery Voltage

To read the battery voltage (register 0x0101):

**Command:**
```
Slave ID: 0x01
Function Code: 0x03
Register Address: 0x0101
Register Count: 0x0001
CRC: Calculated based on the above
```

**Hex representation:**
```
01 03 01 01 00 01 [CRC_LO] [CRC_HI]
```

**Response (example):**
```
Slave ID: 0x01
Function Code: 0x03
Byte Count: 0x02
Data: 0x0105 (261 decimal)
CRC: Calculated based on the above
```

**Interpretation:**
```
Battery Voltage = 0x0105 / 10 = 26.1V
```

### Example 2: Reading Solar Power

To read the solar power (register 0x0109):

**Command:**
```
Slave ID: 0x01
Function Code: 0x03
Register Address: 0x0109
Register Count: 0x0001
CRC: Calculated based on the above
```

**Hex representation:**
```
01 03 01 09 00 01 [CRC_LO] [CRC_HI]
```

**Response (example):**
```
Slave ID: 0x01
Function Code: 0x03
Byte Count: 0x02
Data: 0x00C8 (200 decimal)
CRC: Calculated based on the above
```

**Interpretation:**
```
Solar Power = 200W
```

### Example 3: Reading Controller Temperature

To read the controller temperature (register 0x0103):

**Command:**
```
Slave ID: 0x01
Function Code: 0x03
Register Address: 0x0103
Register Count: 0x0001
CRC: Calculated based on the above
```

**Hex representation:**
```
01 03 01 03 00 01 [CRC_LO] [CRC_HI]
```

**Response (example):**
```
Slave ID: 0x01
Function Code: 0x03
Byte Count: 0x02
Data: 0x2A19 (10777 decimal)
CRC: Calculated based on the above
```

**Interpretation:**
```
Controller Temperature (high byte): 0x2A = 42°C
Battery Temperature (low byte): 0x19 = 25°C
```

### Example 4: Reading Multiple Registers

To read system voltage and current (register 0x000A):

**Command:**
```
Slave ID: 0x01
Function Code: 0x03
Register Address: 0x000A
Register Count: 0x0001
CRC: Calculated based on the above
```

**Hex representation:**
```
01 03 00 0A 00 01 [CRC_LO] [CRC_HI]
```

**Response (example):**
```
Slave ID: 0x01
Function Code: 0x03
Byte Count: 0x02
Data: 0x1214 (4628 decimal)
CRC: Calculated based on the above
```

**Interpretation:**
```
System Voltage (high byte): 0x12 = 18V
System Current (low byte): 0x14 = 20A
```

---

This documentation provides a comprehensive reference for communicating with the Renogy Rover Li solar controller using the Modbus RTU protocol over RS232. It includes all the register addresses, data types, and examples needed to read and interpret data from the controller.