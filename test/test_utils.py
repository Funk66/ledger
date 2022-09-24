from datetime import date

from ledger.utils import isodate


def test_isodate():
    assert date(2020, 2, 20) == isodate("2020-02-20")
