"""Shared test environment configured before application imports."""

from __future__ import annotations

import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEST_APPDATA = ROOT / "tests" / ".appdata"

TEST_APPDATA.mkdir(exist_ok=True)
os.environ["APPDATA"] = str(TEST_APPDATA)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
