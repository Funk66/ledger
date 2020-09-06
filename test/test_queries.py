from ledger.queries import Query


def test_simple_query(parsed_transactions):
    parsed_transaction = parsed_transactions[2]
    assert Query('value > 3000')(parsed_transaction)
    assert not Query('value > 4000')(parsed_transaction)
    assert Query('value is 3975.91')(parsed_transaction)
    assert not Query('date != 2015-09-28')(parsed_transaction)
    # assert Query('valuta <= 2018-09-29')(parsed_transaction)


def test_regex_query(parsed_transactions):
    parsed_transaction = parsed_transactions[2]
    assert Query(r'reference has Payroll \d\d/\d+')(parsed_transaction)
    assert Query(r'subject has Inc\.$')(parsed_transaction)
    assert Query(r'reference has (poll|toll|roll)')(parsed_transaction)


def test_substring_query(parsed_transactions):
    parsed_transaction = parsed_transactions[2]
    assert Query('subject has Hub')(parsed_transaction)
