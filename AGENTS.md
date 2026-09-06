# AGENTS.md — Raspberry Pi Pico Monitor Renogy Rover Li Solar Controller

Guía permanente para agentes de IA y desarrolladores que interactúen con este repositorio.

## 1. Contexto y Arquitectura del Proyecto

Este proyecto es un sistema de telemetría embebida para monitorizar un regulador solar MPPT **Renogy Rover Li** mediante una **Raspberry Pi Pico W** ejecutando **MicroPython 1.25+**.

- **Hardware**: Raspberry Pi Pico W (RP2040 + CYW43439), módulo conversor TTL a RS232 (MAX3232) conectado a UART0 (GPIO0/GPIO1), puerto RJ12 del controlador Renogy Rover Li, LEDs indicadores externos (GPIO13, 14, 15) y monitorización opcional de batería externa vía divisor resistivo en ADC0 (GPIO26).
- **Comunicaciones**: Modbus RTU sobre RS232 a 9600 baudios (8N1) implementado directamente en MicroPython (sin librerías pesadas como `pymodbus`).
- **Integraciones**: Publicación HTTP REST hacia [Home Assistant](docs/info/apis/home-assistant.md) (agrupado bajo un único dispositivo físico con `unique_id`) y hacia una [API Solar propia V2](docs/info/apis/custom-solar-api.md).
- **Atribución**: Nick `@raupulus` · Email `public@raupulus.dev`. Sin firmas de agente en commits, PRs ni documentación.

---

## 2. Estructura Real de Directorios

```
.
├── .agents/                               # Configuraciones y herramientas de agentes
├── .claude -> .agents                     # Enlace simbólico para interoperabilidad
├── CLAUDE.md -> AGENTS.md                 # Enlace simbólico de instrucciones de agente
├── AGENTS.md                              # Este documento (fuente de verdad para agentes)
├── LICENSE                                # Licencia GNU General Public License v3.0
├── README.md                              # Documentación general y cableado rápido
├── 3d Design/                             # Archivos STL para impresión 3D de la carcasa
│   ├── Bottom.stl
│   └── Top.stl
├── src/                                   # Código fuente que corre en la Raspberry Pi Pico
│   ├── .env.example.py                    # Plantilla de configuración de entorno
│   ├── main.py                            # Orquestador del ciclo de vida y bucle de telemetría
│   └── Models/
│       ├── Api.py                         # Cliente HTTP REST hacia API externa V2
│       ├── HomeAssistantConnection.py     # Integración REST y entidades para Home Assistant
│       ├── RenogyRoverLi.py               # Modelo del controlador, decodificación y caché
│       ├── RpiPico.py                     # Abstracción hardware Pico W (WiFi, ADC, LEDs)
│       └── SerialConnection.py            # Driver serie UART0 y cálculo CRC-16 Modbus RTU
├── tests/                                 # Scripts de prueba y verificación
│   ├── test_device_creation.py            # Test de creación de dispositivo en Home Assistant
│   └── verify_entity_grouping.py          # Verificador y reparador de agrupación de entidades
└── docs/
    ├── apis/
    │   └── renogy-rover/                  # Documentación oficial de terceros (destilada y verificada)
    │       ├── README.md
    │       ├── 00-fundamentos.md
    │       ├── ERRATAS.md
    │       ├── LIMITACIONES.md
    │       ├── registros.md
    │       └── src/
    │           └── MODBUS_PROTOCOL.md     # Fuente original sin alterar
    ├── deploys/
    │   ├── rpi-pico-setup.md              # Flasheo de MicroPython y despliegue con mpremote
    │   └── home-assistant-setup.md        # Configuración de paquetes YAML y Lovelace en HA
    ├── future/
    │   └── README.md                      # Propuestas acordadas pero aplazadas (ej. MQTT Discovery)
    ├── images/                            # Diagramas y capturas de interfaz
    └── info/                              # DOCUMENTACIÓN TÉCNICA VIVA DEL PROYECTO
        ├── README.md                      # Índice maestro de documentación viva
        ├── _MODULE_TEMPLATE.md            # Plantilla para documentar nuevos módulos
        ├── DESIGN.md                      # Arquitectura del sistema y flujo de datos
        ├── COMPONENTS.md                  # Inventario de hardware, especificaciones y pines
        ├── hardware-connections.md        # Guía de conexión física paso a paso
        ├── commands.md                    # Comandos de desarrollo, despliegue y pruebas
        ├── decisiones-tecnicas.md         # Registro de decisiones deliberadas de arquitectura
        ├── main.md                        # Documentación del módulo main
        ├── RenogyRoverLi.md               # Documentación del módulo RenogyRoverLi
        ├── SerialConnection.md            # Documentación del módulo SerialConnection
        ├── RpiPico.md                     # Documentación del módulo RpiPico
        ├── Api.md                         # Documentación del módulo Api
        ├── HomeAssistantConnection.md     # Documentación del módulo HomeAssistantConnection
        └── apis/
            ├── renogy-modbus.md           # Cómo integramos la interfaz Modbus
            ├── home-assistant.md          # Cómo integramos la API REST de Home Assistant
            └── custom-solar-api.md        # Contrato de datos con la API propia V2
```

