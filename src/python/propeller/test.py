from math import atan2, radians, cos, sin



TEST_CURVE = [
(0, 0),
(1, 0),
(2, 0),
(3, 0),
(4, 0),
(5, 0),
(6, 0),
(7, 0),
(8, 0),
(9, 0),
(10, 1.5),
(11, 3),
(12, 4.5),
(13, 6),
(14, 7.5),
(15, 9),
(16, 10.5),
(17, 12),
(18, 13.5),
(19, 15),
(20, 15),
(21, 15),
(22, 15),
(23, 15),
(24, 15),
(25, 15),
(26, 15),
(27, 15),
(28, 15),
(29, 15),
(30, 15),
(31, 13.5),
(32, 12),
(33, 10.5),
(34, 9),
(35, 7.5),
(36, 6),
(37, 4.5),
(38, 3),
(39, 1.5),
(40, 0),
(41, 0),
(42, 0),
(43, 0),
(44, 0),
(45, 0),
(46, 0),
(47, 0),
(48, 0),
(49, 0),
(50, 0)
]


BLADE_SPEED_MMS = 2
RADIUS_MM = 45.0 / 2.0


def get_slope_angle(x: float, dx=0.1) -> float:  # x: mm

    x1 = x - dx
    x2 = x + dx

    y1 = radians(get_phi(x1))
    y2 = radians(get_phi(x2))

    return atan2(y2 - y1, x2 - x1)  # rad


def compute_target_speeds(z, phi):  # z in mm , phi in deg

    # phi_target = curve[z]

    # delta_angle = phi_target - phi  # deg
    #
    target_angle = get_slope_angle(z)   #+ radians(P * delta_angle)  # rad

    # print(z, phi, degrees(target_angle), degrees(curve.get_slope_angle(z)))

    v_z = BLADE_SPEED_MMS * cos(target_angle)
    v_phi = BLADE_SPEED_MMS * sin(target_angle) / RADIUS_MM

    return v_z, v_phi  # mm/s und rad/s


def get_phi(z):
    phi = 0
    for i in range(len(TEST_CURVE) - 1):
        if z <= TEST_CURVE[i + 1][0]:
            phi = TEST_CURVE[i + 1][1]
            break
    return phi

def main():


    # lets test
    z = phi = 0

    for z, phi in TEST_CURVE:


        # print(, phi)
        v_z, v_phi = compute_target_speeds(z, phi)
        print(z, v_z, phi, v_phi)




if __name__ == "__main__":
    main()
