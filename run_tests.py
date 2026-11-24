"""Tiny test runner for machines without pytest:  python run_tests.py   (with pytest installed: python -m pytest)"""
import importlib, pkgutil, sys, traceback, types

try:
    import pytest  # noqa
except ImportError:                                        # minimal stand-in for pytest.raises
    import re
    class _Raises:
        def __init__(self, exc, match=None): self.exc, self.match = exc, match
        def __enter__(self): return self
        def __exit__(self, t, v, tb):
            assert t and issubclass(t, self.exc), "did not raise"
            assert not self.match or re.search(self.match, str(v)); return True
    sys.modules["pytest"] = types.SimpleNamespace(raises=lambda e, match=None: _Raises(e, match))

import ai_engine.tests as pkg
ok = bad = 0
for m in pkgutil.iter_modules(pkg.__path__):
    if not m.name.startswith("test_"):
        continue
    mod = importlib.import_module(f"ai_engine.tests.{m.name}")
    for name in dir(mod):
        if name.startswith("test_"):
            try:
                getattr(mod, name)(); ok += 1
            except Exception:
                bad += 1; print("FAIL", m.name, name); traceback.print_exc()
print(f"{ok} passed, {bad} failed")
sys.exit(1 if bad else 0)
