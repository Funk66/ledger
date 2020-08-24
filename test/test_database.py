from datetime import date
from pathlib import Path
from unittest.mock import patch
from sqlite3 import IntegrityError
from pytest import fixture, raises
from typing import List, Tuple, Any
from litecli.main import SQLExecute

from ledger import home
from ledger.database import SQLite, Table, Column


def test_table():
    class Users(Table):
        schema = [
            Column("email", str, primary=True),
            Column("age", int),
            Column("score", float, null=True),
            Column("birthday", date, null=True),
        ]

    class Items(Table):
        schema = [
            Column("id", int, primary=True),
            Column("user", str, reference=Users),
        ]

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
        'PRIMARY KEY ("email"))'
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
