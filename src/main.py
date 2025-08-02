#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      public@raupulus.dev
# @web        https://raupulus.dev
# @gitlab     https://gitlab.com/raupulus
# @github     https://github.com/raupulus
# @twitter    https://twitter.com/raupulus
# @telegram   https://t.me/raupulus_diffusion
#
# Create Date: 2025
# Project Name: Raspberry Pi Pico Monitor Renogy Rover Li Solar Controller
# Description: Aplicación principal para monitorizar un controlador solar Renogy Rover Li
#              usando una Raspberry Pi Pico con MicroPython. Leo datos del
#              controlador y los subo a una API y opcionalmente a Home Assistant.
#
# Dependencies: MicroPython, urequests, ujson, ntptime
#
# Revision 0.02 - Adaptado para Raspberry Pi Pico con MicroPython
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

# Guía de estilos aplicada: PEP8

#######################################
# #        Importo Librerías        # #
#######################################
from Models.RenogyRoverLi import RenogyRoverLi
from Models.Api import Api
from Models.HomeAssistantConnection import HomeAssistantConnection
from Models.RpiPico import RpiPico
import time
import machine
import ntptime
import gc

# Intento importar variables de entorno desde env.py
try:
    import env
except ImportError:
    print("Advertencia: env.py no encontrado. Usando valores predeterminados.")
    # Valores predeterminados si env.py no se encuentra
    env = type('obj', (object,), {
        'DEBUG': False,
        'WIFI_SSID': None,
        'WIFI_PASSWORD': None,
        'WIFI_COUNTRY': 'ES',
        'WIFI_ALTERNATIVES': None,
        'DEVICE_ID': 1,
        'API_URL': None,
        'API_PATH': None,
        'API_TOKEN': None,
        'UPLOAD_API': False,
        'HOME_ASSISTANT_URL': None,
        'HOME_ASSISTANT_TOKEN': None,
        'UPLOAD_HOME_ASSISTANT': False,
        'SERIAL_TX_PIN': 0,
        'SERIAL_RX_PIN': 1,
        'SLEEP_TIME': 60,  # Sleep time in seconds
    })

#######################################
# #             Variables           # #
#######################################

# Modo de depuración
DEBUG = env.DEBUG if hasattr(env, 'DEBUG') else False

# Tiempo de espera entre lecturas (en segundos)
SLEEP_TIME = env.SLEEP_TIME if hasattr(env, 'SLEEP_TIME') else 60

# Pines para conexión serial
SERIAL_TX_PIN = env.SERIAL_TX_PIN if hasattr(env, 'SERIAL_TX_PIN') else 0
SERIAL_RX_PIN = env.SERIAL_RX_PIN if hasattr(env, 'SERIAL_RX_PIN') else 1

# Configuración para subida a la API
UPLOAD_API = env.UPLOAD_API if hasattr(env, 'UPLOAD_API') else False
API_URL = env.API_URL if hasattr(env, 'API_URL') else None
API_PATH = env.API_PATH if hasattr(env, 'API_PATH') else None
API_TOKEN = env.API_TOKEN if hasattr(env, 'API_TOKEN') else None

# Configuración para subida a Home Assistant
UPLOAD_HOME_ASSISTANT = env.UPLOAD_HOME_ASSISTANT if hasattr(env, 'UPLOAD_HOME_ASSISTANT') else False
HOME_ASSISTANT_URL = env.HOME_ASSISTANT_URL if hasattr(env, 'HOME_ASSISTANT_URL') else None
HOME_ASSISTANT_TOKEN = env.HOME_ASSISTANT_TOKEN if hasattr(env, 'HOME_ASSISTANT_TOKEN') else None

# ID del dispositivo
DEVICE_ID = env.DEVICE_ID if hasattr(env, 'DEVICE_ID') else 1

#######################################
# #            FUNCIONES            # #
#######################################

def sync_time():
    """
    Sincronizo la hora del sistema con un servidor NTP.
    
    Returns:
        bool: True si fue exitoso, False en caso contrario
    """
    if DEBUG:
        print("Sincronizando hora con servidor NTP...")
    
    try:
        ntptime.settime()
        if DEBUG:
            print("Hora sincronizada correctamente")
        return True
    except Exception as e:
        if DEBUG:
            print(f"Error al sincronizar la hora: {e}")
        return False

def light_sleep(seconds):
    """
    Pongo el dispositivo en modo de sueño ligero durante el número de segundos especificado.
    Esto preserva la RAM pero mantiene los periféricos encendidos.
    
    Args:
        seconds (int): Número de segundos para dormir
    """
    if DEBUG:
        print(f"Entrando en modo de sueño ligero durante {seconds} segundos...")
    
    # El sueño ligero preserva la RAM pero mantiene los periféricos encendidos
    machine.lightsleep(seconds * 1000)  # Convierto a milisegundos

def collect_garbage():
    """
    Ejecuto la recolección de basura para liberar memoria.
    """
    if DEBUG:
        print("Ejecutando recolección de basura...")
        
    mem_before = gc.mem_free()
    gc.collect()
    mem_after = gc.mem_free()
    
    if DEBUG:
        print(f"Memoria liberada: {mem_after - mem_before} bytes")

