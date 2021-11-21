from asyncio import get_running_loop
from contextlib import redirect_stdout
from io import StringIO

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
        self.text_area = js.document.getElementById("output")
        self.play_button = js.document.getElementById("play")
        self.play_button.onclick = lambda event: self.loop.create_task(self.play())
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
        self.user_program = locals()["user_program"]
        with redirect_stdout(StringIO()) as output:
            try:
                await self.user_program(self.robot)
            except Exception as error:
                print(f"Error: {error}")
        self.text_area.innerHTML = output.getvalue()


async def main():
    app = App()
