from dataclasses import replace
from pytest import fixture, raises

from ledger.store import Store


@fixture
def store(monkeypatch, transactions):
    def init(self):
        self.transactions = transactions[:4]

    monkeypatch.setattr(Store, '__init__', init)
    return Store()


def test_extend(store, transactions):
    store.extend(transactions)
    assert store.transactions == transactions


def test_extend_duplicates_only(store, transactions):
    store.extend(transactions[1:4])
    assert store.transactions == transactions[:4]


def test_extend_new_only(store, transactions):
    store.extend(transactions[4:])
    assert store.transactions == transactions


def test_extend_with_mismatch(store, transactions):
    transactions[1] = replace(transactions[1], subject='test')
    with raises(ValueError):
        store.extend(transactions)


def test_check_transactions(store):
    store.check()


def test_check_failure(store):
    store.transactions[-2].value = 0
    with raises(ValueError):
        store.check()
