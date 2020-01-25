import logging
from csv import reader, writer
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Tuple

from litecli.main import LiteCli, SQLExecute

from .tables import Tags, Transactions


class SQLError(Exception):
    pass


class Client:
    path = Path.home() / '.config/ledger/'

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

    def insert(self, table: str, data: Sequence[Sequence[Any]]) -> None:
        log.info(f'Inserting {len(data)} rows into {table}')
        values = ', '.join(['?'] * len(data[0]))
        cursor = self.sqlexecute.conn.cursor()
        cursor.executemany(f'INSERT INTO {table} VALUES ({values})', data)
        self.sqlexecute.conn.commit()

    def select(self, *args: str) -> List[Tuple[Any]]:
        columns = ', '.join(args) or '*'
        return self.fetch(f'SELECT {columns} FROM transactions')

    def count(self) -> int:
        return self.fetch(f'SELECT COUNT(value) FROM transactions')[0][0]

    def load(self, filename: Path = None) -> None:
        filepath = filename or self.path / 'transactions.csv'
        with open(filepath, encoding='latin-1') as csvfile:
            i = 1
            transactions: List[List[Any]] = []
            tags: List[Tuple[str, int]] = []
            for row in reader(csvfile):
                transactions += [row[:-1]]
                if row[-1]:
                    tags += [(tag, i) for tag in row[-1].split(':')]
                i += 1
        self.insert('transactions', transactions)
        if tags:
            self.insert('tags', tags)

    def save(self, filename: Path = None) -> None:
        columns = [column.name for column in Transactions.columns] + ['tag']
        transactions = self.fetch(f'''
            SELECT {', '.join(columns)}
            FROM transactions LEFT JOIN tags
            ON transactions.rowid=tags.link
            GROUP BY transactions.rowid
            ORDER BY transactions.rowid ASC
        ''')
        filepath = filename or self.path / 'transactions.csv'
        with open(filepath, 'w', encoding='latin-1', newline='') as output:
            csvfile = writer(output)
            csvfile.writerows(transactions)

    def prompt(self):
        lite_cli = LiteCli(
            sqlexecute=self.sqlexecute, liteclirc=self.path / 'config')
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
