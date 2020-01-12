from logging import getLogger
from pathlib import Path
from typing import List, NamedTuple

from yaml import load

from . import home
from .entities import Transaction

log = getLogger(__name__)


class Category(NamedTuple):
    name: str
    keywords: List[str]


def parse(path: Path = home / 'categories.yaml') -> List[Category]:
    def unpack(data: dict, prefix: str = '') -> List[Category]:
        pack: List[Category] = []
        for name, value in data.items():
            category = f"{prefix}:{name}" if prefix else name
            if isinstance(value, dict):
                pack += unpack(value, category)
            elif isinstance(value, list):
                pack.append(Category(category, value))
            elif value is None:
                continue
            else:
                raise ValueError("Invalid categories file")
        return pack

    with open(path) as yml:
        data = load(yml)
    return unpack(data)


def apply(transactions: List[Transaction],
          categories: List[Category] = None) -> None:
    if not categories:
        categories = parse()
    for transaction in transactions:
        for category in categories:
            for keyword in category.keywords:
                if keyword in transaction.subject:
                    if transaction.category and \
                            transaction.category != category:
                        log.warning(
                            f"Transaction {transaction.hash} is already "
                            "categorized: {transaction.category} != {category}"
                        )
                    else:
                        transaction.category = category.name
