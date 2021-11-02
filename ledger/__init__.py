from logging import getLogger
from pathlib import Path


__author__ = "Guillermo Guirao Aguilar"
__email__ = "contact@guillermoguiraoaguilar.com"
__license__ = "MIT"
__version__ = "0.2.1"


log = getLogger('ledger')
home = Path(Path.home() / '.config' / 'ledger')
home.mkdir(parents=True, exist_ok=True)
