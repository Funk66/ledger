from .parsers import sample_transaction
from ledger.queries import Query


def test_simple_query():
    assert Query('value > 3000')(sample_transaction)
    assert not Query('value > 4000')(sample_transaction)
    assert Query('value is 3975.91')(sample_transaction)
    assert not Query('date != 2018-09-28')(sample_transaction)
    assert Query('valuta <= 2018-09-29')(sample_transaction)


def test_regex_query():
    assert Query(r'reference has Payroll \d\d/\d+')(sample_transaction)
    assert Query(r'subject has Inc\.$')(sample_transaction)
    assert Query(r'reference has (poll|toll|roll)')(sample_transaction)


def test_substring_query():
    assert Query('subject has Hub')(sample_transaction)
