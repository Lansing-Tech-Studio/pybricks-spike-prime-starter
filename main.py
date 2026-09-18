"""Competition program: shows a menu of all your missions on the hub.

Buttons:
    LEFT / RIGHT  — pick a mission (the number shows on the hub's screen)
    CENTER        — run the selected mission
    CENTER again  — stop a mission while it is running
    BLUETOOTH     — exit the menu

After a mission finishes, the menu automatically moves to the next one,
so during a match you can just keep pressing CENTER.

Add or reorder missions in menu_config.py — you don't edit this file.
This file just reads that list and builds the menu for you.
"""

# Pybricks MicroPython names this module "usys"; desktop Python calls it
# "sys". Try the hub's name first, then fall back to the desktop one.
try:
    import usys as sys
except ImportError:
    import sys

from pybricks.tools import run_task

from menu import Menu
from menu_config import MENU_ITEMS


# Whole programs that already ran since the hub started this program.
_ran_once = set()


def _import_fresh(name):
    """Import a module by name, running it from the top.

    Importing a file runs it, but only the FIRST time: after that the hub
    remembers it and skips it. Desktop Python lets us forget the cached copy
    (sys.modules) so it runs again every time. The hub's Pybricks firmware
    has no sys.modules, so there a whole program runs once per start —
    restart main.py to run it again. (Use a "function" slot instead if you
    want a mission you can run over and over.)
    """
    modules = getattr(sys, "modules", None)
    if modules is not None:
        if name in modules:
            del modules[name]
    elif name in _ran_once:
        print(name, "already ran. Restart the program to run it again.")
        return
    __import__(name)
    # Only mark it after it finished: if CENTER stopped it partway, the next
    # pick at least tries again.
    _ran_once.add(name)


def _make_runner(item):
    """Build the function the menu calls when this slot is picked.

    There are three kinds of slots:
      - Whole program (no "function"): importing the file runs it.
      - A block's "My Block" ("blocks": True): call it with no robot;
        if it's an async block, drive it with run_task.
      - A plain mission ("function" with no "blocks"): call it with the robot.
    """
    module_name = item["module"]
    func_name = item.get("function")

    # No "function" key → whole program. Picking it re-runs the whole file.
    if not func_name:
        def run_whole(_arg):
            _import_fresh(module_name)
        return run_whole

    # "blocks": True → a My Block. It takes no robot; it may be async.
    if item.get("blocks"):
        def run_block(_arg):
            module = __import__(module_name)
            result = getattr(module, func_name)()
            # An async block returns a coroutine (it has a .send method).
            # run_task actually runs it; a plain block already finished.
            if hasattr(result, "send"):
                run_task(result)
        return run_block

    # Plain mission → call function(robot), the usual way missions work.
    def run_plain(robot):
        module = __import__(module_name)
        try:
            getattr(module, func_name)(robot)
        finally:
            # Runs whether the mission finished or CENTER stopped it.
            _stop_robot(robot)
    return run_plain


def _stop_robot(robot):
    """Let go of the wheels and attachment motors after a mission.

    Pybricks moves end by HOLDing: the motors keep pushing to stay where they
    stopped (and with the gyro on, to keep facing the same way). A program
    run on its own stops everything when it ends, but the menu keeps running,
    so without this the robot would fight you if you picked it up and turned
    it between missions.
    """
    robot.drive_base.stop()
    for motor in (robot.attachment_1, robot.attachment_2):
        if motor is not None:
            motor.stop()


# Does any slot need the robot? Only plain missions do. Block programs and
# whole-program items set up their own devices, so an all-blocks team should
# never build Robot() (that would claim ports they aren't using).
needs_robot = False
for item in MENU_ITEMS:
    if not item.get("enabled", True):
        continue
    if item.get("function") and not item.get("blocks"):
        needs_robot = True
        break

# Only build the robot if something actually needs it.
robot = None
if needs_robot:
    from robot import Robot
    robot = Robot()

# If we have a robot, hand it to every mission; otherwise the menu passes
# the hub instead (block/whole-program runners ignore the argument anyway).
if robot is not None:
    menu = Menu(robot.hub, context=robot)
else:
    menu = Menu()

# Turn each slot from menu_config.py into a menu item. If one slot is broken
# (a bad display number, a missing "module"...), we skip just that one and
# print why, so the rest of the menu still loads.
registered = 0
for item in MENU_ITEMS:
    if not item.get("enabled", True):
        continue
    try:
        menu.add_item(item["display"], _make_runner(item))
        registered += 1
    except Exception as e:
        print("Skipping a broken menu item (" + str(item.get("module", "?")) + "):", e)

# No slots made it in? The menu shows "?" on its own; give a hint too.
if registered == 0:
    print("No missions to show yet. Add one in menu_config.py!")

menu.run(auto_increment=True)
