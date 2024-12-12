from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_controller():
    """Мок-контроллер для подмены PowerSourceController."""
    class MockController:
        async def send_command(self, command):
            pass

        async def set_channel(self, channel, voltage, current):
            await self.send_command(f"SOURce{channel}:CURRent {current}")
            await self.send_command(f"SOURce{channel}:VOLTage {voltage}")
            await self.send_command(f"OUTPut{channel}:STATe ON")
        
        async def disable_channel(self, channel):
            await self.send_command(f"OUTPut{channel}:STATe OFF")

        async def measure_channel(self, channel):
            await self.send_command(f"MEASure{channel}:VOLTage?")
            await self.send_command(f"MEASure{channel}:CURRent?")
            await self.send_command(f"MEASure{channel}:POWer?")

    return MockController()

@pytest.mark.asyncio
async def test_set_channel(mock_controller):
    mock_controller.send_command = AsyncMock()
    await mock_controller.set_channel(1, 5.0, 1.0)
    mock_controller.send_command.assert_any_call("SOURce1:CURRent 1.0")
    mock_controller.send_command.assert_any_call("SOURce1:VOLTage 5.0")
    mock_controller.send_command.assert_any_call("OUTPut1:STATe ON")


@pytest.mark.asyncio
async def test_disable_channel(mock_controller):
    mock_controller.send_command = AsyncMock()
    await mock_controller.disable_channel(1)
    # Проверяем, что метод send_command был вызван с командой для выключения питания
    mock_controller.send_command.assert_any_call("OUTPut1:STATe OFF")


@pytest.mark.asyncio
async def test_measure_channel(mock_controller):
    mock_controller.send_command = AsyncMock()
    await mock_controller.measure_channel(1)
    # Проверяем, что метод send_command был вызван с командами для измерения напряжения, тока и мощности
    mock_controller.send_command.assert_any_call("MEASure1:VOLTage?")
    mock_controller.send_command.assert_any_call("MEASure1:CURRent?")
    mock_controller.send_command.assert_any_call("MEASure1:POWer?")
    