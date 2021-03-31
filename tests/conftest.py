from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def no_warnings(recwarn):
    yield

    warnings = []
    for w in recwarn:  # pragma: no cover
        warnings.append(f"{w.filename}:{w.lineno} {w.message}")

    assert warnings == []


@pytest.fixture
def load_email():
    def inner(name: str) -> bytes:
        file = Path() / "tests" / "data" / f"{name}.email"
        return file.read_bytes()

    return inner
