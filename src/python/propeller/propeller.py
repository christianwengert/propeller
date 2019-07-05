# coding=utf-8
from math import sin, cos, radians
from time import sleep
from src.python.propeller.axis import Axis
from src.python.propeller.curve import PiecewiseLinearCurve


P = 0.1

CURRENT = 1000

PITCH = 8
FULL_TURN = 360.0

Z_AXIS = "192.168.178.11"
PHI = "192.168.178.12"

DIAMETER_MM = 45.0
RADIUS_MM = DIAMETER_MM/2.0

BLADE_SPEED_MMS = 1000

l0 = 100
l1 = 162.5
extra = 20

first_slope_start = l0 + extra
first_slope_end = first_slope_start + l1
mid_point = first_slope_end + l0
second_slope_start = mid_point + l0
second_slope_end = second_slope_start + l1
total_length = second_slope_end + l0 + extra

CURVE = [
    (0.0, 0.0),
    (first_slope_start, 0.0),
    (first_slope_end, 90.0),
    (second_slope_start, 90.0),
    (second_slope_end, 180.0),
]

TEST_CURVE = [
    (0.0, 0.0),
    (10.0, 0.0),
    (20.0, 15.0),
    (30.0, 15.0),
    (40.0, 0),
    (50.0, 0.0),
    (60.0, 15.0),
    (70.0, 15.0),
    (80.0, 0),
    (90.0, 0),
]


curve = PiecewiseLinearCurve(TEST_CURVE)


def phi_angular_from_z_mm_smooth(z: float, smoothing_distance: float) -> float:

    phi1 = phi_angular_from_z_mm(z - smoothing_distance)
    phi2 = phi_angular_from_z_mm(z + smoothing_distance)

    return (phi1 + phi2) / 2


def phi_angular_from_z_mm(z_pos) -> float:
    return curve[z_pos]


def z_mm2angular(z_mm: float) -> float:
    return z_mm * FULL_TURN / PITCH


def z_angular2mm(z_ang: float) -> float:
    return z_ang / FULL_TURN * PITCH


def compute_angular_axis_positions(z_mm: float) -> (float, float):

    phi_angular = phi_angular_from_z_mm(z_mm)
    z_angular = z_mm2angular(z_mm)

    return z_angular, phi_angular


def move_axes(z_mm: float) -> None:

    z_angular, phi_angular = compute_angular_axis_positions(z_mm)

    z_axis.goto(z_angular)
    phi_axis.goto(phi_angular)


z_axis = Axis(Z_AXIS, gear_ratio=FULL_TURN / PITCH)
phi_axis = Axis(PHI)


def main():

    z_axis.goto0()
    phi_axis.goto0()

    must_reset = False

    z = 0.0
    phi = 0.0

    # z_axis.drive(speed=1000, current=1000)
    while z <= curve.end:

        # noinspection PyBroadException
        try:
            if must_reset:
                z_axis.reset(z)
                phi_axis.reset(phi)
                must_reset = False

            z_axis_status = z_axis.status
            phi_axis_status = phi_axis.status

            z = z_axis_status.position
            phi = phi_axis_status.position

            v_z, v_phi = compute_target_speeds(z, phi)

            z_axis.drive(v_z, CURRENT)
            phi_axis.drive(v_phi, CURRENT)

            sleep(0.1)

        except Exception:
            # first stop all;
            must_reset = True

    z_axis.stop()
    phi_axis.stop()

    print('DONE')


def compute_target_speeds(z, phi):

    phi_target = curve[z]

    delta_angle = phi_target - phi

    target_angle = curve.get_slope_angle(z) + radians(P * delta_angle)

    print(z, phi, target_angle, curve.get_slope_angle(z))

    v_z = BLADE_SPEED_MMS * cos(target_angle)
    v_phi = BLADE_SPEED_MMS * sin(target_angle) / RADIUS_MM * 1000

    return v_z, v_phi


# def compute_target_speeds(z, phi):
#
#     phi_target = curve[z]
#
#     delta_slope = tan(phi_target - phi)
#
#     curve_slope = curve.get_slope(z) + P * delta_slope
#
#     rad_factor = RADIUS_MM * pi / 180.0
#     speed_slope = curve_slope * rad_factor
#     speed_slope2 = speed_slope ** 2
#
#     v_z = BLADE_SPEED_MMS / sqrt(speed_slope2 + 1)
#     v_phi = BLADE_SPEED_MMS / sqrt(1.0 / speed_slope2 + 1) / rad_factor
#
#     return v_z, v_phi


if __name__ == "__main__":
    main()
