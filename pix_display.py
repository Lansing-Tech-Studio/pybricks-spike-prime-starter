try:
    from typing import Union
except ImportError:
    pass

from pybricks.hubs import PrimeHub
from pybricks.parameters import Button, Icon
from pybricks.tools import Matrix, wait


class Patterns:
    numbers = [
        [" ### ", " # # ", " # # ", " # # ", " ### "],
        ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
        [" ### ", "   # ", " ### ", " #   ", " ### "],
        [" ### ", "   # ", " ### ", "   # ", " ### "],
        [" # # ", " # # ", " ### ", "   # ", "   # "],
        [" ### ", " #   ", " ### ", "   # ", " ### "],
        [" ### ", " #   ", " ### ", " # # ", " ### "],
        [" ### ", "   # ", "   # ", "   # ", "   # "],
        [" ### ", " # # ", " ### ", " # # ", " ### "],
        [" ### ", " # # ", " ### ", "   # ", " ### "],
        ["# ###", "# # #", "# # #", "# # #", "# ###"],
        [" #  #", "## ##", " #  #", " #  #", " #  #"],
        ["# ###", "#   #", "# ###", "# #  ", "# ###"],
        ["# ###", "#   #", "# ###", "#   #", "# ###"],
        ["# # #", "# # #", "# ###", "#   #", "#   #"],
        ["# ###", "# #  ", "# ###", "#   #", "# ###"],
        ["# ###", "# #  ", "# ###", "# # #", "# ###"],
        ["# ###", "#   #", "#   #", "#   #", "#   #"],
        ["# ###", "# # #", "# ###", "# # #", "# ###"],
        ["# ###", "# # #", "# ###", "#   #", "# ###"],
    ]

    @staticmethod
    def is_valid_pattern(pattern: list[str]):
        if len(pattern) != 5:
            return False
        for line in pattern:
            if len(line) != 5:
                return False
        return True


def display_pattern(hub: PrimeHub, pattern: list[str]):
    """
    Display a pattern on the hub using a visual representation.

    Args:
        hub: PrimeHub instance to display on.
        pattern: List of strings where each string represents a row.
                 Use '#' or anything other than space or zero to turn pixel on,
                 Use space or 0 to turn pixel off,
                 Use a number 1-9 to change the brightness.

    Example:
        display_pattern(hub, [
            "     ",
            " # # ",
            "     ",
            "#   #",
            " ### "
        ])
    """
    rows = []
    for row in pattern:
        pixels = []
        for char in row:
            if char == " ":
                pixels.append(0)
            else:
                try:
                    pixels.append(int(char) * 10)
                except ValueError:
                    pixels.append(100)
        rows.append(pixels)
    hub.display.icon(Matrix(rows))


def display_number(hub: PrimeHub, number: int):
    """
    Display a number (0-99) on the hub using a 5x5 pixel pattern.

    Args:
        hub: PrimeHub instance to display on.
        number: An integer from 0 to 99.
    """
    if number < 0 or number > 99:
        raise ValueError("Number must be between 0 and 99")

    if number < 10:
        hub.display.char(str(number))
    elif number < 20:
        display_pattern(hub, Patterns.numbers[number])
    else:
        hub.display.number(number)


def display_content(hub: PrimeHub, content: Union[str, int, list[str]]):
    if isinstance(content, int):
        if content > -100 and content < 100:
            if content < 0:
                hub.display.number(content)
            else:
                display_number(hub, content)
        else:
            raise ValueError("Number must be between -99 and 99")
    elif isinstance(content, str):
        hub.display.char(content[0])
    else:
        display_pattern(hub, content)


def start_scanner(hub: PrimeHub, interval: int = 80):
    """
    Start a "Knight Rider" style scanner light on the hub's display.

    A bright light slides up the left-hand column (bottom to top) and back
    down again, with a fading tail behind it, like KITT's red light bar.

    The animation runs in the background, so your program keeps going while
    it plays. It stops as soon as anything else is drawn on the display.

    Args:
        hub: PrimeHub instance to display on.
        interval: Milliseconds each frame is shown. Smaller = faster.
    """
    # Row numbers the light visits, in order. Row 4 is the bottom, row 0 is
    # the top. It goes up (4 -> 0) and then back down (1 -> 3), and then the
    # animation repeats from the start.
    path = [4, 3, 2, 1, 0, 1, 2, 3]

    # Brightness of the light and its tail: the light itself, then where it
    # was 1 frame ago, then where it was 2 frames ago.
    brightness = [100, 30, 8]

    frames = []
    for step in range(len(path)):
        # Start with an all-off 5x5 picture.
        rows = [[0, 0, 0, 0, 0] for _ in range(5)]

        # Light up the head and its tail. When the light turns around at the
        # top or bottom, the tail lands on the same spot as the head, so
        # max() keeps the brighter value.
        for age in range(len(brightness)):
            row = path[(step - age) % len(path)]
            rows[row][0] = max(rows[row][0], brightness[age])

        frames.append(Matrix(rows))

    hub.display.animate(frames, interval)


def run_number_selector():
    """
    Run an interactive number selector on the hub.
    Use LEFT/RIGHT buttons to cycle through numbers 0-25.
    Press CENTER button to exit.
    """
    hub = PrimeHub()
    selector = 0
    hub.display.char("?")
    hub.display.icon(
        Matrix(
            [
                [0, 20, 40, 20, 0],
                [20, 40, 60, 40, 20],
                [40, 60, 80, 60, 40],
                [20, 40, 60, 40, 20],
                [0, 20, 40, 20, 0],
            ]
        )
    )
    print(Icon.ARROW_DOWN)
    selector_increment = 0

    while True:
        if hub.buttons.pressed() & {Button.RIGHT, Button.LEFT}:
            if Button.RIGHT in hub.buttons.pressed():
                selector_increment = 1
            elif Button.LEFT in hub.buttons.pressed():
                selector_increment = -1
            while any(hub.buttons.pressed()):
                wait(10)
            selector = (selector + selector_increment) % 26
            display_number(hub, selector)
        wait(10)


if __name__ == "__main__":
    # Run the interactive number selector when this file is executed directly
    run_number_selector()
