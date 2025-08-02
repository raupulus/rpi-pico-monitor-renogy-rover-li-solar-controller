#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @author     Raúl Caro Pastorino
# @email      public@raupulus.dev
# @web        https://raupulus.dev
# @gitlab     https://gitlab.com/raupulus
# @github     https://github.com/raupulus
# @twitter    https://twitter.com/raupulus
# @telegram   https://t.me/raupulus_diffusion
#
# Create Date: 2025-08-02
# Project Name: Raspberry Pi Pico Monitor Renogy Rover Li Solar Controller
# Description: Script de prueba para verificar la creación del dispositivo en Home Assistant
#
# Dependencies: MicroPython, urequests, ujson
#
# Revision 0.01 - File Created
# Additional Comments: Este script verifica que el dispositivo se cree correctamente en Home Assistant
#
# @copyright  Copyright © 2025 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt
#
# Copyright (C) 2025  Raúl Caro Pastorino
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from Models.HomeAssistantConnection import HomeAssistantConnection
from Models.RpiPico import RpiPico
import time

# Intento importar variables de entorno desde env.py
try:
    import env
except ImportError:
    print("Error: env.py no encontrado. Este script requiere la configuración de Home Assistant.")
    import sys
    sys.exit(1)

# Verifico que las variables necesarias estén definidas
if not hasattr(env, 'HOME_ASSISTANT_URL') or not hasattr(env, 'HOME_ASSISTANT_TOKEN'):
    print("Error: HOME_ASSISTANT_URL y HOME_ASSISTANT_TOKEN deben estar definidos en env.py")
    import sys
    sys.exit(1)

# Configuración
DEBUG = True
DEVICE_ID = env.DEVICE_ID if hasattr(env, 'DEVICE_ID') else 1
HOME_ASSISTANT_URL = env.HOME_ASSISTANT_URL
HOME_ASSISTANT_TOKEN = env.HOME_ASSISTANT_TOKEN

def test_device_creation():
    """
    Prueba la creación del dispositivo en Home Assistant.
    """
    print("\n=== Prueba de Creación de Dispositivo en Home Assistant ===\n")
    print(f"URL de Home Assistant: {HOME_ASSISTANT_URL}")
    print(f"ID del Dispositivo: {DEVICE_ID}")
    
    # Inicializo RpiPico (necesario para HomeAssistantConnection)
    rpi_pico = RpiPico(debug=DEBUG)
    
    # Inicializo HomeAssistantConnection
    home_assistant = HomeAssistantConnection(
        controller=rpi_pico,
        url=HOME_ASSISTANT_URL,
        token=HOME_ASSISTANT_TOKEN,
        device_id=DEVICE_ID,
        debug=DEBUG
    )
    
    # Verifico si Home Assistant es accesible
    if not home_assistant.check_connection():
        print("Error: No se puede conectar a Home Assistant. Verifica la URL y el token.")
        return False
    
    print("Home Assistant es accesible.")
    
    # Intento crear el dispositivo
    print("\nCreando dispositivo...")
    device_created = home_assistant.create_device_entity()
    
    if device_created:
        print("✓ Dispositivo creado correctamente.")
    else:
        print("✗ Error al crear el dispositivo.")
        return False
    
    # Verifico si el dispositivo existe
    print("\nVerificando si el dispositivo existe...")
    device_exists = home_assistant.verify_device_exists()
    
    if device_exists:
        print("✓ El dispositivo existe en Home Assistant.")
    else:
        print("✗ El dispositivo no existe en Home Assistant.")
        return False
    
    # Obtengo el ID de entidad del dispositivo
    device_identifier = home_assistant.device_info["identifiers"][0]
    entity_id = f"sensor.{device_identifier}_device"
    
    print(f"\nID de entidad del dispositivo: {entity_id}")
    print(f"Información del dispositivo: {home_assistant.device_info}")
    
    return True

def main():
    """
    Función principal del script.
    """
    result = test_device_creation()
    
    if result:
        print("\n✓ Prueba completada con éxito. El dispositivo se creó correctamente en Home Assistant.")
    else:
        print("\n✗ Prueba fallida. No se pudo crear el dispositivo en Home Assistant.")

if __name__ == "__main__":
    main()