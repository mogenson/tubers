from asyncio import get_running_loop

import js

from .bluetooth import Bluetooth
from .robot import Robot


class App:
    def __init__(self):
        self.editor = js.editor
        self.loop = get_running_loop()
        self.bluetooth = Bluetooth()
        self.disconnected_callback = self.disconnected
        self.robot = Robot(self.bluetooth)
        self.play_button = js.document.getElementById("play")
        self.play_button.onclick = lambda event: self.loop.create_task(self.play())
        self.connect_button = js.document.getElementById("connect")
        self.connect_button.onclick = lambda event: self.loop.create_task(
            self.connect()
        )
        self.connect_button.disabled = False

    def disconnected(self):
        self.connect_button.innerHTML = "Connect"
        self.connect_button.disabled = False
        self.play_button.disabled = True
        print("disconnected")

    async def connect(self):
        if not self.bluetooth.is_connected():
            print("connect")
            self.connect_button.disabled = True
            await self.bluetooth.connect()
            self.connect_button.innerHTML = "Disconnect"
            self.connect_button.disabled = False
            self.play_button.disabled = False
            print("connected")
        else:
            print("disconnect")
            self.connect_button.disabled = True
            self.bluetooth.disconnect()

    async def play(self):
        code = self.editor.getValue()
        exec(
            f"async def user_program(robot): "
            + "".join(f"\n {line}" for line in code.split("\n"))
        )
        await locals()["user_program"](self.robot)


async def main():
    app = App()
