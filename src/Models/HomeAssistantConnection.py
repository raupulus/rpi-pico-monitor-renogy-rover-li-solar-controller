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
    
    def __init__(self, controller, url, token, 
                 retries=DEFAULT_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR,
                 timeout=DEFAULT_TIMEOUT, debug=False):
        """
        Inicializo la conexión con Home Assistant.
        
        Args:
            controller: El objeto controlador para la raspberry pi pico.
            url: La URL base de la instancia de Home Assistant.
            token: El token de acceso de larga duración para Home Assistant.
            retries: Número de reintentos para solicitudes fallidas.
            backoff_factor: Factor de retroceso para reintentos.
            timeout: Tiempo de espera para solicitudes en segundos.
            debug: Bandera booleana opcional para modo de depuración.
        """
        self.URL = url.rstrip('/')  # Elimino la barra final si está presente
        self.TOKEN = token
        self.CONTROLLER = controller
        self.RETRIES = retries
        self.BACKOFF_FACTOR = backoff_factor
        self.TIMEOUT = timeout
        self.DEBUG = debug
        
        # Punto final de la API para estados
        self.API_STATES_ENDPOINT = "/api/states/"
        
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
                
                # Añado atributos si se proporcionan
                if attributes:
                    payload["attributes"] = attributes
                
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
    
    def update_solar_controller_data(self, data):
        """
        Actualizo todos los sensores del controlador solar en Home Assistant.
        
        Este método crea o actualiza sensores para todos los puntos de datos del controlador solar.
        
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
            "last_update": time.time(),
            "friendly_name": "Controlador Solar"
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
            attributes["friendly_name"] = f"Solar {key.replace('_', ' ').title()}"
            
            # Actualizo el sensor
            if self.update_sensor(entity_id, value, attributes):
                success = True
        
        return success
    
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
        
        # Atributos comunes para todos los sensores
        common_attributes = {
            "last_update": time.time(),
            "device_class": "temperature",
            "unit_of_measurement": "°C",
            "friendly_name": "Temperatura del Microcontrolador"
        }
        
        # Actualizo el sensor de temperatura
        if self.update_sensor("sensor.microcontroller_temperature", status["temperature"], common_attributes):
            success = True
        
        # Actualizo el sensor de estado WiFi
        wifi_attributes = {
            "last_update": time.time(),
            "friendly_name": "Estado WiFi del Microcontrolador"
        }
        if self.update_sensor("binary_sensor.microcontroller_wifi", "on" if status["wifi_connected"] else "off", wifi_attributes):
            success = True
        
        # Actualizo el sensor de intensidad de señal WiFi si está disponible
        if status["wifi_connected"] and status["wifi_signal_strength"] is not None:
            signal_attributes = {
                "last_update": time.time(),
                "unit_of_measurement": "dBm",
                "device_class": "signal_strength",
                "friendly_name": "Señal WiFi del Microcontrolador"
            }
            if self.update_sensor("sensor.microcontroller_wifi_signal", status["wifi_signal_strength"], signal_attributes):
                success = True
        
        # Actualizo el sensor de batería si está disponible
        if "battery_percentage" in status:
            battery_attributes = {
                "last_update": time.time(),
                "unit_of_measurement": "%",
                "device_class": "battery",
                "friendly_name": "Batería del Microcontrolador"
            }
            if self.update_sensor("sensor.microcontroller_battery", status["battery_percentage"], battery_attributes):
                success = True
        
        return success