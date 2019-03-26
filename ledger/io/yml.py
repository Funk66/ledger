from yaml import safe_load
from typing import List

from .. import Category, home


def read(filename: str):
    path = home / f'{filename}.yaml'
    if path.exists():
        with open(path) as tagfile:
            return safe_load(tagfile)


def categories() -> List[Category]:
    def parse(value, name=''):
        if value:
            if isinstance(value, dict):
                for subkey, data in value.items():
                    parse(data, f'{name}:{subkey}' if name else subkey)
            elif isinstance(value, list):
                categories.append(Category(name, ' OR '.join(value)))
            elif isinstance(value, str):
                categories.append(Category(name, value))
            else:
                raise ValueError(f'{type(value)} is not a valid category rule')

    categories: List[Category] = []
    parse(read('categories'))
    return categories
