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
# Description: Mi clase de conexión serial para comunicarme con el controlador solar Renogy Rover Li
#              usando el protocolo Modbus RTU a través de UART en la Raspberry Pi Pico.
#
# Dependencies: MicroPython
#
# Revision 0.02 - Adaptado para Raspberry Pi Pico con MicroPython
# Additional Comments: Esta implementación reemplaza pymodbus con comunicación UART directa

# @copyright  Copyright © 2022 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt

# Copyright (C) 2022 Raúl Caro Pastorino
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
# #              Datos              # #
#######################################
##
# Diagrama de conexión:
# Raspberry Pi Pico | Conversor RS232
# ---------------------------------
# TX (GPIO0/Pin1)  | RX
# RX (GPIO1/Pin2)  | TX
# GND              | GND
# 
# El conversor RS232 debe conectarse luego al controlador Renogy Rover Li.
##

#######################################
# #       Importar Librerías        # #
#######################################
from machine import UART, Pin
import time

# Configuraciones predeterminadas
DEFAULT_RETRIES = 5  # Número de reintentos
DEFAULT_TIMEOUT = 3  # Tiempo de espera en segundos
DEFAULT_BAUDRATE = 9600  # Velocidad de transmisión

#######################################
# #            FUNCIONES            # #
#######################################

