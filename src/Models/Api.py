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
# Description: Cliente HTTP REST para envío y consulta de telemetría hacia la API V2
#              (módulo /energy/solar-readings) en MicroPython para Raspberry Pi Pico.
#
# Dependencies: MicroPython, urequests, ujson, gc, time
#
# Revision 0.03 - Adaptado a Contrato API V2 (/api/v2/energy/solar-readings)
# Additional Comments: Soporte para envelope ApiResponseTrait, hardware_device_info y cierre seguro de sockets
#
# @copyright  Copyright © 2022/2026 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt
#
# Copyright (C) 2022/2026  Raúl Caro Pastorino
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
DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_TIMEOUT = 30
DEFAULT_API_PATH = "/api/v2/energy/solar-readings"


class Api:
    """
    Cliente HTTP REST para interactuar con la API V2 (/energy/solar-readings).
    Implementa reintentos con retroceso exponencial, inyección de hardware_device_info,
    mapeo nativo de registros Renogy Rover Li y liberación garantizada de sockets TCP.

    Args:
        controller: Objeto RpiPico que representa el hardware del microcontrolador.
        url: URL base de la API (ej. 'https://api.example.com').
        path: Ruta al endpoint (por defecto '/api/v2/energy/solar-readings').
        token: Token de autenticación Bearer (Sanctum) con ability 'energy:write'.
        device_id: Identificador del dispositivo medidor (hardware_device_id).
        retries: Número de reintentos en solicitudes fallidas.
        backoff_factor: Factor de retroceso para reintentos.
        timeout: Tiempo de espera en segundos para las solicitudes.
        debug: Booleano para activar mensajes de depuración por consola.
    """

    def __init__(self, controller, url, path=DEFAULT_API_PATH, token="", device_id=1,
                 retries=DEFAULT_RETRIES, backoff_factor=DEFAULT_BACKOFF_FACTOR,
                 timeout=DEFAULT_TIMEOUT, debug=False):
        self.URL = url
        self.TOKEN = token
        self.DEVICE_ID = device_id
        self.URL_PATH = path if path else DEFAULT_API_PATH
        self.CONTROLLER = controller
        self.RETRIES = retries
        self.BACKOFF_FACTOR = backoff_factor
        self.TIMEOUT = timeout
        self.DEBUG = debug

    def _build_url(self, path=None):
        """
        Construye y normaliza la URL completa combinando URL base y path sin duplicar segmentos.
        """
        endpoint = path if path is not None else self.URL_PATH
        base = self.URL.rstrip('/') if self.URL else ''
        clean_endpoint = endpoint.lstrip('/')

        # Previene duplicar /api si base ya termina en /api y endpoint empieza por api/
        if base.endswith('/api') and clean_endpoint.startswith('api/'):
            clean_endpoint = clean_endpoint[4:]
        elif base.endswith('/api/v2') and clean_endpoint.startswith('api/v2/'):
            clean_endpoint = clean_endpoint[7:]

        return f"{base}/{clean_endpoint}"

    def _get_hardware_device_info(self):
        """
        Construye la información de salud del microcontrolador según el contrato API V2.
        Campos: temp, voltage, battery_level, cpu, disk, ram, uptime, ip_local, extra.
        """
        info = {
            "temp": None,
            "voltage": None,
            "battery_level": None,
            "cpu": None,
            "disk": None,
            "ram": None,
            "uptime": None,
            "ip_local": None,
            "extra": {}
        }

        # Temperatura interna de CPU de la Pico
        try:
            if hasattr(self.CONTROLLER, 'get_cpu_temperature'):
                info["temp"] = self.CONTROLLER.get_cpu_temperature()
        except Exception:
            pass

        # Uptime en segundos desde el arranque del microcontrolador
        try:
            info["uptime"] = time.ticks_ms() // 1000
        except Exception:
            pass

        # Porcentaje de memoria RAM ocupada en MicroPython
        try:
            free = gc.mem_free()
            alloc = gc.mem_alloc()
            total = free + alloc
            if total > 0:
                info["ram"] = round((alloc / total) * 100, 1)
        except Exception:
            pass

        # Batería externa conectada a pin ADC (si estuviera configurada)
        try:
            if hasattr(self.CONTROLLER, 'external_battery') and self.CONTROLLER.external_battery:
                self.CONTROLLER.read_external_battery()
                info["voltage"] = round(float(self.CONTROLLER.external_battery.get("voltage_current", 0.0)), 2)
                pct = self.CONTROLLER.external_battery.get("voltage_percentage")
                if pct is not None:
                    info["battery_level"] = int(round(float(pct)))
        except Exception:
            pass

        # Conectividad de red e IP local
        try:
            if hasattr(self.CONTROLLER, 'wifi_is_connected') and self.CONTROLLER.wifi_is_connected():
                if hasattr(self.CONTROLLER, 'get_wireless_ip'):
                    info["ip_local"] = self.CONTROLLER.get_wireless_ip()
                if hasattr(self.CONTROLLER, 'get_wireless_rssi'):
                    info["extra"]["wifi_rssi"] = self.CONTROLLER.get_wireless_rssi()
                if hasattr(self.CONTROLLER, 'get_wireless_ssid'):
                    info["extra"]["wifi_ssid"] = self.CONTROLLER.get_wireless_ssid()
        except Exception:
            pass

        return info

    def _build_solar_reading_payload(self, data):
        """
        Construye el cuerpo de la petición para POST /energy/solar-readings
        traduciendo los registros del modelo RenogyRoverLi a los nombres oficiales del contrato V2.
        """
        payload = {
            "hardware_device_id": self.DEVICE_ID,
            "hardware": data.get("hardware"),
            "version": data.get("version"),
            "serial_number": data.get("serial_number"),
            "battery_type": data.get("battery_type"),
            "battery_voltage": data.get("battery_voltage"),
            "battery_current": data.get("battery_current"),
            "battery_power": data.get("battery_power"),
            "battery_percentage": data.get("battery_percentage"),
            "battery_temperature": data.get("battery_temperature"),
            "temperature": data.get("controller_temperature") if "controller_temperature" in data else data.get("temperature"),
            "voltage": data.get("solar_voltage") if "solar_voltage" in data else data.get("voltage"),
            "amperage": data.get("solar_current") if "solar_current" in data else data.get("amperage"),
            "power": data.get("solar_power") if "solar_power" in data else data.get("power"),
            "charging_status": data.get("charging_status"),
            "charging_status_label": data.get("charging_status_label"),
            "light_status": data.get("street_light_status") if "street_light_status" in data else data.get("light_status"),
            "light_brightness": data.get("street_light_brightness") if "street_light_brightness" in data else data.get("light_brightness"),
            "load_voltage": data.get("load_voltage"),
            "load_current": data.get("load_current"),
            "load_power": data.get("load_power"),
            "day_battery_voltage_min": data.get("today_battery_min_voltage") if "today_battery_min_voltage" in data else data.get("day_battery_voltage_min"),
            "day_battery_voltage_max": data.get("today_battery_max_voltage") if "today_battery_max_voltage" in data else data.get("day_battery_voltage_max"),
            "day_charging_current_max": data.get("today_max_charging_current") if "today_max_charging_current" in data else data.get("day_charging_current_max"),
            "day_discharging_current_max": data.get("today_max_discharging_current") if "today_max_discharging_current" in data else data.get("day_discharging_current_max"),
            "day_charging_power_max": data.get("today_max_charging_power") if "today_max_charging_power" in data else data.get("day_charging_power_max"),
            "day_discharging_power_max": data.get("today_max_discharging_power") if "today_max_discharging_power" in data else data.get("day_discharging_power_max"),
            "day_charging_amp_hours": data.get("today_charging_amp_hours") if "today_charging_amp_hours" in data else data.get("day_charging_amp_hours"),
            "day_discharging_amp_hours": data.get("today_discharging_amp_hours") if "today_discharging_amp_hours" in data else data.get("day_discharging_amp_hours"),
            "day_power_generation_wh": data.get("today_power_generation") if "today_power_generation" in data else data.get("day_power_generation_wh"),
            "day_power_consumption_wh": data.get("today_power_consumption") if "today_power_consumption" in data else data.get("day_power_consumption_wh"),
            "total_operating_days": data.get("historical_total_days_operating") if "historical_total_days_operating" in data else data.get("total_operating_days"),
            "total_battery_over_discharges": data.get("historical_total_number_battery_over_discharges") if "historical_total_number_battery_over_discharges" in data else data.get("total_battery_over_discharges"),
            "total_battery_full_charges": data.get("historical_total_number_battery_full_charges") if "historical_total_number_battery_full_charges" in data else data.get("total_battery_full_charges"),
            "total_charging_amp_hours": data.get("historical_total_charging_amp_hours") if "historical_total_charging_amp_hours" in data else data.get("total_charging_amp_hours"),
            "total_discharging_amp_hours": data.get("historical_total_discharging_amp_hours") if "historical_total_discharging_amp_hours" in data else data.get("total_discharging_amp_hours"),
            "total_power_generation_wh": data.get("historical_cumulative_power_generation") if "historical_cumulative_power_generation" in data else data.get("total_power_generation_wh"),
            "total_power_consumption_wh": data.get("historical_cumulative_power_consumption") if "historical_cumulative_power_consumption" in data else data.get("total_power_consumption_wh"),
            "system_voltage": data.get("system_voltage_current") if "system_voltage_current" in data else data.get("system_voltage"),
            "system_intensity": data.get("system_intensity_current") if "system_intensity_current" in data else data.get("system_intensity"),
            "nominal_battery_capacity": data.get("nominal_battery_capacity"),
            "hardware_device_info": self._get_hardware_device_info()
        }

        return payload

    def send_to_api(self, data=None) -> bool:
        """
        Envía telemetría solar a la API V2 (POST /energy/solar-readings) con reintentos y
        liberación estricta de sockets TCP.

        Args:
            data: Diccionario con lecturas del controlador solar.

        Returns:
            bool: True si la petición fue exitosa (200 o 201), False en caso contrario.
        """
        if data is None:
            data = {}

        url = self._build_url()
        headers = {
            "Authorization": f"Bearer {self.TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = self._build_solar_reading_payload(data)

        for attempt in range(self.RETRIES):
            response = None
            try:
                if self.DEBUG:
                    print(f"Enviando telemetría a API V2 (intento {attempt + 1}/{self.RETRIES})")
                    print(f"URL: {url}")

                response = urequests.post(url, headers=headers, json=payload)

                if self.DEBUG:
                    print(f"Estado respuesta API: {response.status_code}")

                # Éxito: 200 o 201
                if response.status_code in (200, 201):
                    try:
                        res_json = ujson.loads(response.text)
                        if self.DEBUG:
                            print(f"Respuesta API V2: {res_json.get('message', 'OK')}")
                            warnings = res_json.get("warnings")
                            if warnings:
                                print(f"Advertencias reportadas por el servidor: {warnings}")
                    except Exception:
                        pass
                    return True

                # Errores HTTP conocidos (401, 403, 422, 429...)
                if self.DEBUG:
                    print(f"Error en API V2 (HTTP {response.status_code}): {response.text}")

                # Si es un error definitivo de credenciales o validación, reintentar no cambiará el resultado
                if response.status_code in (401, 403, 422):
                    return False

            except Exception as e:
                if self.DEBUG:
                    print(f"Excepción de conexión al enviar a API (intento {attempt + 1}/{self.RETRIES}): {e}")

            finally:
                # Cierre imperativo de socket para prevenir fuga de memoria (OSError: ENOMEM)
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        pass
                gc.collect()

            # Espera con retroceso exponencial antes de reintentar
            wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
            time.sleep(wait_time)

        return False

    def get_data_from_api(self, path=None):
        """
        Recupera lecturas o datos desde la API V2 con soporte para reintentos.

        Args:
            path: Ruta relativa opcional. Si no se especifica, usa self.URL_PATH.

        Returns:
            dict | False: Objeto decodificado del envelope o False si falló.
        """
        url = self._build_url(path)
        headers = {
            "Authorization": f"Bearer {self.TOKEN}",
            "Accept": "application/json"
        }

        for attempt in range(self.RETRIES):
            response = None
            try:
                response = urequests.get(url, headers=headers)
                if response.status_code in (200, 201):
                    data = ujson.loads(response.text)
                    return data
                elif self.DEBUG:
                    print(f"Error al obtener datos API (HTTP {response.status_code}): {response.text}")
            except Exception as e:
                if self.DEBUG:
                    print(f"Excepción al leer de la API (intento {attempt + 1}/{self.RETRIES}): {e}")
            finally:
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        pass
                gc.collect()

            wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
            time.sleep(wait_time)

        return False

    def upload(self, data, method='POST'):
        """
        Alias retrocompatible para send_to_api.
        """
        return self.send_to_api(data)
