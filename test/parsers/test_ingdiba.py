from pathlib import Path

from . import sample_transactions
from ledger.parsers import ingdiba


def test_parser():
    csv_file = Path(__file__).parent / 'ingdiba.csv'
    transactions = ingdiba.read(csv_file)
    assert transactions == sample_transactions
