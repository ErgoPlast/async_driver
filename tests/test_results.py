from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_controller():
    """Мок-контроллер для подмены PowerSourceController."""
    class MockController:
        telemetry = {}

        async def send_command(self, command):
            # Симуляция ответов на команды измерения
            if "MEASure" in command:
                if "VOLTage" in command:
                    return "5.0"
                elif "CURRent" in command:
                    return "1.0"
                elif "POWer" in command:
                    return "5.0"
                elif "MEASure" in command and "VOLTage" in command:
                    return "0.0"
            elif "OUTPut" in command:
                return "OK"  # Ответ для команды выключения

        async def measure_channel(self, channel):
            """Метод для измерения значений канала."""
            voltage = await self.send_command(f"MEASure{channel}:VOLTage?")
            current = await self.send_command(f"MEASure{channel}:CURRent?")
            power = await self.send_command(f"MEASure{channel}:POWer?")
            return {
                "voltage": float(voltage),
                "current": float(current),
                "power": float(power),
            }

        async def get_all_channels_status(self):
            """Метод для получения статуса всех каналов."""
            return {
                "timestamp": "2024-12-10",
                "channels": {
                    1: await self.measure_channel(1),
                    2: await self.measure_channel(2),
                    3: await self.measure_channel(3),
                    4: await self.measure_channel(4),
                },
            }

        async def disable_channel(self, channel):
            """Отключение канала питания."""
            await self.send_command(f"OUTPut{channel}:STATe OFF")
            ans = await self.send_command(f"MEASure{channel}:VOLTage?")
            return {"status_channel": ans}

    return MockController()

@pytest.mark.asyncio
async def test_measure_channel(mock_controller):

    mock_controller.send_command = AsyncMock(side_effect=[
        "5.0",  # Voltage response
        "1.0",  # Current response
        "5.0"   # Power response
    ])

    telemetry = await mock_controller.measure_channel(1)

    assert telemetry == {"voltage": 5.0, "current": 1.0, "power": 5.0}

@pytest.mark.asyncio
async def test_status_with_timestamp(mock_controller):
    mock_controller.measure_channel = AsyncMock(side_effect=[
        {"voltage": 5.0, "current": 1.0, "power": 5.0},    # Канал 1
        {"voltage": 3.3, "current": 0.5, "power": 1.65},  # Канал 2
        {"voltage": 12.0, "current": 2.0, "power": 24.0}, # Канал 3
        {"voltage": 0.0, "current": 0.0, "power": 0.0},   # Канал 4
    ])
    result = await mock_controller.get_all_channels_status()

    # Проверяем, что результат имеет корректный формат
    assert "timestamp" in result
    assert "channels" in result

    # Проверяем, что данные по каналам корректны
    channels = result["channels"]
    assert len(channels) == 4

    assert channels[1] == {"voltage": 5.0, "current": 1.0, "power": 5.0}
    assert channels[2] == {"voltage": 3.3, "current": 0.5, "power": 1.65}
    assert channels[3] == {"voltage": 12.0, "current": 2.0, "power": 24.0}
    assert channels[4] == {"voltage": 0.0, "current": 0.0, "power": 0.0}


@pytest.mark.asyncio
async def test_disable_channel(mock_controller):
    mock_controller.send_command = AsyncMock(side_effect=["OK", "Отключено"])  # "OK" для отключения, "0.0" для измерения напряжения
    result = await mock_controller.disable_channel(1)

    # Проверяем, что команды отправлены правильно
    mock_controller.send_command.assert_any_call("OUTPut1:STATe OFF")
    mock_controller.send_command.assert_any_call("MEASure1:VOLTage?")

    # Проверяем результат выполнения
    assert result == {"status_channel": "Отключено"}  # Ожидается, что возвращается Отключено