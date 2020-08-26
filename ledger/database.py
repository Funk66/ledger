import logging
from re import sub
from csv import reader
from pathlib import Path
from datetime import date as day
from functools import wraps
from typing import (
    List,
    Any,
    Callable,
    Optional,
    Tuple,
    Type,
    Dict,
    Generic,
    TypeVar,
)
from dataclasses import dataclass, field, astuple

from litecli.main import SQLExecute  # type: ignore


class SQLError(Exception):
    pass


class TableSchema:
    pass


Row = TypeVar("Row", bound=TableSchema)


class MetaTable(type):
    def __new__(mcs, name, bases, namespace):
        assert "name" not in namespace, "Do not use 'name' as a column"
        namespace.update({"name": name.lower(), "columns": []})
        return super().__new__(mcs, name, bases, namespace)


class Table(Generic[Row], metaclass=MetaTable):
    name: str
    schema: Type[TableSchema]
    columns: List[str]
    types: Dict[Any, str] = {str: "TEXT", int: "INTEGER", float: "FLOAT", day: "DATE"}

    def __init__(self, connection):
        self.connection = connection
        self.columns = []
        columns = []
        primary_keys = []
        foreign_key = ""
        for column, attrs in self.schema.__dataclass_fields__.items():
            self.columns.append(column)
            if str(attrs.type).startswith("typing.Union"):
                kind = attrs.type.__args__[0]
            else:
                kind = attrs.type
            columns.append(f'"{column}" {self.types[kind]}')
            if not attrs.metadata.get("optional"):
                columns[-1] += " NOT NULL"
            if attrs.metadata.get("primary"):
                primary_keys.append(column)
            if attrs.metadata.get("reference"):
                assert not foreign_key, "Feature not implemented: multiple foreign keys"
                foreign_key = (
                    f'FOREIGN KEY ("{column}") '
                    f'REFERENCES {attrs.metadata["reference"].name}("rowid")'
                )
        if primary_keys:
            keys = '", "'.join(primary_keys)
            columns.append(f'PRIMARY KEY ("{keys}")')
        if foreign_key:
            columns.append(foreign_key)
        command = f"CREATE TABLE {self.name} ({', '.join(columns)})"
        connection.cursor().execute(command)

    def fetch(self, command: str) -> List[Tuple[Any, ...]]:
        cursor = self.connection.cursor()
        cursor.execute(sub(r"\s+", " ", command))
        return cursor.fetchall()

    def select(self, order: str = None, limit: int = 0, **kwargs) -> List[Row]:
        for kwarg in kwargs:
            assert kwarg in self.columns, f"{kwarg} is not a valid column"
        command = f"SELECT {', '.join(self.columns)} FROM {self.name}"
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
        return [self.schema(*row) for row in cursor.fetchall()]

    def insert(self, data: List[Row]) -> None:
        cursor = self.connection.cursor()
        columns = ", ".join(["?"] * len(self.columns))
        rows = [astuple(row) for row in data]
        cursor.executemany(f"INSERT INTO {self.name} VALUES ({columns})", rows)
        self.connection.commit()

    def distinct(self, column: str) -> List[Any]:
        assert column in self.columns, f"{column} is not a valid column"
        command = f"SELECT DISTINCT {column} FROM {self.name} WHERE {column}!=''"
        return [row[0] for row in self.fetch(command)]

    def count(self) -> int:
        return self.fetch(f"SELECT COUNT(rowid) FROM {self.name}")[0][0]


@dataclass
class Transaction(TableSchema):
    date: day = field(metadata={"primary": True})
    type: str
    subject: str
    reference: str
    value: float = field(metadata={"primary": True})
    saldo: float = field(metadata={"primary": True})
    account: str = field(metadata={"primary": True})
    valuta: Optional[day] = field(default=None, metadata={"optional": True})
    category: Optional[str] = field(default=None, metadata={"optional": True})
    location: Optional[str] = field(default=None, metadata={"optional": True})
    comment: Optional[str] = field(default=None, metadata={"optional": True})

    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = day.fromisoformat(self.date)
        if self.valuta and isinstance(self.valuta, str):
            self.valuta = day.fromisoformat(self.valuta)


class Transactions(Table):
    schema = Transaction

    def check(self) -> None:
        count = self.fetch(f"SELECT COUNT(rowid) FROM {self.name}")
        rowid = self.fetch(f"SELECT rowid FROM {self.name} ORDER BY rowid DESC LIMIT 1")
        assert count == rowid, "The last rowid does not match the total number of rows"
        for account in self.distinct("account"):
            previous = None
            for transaction in self.select(account=account):
                if previous is not None:
                    assert (
                        previous + transaction.value == transaction.saldo
                    ), f"Error: {previous} + {transaction.value} != {transaction.saldo}"
                previous = transaction[1]


class Tag(TableSchema):
    name: str = field(metadata={"primary": True})
    transaction: str = field(metadata={"primary": True, "reference": Transactions})


@dataclass
class Tags(Table):
    schema = Tag


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
