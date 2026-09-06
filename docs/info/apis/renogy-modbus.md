# Integración con Interfaz Modbus de Renogy Rover Li

Documento explicativo de cómo este proyecto implementa la comunicación con el controlador Renogy Rover Li a través de su interfaz Modbus RTU sobre RS232.

Para la especificación técnica oficial y detallada del protocolo, consulta [Documentación Modbus de Terceros](../../apis/renogy-rover/README.md).

## 1. Arquitectura de Integración

La integración se divide en dos capas desacopladas:

1. **Capa de Transporte Serie y Trama ([`SerialConnection`](../SerialConnection.md))**:
   - Gestiona el puerto físico UART0 a 9600 baudios (8N1).
   - Ensambla las tramas de consulta con función `0x03` (Read Holding Registers) dirigidas al esclavo `0x01`.
   - Calcula y verifica el CRC-16 Modbus (polinomio `0xA001`, little-endian).
   - Reintenta hasta 5 veces con pausas de 100 ms ante falta de respuesta o error de paridad/longitud.

2. **Capa de Dominio y Decodificación ([`RenogyRoverLi`](../RenogyRoverLi.md))**:
   - Mapea las direcciones de memoria Modbus y extrae los campos correspondientes.
   - Aplica factores de conversión de escala:
     - Tensiones: valor crudo dividido entre 10 ($V$).
     - Intensidades: valor crudo dividido entre 100 ($A$).
     - Potencias: lectura entera directa en vatios ($W$).
     - Temperaturas: extracción de bits 0–6 con bit 7 como signo en el registro `0x0103`.
     - Contadores de energía acumulada: combinación de 2 palabras consecutivas de 16 bits en un entero de 32 bits dividido entre 10.000 ($kWh$).
   - Implementa caché en memoria para los registros estáticos (número de serie, versiones de firmware, capacidad y tipo de batería, límites del sistema) para no saturar el bus RS232 en cada ciclo.

## 2. Puntos Críticos y Desviaciones

- **Caché en arranque**: Si el controlador está apagado al iniciar la Pico, los registros estáticos quedarán vacíos hasta el siguiente reinicio del microcontrolador.
- **Luz de carga (Street Light)**: La lectura del registro `0x0120` para la luz de calle presentó inconsistencias en hardware real; el módulo [`RenogyRoverLi`](../RenogyRoverLi.md) calcula una aproximación heurística basada en la tensión fotovoltaica de los paneles.
- Consulta [ERRATAS de la API](../../apis/renogy-rover/ERRATAS.md) y [LIMITACIONES](../../apis/renogy-rover/LIMITACIONES.md) para más detalles.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
