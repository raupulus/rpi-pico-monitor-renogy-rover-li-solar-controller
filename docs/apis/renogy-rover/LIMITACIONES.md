# Limitaciones: Protocolo Renogy Rover Li Modbus

Límites operativos y restricciones técnicas de la interfaz serie del controlador solar.

## 1. Velocidad de Bus Fija (9600 bps)
- El puerto serie del Renogy Rover Li opera exclusivamente a 9600 baudios.
- A esta velocidad, la transmisión de una trama de 8 bytes y recepción de ~10 bytes toma aproximadamente 20 ms sólo en tiempo de línea.
- Con pausas de seguridad de 100 ms entre registros, un ciclo completo de lectura de todos los registros insume entre 1 y 2 segundos. No es adecuado para muestreos de alta frecuencia (< 5 segundos).

## 2. Bus Monomaestro y Sin Concurrencia
- El puerto RS232 del controlador solar es estrictamente punto a punto.
- Si se conecta otro dispositivo (como el módulo Bluetooth oficial de Renogy BT-1/BT-2 o pantalla remota) al mismo puerto RJ12 mediante un bifurcador Y, se producirán colisiones de tramas y corrupción de datos irreversible.

## 3. Caché de Registros Estáticos
- Los registros de información de dispositivo (`0x000A` a `0x001B`, `0xE002`, `0xE004`) no cambian en operación normal. Consultarlos continuamente en cada ciclo desperdicia ancho de banda y ciclos de CPU.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
