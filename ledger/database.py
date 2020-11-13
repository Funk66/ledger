from logging import getLogger
from re import sub
from csv import reader, writer
from pathlib import Path
from datetime import date as day
from functools import wraps
from typing import (
    Set,
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

from litecli.main import LiteCli, SQLExecute  # type: ignore

from . import home, __version__
from .utils import Time


Row = TypeVar("Row")


class MetaTable(type):
    def __new__(mcs, name, bases, ns):
        if name != "Table":
            assert "schema" in ns, f"Must define a schema for Table {name}"
            columns = [column for column in ns["schema"].__annotations__]
            ns.update(name=name.lower(), columns=columns)
        return super().__new__(mcs, name, bases, ns)


class Table(Generic[Row], metaclass=MetaTable):
    name: str
    schema: Type[Row]
    columns: List[str]
    types: Dict[Any, str] = {
        str: "TEXT",
        int: "INTEGER",
        float: "FLOAT",
        day: "DATE",
        Time: "TEXT",
    }

    def __init__(self, connection):
        self.connection = connection
        self.columns = []
        columns = []
        primary_keys = []
        foreign_key = ""
        for column, attrs in self.schema.__dataclass_fields__.items():
            self.columns.append(column)
            if str(attrs.type).startswith("typing.Optional"):
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

    def select(
        self, *args, order: str = None, direction: str = "ASC", limit: int = 0, **kwargs
    ) -> List[Tuple[Any, ...]]:
        all_columns = ["rowid"] + self.columns
        for arg in args + tuple(kwargs.keys()):
            assert arg in all_columns, f"{arg} is not a valid column"
        columns = '", "'.join(args or self.columns)
        command = f'SELECT "{columns}" FROM {self.name}'
        if kwargs:
            command += " WHERE"
            for column, value in kwargs.items():
                command += f" {column}='{value}'"
        if order:
            assert order in all_columns, f"{order} is not a valid column"
            assert direction in ["ASC", "DESC"], f"{direction} is not a valid direction"
            command += f' ORDER BY "{order}" {direction}'
        if limit:
            command += f" LIMIT {limit}"
        cursor = self.connection.cursor()
        cursor.execute(command)
        return cursor.fetchall()

    def insert(self, data: List[Tuple[Any, ...]]) -> None:
        cursor = self.connection.cursor()
        columns = ", ".join(["?"] * len(self.columns))
        cursor.executemany(f"INSERT INTO {self.name} VALUES ({columns})", data)

    def get_one(
        self, order: str = None, direction: str = "ASC", **kwargs
    ) -> Optional[Row]:
        results = self.get_many(order=order, direction=direction, limit=1, **kwargs)
        return results[0] if results else None

    def get_many(
        self, order: str = None, direction: str = "ASC", limit: int = 0, **kwargs
    ) -> List[Row]:
        return [
            self.schema(*row)
            for row in self.select(
                order=order, direction=direction, limit=limit, **kwargs
            )
        ]

    def add_one(self, row: Row) -> None:
        self.add_many([row])

    def add_many(self, rows: List[Row]) -> None:
        self.insert([astuple(row) for row in rows])

    def distinct(self, column: str) -> Set[Any]:
        assert column in self.columns, f"{column} is not a valid column"
        command = f"SELECT DISTINCT {column} FROM {self.name} WHERE {column}!=''"
        return {row[0] for row in self.fetch(command)}

    def count(self) -> int:
        return self.fetch(f"SELECT COUNT(rowid) FROM {self.name}")[0][0]


@dataclass
class Transaction:
    date: day = field(metadata={"primary": True})
    type: str
    subject: str
    reference: str
    value: float = field(metadata={"primary": True})
    saldo: float = field(metadata={"primary": True})
    account: str = field(metadata={"primary": True})
    valuta: Optional[day] = field(default=None, metadata={"optional": True})
    time: Optional[Time] = field(default=None, metadata={"optional": True})
    category: Optional[str] = field(default="", metadata={"optional": True})
    location: Optional[str] = field(default="", metadata={"optional": True})
    comment: Optional[str] = field(default="", metadata={"optional": True})

    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = day.fromisoformat(self.date)
        if self.valuta and isinstance(self.valuta, str):
            self.valuta = day.fromisoformat(self.valuta)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Transaction):
            return False
        return other.hash == self.hash

    @property
    def hash(self):
        return {
            key: getattr(self, key)
            for key, field in self.__dataclass_fields__.items()
            if field.metadata.get("primary")
        }


class Transactions(Table[Transaction]):
    schema = Transaction

    def check(self, account: str = None) -> None:
        count = self.fetch(f"SELECT COUNT(rowid) FROM {self.name}")
        rowid = self.fetch(f"SELECT rowid FROM {self.name} ORDER BY rowid DESC LIMIT 1")
        assert count == rowid, "The last rowid does not match the total number of rows"
        for account in [account] or self.distinct("account"):
            previous = None
            transactions = self.select("value", "saldo", order="rowid", account=account)
            for transaction in transactions:
                if previous is not None:
                    assert (
                        round(previous + transaction[0], 2) == transaction[1]
                    ), f"Error: {previous} + {transaction[0]} != {transaction[1]}"
                previous = transaction[1]

    def categorize(self, transaction: Transaction, category: str) -> None:
        cursor = self.connection.cursor()
        condition = [
            f"{column}='{value}'" for column, value in transaction.hash.items()
        ]
        cursor.execute(
            f"UPDATE transactions SET category='{category}' "
            f"WHERE {' AND '.join(condition)}"
        )


@dataclass
class Tag:
    name: str = field(metadata={"primary": True})
    transaction: int = field(metadata={"primary": True, "reference": Transactions})


class Tags(Table[Tag]):
    schema = Tag


class SQLite:
    def __init__(self, path: Path = Path.home() / ".config/ledger"):
        self.path = path
        self.dirty = False
        self.sqlexecute = SQLExecute(":memory:")
        self.sqlexecute.run = tripwire(self.sqlexecute.run, self)
        self.transactions = Transactions(self.sqlexecute.conn)
        self.tags = Tags(self.sqlexecute.conn)

    def load(self) -> None:
        with open(self.path / "version") as version_file:
            version = version_file.readline().strip()
            if version != __version__:
                raise RuntimeError(f"Running v{__version__} != database v{version}")
        for table in ["transactions", "tags"]:
            with open(self.path / f"{table}.csv", encoding="latin-1") as csvfile:
                getattr(self, table).insert(reader(csvfile))

    def save(self) -> None:
        log.info("Saving data")
        for table in ["transactions", "tags"]:
            with open(self.path / f"{table}.csv", "w", encoding="latin-1") as output:
                csvfile = writer(output)
                csvfile.writerows(getattr(self, table).select())

    def prompt(self) -> None:
        lite_cli = LiteCli(sqlexecute=self.sqlexecute, liteclirc=home / "config")
        lite_cli.run_cli()
        if self.dirty and input("Save? ") == "y":
            self.save()


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
log = getLogger(__name__)
