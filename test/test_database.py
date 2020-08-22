from datetime import date
from sqlite3 import IntegrityError
from pytest import fixture, raises
from typing import List, Tuple, Any

from ledger.tables import Transactions
from ledger.entities import Transaction
from ledger.database import Client


def raw(transaction: Transaction) -> Tuple[Any, ...]:
    return tuple([getattr(transaction, column.name) for column in Transactions.columns])


@fixture
def client(stored_transactions: List[Transaction]) -> Client:
    client = Client()
    client.add_many(stored_transactions)
    return client


def test_transaction_equity(transaction: Transaction):
    data = {**transaction.__dict__}
    data.update(valuta=date(2030, 7, 1), subject="Nobody", reference="Foreign expenses")
    assert transaction == Transaction(**data)
    data.update(value=0)
    assert transaction != Transaction(**data)


def test_count(client: Client):
    assert client.count() == 5


def test_categories(client: Client):
    assert client.categories() == ["gift:holidays", "groceries:food", "others:cash"]


def test_select(client: Client):
    assert client.select("type", limit=1) == [("payment",)]
    data = client.select()
    assert data[0] == (
        date(2015, 6, 2),
        date(2015, 6, 2),
        "payment",
        "TESCO, UK",
        "017278916389756839287389260",
        -9.6,
        4776.06,
        "ingdiba",
        "groceries:food",
        "England",
        "Dinner for two",
        set(),
    )
    assert data[3][-1] == {"holidays", "family"}
    assert data[4][-1] == {"work"}
    assert client.select("value", "date", saldo=4776.06) == [(-9.6, date(2015, 6, 2))]


def test_get_one(client: Client, stored_transactions: List[Transactions]):
    assert client.get_one() == stored_transactions[0]
    assert client.get_one(saldo=4719.1) == stored_transactions[2]
    assert client.get_one(category="nonexistent") is None


def test_get_many(client: Client, stored_transactions: List[Transactions]):
    assert client.get_many() == stored_transactions
    assert client.get_many(category="groceries:food") == [stored_transactions[0], stored_transactions[4]]
    assert client.get_many(type="payment", limit=2) == stored_transactions[:2]


def test_add_one(client: Client, transaction: Transaction):
    client.add_one(transaction)
    assert client.get_one(saldo=transaction.saldo) == transaction
    with raises(IntegrityError):
        client.add_one(transaction)


def test_add_many(client: Client, parsed_transactions: List[Transaction]):
    client.add_many(parsed_transactions)
    assert client.get_one(subject="GitHub Inc.") == parsed_transactions[0]
    assert client.count() == 10


def test_set(client: Client):
    client.set(1, category="restaurant", location="Paris")
    assert client.select(limit=1)[0] == (
        date(2015, 6, 2),
        date(2015, 6, 2),
        "payment",
        "TESCO, UK",
        "017278916389756839287389260",
        -9.6,
        4776.06,
        "ingdiba",
        "restaurant",
        "Paris",
        "Dinner for two",
        set(),
    )


def test_distinct(client: Client):
    assert set(client.distinct("category")) == {"groceries:food", "others:cash", "gift:holidays"}
    with raises(AssertionError):
        client.distinct("column")


def test_check(client: Client):
    client.check()
    client.set(3, saldo=123)
    with raises(AssertionError):
        client.check()
