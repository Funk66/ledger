from datetime import date

from ledger.queries import Query
from ledger.entities import Transaction


transaction = Transaction(
    date=date(2018, 9, 28),
    valuta=date(2018, 9, 28),
    subject="GitHub Inc.",
    type="income",
    reference="Payroll 09/2018",
    value=3975.91,
    saldo=4308.68,
    account='ingdiba',
)


def test_simple_query():
    assert Query('value > 3000')(transaction)
    assert not Query('value > 4000')(transaction)
    assert Query('value is 3975.91')(transaction)
    assert not Query('date != 2018-09-28')(transaction)
    assert Query('valuta <= 2018-09-29')(transaction)


def test_regex_query():
    assert Query(r'reference like Payroll \d\d/\d+')(transaction)
    assert Query(r'subject like .*Inc\.$')(transaction)


def test_substring_query():
    assert Query('subject has Hub')(transaction)
