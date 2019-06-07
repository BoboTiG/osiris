import pytest


@pytest.fixture(autouse=True)
def no_warnings(recwarn):
    yield

    warnings = []
    for w in recwarn:  # pragma: no cover
        warnings.append(f"{w.filename}:{w.lineno} {w.message}")

    assert warnings == []
