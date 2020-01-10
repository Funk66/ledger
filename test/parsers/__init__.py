from datetime import date

from ledger.entities import Transaction

sample_transaction = Transaction(
    date=date(2018, 9, 28),
    valuta=date(2018, 9, 28),
    subject="GitHub Inc.",
    type="income",
    reference="Payroll 09/2018",
    value=3975.91,
    saldo=4308.68,
    account='ingdiba',
)

sample_transactions = [
    sample_transaction,
    Transaction(
        date=date(2018, 10, 1),
        valuta=date(2018, 10, 1),
        subject="RedBull Global Group",
        type="payment",
        reference="Travel expenses 01.10 - 31.10.18",
        value=-19.9,
        saldo=4288.78,
        account='ingdiba',
    ),
    Transaction(
        date=date(2018, 10, 1),
        valuta=date(2018, 10, 1),
        subject="NH Hotels",
        type="payment",
        reference="5428719643 / 50738927",
        value=-484.9,
        saldo=3803.88,
        account='ingdiba',
    ),
    Transaction(
        date=date(2018, 10, 1),
        valuta=date(2018, 10, 1),
        subject="John Smith",
        type="income auto",
        reference="Payback",
        value=100.0,
        saldo=3903.88,
        account='ingdiba',
    ),
    Transaction(
        date=date(2018, 10, 2),
        valuta=date(2018, 10, 2),
        subject="DB Vertrieb GmbH",
        type="payment",
        reference="DB AUTOMAT//BERLIN-SCHOENEF.",
        value=-3.2,
        saldo=3900.68,
        account='ingdiba',
    ),
]
