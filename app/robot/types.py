from dataclasses import dataclass

from .packet import Packet


@dataclass
class Bumpers:
    left: bool
    right: bool

    @classmethod
    def from_packet(cls, packet: Packet):
        return Bumpers(packet.payload[4] & 0x80 != 0, packet.payload[4] & 0x40 != 0)


@dataclass
class Colors:
    WHITE = 0
    BLACK = 1
    RED = 2
    GREEN = 3
    BLUE = 4
    ORANGE = 5
    YELLOW = 6
    MAGENTA = 7
    NONE = 15
    ANY = -1

    colors: list[int]

    @classmethod
    def from_packet(cls, packet: Packet):
        return Colors([c >> i & 0xF for c in packet.payload for i in range(4, -1, -4)])
