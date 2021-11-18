from asyncio import Future, get_running_loop
from struct import pack, unpack

from .bluetooth import Bluetooth
from .packet import Packet


class Robot:
    def __init__(self, bluetooth):
        self.bluetooth = bluetooth
        self.bluetooth.data_received_callback = self._data_received
        self.loop = get_running_loop()
        self.pending = {}
        self._inc = 0

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
        return min(high, max(low, value))

    def _data_received(self, data):
        packet = Packet.from_bytes(data)
        print(f"RX: {packet}")
        if packet.check_crc():
            key = (packet.dev, packet.cmd, packet.inc)
            if key in self.pending.keys():
                future = self.pending.pop(key)
                future.set_result(packet)

    async def write_packet(self, packet):
        """Send a packet"""
        await self.bluetooth.write(packet.to_bytes())
        print(f"TX: {packet}")

    async def drive_distance(self, distance):
        """Drive distance in centimeters"""
        dev, cmd, inc = 1, 8, self.inc
        packet = Packet(dev, cmd, inc, pack(">i", int(distance * 10)))
        future = self.loop.create_future()
        self.pending[(dev, cmd, inc)] = future
        await self.write_packet(packet)
        await future
