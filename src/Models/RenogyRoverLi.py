#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      public@raupulus.dev
# @web        https://raupulus.dev
# @gitlab     https://gitlab.com/raupulus
# @github     https://github.com/raupulus
# @twitter    https://twitter.com/raupulus
# @telegram   https://t.me/raupulus_diffusion

# Create Date: 2022/2025
# Project Name: Raspberry Pi Pico Monitor Renogy Rover Li Solar Controller
# Description: Class for interfacing with Renogy Rover Li solar controller
#              using MicroPython on Raspberry Pi Pico.
#
# Dependencies: MicroPython
#
# Revision 0.02 - Adapted for Raspberry Pi Pico with MicroPython
# Additional Comments: Fixed dictionary unpacking for MicroPython compatibility

# @copyright  Copyright © 2022 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt

# Copyright (C) 2022  Raúl Caro Pastorino
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

from Models.SerialConnection import SerialConnection
from time import sleep, localtime

class RenogyRoverLi:
    serial = None
    DEBUG = False

    """
    Tipos de baterías.
    """
    BATTERY_TYPE = {
        1: 'open',
        2: 'sealed',
        3: 'gel',
        4: 'lithium',
        5: 'self-customized'
    }

    """
    Estados de carga para la batería.
    """
    CHARGING_STATE = {
        0: 'deactivated',
        1: 'activated',
        2: 'mppt',
        3: 'equalizing',
        4: 'boost',
        5: 'floating',
        6: 'current limiting'
    }

    # Atributos para almacenar datos estáticos en caché
    _cached_version = None
    _cached_system_voltage_current = None
    _cached_hardware = None
    _cached_battery_type = None
    _cached_serial_number = None
    _cached_nominal_battery_capacity = None

    sectionMap = {
        'model': {
            'bytes': 8,
            'address': 0x12,
            'type': 'string',
        },
        'system_voltage_current': {
            'bytes': 2,
            'address': 0xa,
            'type': 'float',
        },
        'system_intensity_current': {
            'bytes': 2,
            'address': 0xa,
            'type': 'float',
        },
        'hardware': {
            'bytes': 4,
            'address': 0x14,
            'type': 'string',
        },
        'version': {
            'bytes': 4,
            'address': 0x14,
            'type': 'string',
        },
        'serial_number': {
            'bytes': 4,
            'address': 0x18,
            'type': 'string',
        },
        'battery_percentage': {
            'bytes': 2,
            'address': 0x100,
            'type': 'float',
        },
        'battery_voltage': {
            'bytes': 2,
            'address': 0x101,
            'type': 'float',
        },
        'battery_temperature': {
            'bytes': 2,
            'address': 0x103,
            'type': 'float',
        },
        'controller_temperature': {
            'bytes': 2,
            'address': 0x103,
            'type': 'float',
        },
        'load_voltage': {
            'bytes': 2,
            'address': 0x104,
            'type': 'float',
        },
        'load_current': {
            'bytes': 2,
            'address': 0x105,
            'type': 'float',
        },
        'load_power': {
            'bytes': 2,
            'address': 0x106,
            'type': 'float',
        },
        'solar_voltage': {
            'bytes': 2,
            'address': 0x107,
            'type': 'float',
        },
        'solar_current': {
            'bytes': 2,
            'address': 0x108,
            'type': 'float',
        },
        'solar_power': {
            'bytes': 2,
            'address': 0x109,
            'type': 'float',
        },
        'today_battery_min_voltage': {
            'bytes': 2,
            'address': 0x010B,
            'type': 'float',
        },
        'today_battery_max_voltage': {
            'bytes': 2,
            'address': 0x010C,
            'type': 'float',
        },
        'today_max_charging_current': {
            'bytes': 2,
            'address': 0x010D,
            'type': 'float',
        },
        'today_max_discharging_current': {
            'bytes': 2,
            'address': 0x010E,
            'type': 'float',
        },
        'today_max_charging_power': {
            'bytes': 2,
            'address': 0x010D,
            'type': 'int',
        },
        'today_max_discharging_power': {
            'bytes': 2,
            'address': 0x010E,
            'type': 'int',
        },
        'today_charging_amp_hours': {
            'bytes': 2,
            'address': 0x0111,
            'type': 'int',
        },
        'today_discharging_amp_hours': {
            'bytes': 2,
            'address': 0x0112,
            'type': 'int',
        },
        'today_power_generation': {
            'bytes': 2,
            'address': 0x0113,
            'type': 'int',
        },
        'today_power_consumption': {
            'bytes': 2,
            'address': 0x0114,
            'type': 'int',
        },
        'historical_total_days_operating': {
            'bytes': 2,
            'address': 0x0115,
            'type': 'int',
        },
        'historical_total_number_battery_over_discharges': {
            'bytes': 2,
            'address': 0x0116,
            'type': 'int',
        },
        'historical_total_number_battery_full_charges': {
            'bytes': 2,
            'address': 0x0117,
            'type': 'int',
        },
        'historical_total_charging_amp_hours': {
            'bytes': 4,
            'address': 0x0118,
            'type': 'int',
        },
        'historical_total_discharging_amp_hours': {
            'bytes': 4,
            'address': 0x011A,
            'type': 'int',
        },
        'historical_cumulative_power_generation': {
            'bytes': 4,
            'address': 0x011C,
            'type': 'int',
        },
        'historical_cumulative_power_consumption': {
            'bytes': 4,
            'address': 0x011E,
            'type': 'int',
        },
        'street_light_status': {
            'bytes': 2,
            'address': 0x0120,
            'type': 'bool',
        },
        'street_light_brightness': {
            'bytes': 2,
            'address': 0x0120,
            'type': 'int',
        },
        'charging_status': {
            'bytes': 2,
            'address': 0x0120,
            'type': 'int',
        },
        'nominal_battery_capacity': {
            'bytes': 2,
            'address': 0xE002,
            'type': 'int',
        },
        'battery_type': {
            'bytes': 2,
            'address': 0xE004,
            'type': 'int',
        },
    }

    def __init__ (self, device_id=0, tx_pin=0, rx_pin=1, debug=False):
        """
        Inicializa el controlador RenogyRoverLi.
        
        Args:
            device_id (int): ID del dispositivo para identificación
            tx_pin (int): Número de pin TX (GPIO) para comunicación UART
            rx_pin (int): Número de pin RX (GPIO) para comunicación UART
            debug (bool): Habilitar salida de depuración
        """
        self.device_id = device_id
        self.DEBUG = debug
        self.serial = SerialConnection(tx_pin=tx_pin, rx_pin=rx_pin, debug=debug, 
                                      baudrate=9600, timeout=0.5)

        if (debug):
            print('Modelo RenogyRoverLi instanciado')
            
        # Intento inicializar los datos estáticos en caché
        self._initialize_static_data()
        
    def _initialize_static_data(self):
        """
        Inicializa los datos estáticos en caché.
        Este método intenta leer todos los datos estáticos una sola vez durante la inicialización.
        Si hay algún error, los datos se leerán cuando se soliciten por primera vez.
        """
        if self.DEBUG:
            print('Inicializando datos estáticos en caché')
            
        try:
            # Intento leer la versión del software
            self._cached_version = self.get_version()
            if self.DEBUG and self._cached_version:
                print(f'Versión del software en caché: {self._cached_version}')
        except Exception as e:
            if self.DEBUG:
                print(f'Error al inicializar versión del software: {e}')
                
        try:
            # Intento leer la versión del hardware
            self._cached_hardware = self.get_hardware()
            if self.DEBUG and self._cached_hardware:
                print(f'Versión del hardware en caché: {self._cached_hardware}')
        except Exception as e:
            if self.DEBUG:
                print(f'Error al inicializar versión del hardware: {e}')
                
        try:
            # Intento leer el número de serie
            self._cached_serial_number = self.get_serial_number()
            if self.DEBUG and self._cached_serial_number:
                print(f'Número de serie en caché: {self._cached_serial_number}')
        except Exception as e:
            if self.DEBUG:
                print(f'Error al inicializar número de serie: {e}')
                
        try:
            # Intento leer el voltaje del sistema
            self._cached_system_voltage_current = self.get_system_voltage_current()
            if self.DEBUG and self._cached_system_voltage_current:
                print(f'Voltaje del sistema en caché: {self._cached_system_voltage_current}')
        except Exception as e:
            if self.DEBUG:
                print(f'Error al inicializar voltaje del sistema: {e}')
                
        try:
            # Intento leer el tipo de batería
            self._cached_battery_type = self.get_battery_type()
            if self.DEBUG and self._cached_battery_type:
                print(f'Tipo de batería en caché: {self._cached_battery_type}')
        except Exception as e:
            if self.DEBUG:
                print(f'Error al inicializar tipo de batería: {e}')
                
        try:
            # Intento leer la capacidad nominal de la batería
            self._cached_nominal_battery_capacity = self.get_nominal_battery_capacity()
            if self.DEBUG and self._cached_nominal_battery_capacity:
                print(f'Capacidad nominal de la batería en caché: {self._cached_nominal_battery_capacity}')
        except Exception as e:
            if self.DEBUG:
                print(f'Error al inicializar capacidad nominal de la batería: {e}')

    def get_system_voltage_current (self):
        """
        Devuelve el voltaje actual de consumo en el sistema
        0x000A
        [1] → 8 higher bits: max. voltage supported by the system (V)
        """
        # Si ya tenemos el valor en caché, lo devolvemos directamente
        if self._cached_system_voltage_current is not None:
            if self.DEBUG:
                print('Devolviendo voltaje actual de sistema desde caché')
            return self._cached_system_voltage_current
            
        # Si no está en caché, lo leemos del controlador
        scheme = self.sectionMap['system_voltage_current']

        while True:
            if self.DEBUG:
                print('Leyendo voltaje actual de sistema')

            try:
                response = self.serial.read_register(scheme['address'],
                                                     scheme['bytes'],
                                                     scheme['type'])

                voltage = response[0] >> 8
                
                # Guardamos el resultado en caché
                self._cached_system_voltage_current = voltage
                return self._cached_system_voltage_current
            except Exception as e:
                if self.DEBUG:
                    print('Error al leer voltaje actual de sistema')
                    print(e)

                sleep(5)

        return None

    def get_system_intensity_current (self):
        """
        Devuelve el consumo en amperios actual de consumo en el sistema
        0x000A
        lower bits: rated charging current (A)
        """
        scheme = self.sectionMap['system_intensity_current']

        while True:
            try:
                if self.DEBUG:
                    print('Leyendo intensidad actual de sistema')

                response = self.serial.read_register(scheme['address'],
                                                     scheme['bytes'],
                                                     scheme['type'])

                amps = response[0] & 0x00ff

                return amps
            except Exception as e:
                if self.DEBUG:
                    print('Error al leer intensidad actual de sistema')
                    print(e)

                sleep(5)

        return None

    def get_hardware (self):
        """
        Devuelve la información para la versión del hardware
        0x0016 y 0x0017 Hardware version 4 bytes

        :return:
        """
        # Si ya tenemos el valor en caché, lo devolvemos directamente
        if self._cached_hardware is not None:
            if self.DEBUG:
                print('Devolviendo hardware desde caché')
            return self._cached_hardware
            
        # Si no está en caché, lo leemos del controlador
        if self.DEBUG:
            print('Leyendo hardware')

        scheme = self.sectionMap['hardware']

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        if response:
            major = response[2] & 0x00ff
            minor = response[3] >> 8
            patch = response[3] & 0x00ff

            # Guardamos el resultado en caché
            self._cached_hardware = 'V{}.{}.{}'.format(major, minor, patch)
            return self._cached_hardware

        return None

    def get_version (self):
        """
        Devuelve la información sobre la versión del software
        0x0014 y 0x0015 Software version 4 bytes
        """
        # Si ya tenemos el valor en caché, lo devolvemos directamente
        if self._cached_version is not None:
            if self.DEBUG:
                print('Devolviendo versión desde caché')
            return self._cached_version
            
        # Si no está en caché, lo leemos del controlador
        if self.DEBUG:
            print('Leyendo versión')

        scheme = self.sectionMap['version']

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        if response:
            major = response[0] & 0x00ff
            minor = response[1] >> 8
            patch = response[1] & 0x00ff

            # Guardamos el resultado en caché
            self._cached_version = 'V{}.{}.{}'.format(major, minor, patch)
            return self._cached_version

        return None

    def get_serial_number (self):
        """
        Devuelve el número de serie del controlador
        0x0018 y 0x0019 Serial number 4 bytes
        """
        # Si ya tenemos el valor en caché, lo devolvemos directamente
        if self._cached_serial_number is not None:
            if self.DEBUG:
                print('Devolviendo número de serie desde caché')
            return self._cached_serial_number
            
        # Si no está en caché, lo leemos del controlador
        if self.DEBUG:
            print('Leyendo número de serie')

        scheme = self.sectionMap['serial_number']

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        if response:
            # Guardamos el resultado en caché
            self._cached_serial_number = '{}{}'.format(response[0], response[1])
            return self._cached_serial_number
            
        return None

    def get_battery_percentage (self):
        """
        Devuelve el porcentaje de carga para la batería
        0x0100 Battery capacity SOC 2 bytes
        Current battery capacity value 0-100 (%)
        :return:
        """
        if self.DEBUG:
            print('Leyendo porcentaje de batería')

        scheme = self.sectionMap['battery_percentage']

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_battery_voltage (self):
        """
        Devuelve el voltaje de la batería
        0x0101 Battery voltage 2 bytes
        Battery voltage * 0.1 (V)
        """
        if self.DEBUG:
            print('Leyendo voltaje de batería')

        scheme = self.sectionMap['battery_voltage']

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 10 if response else None

    def get_battery_temperature (self):
        """
        Devuelve la temperatura de la batería en su exterior (sensor externo)
        0x0103 Battery temperature 2 bytes
        Actual temperature value (b7: sign bit; b0-b6: temperature value) (ºC)
        """
        scheme = self.sectionMap['battery_temperature']

        while True:
            try:
                if self.DEBUG:
                    print('Leyendo temperatura de batería')

                response = self.serial.read_register(scheme['address'],
                                                     scheme['bytes'],
                                                     scheme['type'])
                battery_temp_bits = response[0] & 0x00ff
                temp_value = battery_temp_bits & 0x0ff
                sign = battery_temp_bits >> 7

                return -(temp_value - 128) if sign == 1 else temp_value
            except Exception as e:
                print(e)
                print('Error al leer temperatura de batería')
                sleep(5)

        return None

    def get_controller_temperature (self):
        """
        Devuelve la temperatura del controlador de carga
        0x0103 Controller temperature 2 bytes
        Actual temperature value (b7: sign bit; b0-b6: temperature value) (ºC)
        """
        scheme = self.sectionMap['controller_temperature']

        if self.DEBUG:
            print('Leyendo temperatura del controlador solar')

        response = self.serial.read_register(scheme['address'],
                                             scheme['bytes'],
                                             scheme['type'])
        controller_temp_bits = response[0] >> 8
        temp_value = controller_temp_bits & 0x0ff
        sign = controller_temp_bits >> 7

        return -(temp_value - 128) if sign == 1 else temp_value

    def get_load_voltage (self):
        """
        Devuelve el voltaje de la carga actual
        0x0104 Load voltage 2 bytes
        Street light voltage * 0.1 (V)
        """
        scheme = self.sectionMap['load_voltage']

        if self.DEBUG:
            print('Leyendo voltaje para la carga actual de consumo')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 10 if response else None

    def get_load_current (self):
        """
        Devuelve la intensidad de la carga actual
        0x0105 Load current 2 bytes
        Street light current * 0.01 (A)
        """
        scheme = self.sectionMap['load_current']

        if self.DEBUG:
            print('Leyendo intensidad para la carga actual de consumo')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 100 if response else None

    def get_load_power (self):
        """
        Devuelve la potencia de la carga actual
        0x0105 Load current 2 bytes
        Street light power (W)
        """
        scheme = self.sectionMap['load_power']

        if self.DEBUG:
            print('Leyendo potencia para la carga actual de consumo')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_solar_voltage (self):
        """
        Devuelve la tensión del panel solar actualmente.
        0x0107 Solar panel voltage
        Solar panel voltage * 0.1 (V)
        """
        scheme = self.sectionMap['solar_voltage']

        if self.DEBUG:
            print('Leyendo voltaje del panel solar actualmente')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 10 if response else None

    def get_solar_current (self):
        """
        Devuelve la intensidad del panel solar actualmente.
        0x0108 Solar panel current (to controller)
        Solar panel current * 0.01 (A)
        """
        scheme = self.sectionMap['solar_current']

        if self.DEBUG:
            print('Leyendo intensidad del panel solar actualmente')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 100 if response else None

    def get_solar_power (self):
        """
        Devuelve la potencia del panel solar actualmente.
        0x0109 Solar charging power
        Solar charging power (W)
        """
        scheme = self.sectionMap['solar_power']

        if self.DEBUG:
            print('Leyendo potencia del panel solar actualmente')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_today_battery_min_voltage (self):
        """
        Devuelve la tensión mínima de la batería en el día actual
        0x010B Battery's min. voltage of the current day
        Battery's min. voltage of the current day * 0.1 (V)
        """
        scheme = self.sectionMap['today_battery_min_voltage']

        if self.DEBUG:
            print('Leyendo voltaje mínimo en el día para la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 10 if response else None

    def get_today_battery_max_voltage (self):
        """
        Devuelve la tensión máxima de la batería en el día actual
        0x010C Battery's max. voltage of the current day
        Battery's max. voltage of the current day * 0.1 (V)
        """
        scheme = self.sectionMap['today_battery_max_voltage']

        if self.DEBUG:
            print('Leyendo voltaje máximo en el día para la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 10 if response else None

    def get_today_max_charging_current (self):
        """
        Devuelve la intensidad máxima de carga en el día actual
        0x010D Battery's max. charging current of the current day
        Battery's max. charging current of the current day * 0.01 (A)
        """
        scheme = self.sectionMap['today_max_charging_current']

        if self.DEBUG:
            print(
                'Leyendo intensidad máxima de carga en el día para la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 100 if response else None

    def get_today_max_discharging_current (self):
        """
        Devuelve la intensidad máxima de descarga en el día actual
        0x010E Battery's max. discharging current of the current day
        Battery's max. discharging current of the current day * 0.01 (A)
        """
        scheme = self.sectionMap['today_max_discharging_current']

        if self.DEBUG:
            print(
                'Leyendo intensidad máxima de descarga en el día para la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return float(response[0]) / 100 if response else None

    def get_today_max_charging_power (self):
        """
        Devuelve la potencia máxima de carga en el día actual
        0x010F Battery's max. charging power of the current day
        Battery's max. charging power of the current day (W)
        """
        scheme = self.sectionMap['today_max_charging_power']

        if self.DEBUG:
            print('Leyendo potencia máxima de carga en el día para la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_today_max_discharging_power (self):
        """
        Devuelve la potencia máxima de descarga en el día actual
        0x0110 Battery's max. discharging power of the current day
        Battery's max. discharging power of the current day (W)
        """
        scheme = self.sectionMap['today_max_discharging_power']

        if self.DEBUG:
            print(
                'Leyendo potencia máxima de descarga en el día para la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_today_charging_amp_hours (self):
        """
        Devuelve la carga en Ah para el día actual
        0x0111 Charging amp-hrs of the current day (Ah)
        """
        scheme = self.sectionMap['today_charging_amp_hours']

        if self.DEBUG:
            print('Leyendo carga máxima en Ah en el día')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_today_discharging_amp_hours (self):
        """
        Devuelve la descarga en Ah para el día actual
        0x0112 Discharging amp-hrs of the current day (Ah)
        """
        scheme = self.sectionMap['today_discharging_amp_hours']

        if self.DEBUG:
            print('Leyendo descarga máxima en Ah en el día')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_today_power_generation (self):
        """
        Devuelve la potencia de generada en el día actual
        0x0113 Power generation of the current day (kilowatt hour / 10000)
        """
        scheme = self.sectionMap['today_power_generation']

        if self.DEBUG:
            print('Leyendo potencia de generación en el día')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_today_power_consumption (self):
        """
        Devuelve la potencia consumida en el día actual
        0x0114 Power consumption of the current day (kilowatt hour / 10000)
        """
        scheme = self.sectionMap['today_power_consumption']

        if self.DEBUG:
            print('Leyendo potencia de consumición en el día')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_historical_total_days_operating (self):
        """
        Devuelve el número de días que el controlador ha estado operativo.
        0x0115 Total number of operating days - 2 bytes
        """
        scheme = self.sectionMap['historical_total_days_operating']

        if self.DEBUG:
            print('Leyendo número de días operativo el controlador solar')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_historical_total_number_battery_over_discharges (self):
        """
        Devuelve el número de sobre descargas de la batería.
        0x0116 Total number of battery over-discharges - 2 bytes
        """
        scheme = self.sectionMap[
            'historical_total_number_battery_over_discharges']

        if self.DEBUG:
            print('Leyendo número de descargas de la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_historical_total_number_battery_full_charges (self):
        """
        Devuelve el número de cargas completas de la batería.
        0x0117 Total number of battery full-charges - 2 bytes
        """
        scheme = self.sectionMap['historical_total_number_battery_full_charges']

        if self.DEBUG:
            print('Leyendo número de cargas completas de la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_historical_total_charging_amp_hours (self):
        """
        Devuelve la carga total en Ah que ha sido almacenado en la batería.
        0x0118-0x0119 Total charging amp-hrs of the battery - 4 bytes (Ah)
        """
        scheme = self.sectionMap['historical_total_charging_amp_hours']

        if self.DEBUG:
            print('Leyendo carga total en Ah')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        # print('historical_total_charging_amp_hours', response)

        return response[1] if response else None

    def get_historical_total_discharging_amp_hours (self):
        """
        Devuelve la descarga total en Ah que ha sido descargado en la batería.
        0x011A-0x011B Total discharging amp-hrs of the battery - 4 bytes (Ah)
        """
        scheme = self.sectionMap['historical_total_discharging_amp_hours']

        if self.DEBUG:
            print('Leyendo descarga total en Ah')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        # print('historical_total_discharging_amp_hours', response)

        return response[1] if response else None

    def get_historical_cumulative_power_generation (self):
        """
        Devuelve la potencia generada acumulada en el tiempo.
        0x011C-0x011D Cumulative power generation - 4 bytes (kilowatt hour/ 10000)
        """
        scheme = self.sectionMap['historical_cumulative_power_generation']

        if self.DEBUG:
            print('Devuelve la potencia generada acumulada en el tiempo.')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[1] if response else None

    def get_historical_cumulative_power_consumption (self):
        """
        Devuelve la potencia consumida acumulada en el tiempo.
        0x011E-0x011F Cumulative power consumption - 4 bytes (kilowatt hour/ 10000)
        """
        scheme = self.sectionMap['historical_cumulative_power_consumption']

        if self.DEBUG:
            print('Devuelve la potencia consumida acumulada en el tiempo.')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[1] if response else None

    def get_street_light_status (self):
        """
        Devuelve el estado de la luz de calle.
        0x0120 Street light status - 2 byte (bool)
        """
        # scheme = self.sectionMap['street_light_status']

        if self.DEBUG:
            print('Leyendo estado de la luz en la calle')

        # Como me daba problemas obtener este dato, lo saco del voltaje solar.
        return bool(
            self.get_street_light_brightness() > 12.3) if self.get_street_light_brightness() else False

    def get_street_light_brightness (self):
        """
        Devuelve el brillo de la luz de calle.
        0x0120 Street light brightness - 2 byte (0-6, 0-100%)
        """
        # scheme = self.sectionMap['street_light_brightness']

        if self.DEBUG:
            print('Leyendo brillo de la luz en la calle')

        """
        Esto es una prueba, no conseguía obtener la luz real
        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        print('street_light_brightness response:', response)
        print('street_light_brightness response hexadecimal:', hex(response[0]))
        print('street_light_brightness 0x00FF:', response[0] & 0x00FF)
        print('street_light_brightness b:', bin(response[0]))

        return response[0] if response else None
        """

        # Obtengo el valor en proporción a la luz de calle
        voltage = self.get_solar_voltage()

        min_light_voltage = 12.3
        max_light_voltage = 41.5

        ## OJO → Cálculo preparado para dos placas en serie 24v (hasta 40v aprox)
        if voltage >= max_light_voltage:
            porcent = 100
        elif voltage < min_light_voltage:
            porcent = 0
        else:
            porcent = (100 / (max_light_voltage - min_light_voltage)) * (
                        voltage - min_light_voltage)

        return int(porcent)

    def get_charging_status (self):
        """
        Devuelve el estado de carga para la batería.
        0x0120 Charging status - 2 byte (0x00-0x06)
        """
        scheme = self.sectionMap['charging_status']

        if self.DEBUG:
            print('Leyendo estado de carga para la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] & 0x00ff if response else None

    def get_charging_status_label (self):
        """
        Devuelve el estado de la batería.
        0x0120 Charging status - 2 byte (string from self.CHARGING_STATE)
        """
        if self.DEBUG:
            print('Leyendo estado de carga (string) para la batería')

        charging_status = self.get_charging_status()

        return self.CHARGING_STATE.get(
            self.get_charging_status()) if charging_status else self.CHARGING_STATE.get(
            0)

    def get_nominal_battery_capacity (self):
        """
        Devuelve la capacidad nominal de la batería.
        0xE002 Nominal battery capacity - 2 byte (Ah)
        """
        # Si ya tenemos el valor en caché, lo devolvemos directamente
        if self._cached_nominal_battery_capacity is not None:
            if self.DEBUG:
                print('Devolviendo capacidad nominal de la batería desde caché')
            return self._cached_nominal_battery_capacity
            
        # Si no está en caché, lo leemos del controlador
        scheme = self.sectionMap['nominal_battery_capacity']

        if self.DEBUG:
            print('Leyendo capacidad nominal de la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        if response:
            # Guardamos el resultado en caché
            self._cached_nominal_battery_capacity = response[0]
            return self._cached_nominal_battery_capacity
            
        return None

    def get_battery_type (self):
        """
        Devuelve el tipo de batería.
        0xE004 Battery type - 2 byte (string from self.BATTERY_TYPE)
        """
        # Si ya tenemos el valor en caché, lo devolvemos directamente
        if self._cached_battery_type is not None:
            if self.DEBUG:
                print('Devolviendo tipo de batería desde caché')
            return self._cached_battery_type
            
        # Si no está en caché, lo leemos del controlador
        scheme = self.sectionMap['battery_type']

        if self.DEBUG:
            print('Leyendo tipo de batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        if response:
            # Guardamos el resultado en caché
            self._cached_battery_type = self.BATTERY_TYPE.get(response[0])
            return self._cached_battery_type
            
        return None

    def get_today_historical_info_datas (self):
        """
        Devuelve una lista con los datos históricos para el día actual
        :return:
        """
        return {
            'today_battery_max_voltage': self.get_today_battery_max_voltage(),
            'today_battery_min_voltage': self.get_today_battery_min_voltage(),
            'today_max_charging_current': self.get_today_max_charging_current(),
            'today_max_discharging_current': self.get_today_max_discharging_current(),
            'today_max_charging_power': self.get_today_max_charging_power(),
            'today_charging_amp_hours': self.get_today_charging_amp_hours(),
            'today_discharging_amp_hours': self.get_today_discharging_amp_hours(),
            'today_power_generation': self.get_today_power_generation(),
            'today_power_consumption': self.get_today_power_consumption(),

        }

    def get_historical_info_datas (self):
        """
        Devuelve una lista con los datos históricos generales
        :return:
        """
        return {
            'historical_total_days_operating': self.get_historical_total_days_operating(),
            'historical_total_number_battery_over_discharges': self.get_historical_total_number_battery_over_discharges(),
            'historical_total_number_battery_full_charges': self.get_historical_total_number_battery_full_charges(),
            'historical_total_charging_amp_hours': self.get_historical_total_charging_amp_hours(),
            'historical_total_discharging_amp_hours': self.get_historical_total_discharging_amp_hours(),
            'historical_cumulative_power_generation': self.get_historical_cumulative_power_generation(),
            'historical_cumulative_power_consumption': self.get_historical_cumulative_power_consumption(),
        }

    def get_all_controller_info_datas (self):
        """
        Devuelve información del controlador de carga solar.
        :return:
        """
        return {
            'device_id': self.device_id,
            'hardware': self.get_hardware(),
            'version': self.get_version(),
            'serial_number': self.get_serial_number(),
            'system_voltage_current': self.get_system_voltage_current(),
            'system_intensity_current': self.get_system_intensity_current(),
            'battery_type': self.get_battery_type(),
            'nominal_battery_capacity': self.get_nominal_battery_capacity(),
        }

    def get_all_solar_panel_info_datas (self):
        """
        Devuelve toda la información de los paneles solares.
        :return:
        """
        return {
            'solar_current': self.get_solar_current(),
            'solar_voltage': self.get_solar_voltage(),
            'solar_power': self.get_solar_power(),
        }

    def get_all_battery_info_datas (self):
        """
        Devuelve toda la información de la batería.
        :return:
        """
        return {
            'battery_voltage': self.get_battery_voltage(),
            'battery_temperature': self.get_battery_temperature(),
            'battery_percentage': self.get_battery_percentage(),
            'charging_status': self.get_charging_status(),
            'charging_status_label': self.get_charging_status_label(),
        }

    def get_all_load_info_datas (self):
        """
        Devuelve toda la información de carga.
        :return:
        """
        return {
            'load_voltage': self.get_load_voltage(),
            'load_current': self.get_load_current(),
            'load_power': self.get_load_power(),
        }

    def get_all_datas (self):
        """
        Devuelve todos los datos del controlador de carga solar
        :return:
        """
        # Usando dict.update() en lugar de ** unpacking para compatibilidad con MicroPython
        result = {}
        result.update(self.get_today_historical_info_datas())
        result.update(self.get_historical_info_datas())
        result.update(self.get_all_controller_info_datas())
        result.update(self.get_all_solar_panel_info_datas())
        result.update(self.get_all_battery_info_datas())
        result.update(self.get_all_load_info_datas())
        
        # Add additional fields
        additional_fields = {
            'controller_temperature': self.get_controller_temperature(),
            'street_light_status': self.get_street_light_status(),
            'street_light_brightness': self.get_street_light_brightness(),
        }
        result.update(additional_fields)
        
        return result

    def debug (self):
        """
        Función para depurar funcionamiento del modelo proyectando datos por
        consola.
        
        Muestra información detallada sobre el controlador, incluyendo:
        - Datos estáticos en caché
        - Lecturas actuales
        - Estado de la batería
        - Estado de los paneles solares
        - Información histórica
        """

        print("\n" + "="*50)
        print("DEPURACIÓN DEL CONTROLADOR RENOGY ROVER LI")
        print("="*50)
        
        # Mostrar timestamp
        timestamp = localtime()
        print(f"Fecha y hora: {timestamp[0]}/{timestamp[1]}/{timestamp[2]} {timestamp[3]}:{timestamp[4]}:{timestamp[5]}")
        
        # Mostrar información del dispositivo
        print("\n--- INFORMACIÓN DEL DISPOSITIVO ---")
        print(f"ID del dispositivo: {self.device_id}")
        
        # Mostrar datos estáticos en caché
        print("\n--- DATOS ESTÁTICOS EN CACHÉ ---")
        print(f"Versión del software: {self._cached_version if self._cached_version is not None else 'No en caché'}")
        print(f"Versión del hardware: {self._cached_hardware if self._cached_hardware is not None else 'No en caché'}")
        print(f"Número de serie: {self._cached_serial_number if self._cached_serial_number is not None else 'No en caché'}")
        print(f"Voltaje del sistema: {self._cached_system_voltage_current if self._cached_system_voltage_current is not None else 'No en caché'}")
        print(f"Tipo de batería: {self._cached_battery_type if self._cached_battery_type is not None else 'No en caché'}")
        print(f"Capacidad nominal de la batería: {self._cached_nominal_battery_capacity if self._cached_nominal_battery_capacity is not None else 'No en caché'}")
        
        # Mostrar lecturas actuales
        print("\n--- LECTURAS ACTUALES ---")
        print("Estado de la batería:")
        try:
            battery_voltage = self.get_battery_voltage()
            print(f"  Voltaje de la batería: {battery_voltage}V")
        except Exception as e:
            print(f"  Error al leer voltaje de la batería: {e}")
            
        try:
            battery_percentage = self.get_battery_percentage()
            print(f"  Porcentaje de la batería: {battery_percentage}%")
        except Exception as e:
            print(f"  Error al leer porcentaje de la batería: {e}")
            
        try:
            battery_temperature = self.get_battery_temperature()
            print(f"  Temperatura de la batería: {battery_temperature}°C")
        except Exception as e:
            print(f"  Error al leer temperatura de la batería: {e}")
            
        try:
            charging_status = self.get_charging_status_label()
            print(f"  Estado de carga: {charging_status}")
        except Exception as e:
            print(f"  Error al leer estado de carga: {e}")
        
        print("\nEstado de los paneles solares:")
        try:
            solar_voltage = self.get_solar_voltage()
            print(f"  Voltaje de los paneles: {solar_voltage}V")
        except Exception as e:
            print(f"  Error al leer voltaje de los paneles: {e}")
            
        try:
            solar_current = self.get_solar_current()
            print(f"  Corriente de los paneles: {solar_current}A")
        except Exception as e:
            print(f"  Error al leer corriente de los paneles: {e}")
            
        try:
            solar_power = self.get_solar_power()
            print(f"  Potencia de los paneles: {solar_power}W")
        except Exception as e:
            print(f"  Error al leer potencia de los paneles: {e}")
        
        print("\nEstado del controlador:")
        try:
            controller_temperature = self.get_controller_temperature()
            print(f"  Temperatura del controlador: {controller_temperature}°C")
        except Exception as e:
            print(f"  Error al leer temperatura del controlador: {e}")
        
        # Mostrar información histórica
        print("\n--- INFORMACIÓN HISTÓRICA DEL DÍA ---")
        try:
            today_data = self.get_today_historical_info_datas()
            for key, value in today_data.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"  Error al leer información histórica del día: {e}")
            
        print("\n--- INFORMACIÓN HISTÓRICA TOTAL ---")
        try:
            historical_data = self.get_historical_info_datas()
            for key, value in historical_data.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"  Error al leer información histórica total: {e}")
        
        print("\n" + "="*50)
        print("FIN DE LA DEPURACIÓN")
        print("="*50 + "\n")