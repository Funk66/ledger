from datetime import date
from sqlite3 import IntegrityError
from litecli.main import SQLExecute  # type: ignore
from dataclasses import dataclass, field

from ledger.database import Table, TableSchema, Transaction


def test_table():
    @dataclass
    class User(TableSchema):
        email: str = field(metadata={"primary": True})
        age: int = field(metadata={"primary": True})
        score: float = field(metadata={"optional": True})
        birthday: date = field(metadata={"optional": True})

    class Users(Table):
        schema = User

    @dataclass
    class Item(TableSchema):
        id: int = field(metadata={"primary": True})
        user: str = field(metadata={"reference": Users})

    class Items(Table):
        schema = Item

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


def test_select():
    pass
