from pathlib import Path
from argparse import ArgumentParser
from logging import DEBUG, INFO, basicConfig, getLogger
from csv import reader, writer
from typing import List, Any


ROW = List[Any]
ROWS = List[ROW]
log = getLogger(__name__)


class Version(tuple):
    def __new__(cls, version: str):
        return tuple.__new__(Version, [int(n) for n in version.split(".")])

    def __repr__(self) -> str:
        return ".".join((str(n) for n in self))


def read(path: Path) -> ROWS:
    log.info(f"Reading table from {path}")
    with open(path, encoding="latin-1") as csvfile:
        rows = list(reader(csvfile))
    return rows


def write(rows: ROWS, path: Path) -> None:
    log.info(f"Writing table to {path}")
    with open(path, "w", encoding="latin-1") as output:
        csvfile = writer(output)
        csvfile.writerows(rows)


def add_time_column(rows):
    log.info("- Adding 'time' column to table")
    for row in rows:
        row.insert(8, "")
    return rows


versions = [
    (Version("0.2.0"), add_time_column),
]


if __name__ == "__main__":
    default_path = Path.home() / ".config/ledger/transactions.csv"
    parser = ArgumentParser()
    parser.add_argument("-f", "--frm", help="Initial version")
    parser.add_argument(
        "-t", "--to", default=str(versions[-1][0]), help="Final version"
    )
    parser.add_argument(
        "-i", "--input", type=Path, default=default_path, help="Path to the input file"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=default_path,
        help="Path to the output file",
    )
    parser.add_argument("-v", dest="verbose")
    arguments = parser.parse_args()

    basicConfig(level=DEBUG if arguments.verbose else INFO, format="%(message)s")

    version_path = arguments.output.parent / "version"
    if version_path.exists():
        with open(version_path) as version_file:
            initial_version = Version(version_file.readline().strip())
        if arguments.frm and arguments.frm != initial_version:
            raise ValueError(f"Version mismatch: {arguments.frm} != {initial_version}")
        arguments.frm = str(initial_version)

    rows = read(arguments.input)
    last_version = ""
    for version, converter in versions:
        if version >= Version(arguments.frm) and version <= Version(arguments.to):
            log.info(f"Converting to v{version}")
            rows = converter(rows)
            last_version = str(version)
    write(rows, arguments.output)

    if last_version and version_path.exists():
        with open(version_path, "w") as version_file:
            version_file.write(last_version)
