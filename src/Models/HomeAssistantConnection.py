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
# Dependencies: MicroPython, urequests, ujson, gc, time
#
# Revision 0.02 - Optimización de tráfico HTTP mediante filtrado por delta y latido (heartbeat)
# Additional Comments: Reduce peticiones HTTP hasta un 85% sin alterar la estructura de entidades
#
# @copyright  Copyright © 2025/2026 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt
#
# Copyright (C) 2025/2026  Raúl Caro Pastorino
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
import gc

# Configuraciones predeterminadas
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.3
DEFAULT_TIMEOUT = 10
DEFAULT_HEARTBEAT_INTERVAL = 600  # Latido máximo para forzar actualización (10 min)
DEFAULT_STATIC_INTERVAL = 3600    # Intervalo de refresco para sensores estáticos (1 hora)

class HomeAssistantConnection:
    """
    Una clase para conectarme a Home Assistant y enviar datos de sensores.
    
    Esta clase me proporciona métodos para enviar datos a Home Assistant a través de su API REST.
    Incluye mecanismo de reintentos, manejo de errores y optimización por delta para
    minimizar peticiones HTTP y preservar la estabilidad de la conexión WiFi en MicroPython.
    
    Args:
        controller: El objeto controlador para la raspberry pi pico.
        url: La URL base de la instancia de Home Assistant (ej., "http://homeassistant.local:8123").
        token: El token de acceso de larga duración para Home Assistant.
        device_id: ID del dispositivo para identificación en Home Assistant.
        retries: Número de reintentos para solicitudes fallidas.
        backoff_factor: Factor de retroceso para reintentos.
        timeout: Tiempo de espera para solicitudes en segundos.
        debug: Bandera booleana opcional para modo de depuración.
        delta_filtering: Activa o desactiva el filtrado por variación para ahorrar peticiones HTTP.
        heartbeat_interval: Segundos máximos antes de forzar el reenvío de un sensor dinámico sin cambios.
        static_interval: Segundos máximos antes de forzar el reenvío de un sensor estático sin cambios.
    """
    
    # Claves consideradas estáticas o de configuración que rara vez o nunca cambian
    STATIC_KEYS = {
        "hardware",
        "version",
        "serial_number",
        "device_id",
        "battery_type",
        "nominal_battery_capacity",
        "system_voltage_current",
        "system_intensity_current"
    }

    # Umbrales mínimos de variación (deadbands) para considerar que un valor analógico cambió
    DEADBANDS = {
        # Voltajes (0.05 V)
        "battery_voltage": 0.05,
        "solar_voltage": 0.1,
        "load_voltage": 0.1,
        "today_battery_max_voltage": 0.05,
        "today_battery_min_voltage": 0.05,
        "system_voltage_current": 0.1,
        # Corrientes (0.05 A)
        "solar_current": 0.05,
        "load_current": 0.05,
        "battery_charging_current": 0.05,
        "battery_current": 0.05,
        "system_intensity_current": 0.1,
        "today_max_charging_current": 0.05,
        "today_max_discharging_current": 0.05,
        # Potencias (1.0 W)
        "solar_power": 1.0,
        "load_power": 1.0,
        "battery_power": 1.0,
        "today_max_charging_power": 1.0,
        "today_max_discharging_power": 1.0,
        # Temperaturas (0.5 °C)
        "battery_temperature": 0.5,
        "controller_temperature": 0.5,
        "microcontroller_temperature": 0.5,
        # Porcentajes (1.0 %)
        "battery_percentage": 1.0,
        "street_light_brightness": 1.0,
        "microcontroller_battery": 1.0,
        "wifi_signal_strength": 3.0,
    }

    def __init__(self, controller, url, token, device_id=1,
                 retries=DEFAULT_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR,
                 timeout=DEFAULT_TIMEOUT, debug=False,
                 delta_filtering=True, heartbeat_interval=DEFAULT_HEARTBEAT_INTERVAL,
                 static_interval=DEFAULT_STATIC_INTERVAL):
        self.URL = url.rstrip('/')  # Elimino la barra final si está presente
        self.TOKEN = token
        self.CONTROLLER = controller
        self.DEVICE_ID = device_id
        self.RETRIES = retries
        self.BACKOFF_FACTOR = backoff_factor
        self.TIMEOUT = timeout
        self.DEBUG = debug
        self.DELTA_FILTERING = delta_filtering
        self.HEARTBEAT_INTERVAL = heartbeat_interval
        self.STATIC_INTERVAL = static_interval
        
        # Punto final de la API para estados
        self.API_STATES_ENDPOINT = "/api/states/"
        
        # Almaceno la información del dispositivo para asegurar consistencia entre sensores
        self.device_info = None
        
        # Almaceno la última vez que se actualizó la entidad del dispositivo
        self.last_device_update = 0
        
        # Intervalo de actualización para la entidad del dispositivo (en segundos)
        self.device_update_interval = 3600
        
        # Caché de estados y marcas de tiempo enviadas para filtrado por delta
        self._last_sent_states = {}
        self._last_sent_times = {}
        
        # Caché de verificación de dispositivo y accesibilidad para ahorrar peticiones GET
        self.device_verified = False
        self._last_connection_check_time = 0
        self._last_connection_ok = False
        
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
            status["battery_percentage"] = self.CONTROLLER.external_battery.get("voltage_percentage")
            status["battery_voltage"] = self.CONTROLLER.external_battery.get("voltage_current")
        
        return status
    
    def check_connection(self):
        """
        Compruebo si Home Assistant es accesible.
        Cachea temporalmente el resultado positivo para evitar peticiones GET innecesarias en cada ciclo.
        
        Returns:
            bool: True si Home Assistant es accesible, False en caso contrario
        """
        current_time = time.time()
        # Si la conexión fue exitosa hace menos de 5 minutos, asumimos que sigue operativa para ahorrar la petición GET
        if self._last_connection_ok and (current_time - self._last_connection_check_time < 300):
            return True

        response = None
        try:
            url = f"{self.URL}/api/"
            headers = self._get_headers()
            
            response = urequests.get(url, headers=headers)
            
            if response.status_code == 200:
                if self.DEBUG:
                    print("Home Assistant es accesible")
                self._last_connection_check_time = current_time
                self._last_connection_ok = True
                return True
            else:
                if self.DEBUG:
                    print(f"Home Assistant devolvió código de estado: {response.status_code}")
                self._last_connection_ok = False
                return False
                
        except Exception as e:
            self._last_connection_ok = False
            self.device_verified = False
            if self.DEBUG:
                print(f"Error al conectar con Home Assistant: {e}")
            return False
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
            gc.collect()

    def _should_send_update(self, entity_id, key, value, current_time):
        """
        Determina si un sensor debe enviarse a Home Assistant en el ciclo actual.
        Aplica filtrado por delta y latidos periódicos (heartbeat) para minimizar peticiones HTTP.
        """
        if not self.DELTA_FILTERING:
            return True

        # Primera vez que se envía: debe subirse para inicializar la entidad en HA
        if entity_id not in self._last_sent_states:
            return True

        last_value = self._last_sent_states[entity_id]
        last_time = self._last_sent_times.get(entity_id, 0)

        # Determinar intervalo máximo según el tipo de sensor (estático vs dinámico)
        max_interval = self.STATIC_INTERVAL if key in self.STATIC_KEYS else self.HEARTBEAT_INTERVAL
        if (current_time - last_time) >= max_interval:
            return True

        # Comprobación de umbral de variación (deadband) para valores numéricos
        if key in self.DEADBANDS and isinstance(value, (int, float)) and isinstance(last_value, (int, float)):
            return abs(value - last_value) >= self.DEADBANDS[key]

        # Para valores discretos, cadenas, booleanos o listas serializadas
        return value != last_value

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
            response = None
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
                    print(f"Actualizando sensor {entity_id} (intento {attempt+1}/{self.RETRIES}): {state}")
                
                # Envío la petición POST
                response = urequests.post(url, headers=headers, json=payload)
                
                if self.DEBUG:
                    print(f"Estado de Respuesta de Home Assistant: {response.status_code}")
                
                # Compruebo si la respuesta es exitosa
                if response.status_code in [200, 201]:
                    # Guardamos el estado y timestamp en caché de éxito
                    self._last_sent_states[entity_id] = state
                    self._last_sent_times[entity_id] = time.time()
                    self._last_connection_ok = True
                    return True
                else:
                    if self.DEBUG:
                        print(f"Estado de Error de Home Assistant: {response.status_code}")
                        print(f"Texto de Respuesta: {response.text}")
                    
                    # Espero antes de reintentar con retroceso exponencial
                    wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                    time.sleep(wait_time)
                    
            except Exception as e:
                self._last_connection_ok = False
                self.device_verified = False
                if self.DEBUG:
                    print(f"Error al actualizar sensor (intento {attempt+1}/{self.RETRIES}): {e}")
                
                # Espero antes de reintentar con retroceso exponencial
                wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                time.sleep(wait_time)
            finally:
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        pass
                gc.collect()
        
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
        "battery_voltage": {"unit_of_measurement": "V", "device_class": "voltage", "state_class": "measurement"},
        "solar_voltage": {"unit_of_measurement": "V", "device_class": "voltage", "state_class": "measurement"},
        "load_voltage": {"unit_of_measurement": "V", "device_class": "voltage", "state_class": "measurement"},
        "today_battery_max_voltage": {"unit_of_measurement": "V", "device_class": "voltage", "state_class": "measurement"},
        "today_battery_min_voltage": {"unit_of_measurement": "V", "device_class": "voltage", "state_class": "measurement"},
        "system_voltage_current": {"unit_of_measurement": "V", "device_class": "voltage", "state_class": "measurement"},
        
        # Sensores de corriente
        "solar_current": {"unit_of_measurement": "A", "device_class": "current", "state_class": "measurement"},
        "load_current": {"unit_of_measurement": "A", "device_class": "current", "state_class": "measurement"},
        "battery_charging_current": {"unit_of_measurement": "A", "device_class": "current", "state_class": "measurement"},
        "battery_current": {"unit_of_measurement": "A", "device_class": "current", "state_class": "measurement"},
        "system_intensity_current": {"unit_of_measurement": "A", "device_class": "current", "state_class": "measurement"},
        "today_max_charging_current": {"unit_of_measurement": "A", "device_class": "current", "state_class": "measurement"},
        "today_max_discharging_current": {"unit_of_measurement": "A", "device_class": "current", "state_class": "measurement"},
        
        # Sensores de potencia
        "solar_power": {"unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
        "load_power": {"unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
        "battery_power": {"unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
        "today_max_charging_power": {"unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
        "today_max_discharging_power": {"unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"},
        
        # Sensores de energía
        "today_power_generation": {"unit_of_measurement": "Wh", "device_class": "energy", "state_class": "total_increasing"},
        "today_power_consumption": {"unit_of_measurement": "Wh", "device_class": "energy", "state_class": "total_increasing"},
        "historical_cumulative_power_generation": {"unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
        "historical_cumulative_power_consumption": {"unit_of_measurement": "kWh", "device_class": "energy", "state_class": "total_increasing"},
        
        # Sensores de temperatura
        "battery_temperature": {"unit_of_measurement": "C", "device_class": "temperature", "state_class": "measurement"},
        "controller_temperature": {"unit_of_measurement": "C", "device_class": "temperature", "state_class": "measurement"},
        
        # Sensores de porcentaje
        "battery_percentage": {"unit_of_measurement": "%", "device_class": "battery", "state_class": "measurement"},
        "street_light_brightness": {"unit_of_measurement": "%", "device_class": "illuminance", "state_class": "measurement"},
        
        # Sensores de amperios-hora
        "today_charging_amp_hours": {"unit_of_measurement": "Ah", "device_class": None, "state_class": "total_increasing"},
        "today_discharging_amp_hours": {"unit_of_measurement": "Ah", "device_class": None, "state_class": "total_increasing"},
        "historical_total_charging_amp_hours": {"unit_of_measurement": "Ah", "device_class": None, "state_class": "total"},
        "historical_total_discharging_amp_hours": {"unit_of_measurement": "Ah", "device_class": None, "state_class": "total"},
        "nominal_battery_capacity": {"unit_of_measurement": "Ah", "device_class": None, "state_class": "measurement"},
        
        # Sensores de estado
        "charging_status": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "charging_status_label": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "load_switch_status": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "fault_code": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "faults": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "street_light_status": {"unit_of_measurement": None, "device_class": "binary_sensor", "state_class": None},
        
        # Sensores de conteo
        "historical_total_days_operating": {"unit_of_measurement": "days", "device_class": None, "state_class": "total"},
        "historical_total_number_battery_over_discharges": {"unit_of_measurement": None, "device_class": None, "state_class": "total"},
        "historical_total_number_battery_full_charges": {"unit_of_measurement": None, "device_class": None, "state_class": "total"},
        
        # Otros sensores
        "device_id": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "hardware": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "version": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "serial_number": {"unit_of_measurement": None, "device_class": None, "state_class": None},
        "battery_type": {"unit_of_measurement": None, "device_class": None, "state_class": None}
    }
    
    def update_solar_controller_data(self, data):
        """
        Actualizo los sensores del controlador solar en Home Assistant con filtrado por variación.
        
        Aplica filtrado por delta y latidos periódicos para reducir drásticamente las peticiones HTTP
        sin romper los widgets ni las entidades individuales en Home Assistant.
        
        Args:
            data (dict): Diccionario con datos del controlador solar
            
        Returns:
            bool: True si la actualización fue exitosa o no se requirió enviar cambios.
        """
        if not data:
            if self.DEBUG:
                print("No se proporcionaron datos para actualizar los sensores del controlador solar")
            return False
        
        microcontroller_status = self._get_microcontroller_status()
        current_time = time.time()
        
        common_attributes = {
            "microcontroller": microcontroller_status,
            "last_update": current_time
        }
        
        device_id = data.get('device_id', 'unknown')
        self.device_info = {
            "identifiers": [f"renogy_rover_li_{device_id}"],
            "name": f"Controlador Solar Renogy Rover Li {device_id}",
            "manufacturer": "Renogy",
            "model": "Rover Li",
            "sw_version": data.get('version', 'unknown'),
            "suggested_area": "Exterior"
        }
        
        attempted = 0
        success_count = 0
        
        # Actualizo cada punto de datos como un sensor separado si ha variado
        for key, value in data.items():
            if value is None:
                continue

            # Convertir listas (como faults) a formato string legible para Home Assistant
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value) if value else "none"
                
            entity_id = f"sensor.solar_{key.lower().replace(' ', '_')}"
            
            # Filtrado por delta / heartbeat para ahorrar peticiones HTTP
            if not self._should_send_update(entity_id, key, value, current_time):
                continue
                
            attributes = dict(common_attributes)
            replaced_key = key.replace('_', ' ')
            
            if replaced_key.lower().startswith('solar '):
                attributes["friendly_name"] = self._capitalize_words(replaced_key)
            else:
                attributes["friendly_name"] = f"Solar {self._capitalize_words(replaced_key)}"
            
            if key in self.SENSOR_METADATA:
                metadata = self.SENSOR_METADATA[key]
                if metadata["unit_of_measurement"]:
                    attributes["unit_of_measurement"] = metadata["unit_of_measurement"]
                if metadata["device_class"]:
                    attributes["device_class"] = metadata["device_class"]
                if metadata["state_class"]:
                    attributes["state_class"] = metadata["state_class"]
            
            attributes["device"] = self.device_info
            attributes["unique_id"] = f"{self.device_info['identifiers'][0]}_{key.lower().replace(' ', '_')}"
            
            attempted += 1
            if self.update_sensor(entity_id, value, attributes):
                success_count += 1

        if self.DEBUG:
            print(f"Home Assistant: {attempted} sensores requerían actualización ({success_count} exitosos, {len(data) - attempted} omitidos por delta)")

        # Si no hubo sensores pendientes de enviar porque ninguno varió, el estado es exitoso (en sincronía)
        if attempted == 0:
            return True
        
        return success_count > 0
    
    def verify_device_exists(self):
        """
        Verifica si el dispositivo existe en Home Assistant.
        Una vez verificado con éxito, cachea el resultado para no realizar un GET cada ciclo.
        
        Returns:
            bool: True si el dispositivo existe, False en caso contrario
        """
        if self.device_verified:
            return True

        if not self.device_info:
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
            
        device_identifier = self.device_info["identifiers"][0]
        entity_id = f"sensor.{device_identifier}_device"
        
        response = None
        try:
            url = f"{self.URL}{self.API_STATES_ENDPOINT}{entity_id}"
            headers = self._get_headers()
            
            response = urequests.get(url, headers=headers)
            
            if self.DEBUG:
                print(f"Verificando si existe el dispositivo: {entity_id}")
                print(f"Estado de respuesta: {response.status_code}")
            
            if response.status_code == 200:
                self.device_verified = True
                return True
            return False
                
        except Exception as e:
            self.device_verified = False
            if self.DEBUG:
                print(f"Error al verificar si existe el dispositivo: {e}")
            return False
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
            gc.collect()
    
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
            
        current_time = time.time()
        time_since_last_update = current_time - self.last_device_update
        
        if time_since_last_update < self.device_update_interval and self.last_device_update > 0:
            if self.DEBUG:
                print(f"No se actualiza la entidad del dispositivo. Próxima actualización en {self.device_update_interval - time_since_last_update} segundos")
            return True
            
        device_identifier = self.device_info["identifiers"][0]
        entity_id = f"sensor.{device_identifier}_device"
        
        attributes = {
            "friendly_name": self.device_info["name"],
            "device_class": "timestamp",
            "device": self.device_info,
            "unique_id": f"{self.device_info['identifiers'][0]}_device",
            "icon": "mdi:solar-power",
            "last_update_interval": self.device_update_interval
        }
        
        state = current_time
        result = self.update_sensor(entity_id, state, attributes)
        
        if result:
            self.last_device_update = current_time
            if self.DEBUG:
                print(f"Entidad del dispositivo actualizada. Próxima actualización en {self.device_update_interval} segundos")
        
        return result
    
    def update_microcontroller_sensors(self):
        """
        Actualizo los sensores para el estado del microcontrolador en Home Assistant con filtrado por delta.
        
        Returns:
            bool: True si la actualización fue exitosa o no se requirió enviar cambios.
        """
        status = self._get_microcontroller_status()
        current_time = time.time()
        
        if not self.device_info:
            default_device_id = 1
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
        
        attempted = 0
        success_count = 0
        
        # Sensor de temperatura
        if status.get("temperature") is not None:
            entity_id = "sensor.microcontroller_temperature"
            if self._should_send_update(entity_id, "microcontroller_temperature", status["temperature"], current_time):
                attrs = {
                    "last_update": current_time,
                    "device_class": "temperature",
                    "unit_of_measurement": "C",
                    "state_class": "measurement",
                    "friendly_name": "Temperatura del Microcontrolador",
                    "device": self.device_info,
                    "unique_id": f"{self.device_info['identifiers'][0]}_microcontroller_temperature"
                }
                attempted += 1
                if self.update_sensor(entity_id, status["temperature"], attrs):
                    success_count += 1
        
        # Sensor de estado WiFi
        entity_id = "binary_sensor.microcontroller_wifi"
        wifi_state = "on" if status.get("wifi_connected") else "off"
        if self._should_send_update(entity_id, "microcontroller_wifi", wifi_state, current_time):
            attrs = {
                "last_update": current_time,
                "friendly_name": "Estado WiFi del Microcontrolador",
                "device": self.device_info,
                "unique_id": f"{self.device_info['identifiers'][0]}_microcontroller_wifi"
            }
            attempted += 1
            if self.update_sensor(entity_id, wifi_state, attrs):
                success_count += 1
        
        # Sensor de intensidad de señal WiFi si está disponible
        if status.get("wifi_connected") and status.get("wifi_signal_strength") is not None:
            entity_id = "sensor.microcontroller_wifi_signal"
            if self._should_send_update(entity_id, "wifi_signal_strength", status["wifi_signal_strength"], current_time):
                attrs = {
                    "last_update": current_time,
                    "unit_of_measurement": "dBm",
                    "device_class": "signal_strength",
                    "state_class": "measurement",
                    "friendly_name": "Senal WiFi del Microcontrolador",
                    "device": self.device_info,
                    "unique_id": f"{self.device_info['identifiers'][0]}_microcontroller_wifi_signal"
                }
                attempted += 1
                if self.update_sensor(entity_id, status["wifi_signal_strength"], attrs):
                    success_count += 1
        
        # Sensor de batería si está disponible
        if status.get("battery_percentage") is not None:
            entity_id = "sensor.microcontroller_battery"
            if self._should_send_update(entity_id, "microcontroller_battery", status["battery_percentage"], current_time):
                attrs = {
                    "last_update": current_time,
                    "unit_of_measurement": "%",
                    "device_class": "battery",
                    "state_class": "measurement",
                    "friendly_name": "Batería del Microcontrolador",
                    "device": self.device_info,
                    "unique_id": f"{self.device_info['identifiers'][0]}_microcontroller_battery"
                }
                attempted += 1
                if self.update_sensor(entity_id, status["battery_percentage"], attrs):
                    success_count += 1
        
        if attempted == 0:
            return True

        return success_count > 0
