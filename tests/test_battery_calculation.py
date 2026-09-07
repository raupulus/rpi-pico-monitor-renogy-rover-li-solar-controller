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
# Create Date: 2026-09-06
# Project Name: Raspberry Pi Pico Monitor Renogy Rover Li Solar Controller
# Description: Tests unitarios para cálculos de batería, codificación Modbus,
#              serialización API y filtrado por delta de Home Assistant
#
# @copyright  Copyright © 2026 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt

import sys
import unittest
from unittest.mock import MagicMock
import json
import time

# Setup mocks for MicroPython libraries
sys.modules['urequests'] = MagicMock()
sys.modules['ujson'] = json
mock_machine = MagicMock()
mock_adc = MagicMock()
mock_adc.read_u16.return_value = 32768
mock_machine.ADC.return_value = mock_adc
sys.modules['machine'] = mock_machine
sys.modules['network'] = MagicMock()
sys.modules['ntptime'] = MagicMock()
sys.modules['time'] = time
if not hasattr(time, 'sleep_ms'):
    time.sleep_ms = lambda ms: time.sleep(ms / 1000.0)
sys.modules['gc'] = __import__('gc')

# Add src to path
for p in ('src', '.'):
    if p not in sys.path:
        sys.path.insert(0, p)

from Models.RenogyRoverLi import RenogyRoverLi
from Models.Api import Api
from Models.HomeAssistantConnection import HomeAssistantConnection
from Models.RpiPico import RpiPico


