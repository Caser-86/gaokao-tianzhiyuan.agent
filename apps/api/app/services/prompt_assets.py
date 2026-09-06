from __future__ import annotations

from hashlib import sha256
from pathlib import Path


def hash_prompt_file(path: str | Path) -> str | None:
    """Return the SHA-256 identity of a Prompt asset, when it is readable."""

    normalized = str(path).strip()
    if not normalized:
        return None

    try:
        return sha256(Path(normalized).read_bytes()).hexdigest()
    except OSError:
        return None
