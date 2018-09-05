# coding=utf-8
import struct
from time import sleep
from typing import Tuple
import requests
import sh


FULL_TURN = 360.0

PHI_GEAR_RATIO = 100.0 / 2684.0


ZAXIS = "192.168.1.222"
PHI = "192.168.1.102"


def read_data(ip: str) -> Tuple[int, int, int, int]:
    # noinspection PyUnresolvedReferences
    r = sh.curl(f'http://{ip}/getData.cgi?bin')
    data = r.stdout
    uptime, position, speed, current = struct.unpack('iiii', data[0:16])
    return uptime, position, speed, current


def read_angular_pos(ip: str) -> float:
    uptime, position, speed, current = read_data(ip)
    return position / 10.0


def set_angular_pos(pos: int, speed: int=10000, current: int=20000, acc: int=1000, decc: int=1000):
    return f'<control pos="{pos}" speed="{speed}" current="{current}" mode="129" acc="{acc}" decc="{decc}" />'


def send_pos(ip: str, position: float):
    headers = {'type': 'text/plain'}
    position = int(position * 10.0)
    requests.post(f'http://{ip}/writeTicket.cgi',
                  headers=headers,
                  data=set_angular_pos(position))


def move_phi(pos: float):
    """
    Give the angular position of the output shaft in [deg]
    """

    motor_pos = pos / PHI_GEAR_RATIO

    send_pos(PHI, motor_pos)


def read_phi() -> float:
    """
    Returns the output shafts position in [deg]
    """

    motor_pos = read_angular_pos(ZAXIS)
    pos = motor_pos * PHI_GEAR_RATIO
    return pos


def move_z(pos: float):
    """
    pos in [mm]
    the openbuilds lead screw has a pitch of 2mm

    360.0deg == 2mm
    1deg == 2/360 = 0.005555..

    Accuracy is theoretically around 2.5um

    """
    pitch = 8.0  # [mm]
    angular_pos = pos / pitch * 360.0
    send_pos(ZAXIS, angular_pos)


def read_z() -> float:
    """
    Return pos in [mm]]

    Accuracy is theoretically around 2.5um
    """
    pitch = 8.0  # [mm]
    angular_pos = read_angular_pos(ZAXIS)
    pos = angular_pos * pitch / FULL_TURN
    return pos


def main():
    #
    move_z(0)
    print(read_z())
    sleep(5)
    move_z(10)
    print(read_z())
    sleep(5)
    move_z(100)
    print(read_z())
    sleep(5)
    print(read_z())


if __name__ == "__main__":
    main()
