from datetime import date
from pathlib import Path
from typing import List
from pytest import fixture

from ledger.database import Transaction, Tag, SQLite


@fixture
def db(stored_transactions: List[Transaction], stored_tags: List[Tag]) -> SQLite:
    db = SQLite(Path(__file__).parent / "data")
    db.transactions.add_many(stored_transactions)
    db.tags.add_many(stored_tags)
    return db


@fixture
def transaction() -> Transaction:
    return Transaction(
        date=date(2020, 3, 14),
        valuta=date(2020, 3, 15),
        subject="Lupo Lopez",
        type="payment",
        reference="Test-o-matic",
        value=-253.98,
        saldo=12093.67,
        account="cash",
        category="work:freelancing",
        comment="Code update",
    )


@fixture
def stored_transactions() -> List[Transaction]:
    return [
        Transaction(
            date=date(2015, 6, 2),
            valuta=date(2015, 6, 2),
            type="payment",
            subject="TESCO, UK",
            reference="017278916389756839287389260",
            value=-9.6,
            saldo=4776.06,
            account="ingdiba",
            category="groceries:food",
            location="England",
            comment="Dinner for two",
        ),
        Transaction(
            date=date(2015, 6, 2),
            valuta=date(2015, 6, 1),
            type="payment",
            subject="VISA MITTELBRANDENBURGISCHE",
            reference="NR7022601016 DAHLEWITZ    BARGELDAUSZAHLUNG  29.05",
            value=-50.0,
            saldo=4726.06,
            account="ingdiba",
            category="others:cash",
            location="Brandenburg",
        ),
        Transaction(
            date=date(2015, 6, 5),
            valuta=date(2015, 6, 5),
            type="payment",
            subject="PENNY SAGT DANKE. 35302101",
            reference="030618490259981161256009647",
            value=-6.96,
            saldo=4719.1,
            account="ingdiba",
            category="gift:holidays",
        ),
        Transaction(
            date=date(2015, 6, 5),
            valuta=date(2015, 6, 5),
            type="payment",
            subject="WOOLWORTH GMBH FIL  1100*DE",
            reference="EC 61264178 040615181722OC1  64AEE4884DF7559D40FE092777",
            value=-20.56,
            saldo=4698.54,
            account="ingdiba",
            category="holidays:family",
        ),
        Transaction(
            date=date(2015, 6, 5),
            valuta=date(2015, 6, 5),
            type="payment",
            subject="REWE SAGT DANKE. 42655603",
            reference="EC 56018807 040615191727OC1  A52357E244DF469380259F5C3F",
            value=-29.35,
            saldo=4669.19,
            account="ingdiba",
            category="groceries:food",
            comment="Pending for confirmation",
        ),
    ]


@fixture
def stored_tags() -> List[Tag]:
    return [
        Tag(name="weekend", transaction=1),
        Tag(name="family", transaction=3),
        Tag(name="weekend", transaction=3),
        Tag(name="work", transaction=2),
    ]


@fixture
def parsed_transactions() -> List[Transaction]:
    return [
        Transaction(
            date=date(2015, 6, 5),
            valuta=date(2015, 6, 5),
            type="payment",
            subject="WOOLWORTH GMBH FIL  1100*DE",
            reference="EC 61264178 040615181722OC1  64AEE4884DF7559D40FE092777",
            value=-20.56,
            saldo=4698.54,
            account="ingdiba",
        ),
        Transaction(
            date=date(2015, 6, 5),
            valuta=date(2015, 6, 5),
            type="payment",
            subject="REWE SAGT DANKE. 42655603",
            reference="EC 56018807 040615191727OC1  A52357E244DF469380259F5C3F",
            value=-29.35,
            saldo=4669.19,
            account="ingdiba",
        ),
        Transaction(
            date=date(2015, 9, 28),
            valuta=date(2015, 9, 28),
            subject="GitHub Inc.",
            type="income",
            reference="Payroll 09/2015",
            value=3975.91,
            saldo=8645.1,
            account="ingdiba",
        ),
        Transaction(
            date=date(2015, 10, 1),
            valuta=date(2015, 10, 1),
            subject="RedBull Global Group",
            type="payment",
            reference="Travel expenses 01.10 - 31.10.18",
            value=-19.9,
            saldo=8625.2,
            account="ingdiba",
        ),
        Transaction(
            date=date(2015, 10, 1),
            valuta=date(2015, 10, 1),
            subject="NH Hotels",
            type="payment",
            reference="5428719643 / 50738927",
            value=-484.9,
            saldo=8140.3,
            account="ingdiba",
        ),
        Transaction(
            date=date(2015, 10, 1),
            valuta=date(2015, 10, 1),
            subject="John Smith",
            type="income auto",
            reference="Payback",
            value=100.0,
            saldo=8240.3,
            account="ingdiba",
        ),
        Transaction(
            date=date(2015, 10, 2),
            valuta=date(2015, 10, 2),
            subject="DB Vertrieb GmbH",
            type="payment",
            reference="DB AUTOMAT//BERLIN-SCHOENEF.",
            value=-3.2,
            saldo=8237.1,
            account="ingdiba",
        ),
    ]
