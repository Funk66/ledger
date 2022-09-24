from pytest import fixture
from pathlib import Path

from ledger.categories import Category, Categorizer


@fixture(scope="module")
def categorizer():
    sample_file = Path(__file__).parent / "data" / "categories.yaml"
    return Categorizer(sample_file)


def test_parse(categorizer):
    assert categorizer.categories == [
        Category("lodging:hotels", ["NH Hotels", "Astoria"]),
        Category("work", ["GitHub"]),
    ]


def test_apply(categorizer, parsed_transactions):
    categorizer(parsed_transactions)
    assert parsed_transactions[2].category == "work"
    assert parsed_transactions[3].category == ""
    assert parsed_transactions[4].category == "lodging:hotels"
