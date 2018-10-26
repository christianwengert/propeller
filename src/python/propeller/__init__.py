# coding=utf-8
import socket
import struct
from time import sleep
from typing import Tuple
import sh

POS_CONTROL = 129

SPEED = 3000

CURRENT = 600

PITCH = 8
FULL_TURN = 360.0
MULTIPLIER = 10.0

# PHI_GEAR_RATIO = 100.0 / 2684.0


ZAXIS = "192.168.178.11"
PHI = "192.168.178.12"


def read_data(ip: str) -> Tuple[int, int, int, int]:
    # noinspection PyUnresolvedReferences
    r = sh.curl(f'http://{ip}/getData.cgi?bin')
    data = r.stdout
    uptime, position, speed, current = struct.unpack('iiii', data[0:16])
    return uptime, position, speed, current


def read_angular_pos(ip: str) -> float:
    uptime, position, speed, current = read_data(ip)
    return position / MULTIPLIER


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


def main():
    z_socket = connect(ZAXIS)
    phi_socket = connect(PHI)

    def stop_all():
        z_socket.sendall(control_ticket(mode=0, speed=0, current=0, pos=0).encode())
        phi_socket.sendall(control_ticket(mode=0, speed=0, current=0, pos=0).encode())

    z_err = 0.0
    phi_err = 0.0
    angular_z = 0.0
    angular_phi = 0.0

    # LINEAR_STEP = 2
    # DELTA = 0.1
    # z_target = 0
    total_length = 4 * l0 + 2 * l1
    z_socket.sendall(control_ticket(mode=POS_CONTROL, speed=SPEED, current=CURRENT, pos=0).encode())
    phi_socket.sendall(control_ticket(mode=POS_CONTROL, speed=SPEED, current=CURRENT, pos=0).encode())
    sleep(10)

    # Z_SPEED = 10
    # pos = int(total_length / PITCH * FULL_TURN * MULTIPLIER - z_err)
    # z_socket.sendall(control_ticket(mode=POS_CONTROL, speed=Z_SPEED, current=CURRENT, pos=pos).encode())

    i = 1

    STEP = 20
    z_target = 0

    reinit = False
    while True:

        # noinspection PyBroadException
        try:

            if reinit:
                # set current poisiton to 0
                try:
                    # get current position positions
                    latest_z = z_socket.recv(1024 * 1024)[-85 * 2:].decode()
                    idx = latest_z.rfind('>')
                    local_z = latest_z[idx - 85 + 1:idx + 1]
                    angular_z, *junk = parse(local_z)

                    latest_phi = phi_socket.recv(1024 * 1024)[-85 * 2:].decode()
                    idx = latest_phi.rfind('>')
                    local_phi = latest_phi[idx - 85 + 1:idx + 1]
                    angular_phi, *junk = parse(local_phi)

                    z_err = z_err + angular_z
                    phi_err = phi_err + angular_phi
                    z_socket.sendall(system_ticket(mode=2).encode())
                    z_socket.sendall(system_ticket(mode=2).encode())
                    phi_socket.sendall(system_ticket(mode=2).encode())
                    phi_socket.sendall(system_ticket(mode=2).encode())
                    # reset position
                    # pos = int(total_length / PITCH * FULL_TURN * MULTIPLIER - z_err)  # we already advanced to current_z
                    # z_socket.sendall(control_ticket(mode=POS_CONTROL, speed=Z_SPEED, current=CURRENT, pos=pos).encode())
                    reinit = False
                except Exception as e:
                    continue


            latest_z = z_socket.recv(1024 * 1024)[-85 * 2:].decode()
            idx = latest_z.rfind('>')
            local_z = latest_z[idx - 85 + 1:idx + 1]

            # if abs(z_target - (angular_phi + phi_err)) > 0.1:
            z_socket.sendall(control_ticket(mode=133, speed=SPEED, current=CURRENT, pos=z_target - z_err).encode())
            z_target += STEP


            # pos = int(total_length / PITCH * FULL_TURN * MULTIPLIER - z_err)
            # z_socket.sendall(control_ticket(mode=POS_CONTROL, speed=Z_SPEED, current=CURRENT, pos=pos).encode())


            angular_z, *junk = parse(local_z)

            real_z = (angular_z + z_err) / MULTIPLIER / FULL_TURN * PITCH

            latest_phi = phi_socket.recv(1024 * 1024)[-85 * 2:].decode()
            idx = latest_phi.rfind('>')
            local_phi = latest_phi[idx - 85 + 1:idx + 1]

            angular_phi, *junk = parse(local_phi)

            phi_target = int(f(real_z) * MULTIPLIER)

            if abs(phi_target - (angular_phi + phi_err)) > 0.1:
                phi_socket.sendall(control_ticket(mode=133, speed=SPEED, current=CURRENT, pos=phi_target - phi_err).encode())

            if real_z >= total_length:
                # stop all
                stop_all()
                break

            print(real_z, phi_target / MULTIPLIER, angular_phi / MULTIPLIER)
            i += 1
            sleep(1.0 / 10.0)
        #
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


if __name__ == "__main__":
    main()
