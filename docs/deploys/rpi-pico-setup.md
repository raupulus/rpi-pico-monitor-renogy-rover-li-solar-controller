# Guía de Despliegue: Raspberry Pi Pico W

Pasos para preparar la placa, flashear MicroPython e instalar el software del proyecto.

## 1. Requisitos Previos
- Placa **Raspberry Pi Pico W**.
- Cable micro-USB con líneas de datos.
- Archivo binario de MicroPython `.uf2` para Raspberry Pi Pico W (versión recomendada: v1.25.0 o superior).
- Entorno de desarrollo con Python 3 y la herramienta `mpremote`:
  ```bash
  pip install mpremote
  ```

## 2. Instalación del Firmware MicroPython
1. Mantén presionado el botón blanco **BOOTSEL** de la Raspberry Pi Pico W mientras conectas el cable micro-USB al ordenador.
2. Suelta el botón. La placa se montará como unidad de almacenamiento masivo llamada `RPI-RP2`.
3. Arrastra y suelta el archivo `.uf2` de MicroPython en la unidad `RPI-RP2`.
4. La placa se reiniciará automáticamente y quedará lista con el intérprete MicroPython en ejecución.

## 3. Configuración de Entorno
1. En la carpeta `src/`, crea tu archivo local `env.py` copiándolo desde `.env.example.py`:
   ```bash
   cp src/.env.example.py src/env.py
   ```
2. Edita `src/env.py` con tus credenciales reales:
   - `WIFI_SSID` y `WIFI_PASSWORD`
   - Si usas Home Assistant: `UPLOAD_HOME_ASSISTANT = True`, `HOME_ASSISTANT_URL` y `HOME_ASSISTANT_TOKEN`.
   - Si usas la API propia: `UPLOAD_API = True`, `API_URL` y `API_TOKEN`.
   - Pines UART: `SERIAL_TX_PIN = 0`, `SERIAL_RX_PIN = 1`.

## 4. Subida de Archivos a la Placa
Ejecuta los siguientes comandos desde la raíz del repositorio:

```bash
# 1. Copiar configuración
mpremote cp src/env.py :env.py

# 2. Crear directorios y copiar módulos
mpremote mkdir :Models
mpremote cp src/Models/Api.py :Models/Api.py
mpremote cp src/Models/HomeAssistantConnection.py :Models/HomeAssistantConnection.py
mpremote cp src/Models/RenogyRoverLi.py :Models/RenogyRoverLi.py
mpremote cp src/Models/RpiPico.py :Models/RpiPico.py
mpremote cp src/Models/SerialConnection.py :Models/SerialConnection.py

# 3. Copiar pruebas opcionales
mpremote mkdir :tests
mpremote cp tests/test_device_creation.py :tests/test_device_creation.py
mpremote cp tests/verify_entity_grouping.py :tests/verify_entity_grouping.py

# 4. Copiar script principal (inicia la ejecución al alimentar la placa)
mpremote cp src/main.py :main.py
```

## 5. Verificación
Abre la consola serie interactiva para comprobar la inicialización y el primer ciclo:
```bash
mpremote
```
Deberás observar la conexión WiFi, sincronización NTP y la primera lectura de los registros Modbus.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
