from pathlib import Path


__author__ = "Guillermo Guirao Aguilar"
__email__ = "contact@guillermoguiraoaguilar.com"
__license__ = "MIT"
__version__ = "0.1.0"


home = Path(Path.home() / '.config' / 'ledger')
home.mkdir(parents=True, exist_ok=True)
