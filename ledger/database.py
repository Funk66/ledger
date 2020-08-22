import logging
from re import sub
from datetime import date
from functools import wraps
from typing import Any, Callable, List, Optional, Tuple

from litecli.main import LiteCli, SQLExecute

from . import home
from .entities import Transaction
from .tables import Tags, Transactions


class SQLError(Exception):
    pass


class Client:
    """ SQL interface for low-level commands """
    columns = [column.name for column in Transactions.columns] + ["tags"]

    def __init__(self, filename: str = ":memory:"):
        self.dirty = False
        self.sqlexecute = SQLExecute(filename)
        self.sqlexecute.run = tripwire(self.sqlexecute.run, self)
        cursor = self.sqlexecute.conn.cursor()
        cursor.execute(Transactions.create())
        cursor.execute(Tags.create())
        self.sqlexecute.conn.commit()

    def fetch(self, command: str) -> List[Tuple[Any, ...]]:
        cursor = self.sqlexecute.conn.cursor()
        cursor.execute(sub(r"\s+", " ", command))
        return cursor.fetchall()

    def select(self, *args: str, limit: int = 0, **kwargs) -> List[Tuple[Any, ...]]:
        """ Return rows from joined tables.
        Columns are selected as positional arguments and filters as named arguments.
        Defaults to all columns a no filtering. """
        for arg in args:
            assert arg in ["rowid"] + self.columns, f"{arg} is not a valid column"
        columns = args or self.columns
        column_str = [
            'GROUP_CONCAT(tags.tag, ",") tags'
            if column == "tags"
            else f"transactions.{column}"
            for column in columns
        ]
        command = f"""
            SELECT {", ".join(column_str)} FROM transactions
            LEFT JOIN tags ON transactions.rowid = tags.link
        """
        if kwargs:
            command += "WHERE"
            for column, value in kwargs.items():
                command += f" {column}='{value}' "
        command += "GROUP BY transactions.rowid ORDER BY transactions.rowid"
        if limit:
            command += f" LIMIT {limit}"
        rows = self.fetch(command)
        for column, factory in [
            ("tags", lambda tags: set(tags.split(',') if tags else [])),
            ("date", date.fromisoformat),
            ("valuta", date.fromisoformat),
        ]:
            try:
                position = columns.index(column)
            except ValueError:
                continue
            rows = [
                row[:position] + (factory(row[position]),) + row[position+1:]
                for row in rows
            ]
        return rows

    def get_one(self, **kwargs) -> Optional[Transaction]:
        if (transactions := self.get_many(limit=1, **kwargs)):
            return transactions[0]
        return None

    def get_many(self, limit: int = 0, **kwargs) -> List[Optional[Transaction]]:
        rows = self.select(limit=limit, **kwargs)
        return [Transaction(*row) for row in rows]

    def add_one(self, transaction: Transaction) -> None:
        self.add_many([transaction])

    def add_many(self, transactions: List[Transaction]) -> None:
        rows = [transaction.data for transaction in transactions]
        values = ", ".join(["?"] * len(Transactions.columns))
        cursor = self.sqlexecute.conn.cursor()
        cursor.executemany(f"INSERT INTO transactions VALUES ({values})", rows)
        for transaction in transactions:
            for tag in transaction.tags:
                cursor.execute(f"""
                    INSERT INTO tags (tag, link) VALUES (
                        "{tag}",
                        (SELECT rowid FROM transactions WHERE
                            date="{transaction.date}" and
                            value={transaction.value} and
                            saldo={transaction.saldo}
                        )
                    )
                """)
        self.sqlexecute.conn.commit()

    def count(self) -> int:
        return self.fetch("SELECT COUNT(rowid) FROM transactions")[0][0]

    def distinct(self, column: str) -> List[Any]:
        assert column in self.columns, f"{column} is not a valid column"
        command = f"SELECT DISTINCT {column} FROM transactions WHERE {column}!=''"
        return [row[0] for row in self.fetch(command)]

    def categories(self) -> List[str]:
        return [
            category
            for row in self.fetch(
                'SELECT category FROM transactions WHERE category!="" GROUP BY category'
            )
            for category in row
        ]

    def set(self, rowid: int, **kwargs) -> None:
        cursor = self.sqlexecute.conn.cursor()
        values = [f'{key}="{value}"' for key, value in kwargs.items()]
        cursor.execute(
            f'UPDATE transactions SET {", ".join(values)} WHERE rowid={rowid}'
        )

    def prompt(self):
        lite_cli = LiteCli(sqlexecute=self.sqlexecute, liteclirc=home / "config")
        lite_cli.run_cli()
        if self.dirty and input("Save? ") == "y":
            self.save()

    def check(self):
        count = self.fetch("SELECT COUNT(rowid) FROM transactions")
        rowid = self.fetch("SELECT rowid FROM transactions ORDER BY rowid DESC LIMIT 1")
        assert count == rowid, "The last rowid does not match the total number of rows"
        for account in self.distinct("account"):
            previous = None
            for row in self.select("value", "saldo", "rowid", account=account):
                if previous is not None:
                    assert (
                        previous + row[0] == row[1]
                    ), f"Error at row {row[2]}: {previous} + {row[0]} != {row[1]}"
                previous = row[1]


def tripwire(run: Callable[[str], "SQLResponse"], client: Client):
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
