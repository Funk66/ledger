from datetime import datetime
from pathlib import Path
from csv import reader
from typing import List

from ledger.utils import Time, str2date, str2float
from ledger.database import Transaction


def str2datetime(value: str) -> datetime:
    return datetime.strptime(value, '%d.%m.%Y %H:%M')


def read(filename: Path, account: str = '1822') -> List[Transaction]:
    transactions = []
    saldo = .0
    with open(filename, encoding='latin-1') as csvfile:
        data = reader(csvfile, delimiter=';')
        for values in reversed(list(data)):
            value = str2float(values[4])
            saldo += value
            dt = str2datetime(values[1])
            transactions.append(Transaction(
                date=dt.date(),
                time=Time(dt.hour, dt.minute),
                valuta=str2date(values[2]),
                type=types[values[6]],
                subject=values[7].strip(),
                reference="".join([value.strip() for value in values[13:18]]),
                saldo=saldo,
                value=value,
                account=account,
            ))
    return transactions


types = {
    'Debitkartenzahlung': 'payment',
    'Kartenzahlung/-en': 'payment',
    'Überweisung': 'transfer',
    'Gutschrift Überw.': 'income',
    'Entgeltabschluss': 'fee',
    'Rechnungsabschluss': 'fee',
    'Kundenhinweis': 'fee',
}
