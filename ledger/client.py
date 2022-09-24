from argparse import ArgumentParser
from logging import DEBUG, INFO, basicConfig, getLogger
from pathlib import Path
from sys import stdout

from colorful import bold, green, grey, red, yellow  # type: ignore
from IPython import start_ipython  # type: ignore
from traitlets.config import Config  # type: ignore

from .categories import Categorizer
from .database import SQLite
from .parsers import parsers


def parse(filename: Path, bank: str, account: str = "") -> None:
    account = account or bank
    transactions = parsers[bank](filename, account)
    db = SQLite()
    db.load()
    last_transaction = db.transactions.get_one(
        account=account, order="rowid", direction="DESC"
    )
    if last_transaction:
        new_transactions = transactions[
            transactions.index(last_transaction) + 1 :
        ]
        assert len(new_transactions) < len(
            transactions
        ), "No matching transaction found"
    else:
        new_transactions = transactions
    log.info(f"Parsed {len(new_transactions)} new transactions")
    categorizer = Categorizer()
    categorizer(new_transactions)
    db.transactions.add_many(new_transactions)
    db.transactions.check(account)
    db.save()


def categorize() -> None:
    db = SQLite()
    db.load()
    categories = db.transactions.distinct("category")
    transactions = db.transactions.get_many(
        category="", order="date", direction="DESC"
    )
    print(f"{len(transactions)} transactions uncategorized")
    while transactions:
        transaction = transactions.pop()
        print(
            f"{green(transaction.date)} {bold(transaction.subject)} "
            f"{grey(transaction.reference)} {yellow(transaction.value)}"
        )
        try:
            substr = input(">>> ").strip()
        except EOFError:
            if input("Save changes? ") == "y":
                db.save()
            return
        if substr in categories:
            category = substr
        elif matches := [
            category for category in categories if substr in category
        ]:
            if len(matches) == 1:
                category = matches[0]
            else:
                print(red("Matches: ") + ", ".join(matches))
                transactions.append(transaction)
                continue
        else:
            if input("New category? ") != "y":
                transactions.append(transaction)
                continue
            category = substr
            categories.add(category)
        stdout.write(f"\x1b[1A\x1b[2K{category}\n")
        db.transactions.categorize(transaction, category)
    db.save()


def sql():
    db = SQLite()
    db.load()
    db.prompt()


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
    parse_command.add_argument(
        "-a", "--account", help="Account to add transactions to"
    )
    parse_command.add_argument(
        "-b", "--bank", choices=parsers.keys(), help="CSV file format"
    )
    sql_command = subparser.add_parser("sql")
    sql_subparser = sql_command.add_subparsers(dest="subcommand")
    sql_export_command = sql_subparser.add_parser("export")
    sql_export_command.add_argument(
        "filename", type=Path, help="Output filename"
    )
    subparser.add_parser("categorize")
    arguments = parser.parse_args()

    if arguments.command == "parse":
        basicConfig(
            level=DEBUG if arguments.verbose else INFO, format="%(message)s"
        )
        parse(
            arguments.filename,
            arguments.bank,
            arguments.account or arguments.bank,
        )
    elif arguments.command == "sql":
        sql()
    elif arguments.command == "categorize":
        categorize()
    else:
        shell()


log = getLogger(__name__)
