# coding=utf-8
import http
import struct
from time import sleep
from typing import Tuple
import requests
import sh


ZAXIS = "192.168.1.222"
PHI = "192.168.1.102"



GEARS = {ZAXIS: (1,1), PHI: (100, 2684)}


def read_data(ip: str) -> Tuple[int, int, int, int]:
    # noinspection PyUnresolvedReferences
    r = sh.curl(f'http://{ip}/getData.cgi?bin')
    data = r.stdout
    uptime, position, speed, current = struct.unpack('iiii', data[0:16])
    return uptime, position, speed, current


def read_pos(ip: str) -> float:
    uptime, position, speed, current = read_data(ip)
    return position / 10.0


def control_pos(pos: int, speed: int=10000, current: int=20000, acc: int=1000, decc: int=1000):
    return f'<control pos="{pos}" speed="{speed}" current="{current}" mode="129" acc="{acc}" decc="{decc}" />'


def send_pos(ip: str, position: float):

    headers = {'type': 'text/plain'}
    position = int(position * 10.0)
    data = control_pos(0)
    r = requests.post(f'http://{ip}/writeTicket.cgi',
                      headers=headers,
                      data=control_pos(position))



def main():
    #
    send_pos(ZAXIS, 0)
    print(read_pos(ZAXIS))
    sleep(5)
    send_pos(ZAXIS, 360)
    print(read_pos(ZAXIS))
    sleep(5)
    send_pos(ZAXIS, 3600)
    print(read_pos(ZAXIS))
    sleep(5)
    print(read_pos(ZAXIS))
    #                  http://192.168.178.222/getData.cgi?bin

    # try:
    #     r = requests.get(f'http://{ZAXIS}/getData.cgi?bin')
    # except Exception as e:
    #     x = e
    # print(x)

    # r = requests.get(f'http://{ZAXIS}/getData.cgi?bin', headers=HEADERS)
    # a = struct.unpack('iiii', r._content[0:16])
    # uptime, position, speed, current = a
    # print(a)
    #
    # r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=HEADERS, data=control_pos(1000))
    # r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=HEADERS, data=control_pos(-2000))
    # r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=HEADERS, data=control_pos(5000))
    # r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=HEADERS, data=control_pos(-10000))
    # r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=HEADERS, data=control_pos(10000))
    # r = requests.post(f'http://{ZAXIS}/writeTicket.cgi', headers=HEADERS, data=control_pos(0))
    # #


if __name__ == "__main__":
    main()
# curl 'http://192.168.178.222/getData.cgi?bin' -H 'Pragma: no-cache' -H 'DNT: 1' -H
# 'Accept-Encoding: gzip, deflate' -H
# 'Accept-Language: en-GB,en-US;q=0.9,en;q=0.8' -H
# 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 ' \
# '(KHTML, like Gecko) Chrome/65.0.3325.183 Safari/537.36 Vivaldi/1.96.1147.64'
#
# -H 'Accept: */*' -H 'Referer: http://192.168.178.222/'
# -H 'Connection: keep-alive' -H 'Cache-Control: no-cache' --compressed

#
#
# headers = {
# 'Host': '192.168.1.102',
# 'Connection': 'keep-alive',
# 'Pragma': 'no-cache',
# 'Cache-Control': 'no-cache',
# 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.183 Safari/537.36 Vivaldi/1.96.1147.64',
# 'Accept': '*/*',
# 'DNT': '1',
# 'Referer': 'http://192.168.1.102/',
# 'Accept-Encoding': 'gzip, deflate',
# 'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
# }
#
#
#
# h1 = http.client.HTTPConnection(ZAXIS)
# h1.request('GET', '/getData.cgi?bin', body=None, headers={}, encode_chunked=False)
