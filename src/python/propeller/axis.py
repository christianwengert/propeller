import socket
from time import sleep


from src.python.propeller.tickets import create_control_ticket, parse_status_ticket, contains_complete_ticket

SOCKET_TIMEOUT = 1.0  # secs

POS_CONTROL = 129
SPEED_CONTROL = 8
CURRENT = 1000
SPEED = 1000
PORT = 1000

STEPS = 294


class Axis:

    def __init__(self, axis_ip_address: str, gear_ratio=1.0, p0=None):

        self._gear_ratio = gear_ratio
        self._axis_ip_address = axis_ip_address

        self._socket = self._init_socket()
        self._p0 = 0.0
        self._p0 = p0 if p0 is not None else self.status.position

    def _init_socket(self):

        while True:
            # noinspection PyBroadException
            try:
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _socket.settimeout(3)
                _socket.connect((self._axis_ip_address, PORT))
                return _socket

            except Exception as e:
                print(f'Trying to reconnect to {self._axis_ip_address} in {SOCKET_TIMEOUT}s, {e}')
                # timeout = min(timeout * delta, 60)  # limit to every minute at worst
                sleep(SOCKET_TIMEOUT)

    def goto(self, position):
        target = position * self._gear_ratio - self._p0
        ticket = create_control_ticket(mode=POS_CONTROL, speed=SPEED, current=CURRENT, pos=int(target*10))
        self._socket.sendall(ticket)

    def goto0(self):
        ticket = create_control_ticket(mode=POS_CONTROL, speed=SPEED, current=CURRENT, pos=0)
        self._socket.sendall(ticket)

    def drive(self, speed, current):
        rpm = speed * self._gear_ratio * STEPS / 6.0
        ticket = create_control_ticket(mode=SPEED_CONTROL, speed=rpm, current=current, pos=0)
        self._socket.sendall(ticket)

    @property
    def status(self):

        data = self._read_from_socket()

        while not contains_complete_ticket(data):  # read more until we have at least one full message
            data += self._read_from_socket()

        last_msg = data.split('<')[-1].split('/>')[0]

        return AxisStatus.parse(last_msg, self._gear_ratio, self._p0)

    def _read_from_socket(self):
        return self._socket.recv(1024 * 1024).decode(encoding='utf-8')

    def stop(self):
        self._socket.sendall(create_control_ticket(mode=0, speed=0, current=0, pos=0))

    def reset(self, p0):

        # noinspection PyBroadException
        try:
            self.stop()
        except Exception:
            pass

        self._socket.close()
        self._socket = self._init_socket()
        self._p0 = p0


class AxisStatus:

    def __init__(self, position: float, speed: int, torque: int, uptime: int):

        self.uptime = uptime
        self.torque = torque
        self.speed = speed
        self.position = position

    @classmethod
    def parse(cls, raw_msg: str, gear_ratio=1.0, _p0=0.0):

        ticket = parse_status_ticket(raw_msg)

        # Position is in degrees * 10

        return AxisStatus(
            ticket['Position'] / 10.0 / gear_ratio,  # + p0,
            ticket['Speed'],
            ticket['torque'],
            ticket['Time']
        )
