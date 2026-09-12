"""Small SHA-256 helpers for reproducibility and artifact checks."""

import hashlib
from pathlib import Path


def sha256_file(file_path: Path) -> str:
    """Calculate a file's SHA-256 hash without loading it all into memory."""
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    """Return whether a file matches an expected SHA-256 hash."""
    return sha256_file(Path(file_path)) == expected_hash
