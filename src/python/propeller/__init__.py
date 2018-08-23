# coding=utf-8
import struct

import requests

ZAXIS = "192.168.178.222"
PHI = "192.168.178.223"

headers = {'type': 'text/plain'}
# headers = {'type': 'text/plain'}
# data = b'<control pos=\"-10000\" speed=\"10000\" current=\"20000\" mode=\"129\" acc=\"1000\" decc=\"1000\" />'
# r = requests.post(f'http://{HOST}/writeTicket.cgi', headers=headers, data=data)


def control_pos(pos: int, speed: int=10000, current: int=20000, acc: int=1000, decc: int=1000):
    return f'<control pos="{pos}" speed="{speed}" current="{current}" mode="129" acc="{acc}" decc="{decc}" />'





#
r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=headers, data=control_pos(0))


r = requests.get(f'http://{ZAXIS}/getData.cgi?bin')
a = struct.unpack('iiii', r._content[0:16])
uptime, position, speed, current = a
print(a)



r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=headers, data=control_pos(1000))
r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=headers, data=control_pos(-2000))
r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=headers, data=control_pos(5000))
r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=headers, data=control_pos(-10000))
r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=headers, data=control_pos(10000))
r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=headers, data=control_pos(0))
#
# import socket
#
#
#
# PORT = 1000  # The same port as used by the server
#
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.connect((HOST, PORT))
#     for i in range(100):
#         data = s.recv(1024)
#         print('Received', repr(data))