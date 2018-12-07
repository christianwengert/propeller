# coding=utf-8
import socket
from time import sleep


POS_CONTROL = 129
SPEED = 0
CURRENT = 1000
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


def phi_angular_from_z_mm(z) -> int:

    first_slope_start = 10  # todo l0
    first_slope_end = first_slope_start + l1
    mid_point = first_slope_end + l0
    second_slope_start = mid_point + l0
    second_slope_end = second_slope_start + l1

    val = None

    if z < first_slope_start:
        val = 0.0

    if first_slope_start <= z < first_slope_end:
        val = 0.0 + (z - first_slope_start) / l1 * 90.0

    if first_slope_end <= z < second_slope_start:
        val = 90.0

    if second_slope_start <= z < second_slope_end:
        val = 90.0 + (z - second_slope_start) / l1 * 90.0

    if second_slope_end <= z:
        val = 180.0

    if val is None:
        raise ValueError

    return int(val * MULTIPLIER)


def connect(axis):
    ok = False
    timeout = 1
    # delta = 1.2
    while not ok:
        # noinspection PyBroadException
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((axis, 1000))
            return sock
        except Exception as e:
            print(f'Trying to reconnect to {axis} in {timeout}s, {e}')
            # timeout = min(timeout * delta, 60)  # limit to every minute at worst
            sleep(timeout)


class Axis:
    def __init__(self, ip_adress):
        self.socket = connect(ip_adress)
        self.err = 0.0
        self.target = 0.0

    def goto(self, angular_position):
        self.target = angular_position + self.err
        self.socket.sendall(control_ticket(mode=129, speed=SPEED, current=CURRENT, pos=self.target).encode())

    def drive(self, speed, current):
        self.socket.sendall(control_ticket(mode=8, speed=speed, current=current, pos=0).encode())

    # def drive2(self, speed, current, angular_position):
    #     self.target = angular_position + self.err
    #
    #     self.socket.sendall(control_ticket(mode=8, speed=speed, current=current, pos=0).encode())
    #
    #     # self.wait()
    #     # Annahme, z is ver incresing
    #     while self.position < self.target:
    #         sleep(0.05)
    #
    #     self.stop()

    @property
    def position(self):
        return self.read_socket()[0] + self.err

    @property
    def speed(self):
        return self.read_socket()[1]

    def read_socket(self):
        latest = self.socket.recv(1024 * 1024)[-85 * 2:].decode()
        idx = latest.rfind('>')
        local = latest[idx - 85 + 1:idx + 1]
        args = parse(local)  # current PHI
        return args

    def stop(self):
        self.socket.sendall(control_ticket(mode=0, speed=0, current=0, pos=0).encode())

    def reset(self, current_angular_pos):
        # noinspection PyBroadException
        try:
            self.stop()
        except Exception:
            pass
        self.socket.close()
        self.socket = connect(ZAXIS)
        self.err = current_angular_pos - self.position

    def wait(self):
        while abs(self.position - self.target) > 5:
            sleep(0.1)


def z_mm2angular(z_mm):
    return z_mm * MULTIPLIER * FULL_TURN / PITCH


def z_angular2mm(z_ang):
    return z_ang / MULTIPLIER / FULL_TURN * PITCH


def compute_angular_axis_positions(z_mm):
    phi_angular = phi_angular_from_z_mm(z_mm)
    z_angular = z_mm2angular(z_mm)
    return z_angular, phi_angular


def move_axes(z_mm):
    z_angular, phi_angular = compute_angular_axis_positions(z_mm)

    z_axis.goto(z_angular)
    phi_axis.goto(phi_angular)


def parse(msg):
    pos = int(msg[18:28])
    speed = int(msg[37:45])
    torque = int(msg[55:63])
    uptime = int(msg[71:81])
    return pos, speed, torque, uptime


def sendall(socket, data):
    socket.sendall(data)


z_axis = Axis(ZAXIS)
phi_axis = Axis(PHI)


def main():

    total_length = 4 * l0 + 2 * l1

    z_axis.goto(0)
    phi_axis.goto(0)

    # z_axis.wait()
    # phi_axis.wait()

    STEP_MM = 1
    z_target_mm = 0
    z_angular = phi_angular_target = 0

    reinit = False

    # z_axis.drive(speed=1000, current=1000)
    while True:

        # noinspection PyBroadException
        try:
            if reinit:
                z_axis.reset(z_angular)
                phi_axis.reset(phi_angular_target)
                reinit = False
                # z_axis.drive(speed=1000, current=1000)

            z_target_mm += STEP_MM
            z_target_angular = z_mm2angular(z_target_mm)
            phi_angular_target = phi_angular_from_z_mm(z_target_mm)

            z_ok = phi_ok = False

            while not (z_ok and phi_ok):
                z_ok = z_axis.position >= z_target_angular - 5
                phi_ok = phi_axis.position >= phi_angular_target -5

                if z_ok:
                    z_axis.stop()
                else:
                    z_axis.drive(speed=1000, current=200)

                if phi_ok:
                    phi_axis.stop()
                else:
                    phi_axis.drive(speed=1000, current=200)

                print(z_target_mm, z_angular2mm(z_axis.position), phi_angular_target / 10.0, phi_axis.position / 10.0)
                sleep(0.1)


            # sleep(0.1)
            #
            #
            #
            #
            #
            # # if z_axis.speed == 0:
            # #     z_axis.stop()
            #
            # z_axis.drive(speed=1000, current=1000)
            # # z_target_mm += STEP_MM
            # # z_axis.goto(0)
            #
            # z_angular = z_axis.position
            # current_z_mm = z_angular2mm(z_angular)
            # # z_angular = z_mm2angular(current_z_mm)
            #
            #
            # phi_angular_target = phi_angular_from_z_mm(current_z_mm)
            # phi_axis.goto(phi_angular_target)
            #
            # if z_target_mm >= total_length:
            #     z_axis.stop()
            #     phi_axis.stop()
            #     break
            #
            # phi_axis.wait()
            #
            #

            # sleep(0.1)

        except Exception:
            # first stop all;
            reinit = True


if __name__ == "__main__":
    main()
