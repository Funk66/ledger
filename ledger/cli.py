from . import csv, sql, yml, log


def parse(store: sql.Store, filename: str) -> None:
    log.info(f'Reading {filename}')
    hashes = [hsh for row in store.transactions.select('hash') for hsh in row]
    count = store.transactions.count()
    transactions = [transaction.dict() for transaction in csv.ingdiba(filename)
                    if transaction.hash not in hashes]
    store.transactions.insert(transactions)
    for category in yml.categories():
        category.condition = f'rowid > {count} AND ({category.condition})'
        store.update(category)
