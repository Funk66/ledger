from argparse import ArgumentParser
from pathlib import Path
from logging import DEBUG, INFO, basicConfig
from IPython import start_ipython  # type: ignore
from traitlets.config import Config  # type: ignore


def run():
    parser = ArgumentParser()
    parser.add_argument('-v', dest='verbose')
    subparser = parser.add_subparsers(dest='command')
    parse = subparser.add_parser('parse', help='Parse a bank extract')
    parse.add_argument('filename', help='CSV file to parse')
    parse.add_argument('-b', '--bank', help='CSV file format')
    arguments = parser.parse_args()

    basicConfig(level=DEBUG if arguments.verbose else INFO)
    if arguments.command == 'parse':
        print('parse')
    else:
        environment = Path(__file__).parent.absolute() / 'shell.py'
        config = Config()
        shell_config = config.InteractiveShell
        shell_config.autoindent = True
        shell_config.colors = 'Neutral'

        app_config = config.InteractiveShellApp
        app_config.exec_lines = [
            # https://ipython.readthedocs.io/en/stable/config/extensions/autoreload.html
            "%load_ext autoreload",
            "%autoreload 2",
            "%load_ext memory_profiler",

            # automatically prints the execution time of statements
            "%load_ext autotime",

            # executes the shell/shell-init.py script
            f"%run {environment}"
        ]

        start_ipython(config=config)
