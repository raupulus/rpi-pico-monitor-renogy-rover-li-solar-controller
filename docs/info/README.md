# Índice Maestro de Documentación Técnica Viva (`docs/info/`)

Documentación técnica viva del proyecto **Raspberry Pi Pico Monitor Renogy Rover Li Solar Controller**.

## 1. Módulos del Sistema

Cada archivo describe detalladamente qué hace, qué no hace, su modelo de datos, flujos, puntos de entrada y trampas conocidas:

- [`main`](main.md): Orquestador del ciclo de vida, bucle infinito, sincronización horaria y gestión de energía.
- [`RenogyRoverLi`](RenogyRoverLi.md): Decodificación de registros Modbus, factores de escala y caché de datos estáticos.
- [`SerialConnection`](SerialConnection.md): Driver serie UART0 de MicroPython y cálculo de tramas CRC-16 Modbus RTU.
- [`RpiPico`](RpiPico.md): Abstracción de hardware, WiFi STA (con AP alternativos), ADC (temperatura CPU y batería) y LEDs.
- [`Api`](Api.md): Cliente HTTP REST para subida hacia servicio backend externo con retroceso exponencial.
- [`HomeAssistantConnection`](HomeAssistantConnection.md): Integración con API REST de Home Assistant y agrupación bajo dispositivo único.
- [`_MODULE_TEMPLATE.md`](_MODULE_TEMPLATE.md): Plantilla oficial requerida para documentar cualquier nuevo módulo.

## 2. Arquitectura, Hardware y Diseño

- [`DESIGN.md`](DESIGN.md): Arquitectura general, flujo de datos entre capas y esquema de la caja/enclosure 3D.
- [`COMPONENTS.md`](COMPONENTS.md): Inventario de componentes físicos, especificaciones eléctricas y pines.
- [`hardware-connections.md`](hardware-connections.md): Guía de conexionado físico paso a paso (Pico ↔ MAX3232 ↔ Renogy RJ12 ↔ Sensores y LEDs).

## 3. Integración de APIs

- [`apis/renogy-modbus.md`](apis/renogy-modbus.md): Cómo consumimos nosotros la interfaz Modbus del controlador solar.
- [`apis/home-assistant.md`](apis/home-assistant.md): Cómo interactuamos con la REST API de Home Assistant.
- [`apis/custom-solar-api.md`](apis/custom-solar-api.md): Contrato del payload para la API externa de telemetría propia.

## 4. Operativa y Decisiones

- [`commands.md`](commands.md): Comandos de desarrollo local, herramientas de carga a la placa (`mpremote`) y ejecución de pruebas.
- [`decisiones-tecnicas.md`](decisiones-tecnicas.md): Registro de decisiones deliberadas de diseño para prevenir regresiones.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
