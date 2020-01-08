from datetime import date, datetime


def isodate(string: str) -> date:
    return datetime.strptime(string, '%Y-%m-%d').date()
