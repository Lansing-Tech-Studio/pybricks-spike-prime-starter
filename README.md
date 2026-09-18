# Pybricks SPIKE Prime Starter

A starter project for FIRST LEGO League teams programming a LEGO SPIKE Prime robot with [Pybricks](https://pybricks.com/) (Python). Fork this repository, tell it about your robot, and start writing missions!

What you get:

- **`robot.py`** — one file that describes your robot (ports, wheel size, attachments, sensors). Edit it once; every mission uses it.
- **A mission menu** (`main.py`) — pick and run missions right on the hub with the hub's buttons. No computer needed during a match.
- **Two sample missions** and a template for writing your own.

## One-time setup

### 1. Put Pybricks firmware on your hub

Follow the instructions at [code.pybricks.com](https://code.pybricks.com/) to install the Pybricks firmware on your SPIKE Prime hub. While installing, give your hub a name, like `TeamBot`. Keep in mind that if you are going to connect to your robot at a competition, there may be several hubs transmitting their names, so make sure you pick something memorable and unique.

> You can always go back to the official LEGO firmware later using the
> LEGO SPIKE app.

### 2. Set up your computer

**Important note:** Pybricks uses Bluetooth Low Energy (BLE) to send programs to the hub. Make sure your computer has BLE support and that it is enabled. iOS and macOS do not support BLE for Pybricks, so you will need a system running Windows, Linux, Android, or ChromeOS.

You can either use the [Pybricks Code](https://code.pybricks.com/) or [VS Code](https://code.visualstudio.com/). You only need one or the other. VS Code is limited to Python, and is recommended for teams that are trying to learn more about software engineering practices than just programming the robot, whereas Pybricks Code is simpler and more beginner-friendly, and has support for block-based programming (requires purchasing a license).

#### 2.1. Using Pybricks Code

If you want to use block-based programming for [Pybricks Code](https://code.pybricks.com/), you will need to have a license, which can be purchased at <https://pybricks.onfastspring.com/>. Prices vary based on your particular needs.

You should use Chrome to run Pybricks rather than installing a separate app. This will allow you to use the [Pybricks Git extension](https://chromewebstore.google.com/detail/pybricks-git/ebfdckalcnjoogjcdpjomkpnbikcdiap), which allows you to use version control with Pybricks Code. Once you have the extension installed, you can fork this repository and open it in Pybricks Code. You will need to log in to your GitHub account to use the extension. Optionally, you can click the "Install Pybricks Code" button in Chrome in order to give it a shortcut to load from.

#### 2.2. Using VS Code

[VS Code](https://code.visualstudio.com/) to work properly, you also need [Python 3.10+](https://www.python.org/downloads/), so start by installing both of them.

Open this folder in VS Code (it will suggest some extensions — install
them), then in a terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

For VS Code to find your hub, it needs to know the hub's name. Open `.vscode/settings.json` and change `"pybricks.robotName"` from `"MyRobot"` to whatever you named your hub.

### 3. Tell the code about YOUR robot

Open `robot.py` and edit the section at the top:

- Which ports your **wheel motors** are plugged into.
- Your **wheel diameter** (printed on the tire: small SPIKE wheel = 56, big wheel = 88).
- Your **axle track** — the distance in millimeters inbetween your two wheels. Measure it with a ruler.
- Your **attachment motor** port(s). If you only use one attachment motor, leave `ATTACHMENT_2_PORT = None`.
- Any **sensors** you have (color, distance, force). Leave them `None` if you don't have them.

#### 3.1. Tips for wheel configuration

Pybricks lets you tell it how far, in millimeters, you want your robot to move. To do this, Pybricks calculates how many degrees to rotate the wheels. If your wheel diameter is wrong, your robot will drive too far or not far enough. Here's the math for [driving straight](https://github.com/pybricks/pybricks-micropython/blob/6edfe08ddc9041225f3ca84c4af7ec41bab58fd5/lib/pbio/src/drivebase.c#L622):

```python
wheel_circumference_mm = wheel_diameter_mm * 3.14159 # approximation of pi
wheel_rotation_degrees = (distance_mm / wheel_circumference_mm) * 360
```

Since the desired distance is divided by the wheel circumference, if Pybricks thinks your wheel diameter is smaller than it actually is, the calculated rotation will be too large, and the robot will drive too far. If Pybricks thinks your wheel diameter is larger than it actually is, the calculated rotation will be too small, and the robot will not drive far enough. This is an inverse relationship.

Test your wheel diameter using a program that goes forward a known distance (the further the better) and measure how far the robot actually went. If your robot went too far, **increase** the wheel diameter in `robot.py`. If your robot didn't go far enough, **decrease** the wheel diameter.

When turning, Pybricks takes the wheel diameter and axle track (distance inbetween the wheels) into account to calculate how far to rotate each wheel. The further apart the wheels are, the larger the circumference is of the circle the robot is turning inside of. If you want your robot to turn in place, here is the math:

```python
turning_circle_circumference = axle_track * 3.14159          # circumference of the circle each wheel pivots along
fraction_of_circle = turn_angle_deg / 360                    # what portion of a full pivot this turn covers
arc_length = turning_circle_circumference * fraction_of_circle  # distance each wheel travels along the ground

wheel_circumference = wheel_diameter * 3.14159
wheel_deg = 360 * arc_length / wheel_circumference
```

For a robot with a wheel diameter of 62.4 mm and an axle track of 128 mm, a 360° turn requires each wheel to rotate just over 738°, with the left wheel turning forward and the right wheel turning backward. Since the axle track is used as a multiplier for the numerator, this is a direct relationship. If your robot turns too far, the axle track is too large. If your robot doesn't turn far enough, the axle track is too small.

Put your robot in an open space with a reference line to compare against, and then have it turn 360°. If your robot turns too far, **decrease** the axle track in `robot.py`. If your robot doesn't turn far enough, **increase** the axle track. It's good to get your robot to turn well without using the Gyro while calibrating, then you can use the Gyro in your mission programs to make it more accurate when interrupted.

### 4. Running programs

Turn the hub on, then in VS Code open the file you want to run and
press **F5** (the "Pybricks: Run on Robot" configuration). The program
is sent to the hub over Bluetooth and runs there.

From the command line instead:

```bash
pybricksdev run --name YourHubName ble main.py
```

### 5. The mission menu (`main.py`)

Run `main.py` on the hub and a number appears on the hub's screen:

| Button         | What it does                        |
| -------------- | ----------------------------------- |
| LEFT / RIGHT   | Pick a mission                      |
| CENTER         | Run the selected mission            |
| CENTER (again) | Stop the mission while it's running |
| BLUETOOTH      | Exit the menu                       |

After a mission finishes, the menu automatically moves to the next
number — so in a match you can run your missions in order by just
pressing CENTER each time.

**What shows up in the menu lives in `menu_config.py`** — one line per
slot, in the order they appear. `main.py` just reads that list and builds
the menu for you, so you never have to edit `main.py`. The Pybricks Git extension provides a menu editor.

The sample missions:

1. **Go Out and Turn** — drives forward 10 inches, turns 180° using the
   gyro, and stops.
2. **Come Back Home** — drives forward 10 inches (which brings the
   robot home, since Mission 1 turned it around).

In VS Code, you can also run any single mission by opening its file and pressing
F5 — handy while you're testing.

### 6. Writing a new mission

1. Copy `mission_template.py` and name it after your mission, like
   `mission_03_deliver_the_cargo.py`.
2. Write your moves inside the `run(robot)` function.
3. Add **one line** to the `MENU_ITEMS` list in `menu_config.py`, and
   **one matching `import` line** to the `_BUNDLE_HINTS` block just above
   it (see "Why the import hints?" below).

That third step is the only place the menu is defined. Each slot is a
little dictionary. There are three kinds of slot:

```python
MENU_ITEMS = [
    # A plain-Python mission — runs its run(robot) function:
    {"display": 1, "module": "mission_01_go_out_and_turn", "function": "run"},

    # A whole program (a block program OR a Python file) — picking it
    #    runs the entire file from top to bottom. Leave "function" OUT:
    {"display": 3, "module": "my_blocks_program"},

    # One "My Block" from a block program — called with no robot:
    {"display": 4, "module": "arm_moves", "function": "lift_arm", "blocks": True},
]
```

Note that the example skipped loading anything as display item "2". You can use whatever numbering scheme you want. You can also use a single letter like `"A"` or a 5-row pixel pattern (list of 5 strings) for the display.

The keys:

- **`display`** (required) — what shows on the hub screen: a number `0`–`99`,
  a single letter like `"A"`, or a 5-row pixel pattern (list of 5 strings).
- **`module`** (required) — the `.py` file's name, with no `.py` and no
  dots. `"mission_01_go_out_and_turn"` means `mission_01_go_out_and_turn.py`.
- **`function`** (optional) — the function inside that file to call, like
  `"run"`. Leave it out to run the whole file top-to-bottom (kind 2 above).
- **`blocks`** (optional, default `False`) — set `True` for a My Block from
  a block program (kind 3). It's called with no robot and may be async.
- **`enabled`** (optional, default `True`) — set `False` to hide a slot
  without deleting it.

The order of the list is the order the slots appear on the hub. The button
behavior (LEFT/RIGHT to pick, CENTER to run/stop, BLUETOOTH to exit) is the
same no matter which kind of slot it is.

#### Why the import hints?

At the top of `menu_config.py` there's a block that looks like this:

```python
_BUNDLE_HINTS = False
if _BUNDLE_HINTS:
    import mission_01_go_out_and_turn
    import mission_02_come_back_home
```

Those imports never run — `_BUNDLE_HINTS` is always `False`, so the whole
block is skipped. They're there for the **uploader**. Your programs are
sent to the hub over Bluetooth, and the uploader only sends a file if it
can see a real `import` line for it. The menu looks your missions up by
name (the `"module"` text), which the uploader can't see, so without a
hint line the hub says `no module named ...` when you press CENTER.

**So: every `"module"` you list in `MENU_ITEMS` needs a matching
`import` line in that block.** `python3 check_project.py` will tell you
if the block itself is malformed.

Heads up: the Pybricks Git extension's menu editor rewrites this whole
file when you press Save. Older extension versions don't know about the
hint block and will drop it — if your missions stop working right after
a menu Save, check that the block is still at the top of the file.

Common moves cheat-sheet (for `run(robot)` missions):

```python
robot.drive_base.straight(inches(10))   # forward 10 inches
robot.drive_base.straight(inches(-5))   # backward 5 inches
robot.drive_base.turn(90)               # turn right 90 degrees
robot.drive_base.turn(-45)              # turn left 45 degrees
robot.attachment_1.run_angle(500, 180)  # spin attachment: speed, degrees
robot.hub.speaker.beep()                # beep!
```

See the [Pybricks documentation](https://docs.pybricks.com/) for
everything else your robot can do.

### 7. Using block programs

Not everyone writes missions as Python. You can build **block programs**
in the editor at [code.pybricks.com](https://code.pybricks.com/) — drag
blocks together, and the editor turns them into a `.py` file the hub runs.
Those files sync to your fork through the Pybricks Git extension just like
Python missions, and they go in the menu the same way.

A couple of things are different about block files:

- **Block files can't import `robot.py`.** A block program is self-contained,
  so it can't share your team's setup from `robot.py`. Instead, each block
  file carries **its own device setup** inside it (which ports, wheel size,
  and so on). That's built into the blocks at the top of the program.
- **Two ways to put a block file in the menu:**
  - As a **whole-program** slot (kind 2 above, no `"function"`) — picking
    it runs the entire block program from top to bottom. On the hub a
    whole program runs **once each time you start `main.py`** — to run it
    again, stop and restart the program. (A `"function"` slot can run
    again and again.)
  - As a **My Block** slot (kind 3, `"blocks": True`) — this calls one
    named My Block out of a file whose top level is _setup only_ (it sets
    up devices but has no main program blocks of its own).

### 8. The `robot_setup.py` convention

Because every block file has to repeat the same device setup, your team
keeps **one** block file that contains _only_ your setup — no mission
blocks, just the "set up devices" part. Name it `robot_setup.py`.

Make it by copying the provided `robot_setup_template.py` in the editor and
changing the ports and sizes to match your robot. (Because it's a block
file, you edit it at code.pybricks.com, not in a text editor — see
["Files you shouldn't edit"](#files-you-shouldnt-edit) about the template.)

The Pybricks Git extension uses your `robot_setup.py` as the starting point
for **new** block programs, and later will be able to **update the setup in
all your programs at once** when your robot changes — so you fix your setup
in one place instead of every file.

### 9. Files you shouldn't edit

A few files are the framework that makes the menu and the display work.
They're listed as **protected** in `.pybricks-git.json`:

- `main.py`, `menu.py`, `pix_display.py`
- `mission_template.py`, `robot_setup_template.py`
- `check_project.py` (and `.pybricks-git.json` itself)

The Pybricks Git extension **won't save your changes** to these files, and
it puts the original versions back the next time you Pull. That's on
purpose — it keeps everyone's copy working the same way.

When these framework files get improvements, pick them up on GitHub with
**"Sync fork"**, then **Pull** in the editor. Your own files
(`robot.py`, `menu_config.py`, your missions, and your `robot_setup.py`)
are _not_ protected — those are yours to edit freely.

### 10. Checking your project

Before you commit, you can run a quick check on your computer to make sure
your menu and files all line up:

```bash
python3 check_project.py
```

It compiles every `.py` file, checks that `menu_config.py` is valid and
that every module it names actually exists, and validates
`.pybricks-git.json` and your setup files. Fix anything it complains about
and you're good to go.

### 11. Troubleshooting

- **Hub not found / connection times out** — Is the hub turned on and
  nearby? Does the name in `.vscode/settings.json` exactly match your
  hub's name? Is the hub already connected to something else (like the
  Pybricks web IDE)?
- **Robot drives backward** — Swap `CLOCKWISE` and `COUNTERCLOCKWISE`
  for the wheels in `robot.py`.
- **Robot curves when driving straight** — Double-check the wheel
  directions and `AXLE_TRACK_MM` in `robot.py`, and make sure both
  tires are the same size and clean.
- **Turns are off by a few degrees** — Keep the robot perfectly still
  for a second after the program starts so the gyro can settle.
- **`ImportError: no module named 'typing'`** — Your code runs on the
  hub, which doesn't have Python's full standard library. Only import
  from `pybricks.*` (see `menu.py` for the safe way to use typing).

## License

MIT — see [LICENSE](LICENSE).
