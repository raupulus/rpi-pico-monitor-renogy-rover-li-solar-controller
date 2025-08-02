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
# Description: Script para verificar y corregir la agrupación de entidades en Home Assistant
#
# Dependencies: MicroPython, urequests, ujson
#
# Revision 0.01 - File Created
# Additional Comments: Este script verifica que todas las entidades tengan la información
#                     de dispositivo correcta para agruparse en Home Assistant
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

import urequests
import ujson
import time
import sys

# Intento importar variables de entorno desde env.py
try:
    import env
except ImportError:
    print("Error: env.py no encontrado. Este script requiere la configuración de Home Assistant.")
    sys.exit(1)

# Verifico que las variables necesarias estén definidas
if not hasattr(env, 'HOME_ASSISTANT_URL') or not hasattr(env, 'HOME_ASSISTANT_TOKEN'):
    print("Error: HOME_ASSISTANT_URL y HOME_ASSISTANT_TOKEN deben estar definidos en env.py")
    sys.exit(1)

# Configuración
HA_URL = env.HOME_ASSISTANT_URL.rstrip('/')
HA_TOKEN = env.HOME_ASSISTANT_TOKEN
DEVICE_ID = env.DEVICE_ID if hasattr(env, 'DEVICE_ID') else 1
DEBUG = True  # Siempre mostramos mensajes de depuración en este script

# Lista completa de entidades que deberían estar agrupadas
SOLAR_ENTITIES = [
    # Información del Controlador
    "sensor.solar_device_id",
    "sensor.solar_hardware",
    "sensor.solar_version",
    "sensor.solar_serial_number",
    "sensor.solar_system_voltage_current",
    "sensor.solar_system_intensity_current",
    "sensor.solar_battery_type",
    "sensor.solar_nominal_battery_capacity",
    
    # Paneles Solares
    "sensor.solar_solar_current",
    "sensor.solar_solar_voltage",
    "sensor.solar_solar_power",
    
    # Batería
    "sensor.solar_battery_voltage",
    "sensor.solar_battery_temperature",
    "sensor.solar_battery_percentage",
    "sensor.solar_charging_status",
    "sensor.solar_charging_status_label",
    
    # Carga
    "sensor.solar_load_voltage",
    "sensor.solar_load_current",
    "sensor.solar_load_power",
    
    # Datos Históricos de Hoy
    "sensor.solar_today_battery_max_voltage",
    "sensor.solar_today_battery_min_voltage",
    "sensor.solar_today_max_charging_current",
    "sensor.solar_today_max_discharging_current",
    "sensor.solar_today_max_charging_power",
    "sensor.solar_today_charging_amp_hours",
    "sensor.solar_today_discharging_amp_hours",
    "sensor.solar_today_power_generation",
    "sensor.solar_today_power_consumption",
    
    # Datos Históricos Generales
    "sensor.solar_historical_total_days_operating",
    "sensor.solar_historical_total_number_battery_over_discharges",
    "sensor.solar_historical_total_number_battery_full_charges",
    "sensor.solar_historical_total_charging_amp_hours",
    "sensor.solar_historical_total_discharging_amp_hours",
    "sensor.solar_historical_cumulative_power_generation",
    "sensor.solar_historical_cumulative_power_consumption",
    
    # Estadísticas Globales
    "sensor.solar_energy_daily",
    "sensor.solar_energy_weekly",
    "sensor.solar_energy_monthly",
    "sensor.solar_consumption_daily",
    "sensor.solar_consumption_weekly",
    "sensor.solar_consumption_monthly",
    
    # Campos Adicionales
    "sensor.solar_controller_temperature",
    "sensor.solar_street_light_status",
    "sensor.solar_street_light_brightness",
]

MICROCONTROLLER_ENTITIES = [
    "sensor.microcontroller_temperature",
    "binary_sensor.microcontroller_wifi",
    "sensor.microcontroller_wifi_signal",
    "sensor.microcontroller_battery",
]

# Todas las entidades
ALL_ENTITIES = SOLAR_ENTITIES + MICROCONTROLLER_ENTITIES

def get_headers():
    """
    Obtiene las cabeceras para las peticiones a la API de Home Assistant.
    
    Returns:
        dict: Cabeceras para las peticiones a la API
    """
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }

