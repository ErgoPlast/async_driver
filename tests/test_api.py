import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from unittest.mock import AsyncMock

from async_driver.async_server_dc import RestAPI

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_controller():
    """Мок-контроллер для подмены PowerSourceController."""
    class MockController:
        telemetry = {}

        async def set_channel(self, channel, voltage, current):
            self.telemetry[channel] = {"voltage": voltage, "current": current}

        async def disable_channel(self, channel):
            self.telemetry.pop(channel, None)
            return {"status_channel": "Отключен"}

        async def get_all_channels_status(self):
            return {
                "timestamp": "2024-12-10T14",
                "channels": {
                    1: {"voltage": 5.0, "current": 1.0, "power": 5.0},
                    2: {"voltage": 3.3, "current": 0.5, "power": 1.65},
                    3: {"voltage": 12.0, "current": 2.0, "power": 24.0},
                    4: {"voltage": 0.0, "current": 0.0, "power": 0.0},
                },
            }

    return MockController()

@pytest.fixture
async def client(mock_controller):
    """Создание тестового клиента для API."""
    api = RestAPI(mock_controller)
    app = web.Application()
    api.setup_routes(app)
    server = TestServer(app)
    client1 = TestClient(server)
    await server.start_server()
    return client1

@pytest.mark.asyncio
async def test_enable_route(client):
    client_instance = await client
    response = await client_instance.post("/enable", json={"channel": 1, "voltage": 5.0, "current": 1.0})
    assert response.status == 200
    text = await response.text()
    assert text == "Channel enabled"

@pytest.mark.asyncio
async def test_disable_route(client):
    # Отправляем POST-запрос на /disable с указанием канала
    client_instance = await client
    response = await client_instance.post("/disable", json={"channel": 1})
    assert response.status == 200
    text = await response.text()
    assert text == "Channel disabled"

@pytest.mark.asyncio
async def test_status_route(client):
    client_instance = await client
    response = await client_instance.get("/status")
    assert response.status == 200
