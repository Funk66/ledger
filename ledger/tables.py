from dataclasses import dataclass
from typing import List, NewType, Optional, Type

Kind = NewType('Kind', str)
TEXT = Kind('TEXT')  # TODO: add length
FLOAT = Kind('FLOAT')
INTEGER = Kind('INTEGER')
DATE = Kind('DATE')


@dataclass
class Column:
    name: str
    type: str
    null: bool = True
    unique: bool = False
    primary: bool = False
    reference: Optional[Type['Table']] = None

    def __str__(self) -> str:
        definition = [f'"{self.name}" {self.type}']
        if self.unique:
            definition.append('UNIQUE')
        elif not self.null:
            definition.append('NOT NULL')
        return ' '.join(definition)


class MetaTable(type):
    def __new__(mcs, name, bases, namespace):
        namespace.update({'name': name.lower()})
        return super().__new__(mcs, name, bases, namespace)


class Table(metaclass=MetaTable):
    name: str
    columns: List[Column]

    def __init__(self):
        self.columns = []
        for name, attr in self.__dict__.items():
            if isinstance(attr, Column):
                attr.name = name
                self.columns.append(attr)

    @classmethod
    def create(cls) -> str:
        columns = [str(column) for column in cls.columns]
        primary_keys = [col.name for col in cls.columns if col.primary]
        if primary_keys:
            keys = '", "'.join(primary_keys)
            columns.append(f'PRIMARY KEY ("{keys}")')
        foreign_key = [col for col in cls.columns if col.reference]
        if foreign_key:
            columns.append(
                f'FOREIGN KEY ("{foreign_key[0].name}") '  # type: ignore
                f'REFERENCES {foreign_key[0].reference.name}("rowid")')
        return f"CREATE TABLE {cls.name} ({', '.join(columns)})"


class Transactions(Table):
    columns = [
        Column('date', DATE, null=False, primary=True),
        Column('valuta', DATE),
        Column('type', TEXT, null=False),
        Column('subject', TEXT, null=False),
        Column('reference', TEXT, null=False),
        Column('value', FLOAT, null=False, primary=True),
        Column('saldo', FLOAT, null=False, primary=True),
        Column('account', TEXT, null=False),
        Column('category', TEXT),
        Column('comment', TEXT),
    ]


class Tags(Table):
    columns = [
        Column('tag', TEXT, primary=True),
        Column('link', INTEGER, primary=True, reference=Transactions),
    ]
