# Propuestas y Mejoras Futuras (Aplazadas)

Registro de funcionalidades y mejoras de arquitectura decididas pero postergadas para versiones posteriores. No constituye deuda técnica ni errores pendientes.

## 1. Soporte Nativo de Home Assistant MQTT Discovery
- **Propuesta**: Integrar cliente MQTT ligero para MicroPython (`umqtt.simple` / `umqtt.robust`) y publicar mensajes de configuración automática de entidades (*MQTT Discovery*).
- **Motivo del aplazamiento**: La integración HTTP REST directa con `/api/states/` funciona de manera estable, no requiere un broker MQTT intermedio y reduce el consumo de memoria en la Pico W.

## 2. Control Bidireccional de Parámetros de Carga y Salida DC
- **Propuesta**: Permitir encender/apagar la salida de carga (Load / Street Light) o ajustar tipos de batería enviando comandos Modbus de escritura (función `0x06` o `0x10`) recibidos vía webhooks o suscripción.
- **Motivo del aplazamiento**: El caso de uso actual es estrictamente de telemetría y monitorización pasiva no invasiva. La escritura en registros del controlador requiere mecanismos de seguridad adicionales para evitar configuraciones erróneas de voltaje en bancos de baterías.

## 3. Modo de Ultrabajo Consumo con Despertar por RTC Externo
- **Propuesta**: Implementar `machine.deepsleep()` junto con un módulo RTC de precisión (ej. DS3231) para apagar por completo la Pico W entre lecturas si se opera con baterías solares pequeñas.
- **Motivo del aplazamiento**: En la instalación actual, el consumo propio de la Pico W (~20-40 mA) es insignificante comparado con la generación solar y la capacidad de la batería del sistema.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
