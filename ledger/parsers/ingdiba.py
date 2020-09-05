from datetime import datetime
from csv import reader
from typing import List

from ledger.database import Transaction


def date(value):
    return datetime.strptime(value, '%d.%m.%Y').date()


def number(value):
    return float(value.replace('.', '').replace(',', '.'))


def read(filename: str) -> List[Transaction]:
    transactions = []
    with open(filename, encoding='latin-1') as csvfile:
        data = reader(csvfile, delimiter=';')
        for values in reversed(list(data)):
            transactions.append(Transaction(
                date=date(values[0]),
                valuta=date(values[1]),
                type=types[values[3]],
                subject=values[2].strip(),
                reference=values[4].strip(),
                saldo=number(values[5]),
                value=number(values[7]),
                account='ingdiba'
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
