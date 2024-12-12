import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Настройка логгера
logging.basicConfig(level=logging.INFO, filename="telemetry.log", format="%(asctime)s - %(message)s")

class PowerSourceController:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.telemetry = {}

    async def connect(self):
        """Подключение к источнику питания по TCP."""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logging.info("Connected to power source")

    async def send_command(self, command):
        """Отправка команды."""
        self.writer.write(f"{command}\n".encode())
        await self.writer.drain()
        response = await self.reader.readline()
        return response.decode().strip()

    async def set_channel(self, channel, voltage, current):
        """Настройка и включение канала питания."""
        await self.send_command(f"SOURce{channel}:CURRent {current}")
        await self.send_command(f"SOURce{channel}:VOLTage {voltage}")
        await self.send_command(f"OUTPut{channel}:STATe ON")

    async def disable_channel(self, channel):
        """Отключение канала питания."""
        await self.send_command(f"OUTPut{channel}:STATe OFF")
        ans = await self.send_command(f"MEASure{channel}:VOLTage?")
        if int(ans) == 0:
            ans = 'Отключен'
        return {
            "status_channel": ans
        }

    async def measure_channel(self, channel):
        """Запрос телеметрии для канала."""
        voltage = await self.send_command(f"MEASure{channel}:VOLTage?")
        current = await self.send_command(f"MEASure{channel}:CURRent?")
        power = await self.send_command(f"MEASure{channel}:POWer?")
        return {
            "voltage": float(voltage),
            "current": float(current),
            "power": float(power),
        }
    
    async def get_all_channels_status(self):
        """Возвращает текущее состояние всех каналов."""
        status = {}
        for channel in range(1, 5):
            telemetry = await self.measure_channel(channel)
            status[channel] = telemetry
        return {
            "timestamp": datetime.now().isoformat(),
            "channels": status
        }

    async def poll_telemetry(self, interval=5):
        """Постоянный опрос телеметрии всех каналов."""
        while True:
            for channel in range(1, 5):
                self.telemetry[channel] = await self.measure_channel(channel)
                logging.info(f"Channel {channel}: {self.telemetry[channel]}")
            await asyncio.sleep(interval)


class RestAPI:
    def __init__(self, controller):
        self.controller = controller

    async def handle_status(self, request):
        try:
            status = await self.controller.get_all_channels_status()
            return aiohttp.web.json_response(status)
        except Exception as e:
            logging.error(f"Error in handle_status: {e}")
            return aiohttp.web.Response(status=500, text="Internal Server Error")

    async def handle_enable_channel(self, request):
        """Включение канала питания."""
        data = await request.json()
        channel = data["channel"]
        voltage = data["voltage"]
        current = data["current"]
        await self.controller.set_channel(channel, voltage, current)
        return aiohttp.web.Response(text="Channel enabled")

    async def handle_disable_channel(self, request):
        """Отключение канала питания."""
        data = await request.json()
        channel = data["channel"]
        response = await self.controller.disable_channel(channel)
        if response['status_channel'] == 'Отключен':
            return aiohttp.web.Response(text="Channel disabled")
        else:
            return aiohttp.web.Response(status=500, text="Internal Server Error")

    def setup_routes(self, app):
        app.router.add_get("/status", self.handle_status)
        app.router.add_post("/enable", self.handle_enable_channel)
        app.router.add_post("/disable", self.handle_disable_channel)


async def main():
    controller = PowerSourceController(host="192.168.0.10", port=1440) # Заводятся ip/port источника питания
    await controller.connect()

    # Запуск задачи опроса телеметрии
    asyncio.create_task(controller.poll_telemetry())

    # Настройка REST API
    api = RestAPI(controller)
    app = aiohttp.web.Application()
    api.setup_routes(app)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    print("REST API running on http://0.0.0.0:8080")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
