# coding=utf-8
import socket
# import struct
from time import sleep

POS_CONTROL = 129

SPEED = 3000

CURRENT = 600

PITCH = 8
FULL_TURN = 360.0
MULTIPLIER = 10.0


ZAXIS = "192.168.178.11"
PHI = "192.168.178.12"


def control_ticket(mode: int, pos: int, speed: int=10000, current: int=20000, acc: int=400, decc: int=400):
    return f'<control pos="{pos}" speed="{speed}" current="{current}" mode="{mode}" acc="{acc}" decc="{decc}" />'


def system_ticket(mode: int):
    return f'<system mode="{mode}" />'


l0 = 100
l1 = 162.5


def f(z) -> float:

    first_slope_start = 10  # todo l0
    first_slope_end = first_slope_start + l1
    mid_point = first_slope_end + l0
    second_slope_start = mid_point + l0
    second_slope_end = second_slope_start + l1

    if z < first_slope_start:
        return 0.0

    if first_slope_start <= z < first_slope_end:
        return 0.0 + (z - first_slope_start) / l1 * 90.0

    if first_slope_end <= z < second_slope_start:
        return 90.0

    if second_slope_start <= z < second_slope_end:
        return 90.0 + (z - second_slope_start) / l1 * 90.0

    if second_slope_end <= z:
        return 180.0


def connect(axis):
    ok = False
    timeout = 1
    delta = 1.2
    while not ok:
        # noinspection PyBroadException
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((axis, 1000))
            return sock
        except Exception as e:
            print(f'Trying to reconnect to {axis} in {timeout}s, {e}')
            timeout = min(timeout * delta, 60)  # limit to every minute at worst
            sleep(timeout)


def parse(msg):
    pos = int(msg[18:28])
    speed = int(msg[37:45])
    torque = int(msg[55:63])
    uptime = int(msg[71:81])
    return pos, speed, torque, uptime


def sendall(socket, data):
    # try:
    #     read_socket(socket)
    # except Exception as e:
    #     return False

    # try:
    socket.sendall(data)
    # except Exception as e:
    #     return False
    # return True


def main():
    z_socket = connect(ZAXIS)
    phi_socket = connect(PHI)

    def stop_all():
        sendall(z_socket, control_ticket(mode=0, speed=0, current=0, pos=0).encode())
        # sendall(phi_socket, control_ticket(mode=0, speed=0, current=0, pos=0).encode())

    z_err = 0.0
    phi_err = 0.0

    total_length = 4 * l0 + 2 * l1
    sendall(z_socket, control_ticket(mode=POS_CONTROL, speed=SPEED, current=CURRENT, pos=0).encode())
    # sendall(phi_socket, control_ticket(mode=POS_CONTROL, speed=SPEED, current=CURRENT, pos=0).encode())
    while abs(read_motor_position(z_socket)) > 0.5:
        sleep(0.1)

    STEP = 100  # = 2.0deg
    z_target = 0
    angular_z = 0
    angular_phi = 0

    reinit = False
    i = 1
    while True:

        # noinspection PyBroadException
        try:
            if reinit:

                # reset_motors(phi_socket, z_socket)
                current_z = read_motor_position(z_socket)
                # increment errors
                z_err += angular_z - current_z
                # phi_err = phi_err + angular_phi

                # reset target
                z_target = current_z

                reinit = False

            sendall(z_socket, control_ticket(mode=133, speed=SPEED, current=CURRENT, pos=z_target).encode())
            z_target += STEP

            angular_z = read_motor_position(z_socket)

            real_z = (angular_z + z_err) / MULTIPLIER / FULL_TURN * PITCH

            # angular_phi = read_motor_position(phi_socket)
            #
            # phi_target = int(f(real_z) * MULTIPLIER) - phi_err
            #
            # if abs(phi_target - angular_phi) > 0.1:
            #     sendall(phi_socket, control_ticket(mode=133, speed=SPEED, current=CURRENT, pos=phi_target).encode())

            if real_z >= total_length:
                stop_all()
                break

            phi_target = -9999
            print(real_z, phi_target / MULTIPLIER, (angular_phi + phi_err) / MULTIPLIER)
            i += 1
            sleep(1.0 / 10.0)

        except Exception as e:

            # first stop all;
            stop_all()

            # close
            z_socket.close()
            phi_socket.close()

            # reconnect
            z_socket = connect(ZAXIS)
            phi_socket = connect(PHI)

            reinit = True


def reset_motors(phi_socket, z_socket):
    # ensure we are @ zero!
    sendall(z_socket, system_ticket(mode=2).encode())
    sleep(0.5)
    sendall(z_socket, system_ticket(mode=2).encode())
    # sendall(phi_socket, system_ticket(mode=2).encode())
    # sleep(0.5)
    # sendall(phi_socket, system_ticket(mode=2).encode())


def read_motor_position(socket):
    args = read_socket(socket)
    return args[0]


def read_socket(socket):
    latest = socket.recv(1024 * 1024)[-85 * 2:].decode()
    idx = latest.rfind('>')
    local = latest[idx - 85 + 1:idx + 1]
    args = parse(local)  # current PHI
    return args


if __name__ == "__main__":
    main()
