#!/usr/bin/env python3
"""Launch the local Legaia Trace editor."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sdk.server import main

if __name__ == "__main__":
    raise SystemExit(main())
