from pathlib import Path
from csv import reader, writer
from typing import Any, Callable, List, Optional, Sequence, Tuple

from .database import Client
from .tables import Tags, Transactions
from .entities import Transaction


class Store:
    """ High-level interface to the data store """
    path = Path.home() / '.config/ledger/'

    def __init__(self):
        self.client = Client()

    def add(self, transaction: Transaction) -> None:
        data = [getattr(transaction, column.name) for column in Transactions.columns]
        self.insert('transactions', data)
        if transaction.tags:
            rowid = self.count()
            for tag in transaction.tags:
                self.insert('tags', [(tag, rowid)])

    def load(self, filename: Path = None) -> None:
        """ Load stored data """
        filepath = filename or self.path / 'transactions.csv'
        with open(filepath, encoding='latin-1') as csvfile:
            i = 1
            transactions: List[List[Any]] = []
            tags: List[Tuple[str, int]] = []
            for row in reader(csvfile):
                transactions += [row[:-1]]
                if row[-1]:
                    tags += [(tag, i) for tag in row[-1].split(':')]
                i += 1
        self.client.insert('transactions', transactions)
        if tags:
            self.client.insert('tags', tags)

    def save(self, filename: Path = None) -> None:
        """ Save all transactions in memory to a CSV file """
        filepath = filename or self.path / 'transactions.csv'
        transactions = self.client.load()
        with open(filepath, 'w', encoding='latin-1', newline='') as output:
            csvfile = writer(output)
            csvfile.writerows(transactions)

    def extend(self, transactions: List[Transaction]) -> None:
        """ Add new transactions to the database """
        account = transactions[0].account
        columns = ['date', 'value', 'saldo', 'subject', 'reference']
        last_row = self.fetch(f'''
            SELECT {", ".join(columns)} FROM transactions
            WHERE account="{account}"
            ORDER BY date DESC LIMIT 1'''
        )
        last_transaction = Transaction(**dict(zip(columns, last_row)))
        for i in range(len(transactions)):
            if transactions[i] is last_transaction:
                break
        else:
            raise ValueError("No matching transaction found during import")

        try:
            next_transaction = transactions[i+1]
        except IndexError:
            return  # no new transactions to add

        if last_transaction.saldo + next_transaction.value != next_transaction.saldo:
            raise ValueError(
                    "Transaction mismatch: data cannot be appended\n"
                    f"\tLast transaction: {last_transaction}\n"
                    f"\tNext transaction: {next_transaction}\n"
                    )
        # new_rows = [astuple(transaction)]
        # new_transactions = transactions[1:]
