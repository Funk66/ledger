from datetime import date

from pytest import fixture

from ledger.entities import Tags, Transaction


@fixture
def transactions():
    return [
        Transaction(
            date=date(2015, 6, 2),
            valuta=date(2015, 6, 2),
            type='payment',
            subject='TESCO, UK',
            reference='017278916389756839287389260',
            value=-9.6,
            saldo=4776.06,
            account='ingdiba',
            tags=Tags(),
            category='groceries:food',
            comment='',
        ),
        Transaction(
            date=date(2015, 6, 2),
            valuta=date(2015, 6, 1),
            type='payment',
            subject='VISA MITTELBRANDENBURGISCHE',
            reference='NR7022601016 DAHLEWITZ    BARGELDAUSZAHLUNG  29.05',
            value=-50.0,
            saldo=4726.06,
            account='ingdiba',
            tags=Tags(),
            category='others:cash',
            comment='',
        ),
        Transaction(
            date=date(2015, 6, 5),
            valuta=date(2015, 6, 5),
            type='payment',
            subject='PENNY SAGT DANKE. 35302101',
            reference='030618490259981161256009647',
            value=-6.96,
            saldo=4719.1,
            account='ingdiba',
            tags=Tags(),
            category='',
            comment='',
        ),
        Transaction(
            date=date(2015, 6, 5),
            valuta=date(2015, 6, 5),
            type='payment',
            subject='WOOLWORTH GMBH FIL  1100*DE',
            reference=('EC 61264178 040615181722OC1  ',
                       '64AEE4884DF7559D40FE092777'),
            value=-20.56,
            saldo=4698.54,
            account='ingdiba',
            tags=Tags(),
            category='',
            comment='',
        ),
        Transaction(
            date=date(2015, 6, 6),
            valuta=date(2015, 6, 7),
            type='return',
            subject='AWS',
            reference='EMEA services',
            value=10.00,
            saldo=4708.54,
            account='ingdiba',
            tags=Tags(),
            category='',
            comment='',
        ),
        Transaction(
            date=date(2015, 6, 7),
            valuta=date(2015, 6, 7),
            type='payment auto',
            subject='Deutsche Wohnen AG',
            reference='Miete Charlottenburg',
            value=-210.00,
            saldo=4498.54,
            account='ingdiba',
            tags=Tags(),
            category='',
            comment='',
        ),
    ]
