from dataclasses import astuple, dataclass, field
from datetime import date
from filecmp import dircmp
from pathlib import Path
from random import choice
from sqlite3 import IntegrityError
from tempfile import TemporaryDirectory
from typing import List, Optional

from litecli.main import SQLExecute
from pytest import raises

from ledger.database import SQLite, Table, Tag, Transaction


@dataclass
class User:
    email: str = field(metadata={"primary": True})
    age: int = field(metadata={"primary": True})
    score: Optional[float] = field(default=None, metadata={"optional": True})
    birthday: Optional[date] = field(default=None, metadata={"optional": True})

    def __post_init__(self):
        if isinstance(self.birthday, str):
            self.birthday = date.fromisoformat(self.birthday)


class Users(Table):
    schema = User


@dataclass
class Item:
    id: int = field(metadata={"primary": True})
    user: str = field(metadata={"reference": Users})


class Items(Table):
    schema = Item


def test_table_class():
    assert Users.columns == ["email", "age", "score", "birthday"]


def test_create_table():
    connection = SQLExecute(":memory:").conn
    users = Users(connection)
    items = Items(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    commands = cursor.fetchall()
    assert commands[0][0] == (
        "CREATE TABLE users ("
        '"email" TEXT NOT NULL, '
        '"age" INTEGER NOT NULL, '
        '"score" FLOAT, '
        '"birthday" DATE, '
        'PRIMARY KEY ("email", "age"))'
    )
    assert commands[1][0] == (
        "CREATE TABLE items ("
        '"id" INTEGER NOT NULL, '
        '"user" TEXT NOT NULL, '
        'PRIMARY KEY ("id"), '
        'FOREIGN KEY ("user") REFERENCES users("rowid"))'
    )
    assert users.columns == ["email", "age", "score", "birthday"]
    assert items.name == "items"


def test_transaction_schema():
    transaction = Transaction(
        date="2020-02-03",
        type="payment",
        subject="nobody",
        reference="who knows",
        value=123,
        saldo=321,
        account="bank",
        category="yup",
    )
    assert transaction.date == date(2020, 2, 3)
    assert transaction.valuta is None
    assert transaction.hash == {
        "date": date(2020, 2, 3),
        "value": 123,
        "saldo": 321,
        "account": "bank",
    }


def test_add_many():
    data = [
        User("john@smith.com", 21, 3248.13, date(1999, 7, 3)),
        User("ada@lovelace.is", 135),
    ]
    connection = SQLExecute(":memory:").conn
    users = Users(connection)
    users.add_many(data)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    assert [User(*row) for row in cursor.fetchall()] == data


def test_distinct(db: SQLite, stored_transactions: List[Transaction]):
    assert db.transactions.distinct("category") == {
        transaction.category
        for transaction in stored_transactions
        if transaction.category
    }


def test_count(db: SQLite):
    assert db.transactions.count() == 5


def test_categorize(db: SQLite, stored_transactions: List[Transaction]):
    db.transactions.categorize(stored_transactions[0], "test:category")
    assert db.transactions.get_one(category="test:category") == stored_transactions[0]


def test_duplicates(
    db: SQLite, stored_transactions: List[Transaction], stored_tags: List[Tag]
):
    with raises(IntegrityError) as error:
        db.tags.add_one(choice(stored_tags))
    assert str(error.value).startswith("UNIQUE constraint failed")
    with raises(IntegrityError) as error:
        db.transactions.add_one(choice(stored_transactions))


def test_select(db: SQLite, stored_tags: List[Tag]):
    rows = [astuple(tag) for tag in stored_tags]
    assert db.tags.select() == rows
    assert db.tags.select("name") == [(tag.name,) for tag in stored_tags]
    assert db.tags.select(order="rowid", direction="DESC") == rows[::-1]
    assert db.tags.select(limit=1) == rows[:1]
    assert db.tags.select(rowid=1) == rows[:1]


def test_get_one(db: SQLite, stored_transactions: List[Transaction]):
    assert db.transactions.get_one() == stored_transactions[0]
    assert db.transactions.get_one(rowid=3) == stored_transactions[2]
    assert db.transactions.get_one(order="saldo") == stored_transactions[-1]


def test_get_many(db: SQLite, stored_transactions: List[Transaction]):
    assert db.transactions.get_many() == stored_transactions
    assert (
        db.transactions.get_many(date="2015-06-05", order="rowid")
        == stored_transactions[2:]
    )


def test_check_transactions(db: SQLite):
    db.transactions.check()


def test_load(stored_transactions: List[Transaction], stored_tags: List[Tag]):
    db = SQLite(Path(__file__).parent / "data")
    db.load()
    tr = db.transactions.get_many()
    assert tr == stored_transactions
    assert db.tags.get_many() == stored_tags


def test_save(db: SQLite):
    path = db.path
    with TemporaryDirectory() as tmp_dir:
        db.path = Path(tmp_dir)
        db.save()
        dircmp(str(path), tmp_dir)
