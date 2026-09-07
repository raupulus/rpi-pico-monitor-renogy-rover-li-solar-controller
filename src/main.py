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
# Revision 0.03 - Soporte para optimización de tráfico HA por delta/latido y reconexión WiFi
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
        'WIFI_CONNECT_TIMEOUT': 15,
        'MAX_OFFLINE_CYCLES': 15,
        'DEVICE_ID': 1,
        'API_URL': None,
        'API_PATH': '/api/v2/energy/solar-readings',
        'API_TOKEN': None,
        'UPLOAD_API': False,
        'HOME_ASSISTANT_URL': None,
        'HOME_ASSISTANT_TOKEN': None,
        'UPLOAD_HOME_ASSISTANT': False,
        'HA_DELTA_FILTERING': True,
        'HA_HEARTBEAT_INTERVAL': 600,
        'HA_STATIC_INTERVAL': 3600,
        'SERIAL_TX_PIN': 0,
        'SERIAL_RX_PIN': 1,
        'SLEEP_TIME': 60,  # Sleep time in seconds
        'NTP_SYNC_INTERVAL': 86400,  # Sincronización NTP cada 24 horas
        'HISTORICAL_DATA_INTERVAL': 600,  # Refresco de históricos acumulados cada 10 minutos
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

# Parámetros de reconexión y tolerancia a fallos WiFi
WIFI_CONNECT_TIMEOUT = env.WIFI_CONNECT_TIMEOUT if hasattr(env, 'WIFI_CONNECT_TIMEOUT') else 15
MAX_OFFLINE_CYCLES = env.MAX_OFFLINE_CYCLES if hasattr(env, 'MAX_OFFLINE_CYCLES') else 15

# Intervalo de sincronización horaria NTP (por defecto 24 horas = 86400s)
NTP_SYNC_INTERVAL = env.NTP_SYNC_INTERVAL if hasattr(env, 'NTP_SYNC_INTERVAL') else 86400
last_ntp_sync = 0

# Intervalo de actualización de datos históricos acumulativos (por defecto 10 min = 600s)
HISTORICAL_DATA_INTERVAL = env.HISTORICAL_DATA_INTERVAL if hasattr(env, 'HISTORICAL_DATA_INTERVAL') else 600

# Configuración para subida a la API
UPLOAD_API = env.UPLOAD_API if hasattr(env, 'UPLOAD_API') else False
API_URL = env.API_URL if hasattr(env, 'API_URL') else None
API_PATH = env.API_PATH if hasattr(env, 'API_PATH') else '/api/v2/energy/solar-readings'
API_TOKEN = env.API_TOKEN if hasattr(env, 'API_TOKEN') else None

# Configuración para subida a Home Assistant
UPLOAD_HOME_ASSISTANT = env.UPLOAD_HOME_ASSISTANT if hasattr(env, 'UPLOAD_HOME_ASSISTANT') else False
HOME_ASSISTANT_URL = env.HOME_ASSISTANT_URL if hasattr(env, 'HOME_ASSISTANT_URL') else None
HOME_ASSISTANT_TOKEN = env.HOME_ASSISTANT_TOKEN if hasattr(env, 'HOME_ASSISTANT_TOKEN') else None
HA_DELTA_FILTERING = env.HA_DELTA_FILTERING if hasattr(env, 'HA_DELTA_FILTERING') else True
HA_HEARTBEAT_INTERVAL = env.HA_HEARTBEAT_INTERVAL if hasattr(env, 'HA_HEARTBEAT_INTERVAL') else 600
HA_STATIC_INTERVAL = env.HA_STATIC_INTERVAL if hasattr(env, 'HA_STATIC_INTERVAL') else 3600

# ID del dispositivo
DEVICE_ID = env.DEVICE_ID if hasattr(env, 'DEVICE_ID') else 1

#######################################
# #            FUNCIONES            # #
#######################################

def sync_time(force=False):
    """
    Sincronizo la hora del sistema con un servidor NTP una vez al día o al iniciar.
    
    Args:
        force (bool): Si es True, fuerza la sincronización ignorando el intervalo.

    Returns:
        bool: True si fue exitoso o no se requería sincronizar, False en caso de error.
    """
    global last_ntp_sync
    current_time = time.time()

    if not force and last_ntp_sync > 0 and (current_time - last_ntp_sync) < NTP_SYNC_INTERVAL:
        return True

    if DEBUG:
        print("Sincronizando hora con servidor NTP...")
    
    try:
        ntptime.settime()
        last_ntp_sync = time.time()
        if DEBUG:
            print("Hora sincronizada correctamente")
        return True
    except Exception as e:
        if DEBUG:
            print(f"Error al sincronizar la hora: {e}")
        return False

