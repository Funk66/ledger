from pathlib import Path

from ledger.categories import Category, apply, parse

from . import sample_store


def test_parse():
    categories = parse(Path(__file__).parent / 'data' / 'categories.yaml')
    assert categories == [
        Category('groceries:food', ['PENNY', 'TESCO']),
        Category('others', ['WOOLWORTH']),
    ]


def test_apply():
    apply(sample_store,
          parse(Path(__file__).parent / 'data' / 'categories.yaml'))
    assert sample_store[0].category == 'groceries:food'
    assert sample_store[2].category == 'groceries:food'
    assert sample_store[3].category == 'others'
