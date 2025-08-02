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
# Description: Archivo de ejemplo de configuración de entorno para el proyecto.
#              Copia este archivo a env.py y actualiza los valores.
#
# Dependencies: MicroPython
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


# Modo de depuración (True/False)
DEBUG = False

# Configuración WiFi
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"
WIFI_COUNTRY = "ES"  # Código de país (ES para España)

# Redes WiFi alternativas para conectarme si la principal no está disponible
# Formato: lista de diccionarios con ssid y contraseña
WIFI_ALTERNATIVES = [
    {
        "ssid": "alternative_wifi_1",
        "password": "alternative_password_1"
    },
    {
        "ssid": "alternative_wifi_2",
        "password": "alternative_password_2"
    }
]

# ID del dispositivo (utilizado para la API e identificación)
DEVICE_ID = 1

# Configuración de la API
UPLOAD_API = True  # Lo configuro a False para desactivar las subidas a la API
API_URL = "https://api.example.com"  # URL base de la API
API_PATH = "/hardware/v1/solarcharge/store"  # Ruta al endpoint de la API
API_TOKEN = "your_api_token"  # Token de autenticación para la API

# Configuración de Home Assistant
UPLOAD_HOME_ASSISTANT = False  # Lo configuro a False para desactivar las subidas a Home Assistant
HOME_ASSISTANT_URL = "http://homeassistant.local:8123"  # URL de Home Assistant
HOME_ASSISTANT_TOKEN = "your_long_lived_access_token"  # Token de acceso de larga duración

# Configuración de la conexión serial
SERIAL_TX_PIN = 0  # Número de pin GPIO para TX (UART0 TX es GPIO0)
SERIAL_RX_PIN = 1  # Número de pin GPIO para RX (UART0 RX es GPIO1)

# Configuración del tiempo de espera
SLEEP_TIME = 60  # Tiempo de espera entre lecturas en segundos

# Configuración de batería externa (opcional)
# Si tengo una batería externa conectada a un pin ADC
# BATTERY_ADC_PIN = 26  # Número de pin ADC para monitoreo de batería
# BATTERY_MIN_VOLTAGE = 2.5  # Voltaje mínimo de la batería
# BATTERY_MAX_VOLTAGE = 4.2  # Voltaje máximo de la batería