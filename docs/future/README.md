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

## 4. Agrupación en Entidad Maestra con Atributos en Home Assistant (Opción 1)
- **Propuesta**: Enviar toda la telemetría del controlador y del microcontrolador (~35 métricas) en **una única petición HTTP POST** a una sola entidad coordinadora (ej. `sensor.renogy_rover_solar_controller`), alojando todas las mediciones de voltaje, corriente, potencia, históricos y diagnósticos dentro del diccionario `attributes`.
- **Ventaja evaluada**: Reduce el número de conexiones HTTP de ~35 a exactamente 1 por ciclo, minimizando la latencia y el consumo de sockets en MicroPython.
- **Motivo del aplazamiento**: Esta solución rompería inmediatamente los dashboards, tarjetas Lovelace y widgets existentes en Home Assistant, dado que las entidades independientes (`sensor.solar_battery_voltage`, `sensor.solar_solar_power`, etc.) pasarían a estado `unavailable`. Requeriría reconfigurar manualmente cada tarjeta en la interfaz de Home Assistant o definir decenas de *Template Sensors* en `configuration.yaml` para volver a extraer cada atributo como entidad individual.
- **Alternativa adoptada provisionalmente**: Vía A (Filtrado por delta / variación y refresco por latido), la cual reduce un 75%–90% las peticiones manteniendo intactos todos los widgets y entidades nativas sin tocar nada en Home Assistant.
- **Cuándo valorarla**: Se evaluará en una fase posterior cuando se decida rediseñar por completo el panel de control o centralizar la monitorización en Home Assistant con *Template Sensors*.

---
> Raúl Caro Pastorino · <public@raupulus.dev> · [raupulus.dev](https://raupulus.dev)
