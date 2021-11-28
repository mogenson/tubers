from dataclasses import dataclass
from struct import unpack

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


@dataclass
class Lights:
    DARKER = 4
    RIGHT_BRIGHTER = 5
    LEFT_BRIGHTER = 6
    LIGHTER = 7

    state: int
    left: int = 0
    right: int = 0

    @classmethod
    def from_packet(cls, packet: Packet):
        return Lights(
            packet.payload[4],
            unpack(">H", packet.payload[5:7])[0],
            unpack(">H", packet.payload[7:9])[0],
        )


def note(note: str, A4=440) -> float:
    """Convert a note name into frequency in hertz: eg. 'C#5'"""
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = int(note[-1])
    step = notes.index(note[0:-1])
    step += ((octave - 1) * 12) + 1
    return A4 * 2 ** ((step - 46) / 12)
