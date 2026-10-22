# file_hash.py  (Owner: Shlok Jaiswal)
# End-to-end integrity check: if SHA-256 of the sent file equals SHA-256 of the
# received file, the two files are identical.

import hashlib


def calculate_file_hash(filename):
    digest = hashlib.sha256()                    # create an empty SHA-256 calculator
    with open(filename, "rb") as f:              # open the file in binary mode
        while True:
            block = f.read(4096)                 # read 4 KB at a time
            if not block:                        # empty read = end of file
                break
            digest.update(block)                 # feed the block to the calculator
    return digest.hexdigest()                    # final hash as a hex string


def files_match(first, second):
    return calculate_file_hash(first) == calculate_file_hash(second)
