# use function decorators to register event handlers

# no filter argument will call handler for every event
@robot.on_bump()
async def any_bumps(bumpers: Bumpers):
    print(f"any_bumps: {bumpers}")


# handler will only be called for matching event
@robot.on_bump(filter=Bumpers(left=True, right=True))
async def both_bumps(bumpers: Bumpers):
    print(f"both_bumps: {bumpers}")


# named arguments are optional
@robot.on_bump(Bumpers(True, False))
async def left_bumps(bumpers: Bumpers):
    print(f"left_bumps: {bumpers}")


# list of colors can be from 1 to 32 in length
# color sensor will be devided into that many zones
@robot.on_color(Colors([Colors.ANY, Colors.BLACK, Colors.ANY]))
async def black_in_center(colors: Colors):
    print(f"black in center: {colors}")
