import math

def wheel_rotation_for_turn(turn_angle_deg: float, wheel_diameter: float, axle_track: float) -> float:
    """
    Compute the number of degrees each wheel must rotate (in opposite
    directions) for the robot to pivot in place by `turn_angle_deg`.

    wheel_diameter and axle_track must be in the same units (e.g. mm),
    matching how they're passed to pybricks.robotics.DriveBase.

    Returns wheel rotation in degrees. One wheel turns +this amount,
    the other turns -this amount, for an in-place pivot.
    """
    return turn_angle_deg * (axle_track / wheel_diameter)


# --- Optional: showing the full derivation explicitly, for verification ---
def wheel_rotation_for_turn_explicit(turn_angle_deg: float, wheel_diameter: float, axle_track: float) -> float:
    """Same result as above, computed the long way via arc length, to
    confirm the simplified formula is correct."""
    turn_angle_rad = math.radians(turn_angle_deg)
    arc_length = (axle_track / 2) * turn_angle_rad       # distance each wheel travels along the ground
    wheel_circumference = math.pi * wheel_diameter
    wheel_deg = 360 * arc_length / wheel_circumference
    return wheel_deg


if __name__ == "__main__":
    # Example: wheel_diameter=56 mm, axle_track=112 mm (values from Pybricks' own docs example)
    wd, at = 62.4, 128
    for angle in (90, 180, 360):
        simple = wheel_rotation_for_turn(angle, wd, at)
        explicit = wheel_rotation_for_turn_explicit(angle, wd, at)
        print(f"turn {angle:>5}°  ->  wheel rotation {simple:8.3f}°  (explicit check: {explicit:8.3f}°)")