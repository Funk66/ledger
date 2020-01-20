from pathlib import Path

from ledger.database import Client


def test_load():
    client = Client()
    client.load(Path(__file__).parent.absolute() / 'data/transactions.csv')
    data = client.cursor.execute('SELECT * FROM transactions').fetchall()
    assert len(data) == 5
    assert data[0] == ("2015-06-02", "2015-06-02", "payment",
                       "TESCO, UK", "017278916389756839287389260", -9.6,
                       4776.06, "groceries:food", "", "ingdiba")
    data = client.cursor.execute('SELECT * FROM tags').fetchall()
    assert len(data) == 3
    assert data[0] == ("holidays", 1)
