from asyncio import Future, get_running_loop, wait_for
from collections import defaultdict
from struct import pack, unpack

from ..bluetooth import Bluetooth
from ..debug import debug
from .packet import Packet
from .types import Bumpers, Colors


class Robot:
    """
    Object to control Bluetooth connected robot. Use `on_` decorators to
    register event handlers. Use other methods to send commands to robot and
    wait for response. Don't forget to await async methods!
    """

    DEFAULT_TIMEOUT = 3

    def __init__(self, bluetooth):
        self._bluetooth = bluetooth
        self._bluetooth.data_received_callback = self._data_received
        self._loop = get_running_loop()
        self._responses = {}
        self._events = defaultdict(list)
        self._inc = 0
        self._running = False
        self._enable_motors = True

    def on_color(self, filter: Colors = None):
        """
        Decorator for event handler of type: async callback(colors: Colors) Use
        default None filter to pass every event. Set filter to an instance of
        Colors() to only pass events that match filter. Use Colors.ANY for any
        color. Colors.colors length can be from 1 to 32.
        """

        def decorator(callback):
            def filter_function(packet):
                colors = Colors.from_packet(packet)
                if not filter:
                    return colors
                # get size of each zone
                chunk = round(len(colors.colors) / len(filter.colors))
                # chop color list into zones
                zones = [
                    colors.colors[i : i + chunk]
                    for i in range(0, len(colors.colors), chunk)
                ]
                # check if filter color exists in each zone (or is ANY)
                result = map(
                    lambda x: x[0] == Colors.ANY or x[0] in x[1],
                    zip(filter.colors, zones),
                )
                return colors if all(result) else None

            self._events[(4, 2)].append((filter_function, callback))

        return decorator

    def on_bump(self, filter: Bumpers = None):
        """
        Decorator for event handler of type: async callback(bumpers: Bumpers)
        Use default None filter to pass every event. Set filter to an instance
        of Bumpers() to only pass events that match filter.
        """

        def decorator(callback):
            def filter_function(packet):
                bumpers = Bumpers.from_packet(packet)
                return bumpers if not filter or filter == bumpers else None

            self._events[(12, 0)].append((filter_function, callback))

        return decorator

    async def drive_distance(self, distance: float):
        """Drive distance in centimeters"""
        if self._enable_motors:
            dev, cmd, inc = 1, 8, self.inc
            packet = Packet(dev, cmd, inc, pack(">i", int(distance * 10)))
            future = self._loop.create_future()
            self._responses[(dev, cmd, inc)] = future
            await self.write_packet(packet)
        await wait_for(future, self.DEFAULT_TIMEOUT + int(distance / 10))

    @property
    def inc(self):
        """Access then increment wrapping ID"""
        inc = self._inc
        self._inc += 1
        if self._inc > 255:
            self._inc = 0
        return inc

    @staticmethod
    def bound(value, low, high):
        """Constrain value between low and high"""
        return min(high, max(low, value))

    async def run(self):
        """Enable the event handlers and robot communication"""
        self._responses = {}
        self._events = defaultdict(list)
        # on stop handler
        self._events[(0, 4)].append((lambda packet: packet, lambda packet: self.stop()))
        # on stall handler
        self._events[(1, 29)].append(
            (lambda packet: False, lambda enable: self.enable_motors(enable))
        )
        # on cliff handler
        self._events[(20, 0)].append(
            (
                lambda packet: packet.payload[4] == 0,
                lambda enable: self.enable_motors(enable),
            )
        )
        self._inc = 0
        self._running = True

    def is_running(self) -> bool:
        """Return True if robot is running"""
        return self._running

    async def stop(self):
        """Stop robot and end communication"""
        await self.write_packet(Packet(0, 3, self.inc))
        self._running = False

    def enable_motors(self, enable: bool):
        """Block/allow motor commands"""
        self._enable_motors = enable

    def _data_received(self, data: bytes):
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

    async def write_packet(self, packet: Packet):
        """Send a packet to robot"""
        if self._running:
            await self._bluetooth.write(packet.to_bytes())
            debug(f"TX: {packet}")
