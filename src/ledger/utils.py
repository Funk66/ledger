from datetime import date, datetime


def isodate(string: str) -> date:
    return datetime.strptime(string, "%Y-%m-%d").date()


def str2date(value: str) -> date:
    return datetime.strptime(value, "%d.%m.%Y").date()


def str2float(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))
