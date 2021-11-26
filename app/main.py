import asyncio
import sys

import js

from .bluetooth import Bluetooth
from .debug import debug
from .output import OutputIO
from .robot import Robot


class App:
    def __init__(self):
        self.output = OutputIO()
        sys.stdout = self.output
        self.editor = js.editor
        self.loop = asyncio.get_running_loop()
        self.bluetooth = Bluetooth()
        self.bluetooth.disconnected_callback = self.disconnected
        self.robot = Robot(self.bluetooth)
        self.play_button = js.document.getElementById("play")
        self.play_button.onclick = lambda event: self.play()
        self.connect_button = js.document.getElementById("connect")
        self.connect_button.onclick = lambda event: self.loop.create_task(
            self.connect()
        )
        self.connect_button.disabled = False
        self.user_program = None

    def disconnected(self):
        self.connect_button.innerHTML = "Connect"
        self.connect_button.disabled = False
        self.play_button.disabled = True
        debug("disconnected")

    async def connect(self):
        if not self.bluetooth.is_connected():
            debug("connect")
            self.connect_button.disabled = True
            await self.bluetooth.connect()
            self.connect_button.innerHTML = "Disconnect"
            self.connect_button.disabled = False
            self.play_button.disabled = False
            debug("connected")
        else:
            debug("disconnect")
            self.connect_button.disabled = True
            self.bluetooth.disconnect()

    def play(self):
        if not self.robot.is_running():
            self.play_button.innerHTML = "Stop"
            self.output.clear()
            self.robot.run()
            code = self.editor.getValue()
            exec(
                f"async def _user_program(robot): "
                + "".join(f"\n {line}" for line in code.split("\n"))
            )
            self.user_program = self.loop.create_task(
                locals()["_user_program"](self.robot)
            )
        else:
            self.user_program.cancel()
            self.robot.stop()
            self.play_button.innerHTML = "Play"


async def main():
    app = App()