def sleep_pause(seconds):
    """
    Pauso la ejecución durante el número de segundos especificado.
    Uso una pausa simple en lugar de light_sleep debido a problemas de compatibilidad.
    Por algún motivo, la pausa simple no funciona correctamente en
    MicroPython con raspberry pi pico.
    
    Args:
        seconds (int): Número de segundos para pausar
    """
    if DEBUG:
        print(f"Pausando durante {seconds} segundos...")
    
    # Pauso en intervalos de 1 segundo para mantener la estabilidad del bucle
    for _ in range(seconds):
        time.sleep(1)

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
        alternatives_ap=env.WIFI_ALTERNATIVES if hasattr(env, 'WIFI_ALTERNATIVES') else None,
        led_power_pin=env.LED_POWER_PIN if hasattr(env, 'LED_POWER_PIN') else None,
        led_upload_pin=env.LED_UPLOAD_PIN if hasattr(env, 'LED_UPLOAD_PIN') else None,
        led_cycle_pin=env.LED_CYCLE_PIN if hasattr(env, 'LED_CYCLE_PIN') else None
    )
    
    # Configuro monitoreo de batería externa si está definida en el entorno
    if hasattr(env, 'BATTERY_ADC_PIN') and env.BATTERY_ADC_PIN is not None:
        min_v = env.BATTERY_MIN_VOLTAGE if hasattr(env, 'BATTERY_MIN_VOLTAGE') else 2.5
        max_v = env.BATTERY_MAX_VOLTAGE if hasattr(env, 'BATTERY_MAX_VOLTAGE') else 4.2
        rpi_pico.set_external_battery(env.BATTERY_ADC_PIN, min_v, max_v)

    # Enciendo el LED de encendido para indicar que el sistema está funcionando
    rpi_pico.led_power_on()
    
    # Sincronizo la hora al iniciar si el WiFi está conectado
    if (UPLOAD_API or UPLOAD_HOME_ASSISTANT) and rpi_pico.wifi_is_connected():
        sync_time(force=True)
    
    # Inicializo la API si está habilitada
    api = None
    if UPLOAD_API and API_URL and API_TOKEN:
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
            device_id=DEVICE_ID,
            debug=DEBUG,
            delta_filtering=HA_DELTA_FILTERING,
            heartbeat_interval=HA_HEARTBEAT_INTERVAL,
            static_interval=HA_STATIC_INTERVAL
        )
    
    # Inicializo el controlador solar
    solar_controller = RenogyRoverLi(
        device_id=DEVICE_ID,
        tx_pin=SERIAL_TX_PIN,
        rx_pin=SERIAL_RX_PIN,
        debug=DEBUG,
        historical_interval=HISTORICAL_DATA_INTERVAL
    )
    
    # Contador de ciclos consecutivos sin conectividad WiFi
    offline_cycles = 0

    while True:
        try:
            if DEBUG:
                print("Iniciando ciclo de recolección de datos...")
            
            # Verificación y reconexión WiFi activa si se requiere red
            if UPLOAD_API or UPLOAD_HOME_ASSISTANT:
                wifi_ok = rpi_pico.ensure_wifi_connected(timeout=WIFI_CONNECT_TIMEOUT)
                if not wifi_ok:
                    offline_cycles += 1
                    if DEBUG:
                        print(f"Aviso: Sin conexión WiFi (ciclo offline {offline_cycles}/{MAX_OFFLINE_CYCLES})")
                    
                    # Si persiste offline durante demasiados ciclos consecutivos (~15-25 min),
                    # reiniciamos el microcontrolador para limpiar el chip CYW43 y el stack de red
                    if offline_cycles >= MAX_OFFLINE_CYCLES:
                        print(f"Alcanzado el límite de {MAX_OFFLINE_CYCLES} ciclos consecutivos sin WiFi. Reiniciando microcontrolador por seguridad...")
                        time.sleep(2)
                        machine.reset()
                else:
                    if offline_cycles > 0:
                        if DEBUG:
                            print(f"WiFi restablecido tras {offline_cycles} ciclos offline.")
                        offline_cycles = 0

                    # Sincronizo la hora periódicamente (1 vez al día o si aún no se había sincronizado)
                    sync_time(force=False)

            # Enciendo el LED de ciclo para indicar que estoy leyendo datos
            rpi_pico.led_cycle_on()
            
            # Leo datos del controlador solar de forma optimizada por bloques
            params = solar_controller.get_all_datas_fast()
            
            # Apago el LED de ciclo una vez terminada la lectura
            rpi_pico.led_cycle_off()
            
            if DEBUG:
                print('Datos recolectados del controlador solar')
            
            # Subo a la API si está habilitada
            if api and UPLOAD_API:
                if not rpi_pico.wifi_is_connected():
                    if DEBUG:
                        print("Omitiendo subida a la API: sin conexión WiFi")
                else:
                    if DEBUG:
                        print("Subiendo datos a la API...")
                    
                    # Enciendo el LED de subida durante la comunicación con la API
                    rpi_pico.led_upload_on()
                    
                    success = api.send_to_api(params)
                    
                    # Apago el LED de subida después de la comunicación con la API
                    rpi_pico.led_upload_off()
                    
                    if DEBUG:
                        if success:
                            print("Datos subidos a la API correctamente")
                        else:
                            print("Error al subir datos a la API")
            
            # Subo a Home Assistant si está habilitado
            if home_assistant and UPLOAD_HOME_ASSISTANT:
                if not rpi_pico.wifi_is_connected():
                    if DEBUG:
                        print("Omitiendo subida a Home Assistant: sin conexión WiFi")
                else:
                    if DEBUG:
                        print("Subiendo datos a Home Assistant...")
                    
                    # Enciendo el LED de subida durante la comunicación con Home Assistant
                    rpi_pico.led_upload_on()
                    
                    # Primero verifico si Home Assistant es accesible (usa caché de 5 min)
                    if home_assistant.check_connection():
                        # Primero creo una entidad dedicada para el dispositivo (usa intervalo de 1h)
                        device_created = home_assistant.create_device_entity()
                        
                        # Verifico si el dispositivo existe en Home Assistant (usa caché)
                        device_exists = home_assistant.verify_device_exists()
                        
                        if DEBUG:
                            if device_exists:
                                print("El dispositivo 'Controlador Solar Renogy Rover Li' existe en Home Assistant")
                            else:
                                print("ADVERTENCIA: El dispositivo 'Controlador Solar Renogy Rover Li' NO existe en Home Assistant")
                                print("Intentando crear el dispositivo nuevamente...")
                                device_created = home_assistant.create_device_entity()
                                device_exists = home_assistant.verify_device_exists()
                                if not device_exists:
                                    print("ERROR: No se pudo crear el dispositivo en Home Assistant")
                        
                        # Solo actualizo los sensores si el dispositivo existe
                        if device_exists:
                            # Actualizo datos del controlador solar (filtrado por delta)
                            success = home_assistant.update_solar_controller_data(params)
                            
                            # Actualizo sensores del microcontrolador (filtrado por delta)
                            home_assistant.update_microcontroller_sensors()
                            
                            if DEBUG:
                                if success:
                                    print("Datos subidos a Home Assistant correctamente")
                                else:
                                    print("Error al subir datos a Home Assistant")
                        else:
                            if DEBUG:
                                print("No se actualizaron los sensores porque el dispositivo no existe en Home Assistant")
                    else:
                        if DEBUG:
                            print("Home Assistant no es accesible")
                    
                    # Apago el LED de subida después de la comunicación con Home Assistant
                    rpi_pico.led_upload_off()
            
            if DEBUG:
                print(f"Ciclo completado correctamente")
            
            # Ejecuto la recolección de basura
            collect_garbage()
            
            # Parpadeo el LED integrado para indicar un ciclo exitoso
            rpi_pico.led_off()
            time.sleep(0.2)
            rpi_pico.led_on()
            time.sleep(0.2)
            rpi_pico.led_off()
            
            # Aseguro que los LEDs de ciclo y subida estén apagados antes de dormir
            rpi_pico.led_cycle_off()
            rpi_pico.led_upload_off()
            
            # Pauso durante el tiempo configurado en SLEEP_TIME
            if DEBUG:
                print(f"Pausando durante {SLEEP_TIME} segundos antes del próximo ciclo")
            
            # Uso pausa simple en lugar de light_sleep
            sleep_pause(SLEEP_TIME)
            
            # Enciendo el LED integrado nuevamente al despertar
            rpi_pico.led_on()
            
        except Exception as e:
            if DEBUG:
                print(f"Error en el ciclo principal: {e}")
            
            # Aseguro que los LEDs de ciclo y subida estén apagados en caso de error
            rpi_pico.led_cycle_off()
            rpi_pico.led_upload_off()
            
            # Parpadeo el LED integrado rápidamente para indicar un error
            for _ in range(5):
                rpi_pico.led_on()
                time.sleep(0.1)
                rpi_pico.led_off()
                time.sleep(0.1)
            
            # Pauso antes de reintentar
            time.sleep(5)


if __name__ == '__main__':
    loop()
