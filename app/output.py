import contextlib
import io

import js


class OutputIO(io.TextIOBase):
    def __init__(self):
        self.output = js.document.getElementById("output")

    def write(self, string):
        self.output.innerHTML += string


def redirect_output():
    return contextlib.redirect_stdout(OutputIO())
