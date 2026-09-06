# Comandos y Flujo de Trabajo

Guía de comandos y herramientas para el desarrollo, despliegue y pruebas en la Raspberry Pi Pico.

## 1. Verificación de Sintaxis Local

Dado que el código se ejecuta sobre MicroPython, en el entorno de desarrollo local (macOS/Linux) se puede verificar la sintaxis de los scripts con el intérprete Python local:

```bash
# Comprobar sintaxis de los archivos fuente
python3 -m py_compile src/main.py
python3 -m py_compile src/Models/*.py
python3 -m py_compile tests/*.py
```

## 2. Gestión de Archivos en la Raspberry Pi Pico

Se recomienda el uso de [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html) (herramienta oficial de MicroPython) o `rshell`:

### Conexión interactiva (REPL)
```bash
# Abrir consola interactiva REPL en el dispositivo conectado por USB
mpremote
```

### Despliegue de archivos hacia la Pico
```bash
# 1. Copiar archivo de configuración (modificado localmente)
mpremote cp src/env.py :env.py

# 2. Copiar script principal
mpremote cp src/main.py :main.py

# 3. Crear directorio Models y copiar clases
mpremote mkdir :Models
mpremote cp src/Models/Api.py :Models/Api.py
mpremote cp src/Models/HomeAssistantConnection.py :Models/HomeAssistantConnection.py
mpremote cp src/Models/RenogyRoverLi.py :Models/RenogyRoverLi.py
mpremote cp src/Models/RpiPico.py :Models/RpiPico.py
mpremote cp src/Models/SerialConnection.py :Models/SerialConnection.py

# 4. Crear directorio tests y copiar herramientas de verificación
mpremote mkdir :tests
mpremote cp tests/test_device_creation.py :tests/test_device_creation.py
mpremote cp tests/verify_entity_grouping.py :tests/verify_entity_grouping.py
```

### Listar archivos en la Pico
```bash
mpremote ls
mpremote ls :Models
mpremote ls :tests
```

### Reiniciar la placa por software
```bash
mpremote reset
```

## 3. Ejecución de Pruebas y Diagnóstico en la Placa

Los scripts de prueba en `tests/` están diseñados para correr en el intérprete MicroPython de la propia Raspberry Pi Pico (ya que requieren `urequests` y acceso a la red de la placa):

### Prueba de Creación de Dispositivo en Home Assistant
Ejecutar desde el REPL de la placa:
```python
import tests.test_device_creation as t
t.main()
```
O directamente mediante comando `mpremote`:
```bash
mpremote run tests/test_device_creation.py
```

### Auditoría y Reparación de Agrupación de Entidades
Ejecutar desde el REPL interactivo:
```python
import tests.verify_entity_grouping as v
v.main()
```
Opcion 1: Inspecciona todas las entidades registradas en Home Assistant y valida su agrupación.
Opción 2: Reenvía los metadatos corrigiendo identificadores huérfanos o ausentes.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