---

## 3. Tabla de Trampas Técnicas y Gotchas

| Trampa / Particularidad | Impacto | Regla de Oro |
|---|---|---|
| **Falta de `str.title()` en MicroPython** | `AttributeError` en runtime | Usar la función auxiliar `_capitalize_words()` en `HomeAssistantConnection.py`. |
| **Desempaquetado `**` en diccionarios** | Error de sintaxis en MicroPython | No usar `{**a, **b}`. Usar siempre `dict.update()` explícito. |
| **`machine.light_sleep()` en Pico W** | Cuelgue del stack WiFi CYW43439 | Usar siempre `time.sleep()` estándar en bucles de reposo. |
| **Parámetro `bits` en `read_register`** | Confusión semántica | `bits` representa la **cantidad de registros de 16 bits** a solicitar, no bits individuales. |
| **Pausa post-trama Modbus (100 ms)** | Pérdida de tramas o timeouts | El Renogy necesita ~100 ms tras responder antes de admitir otra petición. |
| **LED integrado en Pico W** | Fallo al usar GPIO 25 | Instanciar con `machine.Pin("LED")`, no pin numérico directo. |
| **Caracteres acentuados / `°` en Home Assistant** | Error `Invalid JSON specified` | Pasar siempre las cadenas por `_sanitize_string()` antes de enviar a la API REST. |
| **Fuga de sockets en `urequests`** | `OSError: ENOMEM` tras horas | Invocar obligatoriamente `response.close()` en bloque `finally:` y `gc.collect()` tras cada petición HTTP. |
| **Bucles bloqueantes en WiFi y escaneo CYW43** | Microcontrolador congelado | Usar timeout acotado (`ensure_wifi_connected`), reciclar la interfaz (`active(False)` -> `active(True)`) y nunca hacer `scan()` continuo si la radio está en fallo. |
| **Pérdida prolongada de WiFi / Internet** | Cuelgue o acumulación de errores | Omitir llamadas de red si `not wifi_is_connected()` y reiniciar con `machine.reset()` si se superan `MAX_OFFLINE_CYCLES`. |
| **Ability de token en API V2** | Error HTTP 403 / 404 | Usar endpoint `/api/v2/energy/solar-readings` y token con ability `energy:write` (rutas V1 bajo `/hardware` eliminadas). |
| **Agrupación de entidades en HA** | Entidades dispersas huérfanas | El campo `identifiers` dentro de `device` debe ser idéntico en todas las entidades (`renogy_rover_li_<DEVICE_ID>`). |
| **Caché de registros estáticos** | Datos fijos no refrescados | Si se cambia la batería físicamente, reiniciar la Pico para recargar la caché de `RenogyRoverLi`. |

---

## 4. Protocolo Permanente de Documentación `docs/`

Este protocolo aplica de forma obligatoria en todas las tareas sobre este repositorio:

### Reglas Permanentes
1. **Documentar es parte de la tarea**: Ninguna tarea se considera terminada si su documentación técnica no se actualiza en el **mismo commit** que el código.
2. **Jerarquía de verdad**: `código` > `docs/info/` > `AGENTS.md` > el resto. `docs/planning/`, `docs/future/` y `docs/auditorias/` **nunca** son fuente de verdad de estado.
3. **Discrepancia entre documentación y código**: Se corrige en el commit en que se detecta, no se posterga.
4. **Ciclo de vida de módulos**:
   - Modificas un módulo → actualizas su `.md` en `docs/info/`.
   - Creas un módulo → lo generas a partir de [`_MODULE_TEMPLATE.md`](docs/info/_MODULE_TEMPLATE.md), lo indexas en [`docs/info/README.md`](docs/info/README.md) y en este archivo.
   - Eliminas un módulo → borras su `.md` y lo eliminas de todos los índices.
