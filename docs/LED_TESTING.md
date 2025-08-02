# LED Indicators Testing Guide

Este documento proporciona instrucciones para probar la implementación de los indicadores LED externos en el proyecto.

## Configuración de Prueba

1. **Configuración de Hardware**:
   - Conecta un LED a cada uno de los pines GPIO configurados
   - Usa resistencias apropiadas (220-330 ohm) para proteger los LEDs
   - Conecta el cátodo (pata corta) del LED a GND
   - Conecta el ánodo (pata larga) del LED a través de la resistencia al pin GPIO

2. **Configuración de Software**:
   - Configura los pines LED en tu archivo `env.py`:
   ```python
   LED_POWER_PIN = 15  # Número de pin GPIO para LED de encendido
   LED_UPLOAD_PIN = 14  # Número de pin GPIO para LED de subida a API/Home Assistant
   LED_CYCLE_PIN = 13  # Número de pin GPIO para LED de trabajo del ciclo
   ```
   - Asegúrate de que DEBUG = True para ver mensajes detallados

## Casos de Prueba

### 1. Prueba de Inicialización

**Objetivo**: Verificar que los LEDs se inicializan correctamente.

**Pasos**:
1. Configura los tres LEDs en env.py
2. Ejecuta el programa
3. Observa los mensajes de depuración durante la inicialización

**Resultado Esperado**:
- Deberías ver mensajes como "LED de encendido inicializado en pin X"
- El LED de encendido debería iluminarse inmediatamente y permanecer encendido

### 2. Prueba de Funcionalidad

**Objetivo**: Verificar que los LEDs se encienden y apagan en los momentos adecuados.

**Pasos**:
1. Deja que el programa complete un ciclo completo
2. Observa el comportamiento de cada LED

**Resultado Esperado**:
- LED de Encendido: Permanece encendido durante toda la ejecución
- LED de Ciclo: Se enciende durante la lectura de datos del controlador solar y se apaga después
- LED de Subida: Se enciende durante las subidas a la API y Home Assistant, y se apaga después

### 3. Prueba de Manejo de Errores

**Objetivo**: Verificar que los LEDs se comportan correctamente durante condiciones de error.

**Pasos**:
1. Provoca un error (por ejemplo, desconectando el controlador solar)
2. Observa el comportamiento de los LEDs

**Resultado Esperado**:
- Los LEDs de Ciclo y Subida deberían apagarse
- El LED de Encendido debería permanecer encendido
- El LED integrado debería parpadear rápidamente para indicar el error

### 4. Prueba de Robustez

**Objetivo**: Verificar que el programa funciona correctamente incluso sin LEDs configurados.

**Pasos**:
1. Comenta o elimina las configuraciones de LED en env.py
2. Ejecuta el programa
3. Verifica que el programa funciona normalmente

**Resultado Esperado**:
- El programa debería ejecutarse sin errores
- No debería haber intentos de controlar LEDs no configurados

## Solución de Problemas

Si los LEDs no funcionan como se espera:

1. **Verifica las conexiones físicas**:
   - Asegúrate de que los LEDs estén conectados a los pines correctos
   - Verifica la polaridad de los LEDs
   - Comprueba que las resistencias estén correctamente instaladas

2. **Verifica la configuración**:
   - Confirma que los números de pin en env.py corresponden a los pines GPIO utilizados
   - Asegúrate de que los pines no estén siendo utilizados por otra funcionalidad

3. **Verifica los mensajes de depuración**:
   - Habilita DEBUG = True en env.py
   - Busca mensajes de error relacionados con la inicialización de los LEDs