#!/usr/bin/env python3
"""Dependency-free test runner.

Discovers ``test_*`` functions in ``tests/test_*.py`` and runs them, reporting
pass/fail counts and the first traceback per failure. Equivalent to running
pytest over the same suite; provided so that a machine without pytest can still
verify the invariants before trusting a result.

Warnings are turned into errors, matching the pytest configuration.
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    sys.path.insert(0, str(SRC))
    sys.path.insert(0, str(HERE))
    warnings.simplefilter("error")
    passed, failures = 0, []
    for path in sorted(HERE.glob("test_*.py")):
        module = load(path)
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            fn = getattr(module, name)
            if not callable(fn):
                continue
            try:
                fn()
                passed += 1
            except Exception:  # noqa: BLE001
                failures.append((f"{path.name}::{name}", traceback.format_exc()))
    for name, tb in failures:
        print(f"\nFAILED {name}\n{tb}")
    total = passed + len(failures)
    print(f"\n{passed}/{total} tests passed")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
