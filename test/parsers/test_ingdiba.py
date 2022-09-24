from pathlib import Path

from ledger.parsers import ingdiba


def test_parser(parsed_transactions):
    csv_file = Path(__file__).parent / "ingdiba.csv"
    transactions = ingdiba.read(csv_file)
    assert transactions == parsed_transactions