class TestBatteryCalculationsAndApi(unittest.TestCase):

    def setUp(self):
        # Mock serial connection
        self.mock_serial = MagicMock()
        self.rover = RenogyRoverLi.__new__(RenogyRoverLi)
        self.rover.DEBUG = False
        self.rover.serial = self.mock_serial
        self.rover.device_id = 1
        self.rover.sectionMap = RenogyRoverLi.sectionMap
        self.rover.FAULT_MESSAGES = RenogyRoverLi.FAULT_MESSAGES

        # Mock controller
        self.mock_controller = MagicMock()
        self.mock_controller.get_cpu_temperature.return_value = 30.0
        self.mock_controller.wifi_is_connected.return_value = True
        self.mock_controller.get_wireless_ip.return_value = '192.168.1.100'
        self.mock_controller.get_wireless_rssi.return_value = -65
        self.mock_controller.get_wireless_ssid.return_value = 'mock_network'
        self.mock_controller.external_battery = None

    def test_battery_charging_current(self):
        # 0x0102 with raw value 1550 -> 15.5 A
        self.mock_serial.read_register.return_value = [1550]
        val = self.rover.get_battery_charging_current()
        self.assertEqual(val, 15.5)

    def test_battery_current_net_positive_charging(self):
        # Charging 15.5A, Load 3.2A -> Net +12.3A (charging)
        self.rover.get_battery_charging_current = MagicMock(return_value=15.5)
        self.rover.get_load_current = MagicMock(return_value=3.2)
        val = self.rover.get_battery_current()
        self.assertEqual(val, 12.3)

    def test_battery_current_net_negative_discharging(self):
        # Charging 0.0A, Load 5.0A -> Net -5.0A (discharging to load)
        self.rover.get_battery_charging_current = MagicMock(return_value=0.0)
        self.rover.get_load_current = MagicMock(return_value=5.0)
        val = self.rover.get_battery_current()
        self.assertEqual(val, -5.0)

    def test_battery_power(self):
        # Voltage 13.4V, Net Current 12.3A -> 164.82W
        self.rover.get_battery_voltage = MagicMock(return_value=13.4)
        self.rover.get_battery_current = MagicMock(return_value=12.3)
        val = self.rover.get_battery_power()
        self.assertEqual(val, 164.82)

    def test_fault_decoding(self):
        # Bit 0 (battery_over_discharge) + Bit 3 (load_short_circuit) -> 1 | 8 = 9
        self.rover.get_fault_code = MagicMock(return_value=9)
        faults = self.rover.get_faults()
        self.assertEqual(faults, ['battery_over_discharge', 'load_short_circuit'])

    def test_fault_decoding_empty(self):
        self.rover.get_fault_code = MagicMock(return_value=0)
        faults = self.rover.get_faults()
        self.assertEqual(faults, [])

    def test_load_switch_status(self):
        self.mock_serial.read_register.return_value = [1]
        self.assertEqual(self.rover.get_load_switch_status(), 1)
        self.mock_serial.read_register.return_value = [0]
        self.assertEqual(self.rover.get_load_switch_status(), 0)

    def test_api_payload_structure(self):
        api = Api(
            controller=self.mock_controller,
            url='https://api.example.com',
            token='test_token',
            device_id=1
        )
        data = {
            'hardware': 'V1.0.0',
            'version': 'V1.2.0',
            'battery_voltage': 13.4,
            'battery_charging_current': 15.5,
            'battery_current': 12.3,
            'battery_power': 164.82,
            'load_switch_status': 1,
            'fault_code': 0,
            'faults': []
        }
        payload = api._build_solar_reading_payload(data)

        # Root fields: battery_current and battery_power must be calculated floats
        self.assertEqual(payload['battery_current'], 12.3)
        self.assertEqual(payload['battery_power'], 164.82)

        # Extra fields: non-contract telemetry in hardware_device_info['extra']
        # Los valores en extra deben ser tipos simples (número, texto o booleano)
        extra = payload['hardware_device_info']['extra']
        self.assertEqual(extra['battery_charging_current'], 15.5)
        self.assertEqual(extra['load_switch_status'], 1)
        self.assertEqual(extra['fault_code'], 0)
        self.assertEqual(extra['faults'], "")
        for k, v in extra.items():
            self.assertIsInstance(v, (int, float, str, bool))
            self.assertNotIsInstance(v, (list, dict))

        # Caso con fallos activos: debe formatearse como string simple separado por comas
        data_with_faults = dict(data)
        data_with_faults['faults'] = ['battery_over_discharge', 'load_short_circuit']
        payload_with_faults = api._build_solar_reading_payload(data_with_faults)
        self.assertEqual(payload_with_faults['hardware_device_info']['extra']['faults'], 'battery_over_discharge, load_short_circuit')

    def test_home_assistant_list_sanitization(self):
        ha = HomeAssistantConnection(
            controller=self.mock_controller,
            url='http://homeassistant.local:8123',
            token='test_token',
            device_id=1,
            delta_filtering=False
        )
        updated = {}
        ha.update_sensor = lambda entity_id, state, attributes: updated.update({entity_id: state}) or True

        data = {
            'faults': ['battery_over_discharge', 'load_short_circuit'],
            'battery_current': 12.3,
            'battery_power': 164.82
        }
        ha.update_solar_controller_data(data)

        self.assertEqual(updated['sensor.solar_faults'], 'battery_over_discharge, load_short_circuit')
        self.assertEqual(updated['sensor.solar_battery_current'], 12.3)
        self.assertEqual(updated['sensor.solar_battery_power'], 164.82)

    def test_ha_delta_filtering_reduces_requests(self):
        ha = HomeAssistantConnection(
            controller=self.mock_controller,
            url='http://homeassistant.local:8123',
            token='test_token',
            device_id=1,
            delta_filtering=True,
            heartbeat_interval=600,
            static_interval=3600
        )

        sent_calls = []

        def mock_update_sensor(entity_id, state, attributes=None):
            sent_calls.append((entity_id, state))
            ha._last_sent_states[entity_id] = state
            ha._last_sent_times[entity_id] = time.time()
            return True

        ha.update_sensor = mock_update_sensor

        data = {
            'hardware': 'V1.0.0',
            'battery_voltage': 13.4,
            'solar_power': 150.0,
            'charging_status_label': 'mppt'
        }

        # Ciclo 1: primera vez, se deben enviar todas las 4 entidades
        ha.update_solar_controller_data(data)
        self.assertEqual(len(sent_calls), 4)

        # Ciclo 2: datos idénticos -> se deben omitir todas (0 peticiones)
        sent_calls.clear()
        ha.update_solar_controller_data(data)
        self.assertEqual(len(sent_calls), 0)

        # Ciclo 3: ruido por debajo del deadband (voltaje cambia solo 0.01V, potencia 0.2W)
        sent_calls.clear()
        noisy_data = dict(data)
        noisy_data['battery_voltage'] = 13.41  # Menor que umbral 0.05V
        noisy_data['solar_power'] = 150.2      # Menor que umbral 1.0W
        ha.update_solar_controller_data(noisy_data)
        self.assertEqual(len(sent_calls), 0)

        # Ciclo 4: cambio significativo en solar_power (de 150W a 165W)
        sent_calls.clear()
        changed_data = dict(data)
        changed_data['solar_power'] = 165.0
        ha.update_solar_controller_data(changed_data)
        self.assertEqual(len(sent_calls), 1)
        self.assertEqual(sent_calls[0][0], 'sensor.solar_solar_power')
        self.assertEqual(sent_calls[0][1], 165.0)

        # Ciclo 5: cambio de estado discreto (charging_status_label cambia)
        sent_calls.clear()
        status_changed_data = dict(changed_data)
        status_changed_data['charging_status_label'] = 'float'
        ha.update_solar_controller_data(status_changed_data)
        self.assertEqual(len(sent_calls), 1)
        self.assertEqual(sent_calls[0][0], 'sensor.solar_charging_status_label')
        self.assertEqual(sent_calls[0][1], 'float')

    def test_ha_cached_device_and_connection(self):
        ha = HomeAssistantConnection(
            controller=self.mock_controller,
            url='http://homeassistant.local:8123',
            token='test_token',
            device_id=1
        )
        ha._last_connection_ok = True
        ha._last_connection_check_time = time.time()
        ha.device_verified = True

        # En caché, no debe invocar urequests
        self.assertTrue(ha.verify_device_exists())
        self.assertTrue(ha.check_connection())

    def test_rpi_pico_battery_initialization(self):
        # 1. Instanciación sin parámetros de batería (no debe fallar)
        pico = RpiPico(debug=False)
        self.assertIsNone(pico.external_battery)

        # 2. Configuración vía set_external_battery (como se llama en main.py)
        pico.read_external_battery = MagicMock()
        pico.set_external_battery(26, 2.8, 4.1)
        self.assertIsNotNone(pico.external_battery)
        self.assertEqual(pico.external_battery['pin'], 26)
        self.assertEqual(pico.external_battery['threshold_voltage_min'], 2.8)
        self.assertEqual(pico.external_battery['threshold_voltage_max'], 4.1)

        # 3. Instanciación con battery_adc_pin en constructor (retrocompatibilidad)
        pico_kw = RpiPico(battery_adc_pin=26, battery_min_voltage=3.0, battery_max_voltage=4.2)
        self.assertIsNotNone(pico_kw.external_battery)
        self.assertEqual(pico_kw.external_battery['pin'], 26)

        # 4. Comprobación de método init_wifi
        pico.wifi_is_connected = MagicMock(return_value=True)
        self.assertTrue(pico.init_wifi())

    def test_sync_time_daily_interval(self):
        import ntptime
        ntptime.settime = MagicMock()
        import main
        main.last_ntp_sync = 0
        main.NTP_SYNC_INTERVAL = 86400

        # Primer sync (fuerza o last_ntp_sync == 0)
        res = main.sync_time(force=True)
        self.assertTrue(res)
        self.assertEqual(ntptime.settime.call_count, 1)
        self.assertGreater(main.last_ntp_sync, 0)

        # Segundo sync inmediato sin force (debe omitir la llamada a ntptime)
        res2 = main.sync_time(force=False)
        self.assertTrue(res2)
        self.assertEqual(ntptime.settime.call_count, 1)  # No incrementa

        # Con force=True sí debe sincronizar
        res3 = main.sync_time(force=True)
        self.assertTrue(res3)
        self.assertEqual(ntptime.settime.call_count, 2)

    def test_renogy_static_intensity_cache(self):
        with unittest.mock.patch.object(RenogyRoverLi, '_initialize_static_data', lambda self: None):
            rover = RenogyRoverLi(device_id=1, debug=False)
        rover.serial = MagicMock()
        rover.serial.read_register.return_value = [0x0014]  # 20A
        rover._cached_system_intensity_current = None

        val1 = rover.get_system_intensity_current()
        self.assertEqual(val1, 20)
        self.assertEqual(rover.serial.read_register.call_count, 1)

        # Segunda llamada: debe provenir de caché
        val2 = rover.get_system_intensity_current()
        self.assertEqual(val2, 20)
        self.assertEqual(rover.serial.read_register.call_count, 1)

    def test_renogy_historical_cache_interval(self):
        with unittest.mock.patch.object(RenogyRoverLi, '_initialize_static_data', lambda self: None):
            rover = RenogyRoverLi(device_id=1, debug=False, historical_interval=600)
        rover.serial = MagicMock()
        # Mock 11 registers for 0x0115 block
        mock_hist_block = [10, 2, 5, 0, 150, 0, 120, 0, 80, 0, 60]
        rover.serial.read_register.return_value = mock_hist_block
        rover._cached_historical_datas = None
        rover._last_historical_read_time = 0

        # Primera llamada: lee del serial
        hist1 = rover.get_historical_info_datas(force=False)
        self.assertEqual(hist1['historical_total_days_operating'], 10)
        self.assertEqual(hist1['historical_total_charging_amp_hours'], 150)
        self.assertEqual(rover.serial.read_register.call_count, 1)

        # Segunda llamada inmediata: debe devolver de caché sin llamar al serial
        hist2 = rover.get_historical_info_datas(force=False)
        self.assertEqual(hist2['historical_total_charging_amp_hours'], 150)
        self.assertEqual(rover.serial.read_register.call_count, 1)

        # Con force=True: debe forzar lectura
        hist3 = rover.get_historical_info_datas(force=True)
        self.assertEqual(rover.serial.read_register.call_count, 2)

    def test_renogy_get_all_datas_fast(self):
        with unittest.mock.patch.object(RenogyRoverLi, '_initialize_static_data', lambda self: None):
            rover = RenogyRoverLi(device_id=1, debug=False, historical_interval=600)
        rover.serial = MagicMock()

        # Mock estáticos
        rover._cached_hardware = 'V1.0.0'
        rover._cached_version = 'V1.0.0'
        rover._cached_serial_number = '123456'
        rover._cached_system_voltage_current = 24
        rover._cached_system_intensity_current = 20
        rover._cached_battery_type = 'lithium'
        rover._cached_nominal_battery_capacity = 100

        # Mock bloque 1 (0x0100 a 0x0114 = 21 regs)
        # 0: percentage (90)
        # 1: battery_voltage * 10 (264 -> 26.4V)
        # 2: battery_charging_current * 100 (550 -> 5.5A)
        # 3: temp_reg (controller 30C << 8 | battery 25C) -> (30 << 8) | 25
        # 4: load_voltage * 10 (260 -> 26.0V)
        # 5: load_current * 100 (150 -> 1.5A)
        # 6: load_power (39W)
        # 7: solar_voltage * 10 (350 -> 35.0V)
        # 8: solar_current * 100 (420 -> 4.2A)
        # 9: solar_power (147W)
        # 10: load_switch_status (1)
        # 11-20: diarios (min 24.0, max 28.0, max_chg_a 10.0, max_dis_a 5.0, max_chg_w 300, max_dis_w 150, chg_ah 40, dis_ah 20, gen 5, con 3)
        block1 = [
            90, 264, 550, (30 << 8) | 25,
            260, 150, 39,
            350, 420, 147,
            1,
            240, 280, 1000, 500, 300, 150, 40, 20, 5, 3
        ]

        # Mock bloque 2 (0x0120 a 0x0121 = 2 regs)
        # 0: charging_status (3 -> 'equalizing')
        # 1: fault_code (0)
        block2 = [3, 0]

        # Mock bloque histórico
        mock_hist_block = [10, 0, 5, 0, 200, 0, 150, 0, 90, 0, 70]

        def side_effect(address, bits=2, type_data=None):
            if address == 0x0100 and bits == 21:
                return block1
            elif address == 0x0120 and bits == 2:
                return block2
            elif address == 0x0115 and bits == 11:
                return mock_hist_block
            return None

        rover.serial.read_register.side_effect = side_effect

        data = rover.get_all_datas_fast(refresh_historical=True)

        # Verificación de datos estáticos
        self.assertEqual(data['hardware'], 'V1.0.0')
        self.assertEqual(data['battery_type'], 'lithium')

        # Verificación de datos en tiempo real
        self.assertEqual(data['battery_percentage'], 90)
        self.assertEqual(data['battery_voltage'], 26.4)
        self.assertEqual(data['battery_charging_current'], 5.5)
        self.assertEqual(data['battery_temperature'], 25)
        self.assertEqual(data['controller_temperature'], 30)
        self.assertEqual(data['load_voltage'], 26.0)
        self.assertEqual(data['load_current'], 1.5)
        self.assertEqual(data['load_power'], 39)
        self.assertEqual(data['solar_voltage'], 35.0)
        self.assertEqual(data['solar_current'], 4.2)
        self.assertEqual(data['solar_power'], 147)
        self.assertEqual(data['load_switch_status'], 1)

        # Verificación de cálculos derivados
        # battery_current = 5.5 (chg) - 1.5 (load) = 4.0A
        self.assertEqual(data['battery_current'], 4.0)
        # battery_power = 26.4V * 4.0A = 105.6W
        self.assertEqual(data['battery_power'], 105.6)
        self.assertGreater(data['street_light_brightness'], 0)
        self.assertTrue(data['street_light_status'])

        # Verificación de estado de carga y fallos
        self.assertEqual(data['charging_status'], 3)
        self.assertEqual(data['charging_status_label'], 'equalizing')
        self.assertEqual(data['fault_code'], 0)
        self.assertEqual(data['faults'], [])

        # Verificación de históricos
        self.assertEqual(data['historical_total_days_operating'], 10)
        self.assertEqual(data['historical_total_charging_amp_hours'], 200)

    def test_renogy_get_all_datas_fast_fallback_to_standard(self):
        with unittest.mock.patch.object(RenogyRoverLi, '_initialize_static_data', lambda self: None):
            rover = RenogyRoverLi(device_id=1, debug=False)
        rover.serial = MagicMock()
        # Fallo en lectura por bloque
        rover.serial.read_register.return_value = None

        rover.get_all_datas = MagicMock(return_value={'fallback_key': 'fallback_value'})
        res = rover.get_all_datas_fast()
        self.assertEqual(res, {'fallback_key': 'fallback_value'})
        rover.get_all_datas.assert_called_once()


if __name__ == '__main__':
    unittest.main()