class SerialConnection:
    """
    Mi clase para comunicación serial con dispositivos Modbus RTU usando UART de MicroPython.
    
    Con esta clase implemento el protocolo Modbus RTU para leer registros
    desde un controlador solar Renogy Rover Li conectado a una Raspberry Pi Pico
    a través de un conversor TTL a RS232.
    """
    
    def __init__(self, debug=True, tx_pin=0, rx_pin=1, baudrate=DEFAULT_BAUDRATE,
                 timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        """
        Inicializo la conexión serial.
        
        Args:
            debug (bool): Activo la salida de depuración
            tx_pin (int): Número de pin TX (GPIO)
            rx_pin (int): Número de pin RX (GPIO)
            baudrate (int): Velocidad de transmisión para la comunicación serial
            timeout (float): Tiempo de espera en segundos
            retries (int): Número de reintentos para comunicaciones fallidas
        """
        self.DEBUG = debug
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.baudrate = baudrate
        self.timeout = timeout
        self.retries = retries
        self.uart = None
        
        # Inicializo UART
        self.connect()
        
        if self.DEBUG:
            print(f"Conexión Serial inicializada: TX={tx_pin}, RX={rx_pin}, Baudrate={baudrate}")

    def connect(self):
        """
        Abro la conexión con el dispositivo.
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            # Uso UART0 para la comunicación serial
            # 8 bits, 1 bit de parada, sin paridad
            # Convierto el timeout a milisegundos para la inicialización de UART
            timeout_ms = int(self.timeout * 1000)
            
            self.uart = UART(0, 
                            baudrate=self.baudrate, 
                            tx=Pin(self.tx_pin), 
                            rx=Pin(self.rx_pin),
                            bits=8,
                            parity=None,
                            stop=1,
                            timeout=timeout_ms)  # Paso el timeout durante la inicialización
            
            return True
        except Exception as e:
            if self.DEBUG:
                print(f"Error al conectar con UART: {e}")
            return False

    def close(self):
        """
        Cierro la conexión con el dispositivo.
        
        Returns:
            bool: True si se cerró correctamente
        """
        try:
            # No hay método close explícito en UART de MicroPython
            # Pero puedo desinicializarlo, quizás no tenga sentido
            # TODO: Averiguar si este método tiene sentido
            if self.uart:
                self.uart.deinit()
                self.uart = None
            return True
        except Exception as e:
            if self.DEBUG:
                print(f"Error al cerrar UART: {e}")
            return False

    def _calculate_crc(self, data):
        """
        Calculo el CRC-16 de Modbus RTU para los datos proporcionados.
        
        Args:
            data (bytes): Datos para los que calcular el CRC
            
        Returns:
            bytes: CRC como bytes (2 bytes, little endian)
        """
        crc = 0xFFFF
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        
        # Devuelvo CRC en formato little-endian (byte bajo primero)
        return bytes([crc & 0xFF, crc >> 8])

    def read_register(self, register, bits=2, type_data=None):
        """
        Leo un registro y devuelvo su valor.
        
        Args:
            register (int): Dirección del registro a leer
            bits (int): Número de registros a leer
            type_data (str, opcional): Tipo de datos a devolver
            
        Returns:
            list: Valores del registro o None si hay error
        """
        for attempt in range(self.retries):
            try:
                # Me aseguro de que la conexión esté abierta
                if not self.uart:
                    self.connect()
                
                # Creo mensaje Modbus RTU para leer registros
                # Formato: [slave_id, function_code, reg_addr_hi, reg_addr_lo, reg_count_hi, reg_count_lo, crc_lo, crc_hi]
                slave_id = 1  # ID de esclavo predeterminado para Renogy Rover Li
                function_code = 3  # Código para leer registros
                
                # Convierto dirección de registro y cantidad a bytes
                reg_addr_hi = (register >> 8) & 0xFF
                reg_addr_lo = register & 0xFF
                reg_count_hi = (bits >> 8) & 0xFF
                reg_count_lo = bits & 0xFF
                
                # Creo mensaje sin CRC
                message = bytes([slave_id, function_code, reg_addr_hi, reg_addr_lo, reg_count_hi, reg_count_lo])
                
                # Calculo y añado CRC
                crc = self._calculate_crc(message)
                message += crc
                
                # Limpio buffer de recepción
                self.uart.read()
                
                # Envío mensaje
                self.uart.write(message)
                
                # Espero respuesta (mínimo 5 bytes: slave_id, function_code, byte_count, al menos 2 bytes de CRC)
                time.sleep(0.1)  # Pequeña pausa para asegurar que la respuesta esté lista
                
                # Leo respuesta
                response = self.uart.read()
                
                if not response or len(response) < 5:
                    if self.DEBUG:
                        print(f"Sin respuesta o respuesta demasiado corta: {response}")
                    continue  # Reintento
                
                # Verifico si es una respuesta de error (código de función + 0x80)
                if response[1] == function_code + 0x80:
                    if self.DEBUG:
                        print(f"Respuesta de error: Código de excepción {response[2]}")
                    return None
                
                # Verifico el formato de la respuesta
                if response[0] != slave_id or response[1] != function_code:
                    if self.DEBUG:
                        print(f"Cabecera de respuesta inválida: {response[:2]}")
                    continue  # Reintento
                
                # Obtengo el conteo de bytes
                byte_count = response[2]
                
                # Verifico si la respuesta tiene suficientes datos
                if len(response) < byte_count + 5:  # slave_id + function_code + byte_count + data + 2 bytes CRC
                    if self.DEBUG:
                        print(f"Respuesta demasiado corta: esperaba {byte_count + 5}, recibí {len(response)}")
                    continue  # Reintento
                
                # Extraigo los datos
                data = response[3:3+byte_count]
                
                # Verifico el CRC
                received_crc = response[3+byte_count:3+byte_count+2]
                calculated_crc = self._calculate_crc(response[:3+byte_count])
                
                if received_crc != calculated_crc:
                    if self.DEBUG:
                        print(f"CRC no coincide: recibido {received_crc}, calculado {calculated_crc}")
                    continue  # Reintento
                
                # Analizo los valores de los registros (cada registro es de 2 bytes)
                registers = []
                for i in range(0, byte_count, 2):
                    if i + 1 < byte_count:
                        reg_value = (data[i] << 8) + data[i+1]
                        registers.append(reg_value)
                
                if self.DEBUG:
                    print(f"Registro: {register}, Valor: {registers}")
                
                return registers
                
            except Exception as e:
                if self.DEBUG:
                    print(f"Error al leer registro: {e}")
                time.sleep(0.1)  # Pequeña pausa antes de reintentar
        
        # Todos los reintentos fallaron
        if self.DEBUG:
            print(f"No se pudo leer el registro {register} después de {self.retries} intentos")
        
        return None

    def read_registers(self, registers, bits=2):
        """
        Leo múltiples registros y devuelvo sus valores.
        
        Args:
            registers (list): Lista de direcciones de registros a leer
            bits (int): Número de registros a leer para cada dirección
            
        Returns:
            dict: Diccionario de valores de registro con direcciones de registro como claves
        """
        # Inicializo diccionario para almacenar resultados
        results = {}
        
        # Leo cada registro individualmente
        for register in registers:
            results[register] = self.read_register(register, bits)
        
        # Devuelvo todos los resultados
        return results