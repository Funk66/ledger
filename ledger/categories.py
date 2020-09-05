from logging import getLogger
from pathlib import Path
from typing import List, NamedTuple

from yaml import safe_load

from . import home
from .database import Transaction

log = getLogger(__name__)


class Category(NamedTuple):
    name: str
    keywords: List[str]


class Categorizer:
    def __init__(self, path: Path = home / 'categories.yaml'):
        with open(path) as yml:
            data = safe_load(yml)
        self.categories = self.unpack(data)

    def unpack(self, data: dict, prefix: str = '') -> List[Category]:
        pack: List[Category] = []
        for name, value in data.items():
            category = f"{prefix}:{name}" if prefix else name
            if isinstance(value, dict):
                pack += self.unpack(value, category)
            elif isinstance(value, list):
                pack.append(Category(category, value))
            elif value is None:
                continue
            else:
                raise ValueError("Invalid categories file")
        return pack

    def __call__(self, transactions: List[Transaction]) -> None:
        for transaction in transactions:
            for category in self.categories:
                for keyword in category.keywords:
                    if keyword in transaction.subject:
                        if transaction.category and \
                                transaction.category != category:
                            log.warning(
                                f"Transaction {transaction.reference} is already "
                                "categorized: {transaction.category} != {category}"
                            )
                        else:
                            transaction.category = category.name