def loop():
    """
    Bucle principal del programa que lee datos del controlador solar y los sube.
    """
    # Inicializo Raspberry Pi Pico
    rpi_pico = RpiPico(
        ssid=env.WIFI_SSID if hasattr(env, 'WIFI_SSID') else None,
        password=env.WIFI_PASSWORD if hasattr(env, 'WIFI_PASSWORD') else None,
        debug=DEBUG,
        country=env.WIFI_COUNTRY if hasattr(env, 'WIFI_COUNTRY') else 'ES',
        alternatives_ap=env.WIFI_ALTERNATIVES if hasattr(env, 'WIFI_ALTERNATIVES') else None
    )
    
    # Enciendo el LED para indicar que el programa está ejecutándose
    rpi_pico.led_on()
    
    # Sincronizo la hora si el WiFi está conectado
    if rpi_pico.wifi_is_connected():
        sync_time()
    
    # Inicializo la conexión a la API si está habilitada
    api = None
    if UPLOAD_API and API_URL and API_PATH and API_TOKEN:
        api = Api(
            controller=rpi_pico,
            url=API_URL,
            path=API_PATH,
            token=API_TOKEN,
            device_id=DEVICE_ID,
            debug=DEBUG
        )
    
    # Inicializo la conexión a Home Assistant si está habilitada
    home_assistant = None
    if UPLOAD_HOME_ASSISTANT and HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN:
        home_assistant = HomeAssistantConnection(
            controller=rpi_pico,
            url=HOME_ASSISTANT_URL,
            token=HOME_ASSISTANT_TOKEN,
            debug=DEBUG
        )
    
    # Inicializo el controlador solar
    solar_controller = RenogyRoverLi(
        device_id=DEVICE_ID,
        tx_pin=SERIAL_TX_PIN,
        rx_pin=SERIAL_RX_PIN,
        debug=DEBUG
    )
    
    while True:
        try:
            if DEBUG:
                print("Iniciando ciclo de recolección de datos...")
            
            # Registro el tiempo de inicio
            start_time = time.time()
            
            # Leo datos del controlador solar
            datas = solar_controller.get_all_datas()
            info = solar_controller.get_all_controller_info_datas()
            historical_today = solar_controller.get_today_historical_info_datas()
            historical = solar_controller.get_historical_info_datas()
            
            # Combino todos los datos
            # Uso dict.update() en lugar de ** unpacking para compatibilidad con MicroPython
            params = {}
            params.update(datas)
            params.update(info)
            params.update(historical_today)
            params.update(historical)
            
            if DEBUG:
                print('Datos recolectados del controlador solar')
            
            # Subo a la API si está habilitada
            if api and UPLOAD_API:
                if DEBUG:
                    print("Subiendo datos a la API...")
                
                success = api.send_to_api(params)
                
                if DEBUG:
                    if success:
                        print("Datos subidos a la API correctamente")
                    else:
                        print("Error al subir datos a la API")
            
            # Subo a Home Assistant si está habilitado
            if home_assistant and UPLOAD_HOME_ASSISTANT:
                if DEBUG:
                    print("Subiendo datos a Home Assistant...")
                
                # Primero verifico si Home Assistant es accesible
                if home_assistant.check_connection():
                    # Actualizo datos del controlador solar
                    success = home_assistant.update_solar_controller_data(params)
                    
                    # Actualizo sensores del microcontrolador
                    home_assistant.update_microcontroller_sensors()
                    
                    if DEBUG:
                        if success:
                            print("Datos subidos a Home Assistant correctamente")
                        else:
                            print("Error al subir datos a Home Assistant")
                else:
                    if DEBUG:
                        print("Home Assistant no es accesible")
            
            # Calculo el tiempo de ejecución
            end_time = time.time()
            execution_time = end_time - start_time
            
            if DEBUG:
                print(f"Tiempo de ejecución: {execution_time:.2f} segundos")
            
            # Ejecuto la recolección de basura
            collect_garbage()
            
            # Calculo el tiempo de espera restante
            sleep_time = max(1, SLEEP_TIME - execution_time)
            
            # Parpadeo el LED para indicar un ciclo exitoso
            rpi_pico.led_off()
            time.sleep(0.2)
            rpi_pico.led_on()
            time.sleep(0.2)
            rpi_pico.led_off()
            
            # Uso sueño ligero para preservar la conexión WiFi
            light_sleep(int(sleep_time))
            
            # Enciendo el LED nuevamente al despertar
            rpi_pico.led_on()
            
        except Exception as e:
            if DEBUG:
                print(f"Error en el bucle principal: {e}")
                print(f"Tipo de excepción: {type(e).__name__}")
                import sys
                # Imprimo el traceback de la excepción si está disponible
                if hasattr(sys, 'print_exception'):
                    sys.print_exception(e)
            
            # Parpadeo el LED rápidamente para indicar error
            for _ in range(5):
                rpi_pico.led_on()
                time.sleep(0.1)
                rpi_pico.led_off()
                time.sleep(0.1)
            
            # Calculo el tiempo de ejecución hasta este punto
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Calculo el tiempo de espera restante - asegurándome de respetar SLEEP_TIME
            sleep_time = max(1, SLEEP_TIME - execution_time)
            
            if DEBUG:
                print(f"Ocurrió un error, durmiendo durante {sleep_time} segundos antes del próximo ciclo")
            
            # Uso sueño ligero para preservar la conexión WiFi, incluso después de errores
            light_sleep(int(sleep_time))

def main():
    """
    Punto de entrada principal de la aplicación.
    """
    print('Iniciando Aplicación de Monitoreo Renogy Rover Li')
    
    # Espero a que el hardware se inicialice
    time.sleep(2)
    
    try:
        loop()
    except Exception as e:
        print(f'Error crítico en la aplicación: {e}')
        time.sleep(10)
        # Reinicio el dispositivo en caso de error crítico
        machine.reset()

if __name__ == "__main__":
    main()