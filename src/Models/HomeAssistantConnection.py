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
# Create Date: 2025-08-01
# Project Name: Raspberry Pi Pico Monitor Renogy Rover Li Solar Controller
# Description: Clase de conexión a Home Assistant para enviar datos a Home Assistant
#              utilizando la API REST desde una Raspberry Pi Pico con MicroPython.
#
# Dependencies: MicroPython, urequests, ujson
#
# Revision 0.01 - File Created
# Additional Comments: Esta implementación incluye mecanismo de reintento y manejo de errores
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

# Configuraciones predeterminadas
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.3
DEFAULT_TIMEOUT = 10

class HomeAssistantConnection:
    """
    Una clase para conectarme a Home Assistant y enviar datos de sensores.
    
    Esta clase me proporciona métodos para enviar datos a Home Assistant a través de su API REST.
    Incluyo mecanismo de reintentos y manejo de errores para cuando Home Assistant no está disponible.
    
    Args:
        controller: El objeto controlador para la raspberry pi pico.
        url: La URL base de la instancia de Home Assistant (ej., "http://homeassistant.local:8123").
        token: El token de acceso de larga duración para Home Assistant.
        retries: Número de reintentos para solicitudes fallidas.
        backoff_factor: Factor de retroceso para reintentos.
        timeout: Tiempo de espera para solicitudes en segundos.
        debug: Bandera booleana opcional para modo de depuración.
    """
    
    def __init__(self, controller, url, token, device_id=1,
                 retries=DEFAULT_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR,
                 timeout=DEFAULT_TIMEOUT, debug=False):
        """
        Inicializo la conexión con Home Assistant.
        
        Args:
            controller: El objeto controlador para la raspberry pi pico.
            url: La URL base de la instancia de Home Assistant.
            token: El token de acceso de larga duración para Home Assistant.
            device_id: ID del dispositivo para identificación en Home Assistant.
            retries: Número de reintentos para solicitudes fallidas.
            backoff_factor: Factor de retroceso para reintentos.
            timeout: Tiempo de espera para solicitudes en segundos.
            debug: Bandera booleana opcional para modo de depuración.
        """
        self.URL = url.rstrip('/')  # Elimino la barra final si está presente
        self.TOKEN = token
        self.CONTROLLER = controller
        self.DEVICE_ID = device_id
        self.RETRIES = retries
        self.BACKOFF_FACTOR = backoff_factor
        self.TIMEOUT = timeout
        self.DEBUG = debug
        
        # Punto final de la API para estados
        self.API_STATES_ENDPOINT = "/api/states/"
        
        # Almaceno la información del dispositivo para asegurar consistencia entre sensores
        self.device_info = None
        
        # Almaceno la última vez que se actualizó la entidad del dispositivo
        self.last_device_update = 0
        
        # Intervalo de actualización para la entidad del dispositivo (en segundos)
        # Por defecto, actualizar cada hora (3600 segundos)
        self.device_update_interval = 3600
        
    def _get_headers(self):
        """
        Obtengo las cabeceras para las peticiones a la API de Home Assistant.
        
        Returns:
            dict: Cabeceras para las peticiones a la API
        """
        return {
            "Authorization": f"Bearer {self.TOKEN}",
            "Content-Type": "application/json"
        }
    
    def _get_microcontroller_status(self):
        """
        Obtengo información de estado desde el microcontrolador.
        
        Returns:
            dict: Diccionario con información de estado del microcontrolador
        """
        status = {
            "temperature": self.CONTROLLER.get_cpu_temperature(),
            "wifi_connected": self.CONTROLLER.wifi_is_connected(),
            "wifi_signal_strength": self.CONTROLLER.get_wireless_rssi() if self.CONTROLLER.wifi_is_connected() else None,
        }
        
        # Añado información de la batería si está disponible
        if hasattr(self.CONTROLLER, 'external_battery') and self.CONTROLLER.external_battery:
            self.CONTROLLER.read_external_battery()
            status["battery_percentage"] = self.CONTROLLER.external_battery["voltage_percentage"]
            status["battery_voltage"] = self.CONTROLLER.external_battery["voltage_current"]
        
        return status
    
    def check_connection(self):
        """
        Compruebo si Home Assistant es accesible.
        
        Returns:
            bool: True si Home Assistant es accesible, False en caso contrario
        """
        try:
            url = f"{self.URL}/api/"
            headers = self._get_headers()
            
            response = urequests.get(url, headers=headers)
            
            if response.status_code == 200:
                if self.DEBUG:
                    print("Home Assistant es accesible")
                return True
            else:
                if self.DEBUG:
                    print(f"Home Assistant devolvió código de estado: {response.status_code}")
                return False
                
        except Exception as e:
            if self.DEBUG:
                print(f"Error al conectar con Home Assistant: {e}")
            return False
    
    def update_sensor(self, entity_id, state, attributes=None):
        """
        Actualizo el estado de un sensor en Home Assistant.
        
        Args:
            entity_id (str): El ID de la entidad del sensor (ej., "sensor.solar_battery_voltage")
            state: El valor de estado a establecer
            attributes (dict, opcional): Atributos adicionales para el sensor
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        for attempt in range(self.RETRIES):
            try:
                url = f"{self.URL}{self.API_STATES_ENDPOINT}{entity_id}"
                headers = self._get_headers()
                
                # Preparo la carga útil
                payload = {
                    "state": state
                }
                
                # Añado atributos si se proporcionan, sanitizando los valores
                if attributes:
                    payload["attributes"] = self._sanitize_attributes(attributes)
                
                if self.DEBUG:
                    print(f"Actualizando sensor {entity_id} (intento {attempt+1}/{self.RETRIES}):")
                    print(f"URL: {url}")
                    print(f"Carga útil: {payload}")
                
                # Envío la petición POST
                response = urequests.post(url, headers=headers, json=payload)
                
                if self.DEBUG:
                    print(f"Estado de Respuesta de Home Assistant: {response.status_code}")
                
                # Compruebo si la respuesta es exitosa
                if response.status_code in [200, 201]:
                    return True
                else:
                    if self.DEBUG:
                        print(f"Estado de Error de Home Assistant: {response.status_code}")
                        print(f"Texto de Respuesta: {response.text}")
                    
                    # Espero antes de reintentar con retroceso exponencial
                    wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                    time.sleep(wait_time)
                    
            except Exception as e:
                if self.DEBUG:
                    print(f"Error al actualizar sensor (intento {attempt+1}/{self.RETRIES}): {e}")
                
                # Espero antes de reintentar con retroceso exponencial
                wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                time.sleep(wait_time)
        
        # Todos los reintentos fallaron
        return False
    
    def _capitalize_words(self, text):
        """
        Capitaliza la primera letra de cada palabra en un texto.
        Esta función reemplaza la funcionalidad de .title() que no está disponible en MicroPython.
        
        Args:
            text (str): Texto a capitalizar
            
        Returns:
            str: Texto con la primera letra de cada palabra en mayúscula
        """
        if not text:
            return ""
        
        words = text.split(' ')
        capitalized_words = []
        
        for word in words:
            if word:
                capitalized_words.append(word[0].upper() + word[1:])
            else:
                capitalized_words.append("")
                
        return ' '.join(capitalized_words)
        
    def _sanitize_string(self, text):
        """
        Sanitiza un string para asegurar que sea compatible con JSON.
        Reemplaza caracteres especiales con equivalentes ASCII.
        
        Args:
            text (str): Texto a sanitizar
            
        Returns:
            str: Texto sanitizado
        """
        if not text:
            return ""
            
        # Reemplazo caracteres especiales conocidos
        replacements = {
            "°": "",
            "ñ": "n",
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "Á": "A",
            "É": "E",
            "Í": "I",
            "Ó": "O",
            "Ú": "U",
            "ü": "u",
            "Ü": "U",
            "ç": "c",
            "Ç": "C"
        }
        
        result = text
        for char, replacement in replacements.items():
            result = result.replace(char, replacement)
            
        return result
        
    def _sanitize_attributes(self, attributes):
        """
        Sanitiza todos los valores de texto en un diccionario de atributos.
        
        Args:
            attributes (dict): Diccionario de atributos
            
        Returns:
            dict: Diccionario con valores sanitizados
        """
        if not attributes:
            return {}
            
        result = {}
        for key, value in attributes.items():
            if isinstance(value, str):
                result[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                result[key] = self._sanitize_attributes(value)
            else:
                result[key] = value
                
        return result
    
    # Mapeo de sensores a sus unidades y clases de dispositivo
    SENSOR_METADATA = {
        # Sensores de voltaje
        "battery_voltage": {"unit_of_measurement": "V", "device_class": "voltage"},
        "solar_voltage": {"unit_of_measurement": "V", "device_class": "voltage"},
        "load_voltage": {"unit_of_measurement": "V", "device_class": "voltage"},
        "today_battery_max_voltage": {"unit_of_measurement": "V", "device_class": "voltage"},
        "today_battery_min_voltage": {"unit_of_measurement": "V", "device_class": "voltage"},
        "system_voltage_current": {"unit_of_measurement": "V", "device_class": "voltage"},
        
        # Sensores de corriente
        "solar_current": {"unit_of_measurement": "A", "device_class": "current"},
        "load_current": {"unit_of_measurement": "A", "device_class": "current"},
        "system_intensity_current": {"unit_of_measurement": "A", "device_class": "current"},
        "today_max_charging_current": {"unit_of_measurement": "A", "device_class": "current"},
        "today_max_discharging_current": {"unit_of_measurement": "A", "device_class": "current"},
        
        # Sensores de potencia
        "solar_power": {"unit_of_measurement": "W", "device_class": "power"},
        "load_power": {"unit_of_measurement": "W", "device_class": "power"},
        "today_max_charging_power": {"unit_of_measurement": "W", "device_class": "power"},
        
        # Sensores de energía
        "today_power_generation": {"unit_of_measurement": "Wh", "device_class": "energy"},
        "today_power_consumption": {"unit_of_measurement": "Wh", "device_class": "energy"},
        "historical_cumulative_power_generation": {"unit_of_measurement": "kWh", "device_class": "energy"},
        "historical_cumulative_power_consumption": {"unit_of_measurement": "kWh", "device_class": "energy"},
        
        # Sensores de temperatura
        "battery_temperature": {"unit_of_measurement": "C", "device_class": "temperature"},
        "controller_temperature": {"unit_of_measurement": "C", "device_class": "temperature"},
        
        # Sensores de porcentaje
        "battery_percentage": {"unit_of_measurement": "%", "device_class": "battery"},
        "street_light_brightness": {"unit_of_measurement": "%", "device_class": "illuminance"},
        
        # Sensores de amperios-hora
        "today_charging_amp_hours": {"unit_of_measurement": "Ah", "device_class": None},
        "today_discharging_amp_hours": {"unit_of_measurement": "Ah", "device_class": None},
        "historical_total_charging_amp_hours": {"unit_of_measurement": "Ah", "device_class": None},
        "historical_total_discharging_amp_hours": {"unit_of_measurement": "Ah", "device_class": None},
        "nominal_battery_capacity": {"unit_of_measurement": "Ah", "device_class": None},
        
        # Sensores de estado
        "charging_status": {"unit_of_measurement": None, "device_class": None},
        "charging_status_label": {"unit_of_measurement": None, "device_class": None},
        "street_light_status": {"unit_of_measurement": None, "device_class": "binary_sensor"},
        
        # Sensores de conteo
        "historical_total_days_operating": {"unit_of_measurement": "days", "device_class": None},
        "historical_total_number_battery_over_discharges": {"unit_of_measurement": None, "device_class": None},
        "historical_total_number_battery_full_charges": {"unit_of_measurement": None, "device_class": None},
        
        # Otros sensores
        "device_id": {"unit_of_measurement": None, "device_class": None},
        "hardware": {"unit_of_measurement": None, "device_class": None},
        "version": {"unit_of_measurement": None, "device_class": None},
        "serial_number": {"unit_of_measurement": None, "device_class": None},
        "battery_type": {"unit_of_measurement": None, "device_class": None}
    }
    
    def update_solar_controller_data(self, data):
        """
        Actualizo todos los sensores del controlador solar en Home Assistant.
        
        Este método crea o actualiza sensores para todos los puntos de datos del controlador solar.
        Asigna automáticamente unidades de medida y clases de dispositivo apropiadas para cada sensor.
        
        Args:
            data (dict): Diccionario con datos del controlador solar
            
        Returns:
            bool: True si al menos un sensor se actualizó correctamente, False en caso contrario
        """
        if not data:
            if self.DEBUG:
                print("No se proporcionaron datos para actualizar los sensores del controlador solar")
            return False
        
        # Obtengo el estado del microcontrolador para incluirlo en los atributos
        microcontroller_status = self._get_microcontroller_status()
        
        # Hago seguimiento del éxito de las actualizaciones
        success = False
        
        # Atributos comunes para todos los sensores
        common_attributes = {
            "microcontroller": microcontroller_status,
            "last_update": time.time()
        }
        
        # Información del dispositivo para agrupar sensores
        device_id = data.get('device_id', 'unknown')
        self.device_info = {
            "identifiers": [f"renogy_rover_li_{device_id}"],
            "name": f"Controlador Solar Renogy Rover Li {device_id}",
            "manufacturer": "Renogy",
            "model": "Rover Li",
            "sw_version": data.get('version', 'unknown'),
            "suggested_area": "Exterior"
        }
        
        # Actualizo cada punto de datos como un sensor separado
        for key, value in data.items():
            # Omito valores nulos
            if value is None:
                continue
                
            # Creo el ID de entidad a partir de la clave
            entity_id = f"sensor.solar_{key.lower().replace(' ', '_')}"
            
            # Creo atributos específicos para este sensor
            attributes = dict(common_attributes)
            
            # Uso la función personalizada en lugar de .title() que no está disponible en MicroPython
            replaced_key = key.replace('_', ' ')
            
            # Evito redundancia en nombres como "Solar Solar Voltage"
            if replaced_key.lower().startswith('solar '):
                attributes["friendly_name"] = self._capitalize_words(replaced_key)
            else:
                attributes["friendly_name"] = f"Solar {self._capitalize_words(replaced_key)}"
            
            # Añado metadatos específicos para este tipo de sensor
            if key in self.SENSOR_METADATA:
                metadata = self.SENSOR_METADATA[key]
                if metadata["unit_of_measurement"]:
                    attributes["unit_of_measurement"] = metadata["unit_of_measurement"]
                if metadata["device_class"]:
                    attributes["device_class"] = metadata["device_class"]
            
            # Añado información del dispositivo para agrupar sensores
            attributes["device"] = self.device_info
            
            # Añado unique_id para permitir la gestión desde la UI de Home Assistant
            # Uso el mismo formato que el identificador del dispositivo para mantener consistencia
            attributes["unique_id"] = f"{self.device_info['identifiers'][0]}_{key.lower().replace(' ', '_')}"
            
            # Actualizo el sensor
            if self.update_sensor(entity_id, value, attributes):
                success = True
        
        return success
    
    def verify_device_exists(self):
        """
        Verifica si el dispositivo existe en Home Assistant.
        
        Returns:
            bool: True si el dispositivo existe, False en caso contrario
        """
        if not self.device_info:
            # Si no hay información del dispositivo, creo una predeterminada usando el ID del dispositivo
            self.device_info = {
                "identifiers": [f"renogy_rover_li_{self.DEVICE_ID}"],
                "name": f"Controlador Solar Renogy Rover Li {self.DEVICE_ID}",
                "manufacturer": "Renogy",
                "model": "Rover Li",
                "sw_version": "unknown",
                "suggested_area": "Exterior"
            }
            if self.DEBUG:
                print(f"Advertencia: No hay información de dispositivo para verificar, usando valores predeterminados con ID {self.DEVICE_ID}")
            
        # Creo un ID de entidad para el dispositivo basado en el identificador del dispositivo
        device_identifier = self.device_info["identifiers"][0]
        entity_id = f"sensor.{device_identifier}_device"
        
        try:
            url = f"{self.URL}{self.API_STATES_ENDPOINT}{entity_id}"
            headers = self._get_headers()
            
            response = urequests.get(url, headers=headers)
            
            if self.DEBUG:
                print(f"Verificando si existe el dispositivo: {entity_id}")
                print(f"Estado de respuesta: {response.status_code}")
            
            # Si la respuesta es 200, el dispositivo existe
            return response.status_code == 200
                
        except Exception as e:
            if self.DEBUG:
                print(f"Error al verificar si existe el dispositivo: {e}")
            return False
    
    def create_device_entity(self):
        """
        Crea una entidad dedicada para el dispositivo en Home Assistant.
        Esto asegura que el dispositivo aparezca en la interfaz de Home Assistant.
        
        La entidad se actualiza solo si ha pasado suficiente tiempo desde la última
        actualización (definido por self.device_update_interval) para evitar
        actualizaciones innecesarias y reducir el ruido en los registros.
        
        Returns:
            bool: True si la entidad se creó correctamente o no necesitaba actualización,
                 False en caso contrario
        """
        if not self.device_info:
            # Si no hay información del dispositivo, creo una predeterminada usando el ID del dispositivo
            self.device_info = {
                "identifiers": [f"renogy_rover_li_{self.DEVICE_ID}"],
                "name": f"Controlador Solar Renogy Rover Li {self.DEVICE_ID}",
                "manufacturer": "Renogy",
                "model": "Rover Li",
                "sw_version": "unknown",
                "suggested_area": "Exterior"
            }
            if self.DEBUG:
                print(f"Advertencia: No hay información de dispositivo para crear la entidad, usando valores predeterminados con ID {self.DEVICE_ID}")
            
        # Obtengo el tiempo actual
        current_time = time.time()
        
        # Verifico si ha pasado suficiente tiempo desde la última actualización
        time_since_last_update = current_time - self.last_device_update
        
        # Si no ha pasado suficiente tiempo, no actualizo la entidad
        if time_since_last_update < self.device_update_interval and self.last_device_update > 0:
            if self.DEBUG:
                print(f"No se actualiza la entidad del dispositivo. Próxima actualización en {self.device_update_interval - time_since_last_update} segundos")
            return True  # Devuelvo True porque no es un error, simplemente no es necesario actualizar
            
        # Creo un ID de entidad para el dispositivo basado en el identificador del dispositivo
        device_identifier = self.device_info["identifiers"][0]
        entity_id = f"sensor.{device_identifier}_device"
        
        # Creo atributos para la entidad
        attributes = {
            "friendly_name": self.device_info["name"],
            "device_class": "timestamp",
            "device": self.device_info,
            "unique_id": f"{self.device_info['identifiers'][0]}_device",
            "icon": "mdi:solar-power",
            "last_update_interval": self.device_update_interval  # Añado el intervalo como atributo para referencia
        }
        
        # El estado será la fecha y hora actual
        state = current_time
        
        # Actualizo la entidad en Home Assistant
        result = self.update_sensor(entity_id, state, attributes)
        
        # Si la actualización fue exitosa, actualizo el timestamp de última actualización
        if result:
            self.last_device_update = current_time
            if self.DEBUG:
                print(f"Entidad del dispositivo actualizada. Próxima actualización en {self.device_update_interval} segundos")
        
        return result
    
    def update_microcontroller_sensors(self):
        """
        Actualizo los sensores para el estado del microcontrolador en Home Assistant.
        
        Returns:
            bool: True si al menos un sensor se actualizó correctamente, False en caso contrario
        """
        # Obtengo el estado del microcontrolador
        status = self._get_microcontroller_status()
        
        # Hago seguimiento del éxito de las actualizaciones
        success = False
        
        # Verifico si tenemos información del dispositivo almacenada
        if not self.device_info:
            # Si no hay información del dispositivo, creo una predeterminada
            default_device_id = 1  # Valor predeterminado para device_id
            self.device_info = {
                "identifiers": [f"renogy_rover_li_{default_device_id}"],
                "name": f"Controlador Solar Renogy Rover Li {default_device_id}",
                "manufacturer": "Renogy",
                "model": "Rover Li",
                "sw_version": "unknown",
                "suggested_area": "Exterior"
            }
            if self.DEBUG:
                print("Advertencia: No hay información de dispositivo almacenada, usando valores predeterminados")
        
        # Atributos comunes para todos los sensores
        common_attributes = {
            "last_update": time.time(),
            "device_class": "temperature",
            "unit_of_measurement": "C",
            "friendly_name": "Temperatura del Microcontrolador",
            "device": self.device_info,  # Añado información del dispositivo para agrupar sensores
            "unique_id": f"{self.device_info['identifiers'][0]}_microcontroller_temperature"  # Añado unique_id para permitir la gestión desde la UI
        }
        
        # Actualizo el sensor de temperatura
        if self.update_sensor("sensor.microcontroller_temperature", status["temperature"], common_attributes):
            success = True
        
        # Actualizo el sensor de estado WiFi
        wifi_attributes = {
            "last_update": time.time(),
            "friendly_name": "Estado WiFi del Microcontrolador",
            "device": self.device_info,  # Añado información del dispositivo para agrupar sensores
            "unique_id": f"{self.device_info['identifiers'][0]}_microcontroller_wifi"  # Añado unique_id para permitir la gestión desde la UI
        }
        if self.update_sensor("binary_sensor.microcontroller_wifi", "on" if status["wifi_connected"] else "off", wifi_attributes):
            success = True
        
        # Actualizo el sensor de intensidad de señal WiFi si está disponible
        if status["wifi_connected"] and status["wifi_signal_strength"] is not None:
            signal_attributes = {
                "last_update": time.time(),
                "unit_of_measurement": "dBm",
                "device_class": "signal_strength",
                "friendly_name": "Senal WiFi del Microcontrolador",
                "device": self.device_info,  # Añado información del dispositivo para agrupar sensores
                "unique_id": f"{self.device_info['identifiers'][0]}_microcontroller_wifi_signal"  # Añado unique_id para permitir la gestión desde la UI
            }
            if self.update_sensor("sensor.microcontroller_wifi_signal", status["wifi_signal_strength"], signal_attributes):
                success = True
        
        # Actualizo el sensor de batería si está disponible
        if "battery_percentage" in status:
            battery_attributes = {
                "last_update": time.time(),
                "unit_of_measurement": "%",
                "device_class": "battery",
                "friendly_name": "Batería del Microcontrolador",
                "device": self.device_info,  # Añado información del dispositivo para agrupar sensores
                "unique_id": f"{self.device_info['identifiers'][0]}_microcontroller_battery"  # Añado unique_id para permitir la gestión desde la UI
            }
            if self.update_sensor("sensor.microcontroller_battery", status["battery_percentage"], battery_attributes):
                success = True
        
        return success