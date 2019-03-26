from logging import getLogger, basicConfig
from hashlib import md5
from pathlib import Path
from datetime import datetime
from datetime import date as day
from pydantic import BaseModel, validator
from dataclasses import dataclass
from typing import Dict


class Transaction(BaseModel):
    date: day
    valuta: day
    type: str
    subject: str
    reference: str
    value: float
    saldo: float
    account: str
    category: str = ''
    comment: str = ''
    hash: str = ''

    @validator('value', 'saldo', pre=True)
    def number(cls, value):
        if isinstance(value, str):
            try:
                return float(value.replace('.', '').replace(',', '.'))
            except ValueError:
                return float(value)
        return value

    @validator('date', 'valuta', pre=True)
    def day(cls, value):
        return datetime.strptime(value, '%d.%m.%Y').date()

    @validator('hash', always=True)
    def stamp(cls, value, values, **kwargs):
        if not value:
            stamp = f'{values["date"]}{values["value"]}{values["saldo"]}'
            return md5(bytes(stamp, encoding='utf8')).hexdigest()

    def categorize(self, category: Dict) -> bool:
        pass


class Tag(BaseModel):
    hash: str
    tag: str


@dataclass
class Category:
    name: str
    condition: str


basicConfig(format='%(message)s')
log = getLogger('ledger')
home = Path(Path.home() / '.config' / 'ledger')
home.mkdir(parents=True, exist_ok=True)
