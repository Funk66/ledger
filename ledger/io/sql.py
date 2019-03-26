from datetime import date
from sqlite3 import connect, OperationalError, IntegrityError
from typing import List, Tuple, Any, Optional, Iterable, Dict
from pydantic import BaseModel as Entity

from .. import Transaction, Category, Tag, log


class SQLError(Exception):
    pass


class Table:
    types = {str: 'TEXT', float: 'FLOAT', date: 'DATE'}

    def __init__(
            self,
            store: 'Store',
            name: str,
            entity: Entity,  # TODO: Type[Var]
            foreign: Tuple[Entity, str] = None,
            unique: List[str] = None):
        self.store = store
        self.name = name
        self.columns: Dict[str, type] = entity.__annotations__
        self.create(foreign, unique)

    def execute(self,
                command: str,
                data: Iterable[Iterable[Any]] = None,
                commit: bool = True) -> None:
        log.debug(command)
        try:
            if data:
                self.store.cursor.executemany(command, data)
            else:
                self.store.cursor.execute(command)
        except (OperationalError, IntegrityError):
            raise SQLError(f'Invalid command: {command}')
        if commit and not command.upper().startswith('SELECT'):
            self.store.connection.commit()

    def create(self,
               foreign: Tuple[Entity, str] = None,
               unique: List[str] = None) -> None:
        columns: List[str] = []
        for name, kind in self.columns.items():
            column = f'"{name}" {self.types[kind]}'
            if unique and name in unique:
                column += ' UNIQUE'
            columns.append(column)

        if foreign:
            columns.append(
                'FOREIGN KEY ({1}) REFERENCES {0}({1})'.format(*foreign))

        sql = f'CREATE TABLE IF NOT EXISTS {self.name} ({", ".join(columns)})'
        self.execute(sql, commit=False)

    def insert(self, data: List[Dict[str, Any]]) -> None:
        log.info(f'{len(data)} new {self.name}')
        values = ', '.join(['?'] * len(self.columns))
        rows = [[row[col] for col in self.columns] for row in data]
        self.execute(f'INSERT INTO {self.name} VALUES ({values})', rows)

    def select(self, *args: str) -> List[Tuple[Any]]:
        columns = ', '.join(args) or '*'
        self.execute(f'SELECT {columns} FROM {self.name}')
        return self.store.cursor.fetchall()

    def count(self) -> int:
        column = list(self.columns.keys())[0]
        self.execute(f'SELECT COUNT({column}) FROM {self.name}', commit=False)
        return self.store.cursor.fetchall()[0][0]


class Store:
    def __init__(self, filename: str = ':memory:'):
        self.filename = filename
        self.connection = connect(filename)
        self.cursor = self.connection.cursor()
        self.transactions = Table(
            self, 'transactions', Transaction, unique=['hash'])
        self.tags = Table(self, 'tags', Tag, foreign=('transactions', 'hash'))
        self.connection.commit()

    def execute(self,
                command: str,
                data: Optional[List[Transaction]] = None,
                mode: str = '') -> None:
        method = getattr(self.cursor, f'execute{mode}')
        command = ' '.join(command.split())
        log.debug(f'{command}')
        if data:
            method(command, data)
        else:
            method(command)
        self.connection.commit()

    def select(self, include: List[str] = None,
               exclude: List[str] = None) -> List[List[Any]]:
        if include and exclude:
            raise ValueError(f'Cannot specify both include and exclude')
        columns = [
            'rowid', 'date', 'valuta', 'type', 'category', 'subject',
            'reference', 'value', 'saldo', 'comment', 'account', 'hash'
        ]
        tags = True
        if include:
            columns = include
            tags = 'tags' in include
        elif exclude:
            columns = list(set(columns) - set(exclude))
            tags = 'tags' not in exclude
        headers = [col.capitalize() for col in columns]
        columns = [f'transactions.{column}' for column in columns]
        if tags:
            columns.append('group_concat(tag)')
            headers.append('Tags')
        self.execute(f'''
            SELECT {', '.join(columns)}
            FROM transactions LEFT JOIN tags
            ON transactions.hash=tags.hash
            GROUP BY transactions.hash
            ORDER BY transactions.rowid ASC
        ''')
        return [headers] + self.cursor.fetchall()

    def update(self, category: Category) -> None:
        self.execute(f'''
            UPDATE transactions
            SET category="{category.name}"
            WHERE {category.condition}
        ''')

    def tag(self, tags: List[Tag], index: int = 0) -> None:
        for tag in tags:
            if isinstance(tag['condition'], list):
                tag['condition'] = ' OR '.join(tag['condition'])
            self.execute(f'''
                INSERT INTO tags (hash, tag)
                SELECT hash, "{tag['name']}" AS tag FROM transactions
                WHERE ({tag['condition']}) AND rowid > {index} AND hash NOT IN
                (SELECT hash FROM tags WHERE tag="{tag['name']}");
            ''')
