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



# 1 RPM = 8mm/min
# Wir kriegen 10*degrees
# Wir wollen 100mm weit fahren
# 100 / 8 = Anzahl umdrehungen
# 100 / 8 * 360 * 10 = 100mm

def z_mm_to_deg10(m):
    return m / 8.0 * 360.0 * 10.0


def z_deg10_to_mm(d):
    return d * 8.0 / 360.0 / 10.0


def z_rpm_to_mmps(s):
    return s * 60 / 360.0 * 8 / 10.0


def z_mmps_to_rpm(m):
    return m / 60 * 360 / 8 * 10


def z_rpm_to_ticket(rpm):
    return rpm * 294



def phi_degps_to_rpm(d):
    return d * 60.0 / 360.0


def phi_rpm_to_ticket(rpm):
    return rpm * 294 * 27  # 27 from gear

def main():
    phi_axis = Axis(PHI)

    # phi_axis.goto0()
    # sleep(5)


    # 80000 =10rpm

    p = 0.0

    must_reset = False

    import time
    start = time.time()

    phi_axis_status = phi_axis.status
    p0 = phi_axis_status.position


    while p <= p0 + 360.0 * 10. * 2:

        try:
            phi_axis.drive(speed=phi_rpm_to_ticket(phi_degps_to_rpm(30)), current=CURRENT)
            if must_reset:
                phi_axis.reset(p)

                must_reset = False

            phi_axis_status = phi_axis.status
            p = phi_axis_status.position
            s = phi_axis_status.speed  # Really is rpm



            print(p, s)

            sleep(1)

        except Exception as e:
            # first stop all;
            must_reset = True


    end = time.time()
    print(end-start)

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
