import js

DEBUG = True


def debug(string):
    if DEBUG:
        js.console.log(string)
