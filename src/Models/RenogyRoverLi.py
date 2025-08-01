#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      public@raupulus.dev
# @web        https://raupulus.dev
# @gitlab     https://gitlab.com/raupulus
# @github     https://github.com/raupulus
# @twitter    https://twitter.com/raupulus
# @telegram   https://t.me/raupulus_diffusion

# Create Date: 2022
# Project Name:
# Description:
#
# Dependencies:
#
# Revision 0.01 - File Created
# Additional Comments:

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

#######################################
# #           Descripción           # #
#######################################
## Modelo que representa a un controlador de placas solares Renogy Rover Li
##

#######################################
# #       Importar Librerías        # #
#######################################

from Models.SolarControllers.AbstractModel import AbstractModel
from src.Models.SerialConnection import SerialConnection
import time
import datetime

#######################################
# #             Variables           # #
#######################################

sleep = time.sleep


#######################################
# #            FUNCIONES            # #
#######################################


class RenogyRoverLi(AbstractModel):
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

    tablename = 'renogy_rover_li'

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

    def __init__ (self, device_id=0, port='/dev/ttyUSB0', debug=False):
        self.device_id = device_id
        self.DEBUG = debug
        self.serial = SerialConnection(port=port, debug=debug, baudrate=9600,
                                       method='rtu', timeout=0.5)

        if (debug):
            print('Modelo RenogyRoverLi instanciado')

    def get_system_voltage_current (self):
        """
        Devuelve el voltaje actual de consumo en el sistema
        0x000A
        [1] → 8 higher bits: max. voltage supported by the system (V)
        """
        scheme = self.sectionMap['system_voltage_current']

        while True:
            if self.DEBUG:
                print('Leyendo voltaje actual de sistema')

            try:
                response = self.serial.read_register(scheme['address'],
                                                     scheme['bytes'],
                                                     scheme['type'])

                voltage = response[0] >> 8

                return voltage
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
        if self.DEBUG:
            print('Leyendo hardware')

        scheme = self.sectionMap['hardware']

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        if response:
            major = response[2] & 0x00ff
            minor = response[3] >> 8
            patch = response[3] & 0x00ff

            return 'V{}.{}.{}'.format(major, minor, patch)

        return None

    def get_version (self):
        """
        Devuelve la información sobre la versión del software
        0x0014 y 0x0015 Software version 4 bytes
        """
        if self.DEBUG:
            print('Leyendo versión')

        scheme = self.sectionMap['version']

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        if response:
            major = response[0] & 0x00ff
            minor = response[1] >> 8
            patch = response[1] & 0x00ff

            return 'V{}.{}.{}'.format(major, minor, patch)

        return None

    def get_serial_number (self):
        """
        Devuelve el número de serie del controlador
        0x0018 y 0x0019 Serial number 4 bytes
        """
        if self.DEBUG:
            print('Leyendo número de serie')

        scheme = self.sectionMap['serial_number']

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return '{}{}'.format(response[0], response[1]) if response else None

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
        scheme = self.sectionMap['nominal_battery_capacity']

        if self.DEBUG:
            print('Leyendo capacidad nominal de la batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return response[0] if response else None

    def get_battery_type (self):
        """
        Devuelve el tipo de batería.
        0xE004 Battery type - 2 byte (string from self.BATTERY_TYPE)
        """
        scheme = self.sectionMap['battery_type']

        if self.DEBUG:
            print('Leyendo tipo de batería')

        response = self.serial.read_register(scheme['address'], scheme['bytes'],
                                             scheme['type'])

        return self.BATTERY_TYPE.get(response[0]) if response else None

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
        return {
            **self.get_today_historical_info_datas(),
            **self.get_historical_info_datas(),
            **self.get_all_controller_info_datas(),
            **self.get_all_solar_panel_info_datas(),
            **self.get_all_battery_info_datas(),
            **self.get_all_load_info_datas(),
            **{
                'controller_temperature': self.get_controller_temperature(),
                'street_light_status': self.get_street_light_status(),
                'street_light_brightness': self.get_street_light_brightness(),
            }
        }

    def tablemodel (self):
        """
        Plantea campos como modelo de datos para una base de datos y poder ser
        tomados desde el exterior.
        """
        return {
            'device_id': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'battery_voltage': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'battery_temperature': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'battery_percentage': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'controller_temperature': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'load_voltage': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'load_current': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 2
                },
                'others': None,
            },
            'load_power': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'solar_voltage': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'solar_current': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'solar_power': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'street_light_status': {
                'type': 'Boolean',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'street_light_brightness': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'charging_status': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'charging_status_label': {
                'type': 'String',
                'params': { },
                'others': None,
            },

            'hardware': {
                'type': 'String',
                'params': { },
                'others': None,
            },
            'version': {
                'type': 'String',
                'params': { },
                'others': None,
            },
            'serial_number': {
                'type': 'String',
                'params': { },
                'others': None,
            },
            'system_voltage_current': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'system_intensity_current': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'battery_type': {
                'type': 'String',
                'params': { },
                'others': None,
            },
            'nominal_battery_capacity': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },

            'today_battery_max_voltage': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'today_battery_min_voltage': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'today_max_charging_current': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 2
                },
                'others': None,
            },
            'today_max_discharging_current': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 2
                },
                'others': None,
            },
            'today_max_charging_power': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'today_charging_amp_hours': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'today_discharging_amp_hours': {
                'type': 'Numeric',
                'params': {
                    'precision': 11,
                    'asdecimal': True,
                    'scale': 1
                },
                'others': None,
            },
            'today_power_generation': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'today_power_consumption': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'historical_total_days_operating': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'historical_total_number_battery_over_discharges': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'historical_total_number_battery_full_charges': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'historical_total_charging_amp_hours': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'historical_total_discharging_amp_hours': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'historical_cumulative_power_generation': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },
            'historical_cumulative_power_consumption': {
                'type': 'Integer',
                'params': {
                    'precision': 11,
                },
                'others': None,
            },

            'created_at': {
                'type': 'DateTime',
                'params': None,
                'others': {
                    'default': datetime.datetime.utcnow
                },
            },
        }

    def debug (self):
        """
        Función para depurar funcionamiento del modelo proyectando datos por
        consola.
        """
        pass