import logging
from re import sub
from datetime import date
from functools import wraps
from typing import Any, Callable, List, Optional, Sequence, Tuple

from litecli.main import LiteCli, SQLExecute

from . import home
from .entities import Tags as TagSet
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
        log.debug(sub(r"\s+", " ", command))
        cursor = self.sqlexecute.conn.cursor()
        cursor.execute(command)
        return cursor.fetchall()

    def insert(self, table: str, data: Sequence[Any]) -> None:
        """ Insert one row """
        self.extend(table, [data])

    def extend(self, table: str, data: Sequence[Sequence[Any]]) -> None:
        if (total := len(data)) == 0:
            return
        elif total == 1:
            log.debug(f"Inserting row into {table}")
        else:
            log.debug(f"Inserting {len(data)} rows into {table}")
        values = ", ".join(["?"] * len(data[0]))
        cursor = self.sqlexecute.conn.cursor()
        cursor.executemany(f"INSERT INTO {table} VALUES ({values})", data)
        self.sqlexecute.conn.commit()

    def select(self, *args: str, limit: int = 0, **kwargs) -> List[Tuple[Any, ...]]:
        # TODO: add kwargs for WHERE clause
        """ Return transaction data from joined tables.
        Columns are selected as positional arguments and filters as named arguments.
        Defaults to all columns a no filtering. """
        for arg in args:
            assert arg in self.columns, f"{arg} is not a valid column"
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
            for key, value in kwargs.items():
                command += f" {key}='{value}' "
        command += "GROUP BY transactions.rowid ORDER BY transactions.rowid"
        if limit:
            command += f" LIMIT {limit}"
        rows = self.fetch(command)
        for column, factory in [
            ("tags", lambda tags: TagSet(tags.split(',') if tags else [])),
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

    def count(self) -> int:
        return self.fetch("SELECT COUNT(rowid) FROM transactions")[0][0]

    def categories(self) -> List[str]:
        return [
            category
            for row in self.fetch(
                'SELECT category FROM transactions WHERE category!="" GROUP BY category'
            )
            for category in row
        ]

    def find(self, *args: str, **kwargs) -> Optional[Tuple[Any, ...]]:
        """ Returns a single row matching the given criteria """
        if (results := self.select(*args, limit=1, **kwargs)):
            return results[0]
        return None

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
