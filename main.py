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

from pybricks.pupdevices import DCMotor, Motor
from pybricks.tools import run_task

from menu import Menu
from menu_config import MENU_ITEMS

# The error number Pybricks uses for "EBUSY: Device or resource busy". You
# get it when you set up a Motor on a port that already has one.
_EBUSY = 16

# Programs that can't run again until main.py restarts: whole programs that
# already ran, and block programs whose motors we had to close.
_used_up = set()

# Who has motors set up right now: the shared Robot, a block program's
# module, or None. Only one can hold a port at a time.
_motor_owner = None

# The shared Robot for plain missions. Built the first time one is picked.
_robot = None


def _release_motors():
    """Close the motors of whatever ran last, so the next program can use
    those ports.

    A port can only have one Motor at a time. The program that ran last is
    still loaded, so its motors keep their ports until we close them.
    """
    global _motor_owner
    owner = _motor_owner
    if owner is None:
        return
    _motor_owner = None
    for name in dir(owner):
        thing = getattr(owner, name, None)
        if isinstance(thing, (Motor, DCMotor)) and hasattr(thing, "close"):
            try:
                thing.close()
            except Exception:
                pass
    # A block program sets up its motors only when it's first imported, so
    # it can't get them back without a restart. (The Robot just gets rebuilt.)
    if owner is not _robot:
        _used_up.add(owner.__name__)


def _is_busy(error):
    """True if this error means a motor port is already in use."""
    return isinstance(error, OSError) and error.args and error.args[0] == _EBUSY


def _import_fresh(name):
    """Import a module by name, running it from the top. Returns the module.

    Importing a file runs it, but only the FIRST time: after that the hub
    remembers it and skips it. Desktop Python lets us forget the cached copy
    (sys.modules) so it runs again every time. The hub's Pybricks firmware
    has no sys.modules, so there a whole program runs once per start.
    """
    modules = getattr(sys, "modules", None)
    if modules is not None:
        if name in modules:
            del modules[name]
    return __import__(name)


def _set_up_module(name, whole_program):
    """Import a block program (or whole program), which sets up its motors.

    Returns the module, or None if main.py has to restart first. Restarting
    is the only way to get a used-up program or a stuck port back: picking
    it ends main.py, remembering this slot. Press CENTER to start the menu
    again on this slot, then CENTER once more to run it.
    """
    global _motor_owner
    if name in _used_up:
        _restart_on_this_slot(name + " already ran.")
        return None
    _release_motors()
    try:
        module = _import_fresh(name)
    except Exception as e:
        if not _is_busy(e):
            raise
        # A program stopped partway can leave motors we can't find to close.
        _restart_on_this_slot("A motor port is still in use.")
        return None
    _motor_owner = module
    # Only mark it after it finished: if CENTER stopped it partway, the next
    # pick at least tries again.
    if whole_program and getattr(sys, "modules", None) is None:
        _used_up.add(name)
    return module


def _get_robot():
    """Return the shared Robot, building it if another program has the ports.

    Returns None if main.py has to restart first (see _set_up_module).
    """
    global _robot, _motor_owner
    if _robot is not None and _motor_owner is _robot:
        return _robot
    _release_motors()
    from robot import Robot
    try:
        _robot = Robot()
    except Exception as e:
        if not _is_busy(e):
            raise
        _restart_on_this_slot("A motor port is still in use.")
        return None
    _motor_owner = _robot
    return _robot


def _restart_on_this_slot(why):
    """End main.py, and make the next start open the menu on this slot.

    The slot number is kept in the hub's storage, which survives the program
    ending. Storage byte 0 holds the slot + 1 (0 means "no saved slot").
    """
    try:
        menu.hub.system.storage(0, write=bytes([menu.current_index + 1]))
    except Exception:
        # Older firmware has no storage: fall back to just saying so.
        print(why, "Restart the program to run it.")
        return
    print(why, "Press CENTER to restart the menu on this slot.")
    menu.stop_requested = True


def _saved_slot():
    """Read and clear the slot saved by _restart_on_this_slot, or None.

    Clearing it means a later start (even after a power-off) begins at
    slot 1 as usual, and the saved slot is only shown, never run by itself.
    """
    try:
        saved = menu.hub.system.storage(0, read=1)[0]
        if saved:
            menu.hub.system.storage(0, write=bytes([0]))
    except Exception:
        return None
    if 0 < saved <= len(menu):
        return saved - 1
    return None


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

    # No "function" key → whole program. Importing it runs the whole file.
    if not func_name:
        def run_whole(_arg):
            _set_up_module(module_name, True)
        return run_whole

    # "blocks": True → a My Block. It takes no robot; it may be async.
    if item.get("blocks"):
        def run_block(_arg):
            module = _motor_owner
            if module is None or getattr(module, "__name__", None) != module_name:
                module = _set_up_module(module_name, False)
                if module is None:
                    return
            result = getattr(module, func_name)()
            # An async block returns a coroutine (it has a .send method).
            # run_task actually runs it; a plain block already finished.
            if hasattr(result, "send"):
                run_task(result)
        return run_block

    # Plain mission → call function(robot), the usual way missions work.
    def run_plain(_arg):
        robot = _get_robot()
        if robot is None:
            return
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


# The "running" animation is picked in robot.py. Importing robot.py just
# reads its settings; it doesn't build Robot() or claim any ports.
# (getattr keeps older robot.py files without the setting working.)
import robot as robot_settings
animation = getattr(robot_settings, "RUNNING_ANIMATION", "left")

# The Robot (and its motors) is only built when a plain mission is picked,
# so block programs that set up their own motors aren't fighting it for
# ports. Each runner finds what it needs itself, so no context is passed.
menu = Menu(running_animation=animation)

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

# Restarted to re-run a program? Open the menu on that slot.
slot = _saved_slot()
if slot is not None:
    menu.current_index = slot

menu.run(auto_increment=True)
