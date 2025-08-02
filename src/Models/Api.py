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
# Create Date: 2022/2025
# Project Name: Raspberry Pi Pico Monitor Renogy Rover Li Solar Controller
# Description: Clase de conexión a la API para enviar datos a una API remota y
#              recuperar datos de ella usando MicroPython en Raspberry Pi Pico.
#
# Dependencies: MicroPython, urequests, ujson
#
# Revision 0.02 - Adaptado para Raspberry Pi Pico con MicroPython
# Additional Comments: Esta implementación incluye mecanismo de reintento y estado del microcontrolador
#
# @copyright  Copyright © 2022/2025 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt
#
# Copyright (C) 2022/2025  Raúl Caro Pastorino
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
DEFAULT_TIMEOUT = 30


class Api:
    """
    Una clase que representa una conexión a API con métodos para interactuar con el endpoint.
    Incluyo mecanismo de reintentos y datos de estado del microcontrolador en las peticiones.

    Args:
        controller: El objeto controlador para la raspberry pi pico.
        url: La URL base de la API.
        path: La ruta específica para el endpoint de la API.
        token: El token de autenticación para acceder a la API.
        device_id: El identificador único del dispositivo.
        retries: Número de reintentos para solicitudes fallidas.
        backoff_factor: Factor de retroceso para reintentos.
        timeout: Tiempo de espera para solicitudes en segundos.
        debug: Boolean opcional para indicar modo de depuración.
    """

    def __init__(self, controller, url, path, token, device_id, 
                 retries=DEFAULT_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR,
                 timeout=DEFAULT_TIMEOUT, debug=False):
        self.URL = url
        self.TOKEN = token
        self.DEVICE_ID = device_id
        self.URL_PATH = path
        self.CONTROLLER = controller
        self.RETRIES = retries
        self.BACKOFF_FACTOR = backoff_factor
        self.TIMEOUT = timeout
        self.DEBUG = debug

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
        
        # Añado información de la batería si estuviera disponible
        if hasattr(self.CONTROLLER, 'external_battery') and self.CONTROLLER.external_battery:
            self.CONTROLLER.read_external_battery()
            status["battery_percentage"] = self.CONTROLLER.external_battery["voltage_percentage"]
            status["battery_voltage"] = self.CONTROLLER.external_battery["voltage_current"]
        
        return status

    def _parse_to_json(self, data):
        """
        Convierto datos a formato JSON.
        
        Args:
            data: Datos a convertir a JSON
            
        Returns:
            str: Cadena JSON
        """
        try:
            return ujson.dumps(data)
        except Exception as e:
            if self.DEBUG:
                print(f"Error converting to JSON: {e}")
            return None

    def get_data_from_api(self):
        """
        Recupero datos desde la API con mecanismo de reintento.
        
        Returns:
            dict: Datos de la API o False si falló
        """
        for attempt in range(self.RETRIES):
            try:
                headers = {
                    "Authorization": "Bearer " + self.TOKEN,
                    "Content-Type": "application/json",
                    "Device-Id": str(self.DEVICE_ID)
                }

                url = self.URL + self.URL_PATH

                response = urequests.get(url, headers=headers)
                
                if self.DEBUG:
                    print(f'Estado de Respuesta API: {response.status_code}')

                # Verifico si la respuesta es exitosa
                if response.status_code in [200, 201]:
                    data = ujson.loads(response.text)
                
                    if self.DEBUG:
                        print('Respuesta JSON de la API:', data)
                
                    return data
                else:
                    if self.DEBUG:
                        print(f'Estado de Error API: {response.status_code}')
                    
                    # Espero antes de reintentar con retroceso exponencial
                    wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                    time.sleep(wait_time)
                    
            except Exception as e:
                if self.DEBUG:
                    print(f"Error al obtener datos de la API (intento {attempt+1}/{self.RETRIES}): {e}")
                
                # Espero antes de reintentar con retroceso exponencial
                wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                time.sleep(wait_time)
        
        # Todos los reintentos fallaron
        return False

    def send_to_api(self, data={}) -> bool:
        """
        Envío datos a la API con mecanismo de reintento y estado del microcontrolador.

        Args:
            data: Diccionario con datos para enviar.

        Returns:
            bool: True si la petición fue exitosa, False en caso contrario.
        """
        for attempt in range(self.RETRIES):
            try:
                headers = {
                    "Authorization": "Bearer " + self.TOKEN,
                    "Content-Type": "application/json"
                }

                url = self.URL + self.URL_PATH
                
                # Obtengo el estado del microcontrolador
                microcontroller_status = self._get_microcontroller_status()
                
                # Creo la carga útil con datos, ID del dispositivo y estado del microcontrolador
                """
                payload = {
                    "data": data,
                    "hardware_device_id": self.DEVICE_ID,
                    "microcontroller": microcontroller_status
                }
                """

                payload = data.copy()
                payload["hardware_device_id"] = self.DEVICE_ID
                payload["microcontroller"] = microcontroller_status

                if self.DEBUG:
                    print(f"Enviando a la API (intento {attempt+1}/{self.RETRIES}):")
                    print(f"URL: {url}")
                    print(f"Carga útil: {payload}")

                # Envío la petición POST
                response = urequests.post(url, headers=headers, json=payload)
                
                if self.DEBUG:
                    print(f'Estado de Respuesta API: {response.status_code}')
                    print(f'Texto de Respuesta API: {response.text}')

                # Verifico si la respuesta es exitosa
                if response.status_code in [200, 201]:
                    return True
                else:
                    if self.DEBUG:
                        print(f'Estado de Error API: {response.status_code}')
                    
                    # Espero antes de reintentar con retroceso exponencial
                    wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                    time.sleep(wait_time)
                    
            except Exception as e:
                if self.DEBUG:
                    print(f"Error al enviar datos a la API (intento {attempt+1}/{self.RETRIES}): {e}")
                
                # Espero antes de reintentar con retroceso exponencial
                wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                time.sleep(wait_time)
        
        # Todos los reintentos fallaron
        return False
        
    def upload(self, data, method='POST'):
        """
        Subo datos a la API, manteniendo compatibilidad con la interfaz antigua de API.
        
        Args:
            data: Datos para subir
            method: Método HTTP a usar (por defecto: POST)
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        return self.send_to_api(data)