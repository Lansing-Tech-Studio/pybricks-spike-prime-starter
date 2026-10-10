"""Competition program: shows a menu of all your missions on the hub.

Buttons:
    LEFT / RIGHT  — pick a mission (the number shows on the hub's screen)
    CENTER        — run the selected mission
    CENTER again  — stop a mission while it is running
    BLUETOOTH     — exit the menu

After a mission finishes, the menu automatically moves to the next one,
so during a match you can just keep pressing CENTER.

Need the same mission again? Press LEFT to go back to it and CENTER to run
it. That always works. The one time the menu has to leave is when a block
program has to run after a DIFFERENT block program already ran: the number
blinks, the menu closes, and the hub shows its own slot number. Just press
CENTER once more and your mission runs right away.

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
from pybricks.robotics import DriveBase
from pybricks.tools import run_task

from menu import Menu
from menu_config import MENU_ITEMS

# The error number Pybricks uses for "EBUSY: Device or resource busy". You
# get it when you set up a Motor on a port that already has one.
_EBUSY = 16

# hub.system.info()["program_start_type"] is this when the hub's own buttons
# started main.py (not a computer uploading it).
_STARTED_BY_BUTTONS = 2

# Programs that can't run again until main.py restarts: whole programs
# without a main() that already ran, and block programs whose motors we had
# to close so another program could use the ports.
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


def _stop_devices(owner):
    """Let go of every drive base and motor the owner has set up.

    Pybricks moves end by HOLDing: the motors keep pushing to stay where they
    stopped (and with the gyro on, to keep facing the same way). A program
    run on its own stops everything when it ends, but the menu keeps running,
    so without this the robot would fight you if you picked it up and turned
    it between missions. It also stops motors that CENTER interrupted mid-move.

    Works for the shared Robot and for a block program's module alike.
    """
    for name in dir(owner):
        thing = getattr(owner, name, None)
        if isinstance(thing, (DriveBase, Motor, DCMotor)):
            try:
                thing.stop()
            except Exception:
                pass


def _is_busy(error):
    """True if this error means a motor port is already in use."""
    return isinstance(error, OSError) and error.args and error.args[0] == _EBUSY


def _on_hub():
    """True on the hub's Pybricks firmware, False on desktop Python.

    The hub's usys has no "modules", so there a module can't be imported
    twice: the second import just hands back the copy from the first time.
    """
    return getattr(sys, "modules", None) is None


def _owns_motors(module_name):
    """Return the module if it set up the motors last, else None."""
    owner = _motor_owner
    if owner is not None and getattr(owner, "__name__", None) == module_name:
        return owner
    return None


def _run_main(module):
    """Run a block program's main() again, stopping its motors afterwards.

    A block program is "async def main(): ..." followed by run_task(main()).
    Importing it ran main() once; calling main() again re-runs the mission
    with the motors it already set up.
    """
    try:
        result = module.main()
        # An async main returns a coroutine (it has a .send method).
        # run_task actually runs it; a plain main already finished.
        if hasattr(result, "send"):
            run_task(result)
    finally:
        # Runs whether the mission finished or CENTER stopped it.
        _stop_devices(module)


def _import_fresh(name):
    """Import a module by name, running it from the top. Returns the module.

    Importing a file runs it, but only the FIRST time: after that the hub
    remembers it and skips it. Desktop Python lets us forget the cached copy
    (sys.modules) so it runs again every time. The hub's Pybricks firmware
    has no sys.modules, so there an import runs a file once per start; block
    programs are run again by calling their main() instead (see _run_main).
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
    it ends main.py, remembering this slot. Press CENTER once and the menu
    starts again and runs this slot right away.
    """
    global _motor_owner
    if name in _used_up:
        _restart_on_this_slot(name + " already ran.")
        return None
    _release_motors()
    try:
        module = _import_fresh(name)
    except SystemExit:
        # CENTER stopped a whole program partway through its first run. On
        # the hub the half-finished module is kept, and a block program
        # defines main() and its motors before it runs, so take it over:
        # the next pick can call main() instead of hitting a busy port.
        # (Desktop Python forgets a failed import, so there's nothing to
        # take over there.)
        if _on_hub():
            try:
                module = __import__(name)
            except Exception:
                module = None
            if module is not None:
                _motor_owner = module
                _stop_devices(module)
        raise
    except Exception as e:
        if not _is_busy(e):
            raise
        # A program stopped partway can leave motors we can't find to close.
        _restart_on_this_slot("A motor port is still in use.")
        return None
    _motor_owner = module
    # A whole program with a main() (every block program has one) can run
    # again by calling main(). Without one, the hub can only run it once
    # per start, because an import only runs the file the first time.
    if whole_program and _on_hub() and not callable(getattr(module, "main", None)):
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
    """End main.py, and make the next start run this slot right away.

    The slot number is kept in the hub's storage, which survives the program
    ending. Storage byte 0 holds the slot + 1 (0 means "no saved slot") and
    byte 1 is 1 when the next start should run that slot at once.
    """
    try:
        menu.hub.system.storage(0, write=bytes([menu.current_index + 1, 1]))
    except Exception:
        # Older firmware has no storage: fall back to just saying so.
        print(why, "Restart the program to run it.")
        return
    print(why, "Press CENTER to restart the menu and run this slot.")
    menu.stop_requested = True


def _started_by_buttons():
    """True if the hub's own buttons started main.py (not a computer)."""
    try:
        info = menu.hub.system.info()
        return info.get("program_start_type") == _STARTED_BY_BUTTONS
    except Exception:
        # Older firmware has no info(): play it safe.
        return False


def _saved_slot():
    """Read and clear what _restart_on_this_slot saved.

    Returns (slot, run_now), or (None, False) if nothing was saved. Clearing
    it means a later start begins at slot 1 as usual.

    run_now is only honored when the hub's buttons started main.py. After a
    computer uploads main.py the saved slot is just shown, never run, so a
    fresh upload can't drive the robot off the desk.
    """
    try:
        saved = menu.hub.system.storage(0, read=2)
        if saved[0] or saved[1]:
            menu.hub.system.storage(0, write=bytes([0, 0]))
    except Exception:
        return None, False
    if 0 < saved[0] <= len(menu):
        return saved[0] - 1, saved[1] == 1 and _started_by_buttons()
    return None, False


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
    # Picked again while it still has its motors? Call its main() again.
    if not func_name:
        def run_whole(_arg):
            module = _owns_motors(module_name)
            if module is not None and callable(getattr(module, "main", None)):
                _run_main(module)
                return
            module = _set_up_module(module_name, True)
            if module is not None:
                _stop_devices(module)
        return run_whole

    # "blocks": True → a My Block. It takes no robot; it may be async.
    if item.get("blocks"):
        def run_block(_arg):
            module = _owns_motors(module_name)
            if module is None:
                module = _set_up_module(module_name, False)
                if module is None:
                    return
            try:
                result = getattr(module, func_name)()
                # An async block returns a coroutine (it has a .send method).
                # run_task actually runs it; a plain block already finished.
                if hasattr(result, "send"):
                    run_task(result)
            finally:
                # Runs whether the block finished or CENTER stopped it.
                _stop_devices(module)
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
            _stop_devices(robot)
    return run_plain


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

# Restarted to re-run a program? Open the menu on that slot, and if the hub's
# buttons started us, run it right away.
slot, run_now = _saved_slot()
if slot is not None:
    menu.current_index = slot

menu.run(auto_increment=True, run_now=run_now)
