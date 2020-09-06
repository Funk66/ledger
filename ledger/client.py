from argparse import ArgumentParser
from logging import DEBUG, INFO, basicConfig, getLogger
from pathlib import Path

from IPython import start_ipython  # type: ignore
from traitlets.config import Config  # type: ignore

from .categories import Categorizer
from .database import SQLite
from .parsers import parsers


def parse(filename: Path, bank: str, account: str = None) -> None:
    account = account or bank
    transactions = parsers[bank](filename, account)
    db = SQLite()
    db.load()
    last_transaction = db.transactions.get_one(
        account=account, order="rowid", direction="DESC"
    )
    assert last_transaction, f"No last transaction found for {account}"
    new_transactions = transactions[transactions.index(last_transaction)+1:]
    assert len(new_transactions) < len(transactions), "No matching transaction found"
    log.info(f"Parsed {len(new_transactions)} new transactions")
    categorizer = Categorizer()
    categorizer(new_transactions)
    db.transactions.add_many(new_transactions)
    db.transactions.check(account)
    db.save()


def sql():
    client = SQLite()
    client.load()
    client.prompt()


def shell():
    environment = Path(__file__).parent.absolute() / "shell.py"
    config = Config()
    shell_config = config.InteractiveShell
    shell_config.autoindent = True
    shell_config.colors = "Neutral"

    app_config = config.InteractiveShellApp
    app_config.exec_lines = [
        "%load_ext autoreload",
        "%autoreload 2",
        f"%run {environment}",
    ]

    start_ipython(config=config)


def run():
    parser = ArgumentParser()
    parser.add_argument("-v", dest="verbose")
    subparser = parser.add_subparsers(dest="command")
    parse_command = subparser.add_parser("parse", help="Parse a bank extract")
    parse_command.add_argument("filename", type=Path, help="CSV file to parse")
    parse_command.add_argument("-a", "--account", help="Account to add transactions to")
    parse_command.add_argument(
        "-b", "--bank", choice=["ingdiba"], help="CSV file format"
    )
    sql_command = subparser.add_parser("sql")
    sql_subparser = sql_command.add_subparsers(dest="subcommand")
    sql_export_command = sql_subparser.add_parser("export")
    sql_export_command.add_argument("filename")
    arguments = parser.parse_args()

    if arguments.command == "parse":
        basicConfig(level=DEBUG if arguments.verbose else INFO, format="%(message)s")
        parse(arguments.filename, arguments.bank, arguments.account or arguments.bank)
    elif arguments.command == "sql":
        sql()
    else:
        shell()


log = getLogger(__name__)
