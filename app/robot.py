from asyncio import Future, get_running_loop
from contextlib import redirect_stdout
from struct import pack, unpack

from .bluetooth import Bluetooth
from .output import redirect_output
from .packet import Packet


class Robot:
    def __init__(self, bluetooth):
        self._bluetooth = bluetooth
        self._bluetooth.data_received_callback = self._data_received
        self._loop = get_running_loop()
        self._responses = {}
        self._events = {}
        self._inc = 0
        self._running = False
        self.debug = False

    @property
    def inc(self):
        """Access then increment wrapping id"""
        inc = self._inc
        self._inc += 1
        if self._inc > 255:
            self._inc = 0
        return inc

    @staticmethod
    def bound(value, low, high):
        """Constrain value between low and high"""
        return min(high, max(low, value))

    def run(self):
        self._responses = {}
        self._events = {}
        self._running = True

    def is_running(self):
        return self._running

    def stop(self):
        self._running = False

    async def _run_callback(self, callback):
        with redirect_output():
            try:
                await callback()
            except Exception as error:
                print(f"Error: {error}")

    def _data_received(self, data):
        if not self._running:
            return

        packet = Packet.from_bytes(data)

        if self.debug:
            print(f"RX: {packet}")

        if not packet.check_crc():
            print(f"CRC fail: {packet}")
            return

        key = (packet.dev, packet.cmd, packet.inc)
        if key in self._responses.keys():
            future = self._responses.pop(key)
            future.set_result(packet)

        key = (packet.dev, packet.cmd)
        if key in self._events.keys():
            self._loop.create_task(self._run_callback(self._events[key]))
            # for (filter, callback) in self._events[key]:
            #     if filter(packet):
            #         self._loop.create_task(callback(packet))

    async def write_packet(self, packet):
        """Send a packet"""
        if self._running:
            await self._bluetooth.write(packet.to_bytes())
            print(f"TX: {packet}")

    def on_bump(self, callback):
        self._events[(12, 0)] = callback

    async def drive_distance(self, distance):
        """Drive distance in centimeters"""
        dev, cmd, inc = 1, 8, self.inc
        packet = Packet(dev, cmd, inc, pack(">i", int(distance * 10)))
        future = self.loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(packet)
        await future
