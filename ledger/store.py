from csv import reader, writer
from random import choice
from dataclasses import astuple
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Sequence

from ledger.entities import Tags, Transaction

TransactionList = Generator[Transaction, None, None]


class Store:
    path = Path.home() / '.config/ledger/transactions.csv'
    columns = [field for field in Transaction.__annotations__]

    def __init__(self):
        with open(self.path, encoding='latin-1') as csvfile:
            rows = [row for row in reader(csvfile)]
        assert rows, "Database is empty"
        headers = rows[0]
        if set(headers) != set(self.columns):
            raise ValueError(f"Database columns do not match current schema")
        data = [dict(zip(headers, row[1:])) for row in rows]
        self.transactions = []
        self.hashes = []
        for row in data:
            row['date'] = datetime.strptime(row['date'], '%Y-%m-%d').date()
            row['valuta'] = datetime.strptime(row['valuta'], '%Y-%m-%d').date()
            row['tags'] = Tags(row['tags'].split(','))
            row['value'] = float(row['value'])
            row['saldo'] = float(row['saldo'])
            transaction = Transaction(**row)
            self.transactions.append(transaction)
            self.hashes.append(transaction.hash)

    def __iter__(self) -> TransactionList:
        return self.transactions.__values__()

    def __len__(self) -> int:
        return len(self.transactions)

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Transaction):
            if item.hash in self.transactions:
                return True
        return False

    def get(self,
            query: Callable[[Transaction], bool] = None) -> TransactionList:
        if query:
            return (t for t in self.transactions.values if query(t))
        else:
            return self.transactions[choice(self.hashes)]

    def column(self, column: str) -> Generator[Any, None, None]:
        if column not in self.columns:
            raise AttributeError(f'{column} is not a valid column')
        for transaction in self.transactions.values():
            yield getattr(transaction, column)

    def extend(self, transactions: Sequence[Transaction]) -> None:
        for transaction in transactions:
            if not isinstance(transaction, Transaction):
                raise ValueError(
                    f'Expected <Transaction>, got <{type(transaction)}>')
            if transaction.hash not in self:
                self.transactions.append(transaction)
                self.hashes.append(transaction.hash)
            else:
                original = astuple(self.transactions[transaction.hash])[:6]
                current = astuple(transaction)[:6]
                if current != original:
                    log.warning(f'Mismatch: {current} != {original}')

    def check(self) -> None:
        row = 1
        saldo: Dict[str, float] = {}
        for transaction in self.transactions:
            if transaction.account in saldo:
                previous_saldo = saldo[transaction.account]
                current_saldo = round(transaction.saldo - transaction.value, 2)
                if current_saldo != previous_saldo:
                    log.info(f"Check {transaction.hash} on row {row}")
            saldo[transaction.account] = transaction.saldo
            row += 1

    def save(self, path: Path = None) -> None:
        transactions = [astuple(t) for t in self.transactions]
        with open(
                path or self.path, 'w', encoding='latin-1',
                newline='') as output:
            log.info(f'Writing table to {path or self.path}')
            csvfile = writer(output)
            csvfile.writerow(self.columns)
            csvfile.writerows(transactions)


log = getLogger(__name__)
