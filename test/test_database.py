from datetime import date
from pytest import fixture, raises
from typing import List, Tuple, Any

from ledger.tables import Transactions
from ledger.entities import Transaction, Tags
from ledger.database import Client


def raw(transaction: Transaction) -> Tuple[Any, ...]:
    return tuple([getattr(transaction, column.name) for column in Transactions.columns])


@fixture
def client(stored_transactions: List[Transaction]) -> Client:
    transactions = [raw(transaction) for transaction in stored_transactions]
    tags = [
        (tag, rowid + 1)
        for rowid in range(len(stored_transactions))
        for tag in stored_transactions[rowid].tags
    ]
    client = Client()
    client.extend("transactions", transactions)
    client.extend("tags", tags)
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


def test_insert(client: Client, transaction: Transaction):
    client.insert("transactions", raw(transaction))
    assert client.count() == 6


def test_extend(client: Client, parsed_transactions: List[Transaction]):
    client.extend(
        "transactions", [raw(transaction) for transaction in parsed_transactions]
    )
    assert client.count() == 10


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
        Tags(),
    )
    assert data[3][-1] == Tags(["holidays", "family"])
    assert data[4][-1] == Tags(["work"])
    assert client.select("value", "date", saldo=4776.06) == [(-9.6, date(2015, 6, 2))]


def test_find(client: Client):
    assert client.find("subject", "value", category="groceries:food") == (
        "TESCO, UK",
        -9.6,
    )


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
        Tags(),
    )


def test_distinct(client: Client):
    assert set(client.distinct("category")) == {"groceries:food", "others:cash", "gift:holidays"}
    with raises(AssertionError):
        client.distinct("column")
