from csv import reader
from datetime import datetime
from pathlib import Path
from typing import List

from ledger.database import Transaction
from ledger.utils import str2date, str2float


def str2datetime(value: str) -> datetime:
    return datetime.strptime(value, "%d.%m.%Y %H:%M")


def read(filename: Path, account: str = "1822") -> List[Transaction]:
    transactions = []
    saldo = 0.0
    with open(filename, encoding="latin-1") as csvfile:
        data = reader(csvfile, delimiter=";")
        for values in reversed(list(data)):
            value = str2float(values[4])
            saldo = round(saldo + value, 2)
            dt = str2datetime(values[1])
            transactions.append(
                Transaction(
                    date=dt.date(),
                    time=f"{dt.hour:0>2}:{dt.minute:0>2}",
                    valuta=str2date(values[2]),
                    type=types[values[6]],
                    subject=values[7].strip(),
                    reference="".join(
                        [value.strip() for value in values[13:18]]
                    ),
                    saldo=saldo,
                    value=value,
                    account=account,
                )
            )
    return transactions


types = {
    "Debitkartenzahlung": "payment",
    "Kartenzahlung/-en": "payment",
    "Überweisung": "transfer",
    "Gutschrift Überw.": "income",
    "Entgeltabschluss": "fee",
    "Rechnungsabschluss": "fee",
    "Kundenhinweis": "fee",
}
