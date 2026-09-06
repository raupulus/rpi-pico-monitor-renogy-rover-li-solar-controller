# Erratas y Desviaciones: Renogy Rover Li Modbus

Discrepancias comprobadas entre la documentación oficial de Renogy y las respuestas observadas en el hardware.

## 1. Registro de Farola / Carga Nocturna (`0x0120`)
- **Documentación de Renogy**: Especifica que el registro `0x0120` almacena el estado de encendido/apagado de la luz de calle (bits de carga) y el brillo porcentual (0–100%).
- **Comportamiento en Hardware Real**: El controlador físico suele responder con ceros constantes o lecturas erráticas en estos bits específicos, aun con carga conectada en modo noche.
- **Resolución en el Proyecto**: No confiar directamente en el registro `0x0120` para farola; el código del proyecto calcula una aproximación heurística basada en el voltaje de generación de los paneles solares.

## 2. Inconsistencia de Tiempos de Respuesta
- **Documentación de Renogy**: No especifica tiempo mínimo entre transmisiones consecutivas en el bus RS232.
- **Comportamiento en Hardware Real**: Si se envían peticiones consecutivas sin una pausa mínima de ~100 ms tras recibir una respuesta, el microcontrolador interno del Renogy descarta la siguiente trama o devuelve respuestas incompletas de longitud < 5 bytes.
- **Resolución en el Proyecto**: Incluir `time.sleep(0.1)` obligatorio entre transmisiones en el driver serie.

## 3. Formato del Número de Serie (`0x0018`)
- **Documentación de Renogy**: El número de serie se almacena en 4 registros contiguos.
- **Comportamiento en Hardware Real**: Dependiendo de la revisión de hardware, los bytes altos y bajos de cada palabra pueden venir invertidos o con caracteres no imprimibles al final. Se requiere sanitización para su uso en identificadores de Home Assistant.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
