from dataclasses import dataclass, field, astuple
from datetime import date as day
from typing import Tuple, Any


class Tags(set):
    def __str__(self) -> str:
        return ";".join((str(tag) for tag in self))


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
    category: str = ""
    location: str = ""
    comment: str = ""
    tags: Tags = field(default_factory=Tags)

    def __eq__(self, item: Any) -> bool:
        if (
            isinstance(item, Transaction)
            and item.date == self.date
            and item.value == self.value
            and item.saldo == self.saldo
            and item.account == self.account
        ):
            return True
        return False

    @property
    def data(self) -> Tuple[Any, ...]:
        return astuple(self)[:-1]
