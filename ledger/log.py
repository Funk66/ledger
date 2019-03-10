from logging import getLogger


# TODO: add color to logs


def debug(msg: str) -> None:
    log.debug(msg)


def info(msg: str) -> None:
    log.info(msg)


log = getLogger('ledger')
