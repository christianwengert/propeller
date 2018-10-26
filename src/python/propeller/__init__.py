# coding=utf-8
import socket
import struct
import threading
from time import sleep
from typing import Tuple
import requests
import sh


FULL_TURN = 360.0

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
    return position / 10.0


def control_ticket(mode: int, pos: int, speed: int=10000, current: int=20000, acc: int=400, decc: int=400):
    return f'<control pos="{pos}" speed="{speed}" current="{current}" mode="{mode}" acc="{acc}" decc="{decc}" />'


def system_ticket(mode: int):
    return f'<system mode="{mode}" />'

#
# def send_stepper_pos(ip: str, torque: int):
#     headers = {'type': 'text/plain'}
#     requests.post(f'http://{ip}/writeTicket.cgi',
#                   headers=headers,
#                   data=control_ticket(mode=8, current=torque, pos=0))


def send_pid_pos(ip: str, position: float):
    headers = {'type': 'text/plain'}
    position = int(position * 10.0)
    requests.post(f'http://{ip}/writeTicket.cgi',
                  headers=headers,
                  data=control_ticket(mode=129, pos=position))


def move_phi(pos: float):
    """
    Give the angular position of the output shaft in [deg]
    """
    send_pid_pos(PHI, pos)


def read_phi() -> float:
    """
    Returns the output shafts position in [deg]
    """

    motor_pos = read_angular_pos(PHI)
    return motor_pos


def move_z(pos: float):
    """
    pos in [mm]
    the openbuilds lead screw has a pitch of 2mm

    Accuracy is theoretically around 2.5um
    """
    pitch = 8.0  # [mm]
    angular_pos = pos / pitch * 360.0
    send_pid_pos(ZAXIS, angular_pos)


def read_z() -> float:
    """
    Return pos in [mm]]

    Accuracy is theoretically around 2.5um
    """
    pitch = 8.0  # [mm]
    angular_pos = read_angular_pos(ZAXIS)
    pos = angular_pos * pitch / FULL_TURN
    return pos


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


latest_z = 0
latest_phi = 0


def connect(axis):
    ok = False
    timeout = 1
    delta = 1.2
    while not ok:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ZAXIS, 1000))
            return sock

        except Exception:
            print(f'Trying to reconnect to {axis} in {timeout}s')
            timeout = min(timeout * delta, 60)  # limit to every minute at worst
            sleep(timeout)


z_socket = connect(ZAXIS)
phi_socket = connect(PHI)


def z_worker():
    global latest_z
    latest_z = None
    while True:
        latest_z = z_socket.recv(85)


t_z = threading.Thread(target=z_worker)
t_z.start()


def phi_worker():
    global latest_phi
    latest_phi = None
    while True:
        latest_phi = z_socket.recv(85)


t_phi = threading.Thread(target=phi_worker)
t_phi.start()


def parse(msg):
    pos = int(msg[18:28])
    speed = int(msg[37:45])
    torque = int(msg[55:63])
    uptime = int(msg[71:81])
    return pos, speed, torque, uptime


def main():
    global latest_z, latest_phi, z_socket, phi_socket

    def stop_all():
        z_socket.sendall(control_ticket(mode=0, speed=0, current=0, pos=0).encode())
        phi_socket.sendall(control_ticket(mode=0, speed=0, current=0, pos=0).encode())

    z_err = 0
    phi_err = 0

    # LINEAR_STEP = 2
    # DELTA = 0.1
    # z_target = 0
    total_length = 4 * l0 + 2 * l1
    pitch = 8

    z_socket.sendall(control_ticket(mode=129, speed=3000, current=400, pos=0).encode())
    phi_socket.sendall(control_ticket(mode=129, speed=3000, current=400, pos=0).encode())
    sleep(10)

    pos = int(total_length / pitch * 360 * 10 - z_err)
    z_socket.sendall(control_ticket(mode=129, speed=1, current=600, pos=pos).encode())

    i = 1
    while True:

        try:

            local_z = latest_z.decode()  # copy
            angular_z, *junk = parse(local_z)

            real_z = (angular_z + z_err) / 10.0 / 360.0 * 8

            local_phi = latest_phi.decode()  # copy
            angular_phi, *junk = parse(local_phi)

            phi_target = int(f(real_z) * 10.0)

            if abs(phi_target - (angular_phi + phi_err)) > 0.1:
                phi_socket.sendall(control_ticket(mode=133, speed=3000, current=600, pos=phi_target).encode())

            if real_z >= total_length:
                # stop all
                stop_all()
                break

            # if i % 1000 == 0:
            print(real_z, phi_target / 10.0, angular_phi / 100.0)
            i += 1
            sleep(1.0 / 10.0)

        except Exception:

            # first stop all;
            stop_all()

            # get current positions
            z_err = latest_z.decode()
            phi_err = latest_phi.decode()

            # close
            z_socket.close()
            phi_socket.close()

            # reconnect
            z_socket = connect(ZAXIS)
            phi_socket = connect(PHI)

            # set current poisiton to 0
            z_socket.sendall(system_ticket(mode=2).encode())
            phi_socket.sendall(system_ticket(mode=2).encode())

            # reset position
            pos = int(total_length / pitch * 360 * 10 - z_err)  # we already advanced to current_z
            z_socket.sendall(control_ticket(mode=129, speed=1, current=600, pos=pos).encode())


if __name__ == "__main__":
    main()