5. **Pie de archivo obligatorio**: Todo archivo bajo `docs/` (en cualquier subdirectorio) termina obligatoriamente con esta línea exacta tras un separador `---`:
   ```markdown
   ---
   > Creado: YYYY-MM-DD · Última revisión: YYYY-MM-DD
   ```
   La fecha de creación no se modifica nunca; la de revisión se actualiza en el mismo commit que el fichero.
6. **Planificaciones efímeras**: `docs/planning/` y `docs/auditorias/` están en `.gitignore`. Son exclusivas del desarrollador en curso. Tras cerrar la fase o auditoría, se promociona lo duradero hacia `docs/info/`, `AGENTS.md` o tests, y se **borra** el archivo efímero.
7. **Lectura dirigida**: Al trabajar en un módulo lee **únicamente** su `.md`. Si tocas una API externa, lee `docs/apis/<api>/README.md` → `00-fundamentos.md` + `ERRATAS.md` + `LIMITACIONES.md`. No leas ficheros irrelevantes.
8. **Idioma y convenciones**: Documentación, comentarios y textos en español. Identificadores, nombres de archivo y mensajes de log en inglés.
9. **Sin firmas de agente**: Prohibido añadir `Co-Authored-By`, «Generated with…» o identificadores de sesión en commits o documentación.

### Disparadores de Documentación
- Modificación de lógica, campos o contratos de un módulo → [`docs/info/<modulo>.md`](docs/info/).
- Cambio de integración o consumo de API externa → [`docs/info/apis/<api>.md`](docs/info/apis/).
- Cambio en hardware, pines o esquemas → [`docs/info/COMPONENTS.md`](docs/info/COMPONENTS.md) y [`docs/info/hardware-connections.md`](docs/info/hardware-connections.md).
- Nuevo comando, script o herramienta → [`docs/info/commands.md`](docs/info/commands.md).
- Decisión de diseño deliberada → [`docs/info/decisiones-tecnicas.md`](docs/info/decisiones-tecnicas.md).
- Adición de nuevo directorio en el repo → Actualizar árbol en este archivo (`AGENTS.md`).

---

## 5. Índice de Documentación Viva (`docs/info/`)

- [Índice Maestro (`docs/info/README.md`)](docs/info/README.md)
- [Plantilla de Módulo (`docs/info/_MODULE_TEMPLATE.md`)](docs/info/_MODULE_TEMPLATE.md)
- [Diseño y Arquitectura (`docs/info/DESIGN.md`)](docs/info/DESIGN.md)
- [Componentes de Hardware (`docs/info/COMPONENTS.md`)](docs/info/COMPONENTS.md)
- [Conexiones y Cableado (`docs/info/hardware-connections.md`)](docs/info/hardware-connections.md)
- [Comandos y Despliegue (`docs/info/commands.md`)](docs/info/commands.md)
- [Decisiones Técnicas (`docs/info/decisiones-tecnicas.md`)](docs/info/decisiones-tecnicas.md)
- Módulos:
  - [`main` (`docs/info/main.md`)](docs/info/main.md)
  - [`RenogyRoverLi` (`docs/info/RenogyRoverLi.md`)](docs/info/RenogyRoverLi.md)
  - [`SerialConnection` (`docs/info/SerialConnection.md`)](docs/info/SerialConnection.md)
  - [`RpiPico` (`docs/info/RpiPico.md`)](docs/info/RpiPico.md)
  - [`Api` (`docs/info/Api.md`)](docs/info/Api.md)
  - [`HomeAssistantConnection` (`docs/info/HomeAssistantConnection.md`)](docs/info/HomeAssistantConnection.md)
- Integraciones API:
  - [Renogy Modbus (`docs/info/apis/renogy-modbus.md`)](docs/info/apis/renogy-modbus.md)
  - [Home Assistant REST (`docs/info/apis/home-assistant.md`)](docs/info/apis/home-assistant.md)
  - [API Solar Propia (`docs/info/apis/custom-solar-api.md`)](docs/info/apis/custom-solar-api.md)

---

## 6. Comandos Rápidos de Referencia

```bash
# Verificación de sintaxis local
python3 -m py_compile src/main.py src/Models/*.py tests/*.py

# Abrir consola interactiva REPL en la Raspberry Pi Pico
mpremote

# Copiar todo el código fuente a la placa
mpremote cp src/env.py :env.py
mpremote cp src/main.py :main.py
mpremote cp src/Models/*.py :Models/
mpremote cp tests/*.py :tests/

# Ejecutar test de conexión con Home Assistant desde la placa
mpremote run tests/test_device_creation.py
```
