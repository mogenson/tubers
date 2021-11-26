from asyncio import Future, get_running_loop, wait_for
from collections import defaultdict
from contextlib import redirect_stdout
from struct import pack, unpack

from .bluetooth import Bluetooth
from .debug import debug
from .packet import Packet


class Robot:
    DEFAULT_TIMEOUT = 3

    def __init__(self, bluetooth):
        self._bluetooth = bluetooth
        self._bluetooth.data_received_callback = self._data_received
        self._loop = get_running_loop()
        self._responses = {}
        self._events = defaultdict(list)
        self._inc = 0
        self._running = False

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
        self._events = defaultdict(list)
        self._running = True

    def is_running(self):
        return self._running

    def stop(self):
        self._running = False

    def _data_received(self, data):
        if not self._running:
            return

        packet = Packet.from_bytes(data)
        debug(f"RX: {packet}")

        if not packet.check_crc():
            debug(f"CRC fail: {packet}")
            return

        key = (packet.dev, packet.cmd, packet.inc)
        if key in self._responses.keys():
            future = self._responses.pop(key)
            future.set_result(packet)

        key = (packet.dev, packet.cmd)
        if key in self._events.keys():
            for (filter, callback) in self._events[key]:
                args = filter(packet)
                if args:
                    self._loop.create_task(callback(args))

    async def write_packet(self, packet):
        """Send a packet"""
        if self._running:
            await self._bluetooth.write(packet.to_bytes())
            debug(f"TX: {packet}")

    def on_bump(self, filter=None):
        def decorator(callback):
            def filter_function(packet):
                left = packet.payload[4] & 0x80 != 0
                right = packet.payload[4] & 0x40 != 0
                if not filter or filter == (left, right):
                    return (left, right)

            self._events[(12, 0)].append((filter_function, callback))

        return decorator

    async def drive_distance(self, distance):
        """Drive distance in centimeters"""
        dev, cmd, inc = 1, 8, self.inc
        packet = Packet(dev, cmd, inc, pack(">i", int(distance * 10)))
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(packet)
        await wait_for(future, self.DEFAULT_TIMEOUT + int(distance / 10))
