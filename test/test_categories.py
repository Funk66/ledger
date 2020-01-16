from pytest import fixture
from pathlib import Path

from ledger.categories import Category, Categorizer


@fixture(scope='module')
def categorizer():
    sample_file = Path(__file__).parent / 'data' / 'categories.yaml'
    return Categorizer(sample_file)


def test_parse(categorizer):
    assert categorizer.categories == [
        Category('groceries:food', ['PENNY', 'TESCO']),
        Category('others', ['WOOLWORTH']),
    ]


def test_apply(categorizer, transactions):
    categorizer(transactions)
    assert transactions[0].category == 'groceries:food'
    assert transactions[2].category == 'groceries:food'
    assert transactions[3].category == 'others'
