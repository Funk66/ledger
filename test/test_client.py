from pathlib import Path
from unittest.mock import patch, DEFAULT as Mock
from typing import List
from tempfile import TemporaryDirectory
from distutils.dir_util import copy_tree

from ledger.client import parse
from ledger.database import SQLite, Transaction
from ledger.categories import Categorizer


def test_parse(
    stored_transactions: List[Transaction], parsed_transactions: List[Transaction],
):
    test_dir = Path(__file__).parent
    with TemporaryDirectory() as tmp_dir:
        with patch.multiple("ledger.client", SQLite=Mock, Categorizer=Mock) as mocks:
            copy_tree(str(test_dir / "data"), tmp_dir)
            db = SQLite(Path(tmp_dir))
            mocks["SQLite"].return_value = db
            mocks["Categorizer"] = Categorizer(Path(tmp_dir) / "categories.yaml")
            parse(test_dir / "parsers/ingdiba.csv", "ingdiba", "ingdiba")
            all_transactions = stored_transactions + parsed_transactions[2:]
            assert db.transactions.get_many() == all_transactions
            assert sum(1 for line in open(Path(tmp_dir) / "transactions.csv")) == len(
                all_transactions
            )
