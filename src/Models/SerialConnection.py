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
##
##

#######################################
# #       Importar Librerías        # #
#######################################
#from pymodbus.client import ModbusSerialClient as ModbusClient ## pymodbus 3.1
from pymodbus.client.sync import ModbusSerialClient as ModbusClient ## pymodbus 2.1.0
from pymodbus.constants import Defaults

Defaults.RetryOnEmpty = True
Defaults.Timeout = 3
Defaults.Retries = 5

# result = client.read_holding_registers(0x0107,1,unit=1)

#######################################
# #            FUNCIONES            # #
#######################################

class SerialConnection:
    client = None
    DEBUG = False

    def __init__ (self, debug=True, port='/dev/ttyUSB0', baudrate=9600,
                  timeout=0.5, method='rtu'):

        self.client = ModbusClient(method=method, port=port, stopbits=1,
                                   bytesize=8, parity='N',
                                   debug=debug,
                                   auto_open=True,
                                   baudrate=baudrate, timeout=timeout)

        self.DEBUG = debug

    def connect (self):
        """
        Abre la conexión con el dispositivo.
        :return:
        """
        return self.client.connect()

    def close (self):
        """
        Cierra la conexión con el dispositivo.
        :return:
        """
        return self.client.close()

    def read_register (self, register, bits=2, type_data=None):
        """
        Lee un registro y devuelve su resultado.
        :param register:
        :return:
        """
        self.connect()
        response = self.client.read_holding_registers(register, bits, unit=1)
        self.close()

        if response.isError() and self.DEBUG:
            print("Error: " + str(response.function_code))
        elif self.DEBUG and response.registers:
            msg = "Registro: {}, Valor: {}".format(register, response.registers)
            print(msg)

        value = response.registers if not response.isError() and response.registers else None

        if self.DEBUG:
            print(type(value))

        """
        if value and type_data and type_data == 'string':
            return str(value)
        elif value and type_data and type_data == 'int':
            return int(value)
        elif value and type_data and type_data == 'float':
            return float(value)
        """

        return value

    def read_registers (self, registers, bits=2):
        """
        Lee una lista de registros y devuelve sus resultados en el mismo orden.
        :param registers:
        :return:
        """
        results = {}

        for register in registers:
            #TODO → Utilizar atributos del diccionario (type, bits, address)
            results.append(self.read_register(register, bits))

        return results