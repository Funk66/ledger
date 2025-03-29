from logging import getLogger
from pathlib import Path

__version__ = "0.2.1"
log = getLogger("ledger")
home = Path(Path.home() / ".config" / "ledger")
home.mkdir(parents=True, exist_ok=True)
