# Renogy Rover Li — Especificación Oficial Modbus RTU

Documentación técnica de terceros destilada y verificada para el protocolo Modbus RTU del controlador solar Renogy Rover Li.

## Cabecera de Verificación
- **Fuente oficial original**: Manual de especificación de protocolo serie Renogy Rover Li (puerto RS232 RJ12).
- **Documento fuente preservado en el repositorio**: [`src/MODBUS_PROTOCOL.md`](src/MODBUS_PROTOCOL.md)
- **Fecha de obtención / documentación de fuentes**: 2022-08-01
- **Fecha de última verificación contra hardware real**: 2026-09-06

## Estructura de esta documentación
- [`00-fundamentos.md`](00-fundamentos.md): Parámetros de capa física RS232, estructura de trama Modbus RTU y algoritmo CRC-16.
- [`ERRATAS.md`](ERRATAS.md): Discrepancias verificadas entre el manual de Renogy y el comportamiento del hardware físico.
- [`LIMITACIONES.md`](LIMITACIONES.md): Límites de tasa de refresco, tiempos de respuesta y concurrencia en el bus.
- [`registros.md`](registros.md): Mapa completo de registros holding Modbus organizados por dominio funcional.
- `src/`: Directorio que contiene las especificaciones originales sin alterar (sólo lectura de referencia).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
