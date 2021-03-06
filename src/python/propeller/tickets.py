import re


def create_control_ticket(mode: int, pos: int, speed: int, current=600.0, acc=200000.0, decc=200000.0) -> bytes:

    ticket = f'<control pos="{pos}" speed="{speed}" current="{int(current)}" mode="{mode}" acc="{int(acc)}" decc="{int(decc)}" />'
    return ticket.encode(encoding='utf-8')


def create_system_ticket(mode: int) -> bytes:

    ticket = f'<system mode="{mode}" a="1" b="2" c="3" />'
    return ticket.encode(encoding='utf-8')


def parse_status_ticket(msg: str):

    m = re.match(r'.*Position=\"\s*(-?[0-9]+).*Speed=\"\s*(-?[0-9]+).*torque=\"\s*(-?[0-9]+).*Time=\"\s*(-?[0-9]+)', msg)
    return dict(zip(['Position', 'Speed', 'torque', 'Time'], map(int, m.groups())))


def contains_complete_ticket(data: str):

    if '<' not in data:
        return False

    if '/>' not in data:
        return False

    return data.rfind('<') < data.rfind('/>')
