from dataclasses import dataclass, field
from datetime import date as day
from hashlib import md5
from typing import Union, Any


class Tags(set):
    def __str__(self) -> str:
        return ', '.join((str(tag) for tag in self))


@dataclass
class Transaction:
    date: day
    valuta: day
    type: str
    subject: str
    reference: str
    value: float
    saldo: float
    account: str
    tags: Tags = field(default_factory=Tags)
    category: str = ''
    comment: str = ''
    hash: str = ''

    def __post_init__(self):
        if not self.hash:
            stamp = f"{self.date}{self.value}{self.saldo}"
            self.hash = md5(bytes(stamp, encoding='utf8')).hexdigest()

    def __eq__(self, item: Any) -> bool:
        if isinstance(item, Transaction) and item.hash == self.hash:
            return True
        return False


class Condition:
    def __init__(self, definitions: Union[str, list]):
        if isinstance(definitions, str):
            self.key, self.method, self.value = definitions.split()

    def __call__(self, transaction: Transaction) -> bool:
        value = getattr(transaction, self.key)
        method = getattr(value, f'__{self.method}__')
        return method(self.value)


class Filter:
    def __init__(self, key, operator, value):
        self.key = getattr(Transaction, key)
        self.operator = getattr(self.key, operator)
        self.value = value

    def __call__(self, transaction: Transaction):
        return self.operator(self.value)
