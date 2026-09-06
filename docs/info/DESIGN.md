# Diseño del Sistema y Arquitectura

Documento de diseño técnico general de la solución de monitorización del controlador solar Renogy Rover Li.

## 1. Arquitectura General del Sistema

El sistema actúa como puente de telemetría IoT entre el puerto serie RS232 de un controlador solar MPPT Renogy Rover Li y redes IP (Home Assistant y API REST externa).

```mermaid
flowchart LR
    subgraph Solar["Instalación Solar"]
        SP[Paneles Solares] --> RR[Renogy Rover Li]
        BAT[Batería 12V/24V] <--> RR
        LOAD[Salida Carga DC] <-- RR
    end

    subgraph Hardware["Módulo Monitor (Carcasa 3D)"]
        MAX[Conversor TTL a RS232] <-->|RJ12 RS232| RR
        PICO[Raspberry Pi Pico W] <-->|UART0 GPIO0/1| MAX
        EXT_BAT[Batería Externa Opcional] -->|Divisor Resistivo| ADC[GPIO26 ADC0]
        LEDS[LEDs de Estado: Power/Upload/Cycle] <-- PICO
    end

    subgraph CloudLocal["Red y Visualización"]
        WIFI((Red WiFi))
        PICO -->|WiFi 2.4GHz| WIFI
        WIFI -->|HTTP REST| HA[Home Assistant]
        WIFI -->|HTTP REST| API[API Solar Externa]
    end
```

## 2. Flujo de Datos y Operación

El bucle de ejecución opera de forma secuencial y determinista en [`src/main.py`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/main.py):

1. **Inicialización**:
   - Inicialización del microcontrolador [`RpiPico`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RpiPico.py) y conexión WiFi STA (con conmutación a AP alternativo en caso de pérdida).
   - Encendido del LED de Power (GPIO15).
   - Sincronización horaria vía NTP (`ntptime`).
   - Inicialización de [`SerialConnection`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/SerialConnection.py) a 9600 bps sobre UART0.
   - Instanciación de [`RenogyRoverLi`](file:///Users/fryntiz/git/rpi-pico-monitor-renogy-rover-li-solar-controller/src/Models/RenogyRoverLi.py) con carga y cacheo de registros estáticos.
2. **Ciclo de Telemetría**:
   - Activación de LED de Ciclo (GPIO13).
   - Consulta Modbus RTU de registros dinámicos del controlador solar (batería, paneles, carga, estadísticas del día, contadores acumulados).
   - Lectura de telemetría del propio microcontrolador (temperatura de CPU vía ADC4, intensidad de señal WiFi RSSI, tensión de batería externa vía ADC0 si está habilitada).
   - Apagado del LED de Ciclo.
3. **Publicación y Subida**:
   - Activación de LED de Subida (GPIO14).
   - Envío a API REST externa (si `UPLOAD_API = True`).
   - Envío a Home Assistant REST API (si `UPLOAD_HOME_ASSISTANT = True`), actualizando la entidad de dispositivo y todas las entidades de sensor hijas.
   - Apagado del LED de Subida.
4. **Mantenimiento y Espera**:
   - Parpadeo de confirmación en LED integrado.
   - Recolección explícita de basura con `gc.collect()`.
   - Espera inactiva configurable mediante `SLEEP_TIME` (predeterminado 60s).

## 3. Indicadores de Estado Visuales

El diseño incluye 4 señales luminosas para diagnóstico sin necesidad de consola serie:

| Indicador | Pin | Comportamiento Normal | Comportamiento en Fallo |
|---|---|---|---|
| **LED Power** | GPIO15 | Encendido fijo mientras el dispositivo tiene alimentación | Apagado si no hay alimentación o fallo crítico de inicialización |
| **LED Upload** | GPIO14 | Se enciende durante la subida HTTP a APIs y se apaga al terminar | Permanece apagado si la subida está desactivada o falla |
| **LED Cycle** | GPIO13 | Se enciende durante la lectura de registros serie y se apaga al finalizar | Se apaga si falla la lectura |
| **LED Integrado** | Onboard Pin | 1 destello corto al completar un ciclo exitoso | 5 parpadeos rápidos ante excepciones o fallos en el ciclo |

## 4. Diseño Mecánico y Carcasa 3D

Los archivos de diseño mecánico se encuentran en el directorio `3d Design/`:
- Diseñado para alojar una Raspberry Pi Pico W, el módulo conversor TTL a RS232 (MAX3232) y conexiones cableadas.
- Conectores accesibles para alimentación USB / entrada de terminales y conector RJ12 hacia el controlador solar.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
