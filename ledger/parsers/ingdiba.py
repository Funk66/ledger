from pathlib import Path
from csv import reader
from typing import List

from ledger.utils import str2date, str2float
from ledger.database import Transaction


def read(filename: Path, account: str = 'ingdiba') -> List[Transaction]:
    transactions = []
    with open(filename, encoding='latin-1') as csvfile:
        data = reader(csvfile, delimiter=';')
        for values in reversed(list(data)):
            transactions.append(Transaction(
                date=str2date(values[0]),
                valuta=str2date(values[1]),
                type=types[values[3]],
                subject=values[2].strip(),
                reference=values[5].strip(),
                saldo=str2float(values[6]),
                value=str2float(values[8]),
                account=account,
            ))
    return transactions


types = {
    'Lastschrift': 'payment',
    'Lastschrifteinzug': 'payment',
    'Überweisung': 'transfer',
    'Abbuchung': 'debit',
    'Entgelt': 'fee',
    'Gehalt/Rente': 'payroll',
    'Gutschrift': 'income',
    'Retouren': 'return',
    'Gutschrift aus Dauerauftrag': 'income auto',
    'Dauerauftrag / Terminueberweisung': 'payment auto',
    'Dauerauftrag/Terminueberweisung': 'payment auto'
}
