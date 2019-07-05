def create_control_ticket(mode: int, pos: float, speed: float, current=600.0, acc=200000.0, decc=200000.0) -> bytes:

    ticket = f'<control pos="{int(pos*10)}" speed="{int(speed/6)}" current="{int(current)}" mode="{mode}" acc="{int(acc)}" decc="{int(decc)}" />'
    return ticket.encode(encoding='utf-8')


def create_system_ticket(mode: int) -> bytes:

    ticket = f'<system mode="{mode}" />'
    return ticket.encode(encoding='utf-8')


def _parse_field(field: str) -> (str, int):

    key, value = field.split('=')

    return key.strip(' '), int(value.strip(' ').strip('"'))


def parse_status_ticket(msg: str):

    fields = msg.split(' ')

    if 'HDrive' not in fields[0]:
        raise ValueError('not a valid HDrive ticket')

    return dict(map(_parse_field, fields[1:-1]))


def contains_complete_ticket(data: str):

    if '<' not in data:
        return False

    if '/>' not in data:
        return False

    return data.rfind('<') < data.rfind('/>')