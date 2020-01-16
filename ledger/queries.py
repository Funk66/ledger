from enum import Enum
from re import compile
from datetime import date
from typing import TypeVar, Type, Any, Callable, Union, List
from functools import partial

from .entities import Transaction
from .utils import isodate


T = TypeVar('T')


class Operator(Enum):
    gt = '>'
    ge = '>='
    lt = '<'
    le = '<='
    ne = '!='
    eq = 'is'
    re = 'has'


class Query:
    def __init__(self, query: str):
        self.key, operator, value = query.split(maxsplit=2)
        self.operator = Operator(operator)
        datatype = Transaction.__annotations__[self.key]
        self.value = converter(value, datatype)
        if self.operator is Operator.re:
            self.check = compile(self.value).search
        else:
            method = getattr(datatype, f'__{self.operator.name}__')
            self.check = partial(self.__inv__, method)

    def __str__(self) -> str:
        return f"{self.key} {self.operator.value} {self.value}"

    def __inv__(self, method: Callable[[Any, Any], bool], value: Any) -> bool:
        return method(value, self.value)

    def __call__(self, transaction: Transaction) -> bool:
        return bool(self.check(getattr(transaction, self.key)))


class Filter:
    def __init__(self, data: List[Transaction]):
        self.queries: List[Union[Query, Callable[[Transaction], bool]]] = []
        self.data = [data]

    def __str__(self) -> str:
        queries = '> and <'.join([str(query) for query in self.queries])
        return f"Filter <{queries}>"

    def add(self, query: Union[Query, Callable[[Transaction], bool]]) -> None:
        self.queries.append(query)
        self.data.append([row for row in self.data[-1] if query(row)])

    def pop(self) -> None:
        self.queries.pop()
        self.data.pop()

    def drop(self) -> None:
        self.queries = []
        self.data = self.data[:1]


def converter(value: str, datatype: Type[T]) -> T:
    if datatype is float:
        return float(value)
    elif datatype is date:
        return isodate(value)
    else:
        return value
