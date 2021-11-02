from csv import reader
from datetime import datetime
from pathlib import Path
from typing import List

from ledger.database import Transaction


def str2datetime(value: str) -> datetime:
    if len(value) == 18:
        value = value.replace(" ", " 0")
    return datetime.fromisoformat(value)


def read(filename: Path, account: str = "revolut") -> List[Transaction]:
    transactions = []
    with open(filename) as csvfile:
        data = list(reader(csvfile))
        for values in data[1:]:
            started = str2datetime(values[2])
            completed = str2datetime(values[2])
            fee = -float(values[6])
            transactions.append(
                Transaction(
                    date=started.date(),
                    valuta=completed.date(),
                    time=str(started.time()),
                    type=types[values[0]],
                    subject=values[4],
                    reference="",
                    value=float(values[5]),
                    saldo=float(values[9]) - fee,
                    account=account,
                )
            )
            if fee:
                transactions.append(
                    Transaction(
                        date=started.date(),
                        valuta=completed.date(),
                        time=str(started.time()),
                        type="fee",
                        subject=values[4],
                        reference="",
                        value=fee,
                        saldo=float(values[9]),
                        account=account,
                    )
                )
    return transactions


types = {
    "TRANSFER": "transfer",
    "CARD_PAYMENT": "payment",
}
