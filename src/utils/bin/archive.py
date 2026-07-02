"""Archive extraction helpers for managed binaries."""

import shutil
import zipfile
from typing import Iterable


def extract_zip_member_ending_with(
    zip_path: str,
    dest_path: str,
    suffixes: Iterable[str],
) -> bool:
    """Extract the first ZIP member whose filename ends with one of suffixes."""
    suffix_tuple = tuple(suffixes)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for file_info in zip_ref.filelist:
            if not file_info.filename.endswith(suffix_tuple):
                continue
            with zip_ref.open(file_info) as source:
                with open(dest_path, "wb") as target:
                    shutil.copyfileobj(source, target)
            return True
    return False