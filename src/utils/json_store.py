"""UTF-8 JSON I/O. Callers own schemas, defaults and error reporting."""

from contextlib import suppress
import json
import os
from pathlib import Path
import tempfile


def read_json(path):
    with open(path, 'r', encoding='utf-8') as stream:
        return json.load(stream)


def write_json_atomic(path, value) -> None:
    """Replace only after a complete, flushed write in the same directory."""
    destination = Path(path).absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', dir=destination.parent,
            prefix=f'.{destination.name}.', suffix='.tmp', delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            # Do not hide the write/replace failure if cleanup itself fails.
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
