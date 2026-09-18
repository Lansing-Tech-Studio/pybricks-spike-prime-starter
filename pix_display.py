try:
    from typing import Optional, Union
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


# The animation names you can pick for RUNNING_ANIMATION in robot.py.
SCANNER_EDGES = ("left", "right", "top", "bottom")
BORDER_DIRECTIONS = ("clockwise", "counterclockwise")


def _edge_pixels(edge: str):
    """
    List the (row, column) spots along one edge of the 5x5 display.

    Row 0 is the top, row 4 is the bottom. Column 0 is the left, column 4 is
    the right. Up-and-down edges are listed bottom to top; side-to-side edges
    are listed left to right.
    """
    if edge == "left":
        return [(row, 0) for row in (4, 3, 2, 1, 0)]
    if edge == "right":
        return [(row, 4) for row in (4, 3, 2, 1, 0)]
    if edge == "top":
        return [(0, col) for col in (0, 1, 2, 3, 4)]
    if edge == "bottom":
        return [(4, col) for col in (0, 1, 2, 3, 4)]
    raise ValueError("edge must be one of " + str(SCANNER_EDGES))


def _border_pixels():
    """
    List the 16 (row, column) spots around the outside of the display, going
    clockwise: across the top, down the right side, back along the bottom,
    and up the left side.
    """
    top = [(0, col) for col in (0, 1, 2, 3, 4)]
    right = [(row, 4) for row in (1, 2, 3, 4)]
    bottom = [(4, col) for col in (3, 2, 1, 0)]
    left = [(row, 0) for row in (3, 2, 1)]
    return top + right + bottom + left


def _start_path_animation(hub: PrimeHub, path, interval: int):
    """
    Animate a light moving through `path`, a list of (row, column) spots,
    with a fading tail behind it. When it reaches the end of the list it
    starts over from the beginning.
    """
    # Brightness of the light and its tail: the light itself, then where it
    # was 1 frame ago, then where it was 2 frames ago.
    brightness = [100, 30, 8]

    frames = []
    for step in range(len(path)):
        # Start with an all-off 5x5 picture.
        rows = [[0, 0, 0, 0, 0] for _ in range(5)]

        # Light up the head and its tail. When a scanner turns around at an
        # end, the tail lands on the same spot as the head, so max() keeps
        # the brighter value.
        for age in range(len(brightness)):
            row, col = path[(step - age) % len(path)]
            rows[row][col] = max(rows[row][col], brightness[age])

        frames.append(Matrix(rows))

    hub.display.animate(frames, interval)


def start_scanner(hub: PrimeHub, edge: str = "left", interval: int = 80):
    """
    Start a "Knight Rider" style scanner light on the hub's display.

    A bright light slides along one edge of the display and back again, with
    a fading tail behind it, like KITT's red light bar.

    The animation runs in the background, so your program keeps going while
    it plays. It stops as soon as anything else is drawn on the display.

    Args:
        hub: PrimeHub instance to display on.
        edge: Which edge the light slides along: "left", "right", "top",
            or "bottom".
        interval: Milliseconds each frame is shown. Smaller = faster.
    """
    # Go out along the edge, then come back. The two end spots are only
    # visited once per trip so the light doesn't pause at the ends.
    # For example, the left edge goes up rows 4 -> 0, then back down 1 -> 3.
    there = _edge_pixels(edge)
    back = [there[i] for i in range(len(there) - 2, 0, -1)]
    _start_path_animation(hub, there + back, interval)


def start_border_chase(hub: PrimeHub, clockwise: bool = True, interval: int = 50):
    """
    Start a light running around the outside edge of the hub's display.

    The animation runs in the background, so your program keeps going while
    it plays. It stops as soon as anything else is drawn on the display.

    Args:
        hub: PrimeHub instance to display on.
        clockwise: True to go clockwise, False to go counterclockwise.
        interval: Milliseconds each frame is shown. Smaller = faster.
    """
    path = _border_pixels()
    if not clockwise:
        path = [path[i] for i in range(len(path) - 1, -1, -1)]
    _start_path_animation(hub, path, interval)


def start_running_animation(hub: PrimeHub, style: Optional[str] = "left"):
    """
    Start the animation shown while a menu item is running.

    Args:
        hub: PrimeHub instance to display on.
        style: One of:
            "left", "right", "top", "bottom" - a scanner light sliding back
                and forth along that edge.
            "clockwise", "counterclockwise" - a light running around the
                outside of the display.
            None - no animation; the display is turned off.
    """
    if style is None:
        hub.display.off()
    elif style in SCANNER_EDGES:
        start_scanner(hub, edge=style)
    elif style in BORDER_DIRECTIONS:
        start_border_chase(hub, clockwise=(style == "clockwise"))
    else:
        # A typo here shouldn't stop a mission from running, so warn and
        # use the plain left-edge scanner instead.
        print(
            "Unknown animation",
            repr(style),
            "- pick one of",
            SCANNER_EDGES + BORDER_DIRECTIONS,
            "or None. Using 'left'.",
        )
        start_scanner(hub, edge="left")


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
