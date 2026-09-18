"""Your robot's setup, all in one place.

This is the ONLY file you need to change when your robot's build changes.
Every mission imports this file, so fix a port or measurement here once
and all of your programs pick it up.
"""

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import (
    ColorSensor,
    ForceSensor,
    Motor,
    UltrasonicSensor,
)
from pybricks.parameters import Direction, Port
from pybricks.robotics import DriveBase

# ============================================================
#  EDIT THIS SECTION TO MATCH YOUR ROBOT
# ============================================================

# --- Drive wheels ---
# Which port is each wheel motor plugged into?
# If your robot drives backward when you tell it to go forward,
# swap CLOCKWISE and COUNTERCLOCKWISE below.
LEFT_WHEEL_PORT = Port.A
LEFT_WHEEL_DIRECTION = Direction.COUNTERCLOCKWISE
RIGHT_WHEEL_PORT = Port.B
RIGHT_WHEEL_DIRECTION = Direction.CLOCKWISE

# --- Robot measurements (in millimeters) ---
# Wheel diameter is printed on the LEGO tire itself
# (small SPIKE wheel = 56, big wheel = 88).
WHEEL_DIAMETER_MM = 56
# Axle track is the distance between the CENTERS of the two wheels,
# measured straight across the robot. Measure yours with a ruler!
AXLE_TRACK_MM = 114

# --- Attachment motors ---
# Motors that move your arms, lifts, and other attachments.
# If you only have one attachment motor, leave ATTACHMENT_2_PORT = None.
ATTACHMENT_1_PORT = Port.D
ATTACHMENT_2_PORT = None  # e.g. Port.C if you add a second one

# --- Sensors ---
# Set the port for any sensor your robot has, or None if you don't have it.
COLOR_SENSOR_PORT = None  # e.g. Port.E
DISTANCE_SENSOR_PORT = None  # the ultrasonic "eyes" sensor
FORCE_SENSOR_PORT = None  # the push-button touch sensor

# --- Gyro ---
# The gyro (inside the hub) makes turns and straight lines more accurate.
# You almost always want this on.
USE_GYRO = True

# --- Menu animation ---
# What the hub's screen shows while a mission is running from the menu.
#   "left", "right", "top", "bottom"  - a light slides back and forth
#                                       along that edge of the screen
#   "clockwise", "counterclockwise"   - a light runs around the outside
#                                       edge of the screen
#   None                              - screen stays dark
RUNNING_ANIMATION = "left"

# ============================================================
#  END OF EDIT SECTION — you shouldn't need to change below here
# ============================================================

MM_PER_INCH = 25.4


def inches(n):
    """Convert inches to millimeters.

    Pybricks measures distance in millimeters, but FLL mats are usually
    measured in inches. Example: robot.drive_base.straight(inches(10))
    """
    return n * MM_PER_INCH


class Robot:
    """All of your robot's parts in one object.

    Make one with Robot(), then use its parts:
        robot = Robot()
        robot.drive_base.straight(inches(10))   # drive forward
        robot.drive_base.turn(90)               # turn right 90 degrees
        robot.attachment_1.run_angle(500, 180)  # spin attachment motor

    Parts you set to None above (extra motors, sensors) will be None here,
    so only use them if your robot actually has them.
    """

    def __init__(self):
        self.hub = PrimeHub()

        # Drive wheels and drive base
        self.left_wheel = Motor(LEFT_WHEEL_PORT, LEFT_WHEEL_DIRECTION)
        self.right_wheel = Motor(RIGHT_WHEEL_PORT, RIGHT_WHEEL_DIRECTION)
        self.drive_base = DriveBase(
            self.left_wheel,
            self.right_wheel,
            WHEEL_DIAMETER_MM,
            AXLE_TRACK_MM,
        )
        self.drive_base.use_gyro(USE_GYRO)

        # Attachment motors (None if you don't have one)
        self.attachment_1 = (
            Motor(ATTACHMENT_1_PORT) if ATTACHMENT_1_PORT is not None else None
        )
        self.attachment_2 = (
            Motor(ATTACHMENT_2_PORT) if ATTACHMENT_2_PORT is not None else None
        )

        # Sensors (None if you don't have them)
        self.color_sensor = (
            ColorSensor(COLOR_SENSOR_PORT) if COLOR_SENSOR_PORT is not None else None
        )
        self.distance_sensor = (
            UltrasonicSensor(DISTANCE_SENSOR_PORT)
            if DISTANCE_SENSOR_PORT is not None
            else None
        )
        self.force_sensor = (
            ForceSensor(FORCE_SENSOR_PORT) if FORCE_SENSOR_PORT is not None else None
        )
