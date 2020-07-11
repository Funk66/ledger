from argparse import ArgumentParser
from logging import DEBUG, INFO, basicConfig
from pathlib import Path

from IPython import start_ipython  # type: ignore
from traitlets.config import Config  # type: ignore

from .categories import Categorizer
from .database import Client
from .parsers import parsers
from .store import Store


def parse(filename: str, bank: str):
    transactions = parsers[bank](filename)
    categorizer = Categorizer()
    categorizer(transactions)
    store = Store()
    store.extend(transactions)
    store.check()
    store.save()


def sql():
    client = Client()
    client.load()
    client.prompt()


def shell():
    environment = Path(__file__).parent.absolute() / 'shell.py'
    config = Config()
    shell_config = config.InteractiveShell
    shell_config.autoindent = True
    shell_config.colors = 'Neutral'

    app_config = config.InteractiveShellApp
    app_config.exec_lines = [
        "%load_ext autoreload", "%autoreload 2", f"%run {environment}"
    ]

    start_ipython(config=config)


def run():
    parser = ArgumentParser()
    parser.add_argument('-v', dest='verbose')
    subparser = parser.add_subparsers(dest='command')
    parse_command = subparser.add_parser('parse', help='Parse a bank extract')
    parse_command.add_argument('filename', help='CSV file to parse')
    parse_command.add_argument('-b', '--bank', help='CSV file format')
    sql_command = subparser.add_parser('sql')
    sql_subparser = sql_command.add_subparsers(dest='subcommand')
    sql_export_command = sql_subparser.add_parser('export')
    sql_export_command.add_argument('filename')
    arguments = parser.parse_args()

    if arguments.command == 'parse':
        basicConfig(level=DEBUG if arguments.verbose else INFO)
        parse(arguments.filename, arguments.bank)
    elif arguments.command == 'sql':
        sql()
    else:
        shell()
