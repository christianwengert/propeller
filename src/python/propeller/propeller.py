# coding=utf-8
from math import sin, cos, radians, degrees
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

BLADE_SPEED_MMS = 2

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


def z_mm_to_deg10(m):
    return m / 8.0 * 360.0 * 10.0


def z_deg10_to_mm(d):
    return d * 8.0 / 360.0 / 10.0


def z_rpm_to_mmps(s):
    return s * 60 / 360.0 * 8 / 10.0


def z_mmps_to_rpm(m):
    return m / 60 * 360 / 8 * 10


def z_rpm_to_ticket(rpm):
    return int(rpm * 294)



def phi_degps_to_rpm(d):
    return d * 60.0 / 360.0


def phi_rpm_to_ticket(rpm):
    return int(rpm * 294 * 27)  # 27 from gear


z_axis = Axis(Z_AXIS)
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

            z = z_deg10_to_mm(z_axis_status.position)
            phi = phi_axis_status.position / 10.0

            v_z, v_phi = compute_target_speeds(z, phi)

            z_axis.drive(z_rpm_to_ticket(z_mmps_to_rpm(v_z)), CURRENT)

            phi_axis.drive(phi_rpm_to_ticket(phi_degps_to_rpm(degrees(v_phi))), CURRENT)

            sleep(0.1)

        except Exception:
            # first stop all;
            must_reset = True

    z_axis.stop()
    phi_axis.stop()

    print('DONE')


def compute_target_speeds(z, phi):  # z in mm , phi in deg

    phi_target = curve[z]

    delta_angle = phi_target - phi  # deg

    target_angle = curve.get_slope_angle(z) + radians(P * delta_angle)  # rad

    print(z, phi, degrees(target_angle), degrees(curve.get_slope_angle(z)))

    v_z = BLADE_SPEED_MMS * cos(target_angle)
    v_phi = BLADE_SPEED_MMS * sin(target_angle) / RADIUS_MM

    return v_z, v_phi  # mm/s und rad/s


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