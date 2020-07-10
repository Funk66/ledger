from csv import reader, writer
from dataclasses import astuple
from loguru import logger
from pathlib import Path
from random import random
from typing import Any, Callable, Dict, Generator, Sequence

from ledger.entities import Tags, Transaction
from ledger.utils import isodate
from ledger.queries import Filter
from ledger.tables import Table

TransactionList = Generator[Transaction, None, None]


class Store:
    path = Path.home() / '.config/ledger/transactions.csv'
    columns = [field for field in Transaction.__annotations__]

    def __init__(self):
        self.filter = Filter([])
        self.transactions = []

    def __iter__(self) -> TransactionList:
        return self.transactions.__values__()

    def __len__(self) -> int:
        return len(self.transactions)

    def print(self) -> None:
        data = [astuple(row) for row in self.filter.data[-1]]
        table = Table(self.columns, data)
        print(table.header())
        print(table.rows())

    def get(self,
            query: Callable[[Transaction], bool] = None) -> TransactionList:
        if query:
            return (t for t in self.transactions.values if query(t))
        else:
            return self.transactions[round(random()*len(self.transactions))]

    def column(self, column: str) -> Generator[Any, None, None]:
        if column not in self.columns:
            raise AttributeError(f'{column} is not a valid column')
        for transaction in self.transactions.values():
            yield getattr(transaction, column)

    def extend(self, transactions: Sequence[Transaction]) -> None:
        first = transactions[0].hash
        start = 0
        total = len(self.transactions)
        while start < total:
            if self.transactions[start].hash == first:
                break
            start += 1
        end = total - start
        for i in range(end):
            original = astuple(self.transactions[i + start])[:6]
            current = astuple(transactions[i])[:6]
            if current != original:
                raise ValueError(f'Mismatch: {current} != {original}')

        self.transactions += transactions[end:]
        logger.info(f"{len(self.transactions) - total} new transactions")

    def check(self) -> None:
        row = 1
        saldo: Dict[str, float] = {}
        for transaction in self.transactions:
            if transaction.account in saldo:
                previous_saldo = saldo[transaction.account]
                current_saldo = round(transaction.saldo - transaction.value, 2)
                if current_saldo != previous_saldo:
                    raise ValueError(f"Check {transaction.hash} on row {row}")
            saldo[transaction.account] = transaction.saldo
            row += 1
        logger.info("Check passed")

    def load(self):
        logger.info("Loading store")
        with open(self.path, encoding='latin-1') as csvfile:
            rows = [row for row in reader(csvfile)]
        assert rows, "Database is empty"
        headers = rows[0]
        if set(headers) != set(self.columns):
            raise ValueError(f"Database columns do not match current schema")
        data = [dict(zip(headers, row)) for row in rows[1:]]
        self.transactions = []
        for row in data:
            row['date'] = isodate(row['date'])
            row['valuta'] = isodate(row['valuta'])
            row['tags'] = Tags(row['tags'].split(','))
            row['value'] = float(row['value'])
            row['saldo'] = float(row['saldo'])
            transaction = Transaction(**row)
            self.transactions.append(transaction)
        self.filter.data = [self.transactions]

    def save(self, path: Path = None) -> None:
        logger.info("Writing store")
        transactions = [astuple(t) for t in self.transactions]
        with open(
                path or self.path, 'w', encoding='latin-1',
                newline='') as output:
            logger.info(f'Writing table to {path or self.path}')
            csvfile = writer(output)
            csvfile.writerow(self.columns)
            csvfile.writerows(transactions)
