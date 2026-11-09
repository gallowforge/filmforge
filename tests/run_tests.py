#!/usr/bin/env python3
"""Run every test without pytest: python3 tests/run_tests.py   (pytest also collects the same files)."""
import importlib
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    mods = sorted(f[:-3] for f in os.listdir(HERE) if f.startswith("test_") and f.endswith(".py"))
    passed, failed = 0, []
    t0 = time.time()
    for name in mods:
        mod = importlib.import_module(name)
        for fn in sorted(k for k in dir(mod) if k.startswith("test_")):
            try:
                getattr(mod, fn)()
                passed += 1
                print(f"ok    {name}.{fn}")
            except Exception:
                failed.append(f"{name}.{fn}")
                print(f"FAIL  {name}.{fn}")
                traceback.print_exc()
    print(f"\n{passed} passed, {len(failed)} failed in {time.time() - t0:.1f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
