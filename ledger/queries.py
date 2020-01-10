from enum import Enum
from abc import ABC, abstractmethod
from re import compile
from datetime import date
from typing import TypeVar, Type, Any, Callable, List, Union
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

    def __inv__(self, method: Callable[[Any, Any], bool], value: Any) -> bool:
        return method(value, self.value)

    def __call__(self, transaction: Transaction) -> bool:
        return bool(self.check(getattr(transaction, self.key)))


def converter(value: str, datatype: Type[T]) -> T:
    if datatype is float:
        return float(value)
    elif datatype is date:
        return isodate(value)
    else:
        return value
