import logging
from csv import reader, writer
from pathlib import Path
from sqlite3 import IntegrityError, OperationalError, connect
from typing import Any, List, Sequence, Tuple

from .tables import Tags, Transactions


class SQLError(Exception):
    pass


class Client:
    path = Path.home() / '.config/ledger/transactions.csv'

    def __init__(self, filename: str = ':memory:'):
        self.filename = filename
        self.connection = connect(filename)
        self.cursor = self.connection.cursor()
        self.cursor.execute(Transactions.create())
        self.cursor.execute(Tags.create())
        self.connection.commit()

    def execute(self, command: str,
                data: Sequence[Sequence[Any]] = None) -> None:
        log.debug(command)
        try:
            if data:
                self.cursor.executemany(command, data)
            else:
                self.cursor.execute(command)
        except (OperationalError, IntegrityError):
            raise SQLError(f'Invalid command: {command}')
        self.connection.commit()

    def insert(self, table: str, data: Sequence[Sequence[Any]]) -> None:
        log.info(f'Inserting {len(data)} rows into {table}')
        values = ', '.join(['?'] * len(data[0]))
        self.execute(f'INSERT INTO {table} VALUES ({values})', data)

    def select(self, *args: str) -> List[Tuple[Any]]:
        columns = ', '.join(args) or '*'
        self.cursor.execute(f'SELECT {columns} FROM transactions')
        return self.cursor.fetchall()

    def count(self) -> int:
        self.cursor.execute(f'SELECT COUNT(value) FROM transactions')
        return self.cursor.fetchall()[0][0]

    def load(self, filename: Path = None) -> None:
        with open(filename or self.path, encoding='latin-1') as csvfile:
            i = 1
            transactions: List[List[Any]] = []
            tags: List[Tuple[str, int]] = []
            for row in reader(csvfile):
                transactions += [row[:-1]]
                if row[-1]:
                    tags += [(tag, i) for tag in row[-1].split(':')]
                i += 1
        self.insert('transactions', transactions)
        self.insert('tags', tags)

    def save(self, filename: Path = None) -> None:
        columns = [column.name for column in Transactions.columns]
        self.cursor.execute(f'''
            SELECT {', '.join(columns)}
            FROM transactions LEFT JOIN tags
            ON transactions.rowid=tags.transaction
            GROUP BY transaction.rowid
            ORDER BY transactions.rowid ASC
        ''')
        transactions = self.cursor.fetchall()
        with open(
                filename or self.path, 'w', encoding='latin-1',
                newline='') as output:
            csvfile = writer(output)
            csvfile.writerows(transactions)


log = logging.getLogger(__name__)