def get_entity(entity_id):
    """
    Obtiene la información de una entidad de Home Assistant.
    
    Args:
        entity_id (str): ID de la entidad
        
    Returns:
        dict: Información de la entidad o None si no existe
    """
    try:
        url = f"{HA_URL}/api/states/{entity_id}"
        headers = get_headers()
        
        response = urequests.get(url, headers=headers)
        
        if response.status_code == 200:
            return ujson.loads(response.text)
        elif response.status_code == 404:
            print(f"La entidad {entity_id} no existe en Home Assistant")
            return None
        else:
            print(f"Error al obtener la entidad {entity_id}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Excepción al obtener la entidad {entity_id}: {e}")
        return None

def update_entity(entity_id, state, attributes):
    """
    Actualiza una entidad en Home Assistant.
    
    Args:
        entity_id (str): ID de la entidad
        state: Estado de la entidad
        attributes (dict): Atributos de la entidad
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        url = f"{HA_URL}/api/states/{entity_id}"
        headers = get_headers()
        
        payload = {
            "state": state,
            "attributes": attributes
        }
        
        response = urequests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            print(f"Entidad {entity_id} actualizada correctamente")
            return True
        else:
            print(f"Error al actualizar la entidad {entity_id}: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"Excepción al actualizar la entidad {entity_id}: {e}")
        return False

def check_entity_grouping(entity_id):
    """
    Verifica si una entidad está correctamente agrupada.
    
    Args:
        entity_id (str): ID de la entidad
        
    Returns:
        dict: Resultado de la verificación con las claves:
            - exists: True si la entidad existe, False en caso contrario
            - has_device: True si la entidad tiene información de dispositivo, False en caso contrario
            - has_unique_id: True si la entidad tiene un ID único, False en caso contrario
            - correct_device_id: True si el ID del dispositivo es correcto, False en caso contrario
            - entity_data: Datos de la entidad si existe, None en caso contrario
    """
    entity_data = get_entity(entity_id)
    
    if not entity_data:
        return {
            "exists": False,
            "has_device": False,
            "has_unique_id": False,
            "correct_device_id": False,
            "entity_data": None
        }
    
    # Verifico si tiene información de dispositivo
    has_device = "device" in entity_data.get("attributes", {})
    
    # Verifico si tiene ID único
    has_unique_id = "unique_id" in entity_data.get("attributes", {})
    
    # Verifico si el ID del dispositivo es correcto
    correct_device_id = False
    if has_device:
        device_info = entity_data["attributes"]["device"]
        if "identifiers" in device_info:
            identifiers = device_info["identifiers"]
            # Check for both old and new format device identifiers
            expected_id_old = f"solar_controller_{DEVICE_ID}"
            expected_id_new = f"renogy_rover_li_{DEVICE_ID}"
            correct_device_id = expected_id_old in identifiers or expected_id_new in identifiers
    
    return {
        "exists": True,
        "has_device": has_device,
        "has_unique_id": has_unique_id,
        "correct_device_id": correct_device_id,
        "entity_data": entity_data
    }

def fix_entity_grouping(entity_id, entity_data):
    """
    Corrige la agrupación de una entidad.
    
    Args:
        entity_id (str): ID de la entidad
        entity_data (dict): Datos actuales de la entidad
        
    Returns:
        bool: True si la corrección fue exitosa, False en caso contrario
    """
    if not entity_data:
        print(f"No se puede corregir la entidad {entity_id} porque no existe")
        return False
    
    # Obtengo los atributos actuales
    attributes = entity_data.get("attributes", {})
    
    # Creo la información del dispositivo usando el nuevo formato
    device_info = {
        "identifiers": [f"renogy_rover_li_{DEVICE_ID}"],
        "name": f"Controlador Solar Renogy Rover Li {DEVICE_ID}",
        "manufacturer": "Renogy",
        "model": "Rover Li",
        "sw_version": attributes.get("version", "unknown"),
        "suggested_area": "Exterior"
    }
    
    # Añado la información del dispositivo a los atributos
    attributes["device"] = device_info
    
    # Añado un ID único si no tiene, usando el nuevo formato
    if "unique_id" not in attributes:
        device_identifier = f"renogy_rover_li_{DEVICE_ID}"
        entity_suffix = entity_id.split('.')[-1]
        unique_id = f"{device_identifier}_{entity_suffix}"
        attributes["unique_id"] = unique_id
    
    # Actualizo la entidad
    return update_entity(entity_id, entity_data["state"], attributes)

def check_all_entities():
    """
    Verifica todas las entidades y muestra un resumen.
    
    Returns:
        dict: Resumen de la verificación con las claves:
            - total: Número total de entidades verificadas
            - existing: Número de entidades que existen
            - missing: Número de entidades que no existen
            - grouped: Número de entidades correctamente agrupadas
            - ungrouped: Número de entidades no agrupadas
            - fixable: Número de entidades que se pueden corregir
    """
    total = len(ALL_ENTITIES)
    existing = 0
    missing = 0
    grouped = 0
    ungrouped = 0
    fixable = 0
    
    print("\n=== Verificando agrupación de entidades ===\n")
    
    for entity_id in ALL_ENTITIES:
        print(f"Verificando {entity_id}...")
        result = check_entity_grouping(entity_id)
        
        if result["exists"]:
            existing += 1
            
            if result["has_device"] and result["correct_device_id"] and result["has_unique_id"]:
                grouped += 1
                print(f"  ✓ Correctamente agrupada")
            else:
                ungrouped += 1
                print(f"  ✗ No agrupada correctamente")
                
                if not result["has_device"]:
                    print(f"    - No tiene información de dispositivo")
                elif not result["correct_device_id"]:
                    print(f"    - El ID del dispositivo es incorrecto")
                
                if not result["has_unique_id"]:
                    print(f"    - No tiene ID único")
                
                fixable += 1
        else:
            missing += 1
            print(f"  ? No existe")
    
    return {
        "total": total,
        "existing": existing,
        "missing": missing,
        "grouped": grouped,
        "ungrouped": ungrouped,
        "fixable": fixable
    }

def fix_all_entities():
    """
    Corrige todas las entidades que no están correctamente agrupadas.
    
    Returns:
        dict: Resumen de la corrección con las claves:
            - total: Número total de entidades verificadas
            - fixed: Número de entidades corregidas
            - failed: Número de entidades que no se pudieron corregir
    """
    total = len(ALL_ENTITIES)
    fixed = 0
    failed = 0
    
    print("\n=== Corrigiendo agrupación de entidades ===\n")
    
    for entity_id in ALL_ENTITIES:
        print(f"Verificando {entity_id}...")
        result = check_entity_grouping(entity_id)
        
        if result["exists"] and not (result["has_device"] and result["correct_device_id"] and result["has_unique_id"]):
            print(f"  Corrigiendo {entity_id}...")
            if fix_entity_grouping(entity_id, result["entity_data"]):
                fixed += 1
                print(f"  ✓ Corregida")
            else:
                failed += 1
                print(f"  ✗ No se pudo corregir")
    
    return {
        "total": total,
        "fixed": fixed,
        "failed": failed
    }

def main():
    """
    Función principal del script.
    """
    print("\n=== Verificador de Agrupación de Entidades en Home Assistant ===\n")
    print(f"URL de Home Assistant: {HA_URL}")
    print(f"ID del Dispositivo: {DEVICE_ID}")
    
    # Verifico la conexión con Home Assistant
    print("\nVerificando conexión con Home Assistant...")
    try:
        url = f"{HA_URL}/api/"
        headers = get_headers()
        
        response = urequests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("✓ Conexión exitosa con Home Assistant")
        else:
            print(f"✗ Error al conectar con Home Assistant: {response.status_code}")
            return
            
    except Exception as e:
        print(f"✗ Excepción al conectar con Home Assistant: {e}")
        return
    
    # Muestro el menú
    while True:
        print("\n=== Menú ===")
        print("1. Verificar agrupación de entidades")
        print("2. Corregir agrupación de entidades")
        print("3. Salir")
        
        option = input("\nSelecciona una opción (1-3): ")
        
        if option == "1":
            summary = check_all_entities()
            
            print("\n=== Resumen ===")
            print(f"Total de entidades: {summary['total']}")
            print(f"Entidades existentes: {summary['existing']}")
            print(f"Entidades no existentes: {summary['missing']}")
            print(f"Entidades correctamente agrupadas: {summary['grouped']}")
            print(f"Entidades no agrupadas correctamente: {summary['ungrouped']}")
            print(f"Entidades que se pueden corregir: {summary['fixable']}")
            
        elif option == "2":
            summary = fix_all_entities()
            
            print("\n=== Resumen ===")
            print(f"Total de entidades verificadas: {summary['total']}")
            print(f"Entidades corregidas: {summary['fixed']}")
            print(f"Entidades que no se pudieron corregir: {summary['failed']}")
            
        elif option == "3":
            print("\n¡Hasta luego!")
            break
            
        else:
            print("\nOpción no válida. Por favor, selecciona una opción del 1 al 3.")

if __name__ == "__main__":
    main()