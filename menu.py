try:
    from typing import Optional, Union
except ImportError:
    pass

from pybricks.hubs import PrimeHub
from pybricks.parameters import Button
from pybricks.tools import wait
from pybricks.parameters import Color
import pix_display


class Menu:
    """
    A menu system for the Spike Prime hub that displays numbers and executes associated functions.

    Use LEFT/RIGHT buttons to navigate through menu items.
    Press CENTER button to execute the selected function.
    Press BLUETOOTH button to exit the menu.

    Note: The stop button is set to BLUETOOTH to allow CENTER button to be used for menu selection.

    A menu item's function doesn't have to be a plain mission function. main.py
    builds items from menu_config.py, so a function here may be a loader-made
    closure that imports and runs a whole program file, or that calls a block
    program's "My Block" (including an async one). A whole-program item runs its
    file's top level while CENTER is the stop button, so pressing CENTER stops it
    the same as any mission — the swap/SystemExit/auto_increment handling below
    works for all of these kinds for free.
    """

    def __init__(self, hub: Optional[PrimeHub] = None, context=None):
        """
        Initialize the menu system.

        Args:
            hub: PrimeHub instance. If None, creates a new instance.
            context: Object passed to each menu item's function when it runs.
                If None, the hub is passed instead.
        """
        self.hub = hub if hub is not None else PrimeHub()
        self.context = context
        self.menu_items = []
        self.current_index = 0

    def add_item(self, display: Union[int, str, list[str]], function):
        """
        Add a menu item to the menu.

        Args:
            display: The number/char/pattern to display for this menu item.
            function: The function to execute when this item is selected. This
                may be a plain mission function, or a loader-generated closure
                from main.py that wraps a module import (a whole-program item
                that runs a file's top level under the CENTER stop button) or
                an async block program function.
        """
        if isinstance(display, int):
            if display < 0 or display > 99:
                raise ValueError("Menu item number must be between 0 and 99")

        self.menu_items.append({"display": display, "function": function})

    def clear_items(self):
        """Remove all menu items."""
        self.menu_items.clear()
        self.current_index = 0

    def get_current_item(self):
        """
        Get the currently selected menu item.

        Returns:
            dict: The current menu item, or None if no items exist.
        """
        if not self.menu_items:
            return None
        return self.menu_items[self.current_index]

    def _display_current_item(self):
        """Display the number for the currently selected menu item."""
        if not self.menu_items:
            self.hub.display.char("?")
            return

        current_item = self.get_current_item()
        if current_item is None:
            return
        pix_display.display_content(self.hub, current_item["display"])

    def _wait_for_release(self, button):
        """Wait until the given button is released."""
        while button in self.hub.buttons.pressed():
            wait(10)

    def _navigate_left(self):
        """Navigate to the previous menu item."""
        if self.menu_items:
            self.current_index = (self.current_index - 1) % len(self.menu_items)
            self._display_current_item()

    def _navigate_right(self):
        """Navigate to the next menu item."""
        if self.menu_items:
            self.current_index = (self.current_index + 1) % len(self.menu_items)
            self._display_current_item()

    def _execute_current_function(self, auto_increment):
        """Execute the function associated with the current menu item."""
        current_item = self.get_current_item()
        if current_item and current_item["function"]:
            try:
                # Show a scanning light while the function is executing. It
                # runs in the background and stops when the menu redraws.
                pix_display.start_scanner(self.hub)

                # Wait for CENTER release before making it the stop button
                self._wait_for_release(Button.CENTER)

                # Set stop button to CENTER so it can interrupt the running function
                self.hub.system.set_stop_button(Button.CENTER)

                # Execute the function, passing the context (or hub if no context)
                argument = self.context if self.context is not None else self.hub
                current_item["function"](argument)

                # Return to displaying the current number
                if auto_increment:
                    self._navigate_right()
                self._display_current_item()

            except SystemExit:
                # CENTER was pressed to stop the running function
                # Silence the speaker in case it was mid-beep
                self.hub.speaker.beep(1, 1)
                self._wait_for_release(Button.CENTER)
                self._display_current_item()

            except Exception as e:
                # Show error indicator
                self.hub.light.blink(Color.RED, [500, 500])
                wait(1000)
                # Return to displaying the current number
                self._display_current_item()
                # Re-raise the exception for debugging
                raise
            finally:
                # Restore stop button to BLUETOOTH for the menu
                self.hub.system.set_stop_button(Button.BLUETOOTH)

    def run(self, show_startup=False, auto_increment=False):
        """
        Run the menu system. This is the main loop that handles user input.

        Args:
            show_startup: If True, shows a startup indicator before beginning.
            auto_increment: If True, Automatically moves to the next program.

        Returns:
            bool: True if menu exited normally, False if no menu items exist.

        Controls:
            - LEFT: Navigate to previous menu item
            - RIGHT: Navigate to next menu item
            - CENTER: Execute the selected function
            - BLUETOOTH: Exit menu (also stops the program)
        """
        # Set the stop button to BLUETOOTH so CENTER can be used for selection
        self.hub.system.set_stop_button(Button.BLUETOOTH)

        if not self.menu_items:
            self.hub.display.char("?")
            wait(1000)
            return False

        if show_startup:
            # Show startup indicator
            self.hub.display.char("M")
            wait(500)

        # Display the initial menu item
        self._display_current_item()

        while True:
            pressed_buttons = self.hub.buttons.pressed()

            if pressed_buttons:
                if Button.LEFT in pressed_buttons:
                    self._navigate_left()
                    self._wait_for_release(Button.LEFT)

                elif Button.RIGHT in pressed_buttons:
                    self._navigate_right()
                    self._wait_for_release(Button.RIGHT)

                elif Button.CENTER in pressed_buttons:
                    self._execute_current_function(auto_increment)
                    self._wait_for_release(Button.CENTER)

                elif Button.BLUETOOTH in pressed_buttons:
                    # Exit the menu
                    self.hub.display.char("X")
                    wait(300)
                    self.hub.display.off()
                    self._wait_for_release(Button.BLUETOOTH)
                    return True

            wait(10)

    def __len__(self):
        """Return the number of menu items."""
        return len(self.menu_items)

    def __str__(self):
        """Return a string representation of the menu."""
        if not self.menu_items:
            return "Menu: Empty"

        items_str = []
        for i, item in enumerate(self.menu_items):
            marker = ">" if i == self.current_index else " "
            items_str.append(f"{marker} {item['display']}")

        return f"Menu ({len(self.menu_items)} items):\n" + "\n".join(items_str)


# Example usage and demo functions
def demo_function_1(hub):
    """Demo function 1 - could be anything you want to execute."""
    print("Executing function 1!")
    hub.speaker.beep(440, 500)  # Beep at 440Hz for 500ms


def demo_function_2(hub):
    """Demo function 2 - could be anything you want to execute."""
    print("Executing function 2!")
    hub.speaker.beep(880, 300)  # Higher pitch beep


def demo_function_3(hub):
    """Demo function 3 - could be anything you want to execute."""
    print("Executing function 3! Press center button to stop.")
    offset = 0
    while True:
        offset ^= 1
        hub.speaker.beep(220 + (offset * 20), 700)


if __name__ == "__main__":
    # Demo of how to use the Menu class
    hub = PrimeHub()
    menu = Menu(hub)

    # Add some demo menu items
    menu.add_item(1, demo_function_1)
    menu.add_item("A", demo_function_2)
    menu.add_item(["  8  ", " 898 ", "86#68", "6 # 6", "  #  "], demo_function_3)

    print("Starting menu demo...")
    print(menu)

    # Run the menu
    menu.run()
