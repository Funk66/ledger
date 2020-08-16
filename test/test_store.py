from pytest import fixture
from pathlib import Path

from ledger.store import Store


@fixture(scope="module")
def db() -> Store:
    db = Store()
    db.load(Path(__file__).parent.absolute() / 'data/transactions.csv')
    return db
