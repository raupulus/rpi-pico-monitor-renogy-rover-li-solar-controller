# Mapa Oficial de Registros Modbus — Renogy Rover Li

Referencia de direcciones de registros de retención (`Function 0x03`) verificadas contra el hardware.

## 1. Información del Sistema y Hardware

| Dirección (Hex) | Longitud (Palabras) | Tipo | Descripción y Escalado |
|---|---|---|---|
| `0x000A` | 1 | 2x Byte | Byte Alto: Tensión máxima del sistema ($V$). Byte Bajo: Corriente nominal ($A$). |
| `0x0012` | 4 | String | Nombre del modelo del controlador. |
| `0x0014` | 2 | String | Versión de software (`V{mayor}.{menor}.{parche}`). |
| `0x0016` | 2 | String | Versión de hardware. |
| `0x0018` | 4 | String | Número de serie del controlador. |

## 2. Estado de Batería y Parámetros en Tiempo Real

| Dirección (Hex) | Longitud (Palabras) | Tipo | Descripción y Escalado |
|---|---|---|---|
| `0x0100` | 1 | uint16 | Porcentaje de carga de batería (SOC, $0 - 100\%$). |
| `0x0101` | 1 | uint16 | Tensión de batería en voltios (escala $\times 0.1$, dividir por 10). |
| `0x0102` | 1 | uint16 | Corriente de carga de batería en amperios (escala $\times 0.01$). |
| `0x0103` | 1 | 2x Byte | Byte Alto: Temperatura controlador (°C). Byte Bajo: Temperatura batería (°C). Bit 7 indica signo negativo. |
| `0xE002` | 1 | uint16 | Capacidad nominal de la batería ($Ah$). |
| `0xE004` | 1 | uint16 | Tipo de batería: 1=Open, 2=Sealed, 3=Gel, 4=Lithium, 5=Custom. |

## 3. Paneles Solares (PV)

| Dirección (Hex) | Longitud (Palabras) | Tipo | Descripción y Escalado |
|---|---|---|---|
| `0x0107` | 1 | uint16 | Tensión de paneles fotovoltaicos (escala $\times 0.1$, dividir por 10). |
| `0x0108` | 1 | uint16 | Intensidad fotovoltaica (escala $\times 0.01$, dividir por 100). |
| `0x0109` | 1 | uint16 | Potencia solar instantánea en vatios ($W$). |

## 4. Salida de Consumo (Load)

| Dirección (Hex) | Longitud (Palabras) | Tipo | Descripción y Escalado |
|---|---|---|---|
| `0x0104` | 1 | uint16 | Tensión de salida de carga (escala $\times 0.1$, dividir por 10). |
| `0x0105` | 1 | uint16 | Intensidad de salida de carga (escala $\times 0.01$, dividir por 100). |
| `0x0106` | 1 | uint16 | Potencia de consumo de carga en vatios ($W$). |
| `0x010A` | 1 | uint16 | Estado del interruptor de carga DC (bit 0: 0 = OFF, 1 = ON). |

## 5. Estadísticas del Día en Curso

| Dirección (Hex) | Longitud (Palabras) | Tipo | Descripción y Escalado |
|---|---|---|---|
| `0x010B` | 1 | uint16 | Tensión mínima de batería registrada hoy (escala $\times 0.1$). |
| `0x010C` | 1 | uint16 | Tensión máxima de batería registrada hoy (escala $\times 0.1$). |
| `0x010D` | 1 | uint16 | Intensidad máxima de carga hoy (escala $\times 0.01$). |
| `0x010E` | 1 | uint16 | Intensidad máxima de descarga hoy (escala $\times 0.01$). |
| `0x010F` | 1 | uint16 | Potencia máxima de carga hoy ($W$). |
| `0x0110` | 1 | uint16 | Potencia máxima de descarga hoy ($W$). |
| `0x0111` | 1 | uint16 | Amperios-hora cargados hoy ($Ah$). |
| `0x0112` | 1 | uint16 | Amperios-hora descargados hoy ($Ah$). |
| `0x0113` | 1 | uint16 | Energía fotovoltaica generada hoy en vatios-hora ($Wh$). |
| `0x0114` | 1 | uint16 | Energía consumida por la carga hoy en vatios-hora ($Wh$). |

## 6. Históricos Acumulativos

| Dirección (Hex) | Longitud (Palabras) | Tipo | Descripción y Escalado |
|---|---|---|---|
| `0x0115` | 1 | uint16 | Días totales en funcionamiento. |
| `0x0116` | 1 | uint16 | Número total de sobredescargas de la batería. |
| `0x0117` | 1 | uint16 | Número total de cargas completas de la batería. |
| `0x0118` | 2 | uint32 | Amperios-hora totales cargados ($Ah$, 32 bits en 2 registros). |
| `0x011A` | 2 | uint32 | Amperios-hora totales descargados ($Ah$, 32 bits en 2 registros). |
| `0x011C` | 2 | uint32 | Energía acumulada generada (valor crudo / 10000 = $kWh$). |
| `0x011E` | 2 | uint32 | Energía acumulada consumida (valor crudo / 10000 = $kWh$). |

## 7. Estados de Operación y Alarmas

| Dirección (Hex) | Longitud (Palabras) | Tipo | Descripción y Escalado |
|---|---|---|---|
| `0x0120` | 1 | uint16 | Byte bajo bits 0–7: Estado de carga (0=Desactivado, 1=Activado, 2=MPPT, 3=Ecualización, 4=Boost, 5=Flotación, 6=Limitación de corriente). |
| `0x0121` | 1 | uint16 | Registro de fallos y alarmas (16 bits). Ver tabla inferior. |

### Decodificación de Fallos (`0x0121`)
| Bit | Identificador | Significado |
|---|---|---|
| `0` | `battery_over_discharge` | Sobredescarga de batería |
| `1` | `battery_over_voltage` | Sobretensión en batería |
| `2` | `battery_under_voltage` | Tensión baja de batería |
| `3` | `load_short_circuit` | Cortocircuito en salida de carga |
| `4` | `load_over_current` | Sobrecorriente en salida de carga |
| `5` | `controller_over_temperature` | Sobretemperatura en el controlador |
| `6` | `battery_over_temperature` | Sobretemperatura en la batería |
| `7` | `solar_input_over_power` | Exceso de potencia de entrada solar |
| `8` | `solar_input_short_circuit` | Cortocircuito en entrada solar |
| `9` | `solar_input_over_voltage` | Sobretensión en entrada solar |
| `10` | `solar_counter_current` | Corriente inversa hacia paneles |
| `11` | `solar_input_reversed_polarity` | Polaridad invertida en paneles solares |
| `12` | `battery_reversed_polarity` | Polaridad invertida en bornes de batería |
| `13` | `battery_open_circuit` | Circuito de batería abierto |
| `14` | `load_open_circuit` | Circuito de carga abierto |

---
> Raúl Caro Pastorino · <public@raupulus.dev> · [raupulus.dev](https://raupulus.dev)
