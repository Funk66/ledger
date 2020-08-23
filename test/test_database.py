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


def test_select(client: Client, stored_transactions: List[Transaction]):
    assert client.select("type", limit=1) == [("payment",)]
    data = client.select()
    assert data[0][:-1] == stored_transactions[0].data
    assert data[3][-1] == stored_transactions[3].tags
    assert data[4][-1] == stored_transactions[4].tags
    assert client.select("value", "date", saldo=4776.06) == [(-9.6, date(2015, 6, 2))]


def test_get_one(client: Client, stored_transactions: List[Transaction]):
    assert client.get_one() == stored_transactions[0]
    assert client.get_one(saldo=4719.1) == stored_transactions[2]
    assert client.get_one(category="nonexistent") is None


def test_get_many(client: Client, stored_transactions: List[Transaction]):
    assert client.get_many() == stored_transactions
    assert client.get_many(category="groceries:food") == [
        stored_transactions[0],
        stored_transactions[4],
    ]
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


def test_add_many_with_duplicate(
    client: Client,
    stored_transactions: List[Transaction],
    parsed_transactions: List[Transaction],
):
    with raises(IntegrityError):
        client.add_many(parsed_transactions + stored_transactions[-2:-1])


def test_set(client: Client, stored_transactions: List[Transaction]):
    transaction = stored_transactions[0]
    transaction.category = "restaurant"
    transaction.location = "Paris"
    client.set(1, category="restaurant", location="Paris")
    assert client.select(limit=1)[0][:-1] == transaction.data


def test_distinct(client: Client):
    assert set(client.distinct("category")) == {
        "groceries:food",
        "others:cash",
        "gift:holidays",
    }
    with raises(AssertionError):
        client.distinct("column")


def test_check(client: Client):
    client.check()
    client.set(3, saldo=123)
    with raises(AssertionError, match="Error at row 3"):
        client.check()
    cursor = client.sqlexecute.conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE rowid = 2")
    client.sqlexecute.conn.commit()
    with raises(AssertionError, match="The last rowid does not match"):
        client.check()
