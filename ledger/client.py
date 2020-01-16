from argparse import ArgumentParser
from logging import DEBUG, INFO, basicConfig
from pathlib import Path

from IPython import start_ipython  # type: ignore
from traitlets.config import Config  # type: ignore

from .categories import Categorizer
from .store import Store
from .parsers import parsers


def parse(filename: str, bank: str):
    transactions = parsers[bank](filename)
    categorizer = Categorizer()
    categorizer(transactions)
    store = Store()
    store.extend(transactions)
    store.check()
    store.save()


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
    arguments = parser.parse_args()

    basicConfig(level=DEBUG if arguments.verbose else INFO)
    if arguments.command == 'parse':
        parse(arguments.filename, arguments.bank)
    else:
        shell()
