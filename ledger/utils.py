from datetime import datetime, date, time


class Time(time):
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], str):
            args = ([int(n) for n in args[0].split(":")])
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.hour:0>2}:{self.minute:0>2}"


def isodate(string: str) -> date:
    return datetime.strptime(string, '%Y-%m-%d').date()


def str2date(value: str) -> date:
    return datetime.strptime(value, '%d.%m.%Y').date()


def str2float(value: str) -> float:
    return float(value.replace('.', '').replace(',', '.'))
