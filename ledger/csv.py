from csv import reader, writer
from typing import List

from . import Transaction, sql, home


def write(store: sql.Store) -> None:
    with open(home / 'transactions.csv', 'w') as output:
        writer(output).writerows(store.select())


def ingdiba(filename: str) -> List[Transaction]:
    transactions = []
    with open(filename, encoding='latin-1') as csvfile:
        data = reader(csvfile, delimiter=';')
        for values in reversed(list(data)):
            transactions.append(Transaction(
                date=values[0],
                valuta=values[1],
                type=types[values[3]],
                subject=values[2].strip(),
                reference=values[4].strip(),
                saldo=values[5],
                value=values[7],
                account='ing-diba'
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
    'Gutschrift aus Dauerauftrag': 'income auto',
    'Dauerauftrag / Terminueberweisung': 'payment auto',
    'Dauerauftrag/Terminueberweisung': 'payment auto'
}
