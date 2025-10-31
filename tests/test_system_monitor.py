import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plugins.system_monitor import SystemMonitorPlugin

class TestSystemMonitorPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = SystemMonitorPlugin()

    @patch('plugins.system_monitor.psutil')
    def test_get_cpu_usage(self, mock_psutil):
        mock_psutil.cpu_percent.return_value = 55.5
        self.assertEqual(self.plugin.get_cpu_usage(), 55.5)
        mock_psutil.cpu_percent.assert_called_once_with(interval=None)

    @patch('plugins.system_monitor.psutil')
    def test_get_memory_usage(self, mock_psutil):
        mock_vm = MagicMock()
        mock_vm.percent = 42.1
        mock_psutil.virtual_memory.return_value = mock_vm
        self.assertEqual(self.plugin.get_memory_usage(), 42.1)

    @patch('plugins.system_monitor.psutil')
    def test_get_battery_status_with_battery(self, mock_psutil):
        mock_battery = MagicMock()
        mock_battery.percent = 99
        mock_battery.power_plugged = True
        mock_psutil.sensors_battery.return_value = mock_battery

        expected_status = {"percent": 99, "power_plugged": True}
        self.assertEqual(self.plugin.get_battery_status(), expected_status)

    @patch('plugins.system_monitor.psutil')
    def test_get_battery_status_no_battery(self, mock_psutil):
        mock_psutil.sensors_battery.return_value = None
        self.assertIsNone(self.plugin.get_battery_status())

    @patch.object(SystemMonitorPlugin, 'get_cpu_usage', return_value=73.2)
    def test_handle_cpu_usage(self, mock_get_cpu):
        mock_assistant = MagicMock()
        command = ("get_cpu_usage", {})
        self.plugin.handle(command, mock_assistant)
        mock_assistant.speak.assert_called_once_with("Current CPU usage is at 73.2%.")

    @patch.object(SystemMonitorPlugin, 'get_memory_usage', return_value=60.8)
    def test_handle_memory_usage(self, mock_get_mem):
        mock_assistant = MagicMock()
        command = ("get_memory_usage", {})
        self.plugin.handle(command, mock_assistant)
        mock_assistant.speak.assert_called_once_with("Current memory usage is at 60.8%.")

    @patch.object(SystemMonitorPlugin, 'get_battery_status')
    def test_handle_battery_status_plugged_in(self, mock_get_battery):
        mock_get_battery.return_value = {"percent": 88, "power_plugged": True}
        mock_assistant = MagicMock()
        command = ("get_battery_status", {})
        self.plugin.handle(command, mock_assistant)
        mock_assistant.speak.assert_called_once_with("Battery is at 88%, and is plugged in.")

    @patch.object(SystemMonitorPlugin, 'get_battery_status')
    def test_handle_battery_status_unplugged(self, mock_get_battery):
        mock_get_battery.return_value = {"percent": 54, "power_plugged": False}
        mock_assistant = MagicMock()
        command = ("get_battery_status", {})
        self.plugin.handle(command, mock_assistant)
        mock_assistant.speak.assert_called_once_with("Battery is at 54%, and is not plugged in.")

    @patch.object(SystemMonitorPlugin, 'get_battery_status', return_value=None)
    def test_handle_battery_status_no_battery(self, mock_get_battery):
        mock_assistant = MagicMock()
        command = ("get_battery_status", {})
        self.plugin.handle(command, mock_assistant)
        mock_assistant.speak.assert_called_once_with("No battery detected in the system.")


if __name__ == '__main__':
    unittest.main()
