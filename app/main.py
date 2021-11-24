from asyncio import get_running_loop
from contextlib import redirect_stdout
from io import TextIOBase

import js

from .bluetooth import Bluetooth
from .robot import Robot


class HTMLElementIO(TextIOBase):
    def __init__(self, element):
        self.element = element
        self.element.innerHTML = ""

    def write(self, string):
        self.element.innerHTML += string


class App:
    def __init__(self):
        self.editor = js.editor
        self.loop = get_running_loop()
        self.bluetooth = Bluetooth()
        self.disconnected_callback = self.disconnected
        self.robot = Robot(self.bluetooth)
        self.text_area = js.document.getElementById("output")
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

    def play(self):
        if not self.robot.is_running():
            self.play_button.innerHTML = "Stop"
            self.robot.run()
            self.user_program = self.loop.create_task(self.run_user_program())
        else:
            self.user_program.cancel()
            self.robot.stop()
            self.play_button.innerHTML = "Play"

    async def run_user_program(self):
        code = self.editor.getValue()
        exec(
            f"async def user_program(robot): "
            + "".join(f"\n {line}" for line in code.split("\n"))
        )
        with redirect_stdout(HTMLElementIO(self.text_area)):
            try:
                await locals()["user_program"](self.robot)
            except Exception as error:
                print(f"Error: {error}")


async def main():
    app = App()
