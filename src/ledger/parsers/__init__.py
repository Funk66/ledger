from . import d1822, ingdiba, revolut

parsers = {
    "ingdiba": ingdiba.read,
    "1822direkt": d1822.read,
    "revolut": revolut.read,
}
