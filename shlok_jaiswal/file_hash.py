# file_hash.py  (Owner: Shlok Jaiswal)
# End-to-end integrity check: if SHA-256 of the sent file equals SHA-256 of the
# received file, the two files are identical.

import hashlib


def calculate_file_hash(filepath, chunk_size=4096):
    """Compute SHA-256 hash of a file by reading it in chunks.

    Args:
        filepath: path to the file to hash
        chunk_size: bytes read per iteration (default 4096)

    Returns:
        hex digest string of the SHA-256 hash
    """
    digest = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def files_match(file1, file2):
    """Return True if two files have identical SHA-256 hashes."""
    return calculate_file_hash(file1) == calculate_file_hash(file2)