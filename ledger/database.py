import logging
from re import sub
from csv import reader
from pathlib import Path
from datetime import date as day
from functools import wraps
from typing import Any, Callable, List, Optional, Tuple, Type, NamedTuple, Dict

from litecli.main import LiteCli, SQLExecute

from . import home


class SQLError(Exception):
    pass


class Column(NamedTuple):
    name: str
    type: type
    null: bool = False
    primary: bool = False
    reference: Optional[Type["Table"]] = None
    types: Dict[Any, str] = {str: "TEXT", int: "INTEGER", float: "FLOAT", day: "DATE"}

    def __str__(self) -> str:
        definition = f'"{self.name}" {self.types[self.type]}'
        if not self.null:
            definition += " NOT NULL"
        return definition


class MetaTable(type):
    def __new__(mcs, name, bases, namespace):
        assert "name" not in namespace, "Do not use 'name' as a column"
        namespace.update({"name": name.lower(), "columns": []})
        return super().__new__(mcs, name, bases, namespace)


class Table(metaclass=MetaTable):
    name: str
    schema: List[Column]
    columns: List[str]

    def __init__(self, connection):
        self.connection = connection
        self.columns = [column.name for column in self.schema]
        columns = [str(column) for column in self.schema]
        primary_keys = [col.name for col in self.schema if col.primary]
        if primary_keys:
            keys = '", "'.join(primary_keys)
            columns.append(f'PRIMARY KEY ("{keys}")')
        foreign_key = [col for col in self.schema if col.reference]
        if foreign_key:
            columns.append(
                f'FOREIGN KEY ("{foreign_key[0].name}") '  # type: ignore
                f'REFERENCES {foreign_key[0].reference.name}("rowid")'
            )
        command = f"CREATE TABLE {self.name} ({', '.join(columns)})"
        connection.cursor().execute(command)

    def fetch(self, command: str) -> List[Tuple[Any, ...]]:
        cursor = self.connection.cursor()
        cursor.execute(sub(r"\s+", " ", command))
        return cursor.fetchall()

    def select(
        self, *args: str, order: str = None, limit: int = 0, **kwargs
    ) -> List[Tuple[Any, ...]]:
        for arg in args:
            assert arg in self.columns, f"{arg} is not a valid column"
        command = f"SELECT {', '.join(args or self.columns)} FROM {self.name}"
        if kwargs:
            command += " WHERE"
            for column, value in kwargs.items():
                command += f" {column}='{value}'"
        if order:
            command += " ORDER BY {order}"
        if limit:
            command += f" LIMIT {limit}"
        cursor = self.connection.cursor()
        cursor.execute(command)
        return cursor.fetchall()

    def insert(self, data) -> None:
        pass

    def distinct(self, column: str) -> List[Any]:
        assert column in self.columns, f"{column} is not a valid column"
        command = f"SELECT DISTINCT {column} FROM {self.name} WHERE {column}!=''"
        return [row[0] for row in self.fetch(command)]

    def count(self) -> int:
        return self.fetch(f"SELECT COUNT(rowid) FROM {self.name}")[0][0]


class Transactions(Table):
    schema = [
        Column("date", day, primary=True),
        Column("valuta", day, null=True),
        Column("type", str),
        Column("subject", str),
        Column("reference", str),
        Column("value", float, primary=True),
        Column("saldo", float, primary=True),
        Column("account", str, primary=True),
        Column("category", str, null=True),
        Column("location", str, null=True),
        Column("comment", str, null=True),
    ]

    def check(self):
        count = self.fetch(f"SELECT COUNT(rowid) FROM {self.name}")
        rowid = self.fetch(f"SELECT rowid FROM {self.name} ORDER BY rowid DESC LIMIT 1")
        assert count == rowid, "The last rowid does not match the total number of rows"
        for account in self.distinct("account"):
            previous = None
            for row in self.select("value", "saldo", "rowid", account=account):
                if previous is not None:
                    assert (
                        previous + row[0] == row[1]
                    ), f"Error at row {row[2]}: {previous} + {row[0]} != {row[1]}"
                previous = row[1]


class Tags(Table):
    schema = [
        Column("name", str, primary=True),
        Column("transaction", int, primary=True, reference=Transactions),
    ]


class SQLite:
    def __init__(self, filename: str = ":memory:"):
        self.dirty = False
        self.sqlexecute = SQLExecute(filename)
        self.sqlexecute.run = tripwire(self.sqlexecute.run, self)
        self.transactions = Transactions(self.sqlexecute.conn)
        self.tags = Tags(self.sqlexecute.conn)
        self.sqlexecute.conn.commit()

    def load(self, path: Path) -> None:
        for table in ["transactions", "tags"]:
            with open(path / "transactions.csv", encoding="latin-1") as csvfile:
                getattr(self, table).insert(reader(csvfile))

    def save(self, path: Path) -> None:
        pass


def tripwire(run: Callable[[str], "SQLResponse"], client: SQLite):
    @wraps(run)
    def wrapper(statement: str) -> "SQLResponse":
        if statement.lower().startswith("update"):
            client.dirty = True
        return run(statement)

    return wrapper


SQLResponse = Tuple[
    Optional[str], Optional[List[Tuple[Any]]], Optional[Tuple[str]], Optional[str]
]
log = logging.getLogger(__name__)
