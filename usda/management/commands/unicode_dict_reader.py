import csv, codecs

"""
Adapted from the csv examples:

http://docs.python.org/2/library/csv.html#csv-examples
"""

class UnicodeDictReader:
    """
    A UnicodeDictReader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding, decoding each field entry to
    unicode.
    """
    def __init__(self, f, dialect=csv.excel, fieldnames=None, restkey=None, restval=None, encoding="utf-8", *args, **kwds):
        self._encoding = encoding
        self._reader = csv.DictReader(f, dialect=dialect, fieldnames=fieldnames, restkey=restkey, restval=restval, *args, **kwds)

    def next(self):
        row = self._reader.next()
        return dict(zip(row.keys(), [codecs.decode(s, self._encoding) for s in row.values()]))

    def __iter__(self):
        return self