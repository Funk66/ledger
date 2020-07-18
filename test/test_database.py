from datetime import date
from pytest import fixture, raises
from typing import List

from ledger.tables import Transactions
from ledger.entities import Transaction
from ledger.database import Client


@fixture
def client(stored_transactions: List[Transaction]) -> Client:
    transactions = [
        tuple([getattr(transaction, column.name) for column in Transactions.columns])
        for transaction in stored_transactions
    ]
    tags = [
        (tag, rowid + 1)
        for rowid in range(len(stored_transactions))
        for tag in stored_transactions[rowid].tags
    ]
    client = Client()
    client.extend("transactions", transactions)
    client.extend("tags", tags)
    return client


def test_transaction_equity(transaction):
    data = {**transaction.__dict__}
    data.update(valuta=date(2030, 7, 1), subject="Nobody", reference="Foreign expenses")
    assert transaction == Transaction(**data)
    data.update(value=0)
    assert transaction != Transaction(**data)


def test_count(client: Client):
    assert client.count() == 5


def test_categories(client: Client):
    assert client.categories() == ["gift:holidays", "groceries:food", "others:cash"]
