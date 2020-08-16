from datetime import date
from pytest import fixture, raises
from typing import List, Tuple, Any

from ledger.tables import Transactions
from ledger.entities import Transaction
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
    assert client.select("type") == [("payment",) for _ in range(5)]
    assert len(client.select(limit=1)[0]) == len(Transactions.columns)


def test_set(client: Client):
    client.set(1, category="restaurant", location="Paris")
    assert client.select(limit=1)[0] == (
        '2015-06-02',
        '2015-06-02',
        "payment",
        "TESCO, UK",
        "017278916389756839287389260",
        -9.6,
        4776.06,
        "ingdiba",
        "restaurant",
        "Paris",
        "Dinner for two",
    )
