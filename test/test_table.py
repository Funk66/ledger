from ledger.tables import DATE, FLOAT, TEXT, Column, Table


class Users(Table):
    columns = [
        Column('name', TEXT, null=False, primary=True),
        Column('birthday', DATE, null=False),
    ]


class Ledger(Table):
    columns = [
        Column('credit', FLOAT),
        Column('user', TEXT, unique=True, reference=Users)
    ]


def test_table():
    assert Users.create() == ('CREATE TABLE users ('
                              '"name" TEXT NOT NULL, '
                              '"birthday" DATE NOT NULL, '
                              'PRIMARY KEY ("name"))')
    assert Ledger.create() == ('CREATE TABLE ledger ('
                               '"credit" FLOAT, '
                               '"user" TEXT UNIQUE, '
                               'FOREIGN KEY ("user") '
                               'REFERENCES users("rowid"))')
