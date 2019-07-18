# coding=utf-8
import select
import sys
from math import sin, cos, radians, sqrt
from time import sleep
from src.python.propeller.axis import Axis
from src.python.propeller.curve import PiecewiseLinearCurve
import time

"""
0.1 s und eng gespannt: reisst immer
0.33333 und weniger eng gespannt 

0.1s darauf achten, dass die halter schon in der verleangerung des saegeblatts sind
      uns sehr eng gespannt
      
naechster versich: oben gar nicht so fest spannen
niederhalter nicht zu fest sonst slipping


9.7.2019
- oben locker
- stark gespannt (1kHz)
- nicht zu fest der niederhalter
- 2-3mm spiel am blatt
- oben gar nicht fiuxiert
- blatt nach links oben und unten schieben
- blade speed 0.1mm/s

"""

P = 0.333333

CURRENT = 200

POSITION_CONST = 10.0
PITCH = 8
FULL_TURN = 360.0

Z_AXIS = "192.168.178.11"
PHI = "192.168.178.12"

DIAMETER_MM = 45.0
RADIUS_MM = DIAMETER_MM / 2.0

BLADE_SPEED_MMS = 0.3333333

l0 = 100
l1 = 162.5
extra = 15

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
#
TEST_CURVE = [
    (0.0, 0.0),
    (10.0, 0.0),
    (20.0, 25.5),
    (30.0, 25.5),
    (40.0, 0),
    (50.0, 0.0),
    (60.0, 25.46),
    (70.0, 25.46),
    (80.0, 0),
    (90.0, 0),
]


def deg_to_arclength(deg, radius):
    rad = radians(deg)
    return rad * radius


curve = PiecewiseLinearCurve(CURVE, 10)

print(f'ETA {curve.end/BLADE_SPEED_MMS/60:.1f} minutes')

z_axis = Axis(Z_AXIS, FULL_TURN/PITCH)
phi_axis = Axis(PHI)


def main():

    # z_axis.goto0()
    # phi_axis.goto0()
    # sleep(3)

    must_reset = False

    z = 0.0
    phi = 0.0

    start = time.time()

    while z <= curve.end:
        check_for_pause()

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

            v_z, v_phi = compute_target_speeds(z, phi)  # mm/s und deg/s
            # print(v_z, v_phi * 27 / 3.14*180)

            z_axis.drive(v_z, CURRENT)

            phi_axis.drive(v_phi * 10 / 3.14 * 180, CURRENT)
            # print(v_phi)
            #
            # print('.')

            sleep(0.1)

        except Exception:
            # first stop all;
            must_reset = True

    print(time.time() - start)
    z_axis.stop()
    phi_axis.stop()

    print('DONE')


def check_for_pause():
    kb_input = select.select([sys.stdin], [], [], 1)[0]
    if kb_input:
        value = sys.stdin.readline().rstrip()
        print(f'you typed "{value}"')
        if value.lower() in ['s', 'stop']:
            z_axis.drive(0, CURRENT)
            phi_axis.drive(0, CURRENT)
            print('Type "c" or "continue" to continue\n')
            while True:

                input2 = select.select([sys.stdin], [], [], 1)[0]
                if input2:
                    value2 = sys.stdin.readline().rstrip()
                    if value2.lower() in ['c', 'continue']:
                        break


def compute_target_speeds(z, phi):  # z in mm , phi in deg

    phi_target = curve[z]

    delta_angle = phi_target - phi  # deg

    target_angle = curve.get_slope_angle(z) + radians(P * delta_angle)  # rad
    # print(degrees(target_angle))
    # print(z, phi, degrees(target_angle), degrees(curve.get_slope_angle(z)))

    v_z = BLADE_SPEED_MMS * cos(target_angle)
    v_phi = BLADE_SPEED_MMS * sin(target_angle) / RADIUS_MM

    # print(f'{phi:.2}\t{target_angle:.2}')
    print(phi, target_angle, v_z, v_phi * RADIUS_MM, sqrt(v_z**2 + (v_phi * RADIUS_MM)**2))

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
