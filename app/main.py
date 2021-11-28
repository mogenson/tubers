import asyncio
import sys

import js

from .bluetooth import Bluetooth
from .debug import debug
from .output import OutputIO
from .robot import *


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
        self.play_button.onclick = lambda event: self.loop.create_task(self.play())
        self.connect_button = js.document.getElementById("connect")
        self.connect_button.onclick = lambda event: self.loop.create_task(
            self.connect()
        )
        self.connect_button.disabled = False
        self.user_program = None
        self.set_examples()

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

    async def play(self):
        if not self.robot.is_running():
            self.play_button.innerHTML = "Stop"
            self.output.clear()
            await self.robot.run()
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
            await self.robot.stop()
            self.play_button.innerHTML = "Play"

    def set_examples(self):
        def _set_example(id):
            with open(sys.path[-1] + "/examples/" + id + ".py") as example:
                self.editor.setValue(example.read(), -1)

        for id in ["events", "plot", "import"]:
            js.document.getElementById(id).onclick = lambda event, id=id: _set_example(
                id
            )


async def main():
    app = App()
