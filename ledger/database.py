import logging
from functools import wraps
from typing import Any, Callable, List, Optional, Sequence, Tuple

from litecli.main import LiteCli, SQLExecute

from . import home
from .tables import Tags, Transactions


class SQLError(Exception):
    pass


class Client:
    """ SQL interface for low-level commands """
    def __init__(self, filename: str = ':memory:'):
        self.dirty = False
        self.sqlexecute = SQLExecute(filename)
        self.sqlexecute.run = tripwire(self.sqlexecute.run, self)
        cursor = self.sqlexecute.conn.cursor()
        cursor.execute(Transactions.create())
        cursor.execute(Tags.create())
        self.sqlexecute.conn.commit()

    def fetch(self, command: str) -> List[Tuple[Any]]:
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
            log.debug(f'Inserting row into {table}')
        else:
            log.debug(f'Inserting {len(data)} rows into {table}')
        values = ', '.join(['?'] * len(data[0]))
        cursor = self.sqlexecute.conn.cursor()
        cursor.executemany(f'INSERT INTO {table} VALUES ({values})', data)
        self.sqlexecute.conn.commit()

    def select(self, *args: str, limit: int = 0) -> List[Tuple[Any]]:
        """ Return selected columns from all transactions """
        columns = ', '.join(args) or '*'
        command = f'SELECT {columns} FROM transactions'
        if limit:
            command += f" LIMIT {limit}"
        return self.fetch(command)

    def count(self) -> int:
        return self.fetch(f'SELECT COUNT(value) FROM transactions')[0][0]

    def categories(self) -> List[str]:
        return [
            category
            for row in self.fetch(
                'SELECT category FROM transactions WHERE category!="" GROUP BY category'
            )
            for category in row
        ]

    def find(self, **kwargs) -> List[Tuple[Any]]:
        # TODO: optionally return one
        columns = ['rowid'] + [column.name for column in Transactions.columns]
        values = [f'{key}="{value}"' for key, value in kwargs.items()]
        return self.fetch(f'SELECT {", ".join(columns)} FROM transactions '
                          f'WHERE {", ".join(values)}')

    def set(self, rowid: int, **kwargs) -> None:
        cursor = self.sqlexecute.conn.cursor()
        values = [f'{key}="{value}"' for key, value in kwargs.items()]
        cursor.execute(f'UPDATE transactions SET {", ".join(values)} '
                       f'WHERE rowid={rowid}')

    def prompt(self):
        lite_cli = LiteCli(
            sqlexecute=self.sqlexecute, liteclirc=home / 'config')
        lite_cli.run_cli()
        if self.dirty and input('Save? ') == 'y':
            self.save()


def tripwire(run: Callable[[str], 'SQLResponse'],
             client: Client):
    @wraps(run)
    def wrapper(statement: str) -> 'SQLResponse':
        if statement.lower().startswith('update'):
            client.dirty = True
        return run(statement)

    return wrapper


SQLResponse = Tuple[Optional[str], Optional[List[Tuple[Any]]], Optional[
    Tuple[str]], Optional[str]]
log = logging.getLogger(__name__)
