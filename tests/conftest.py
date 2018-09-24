from os import getenv
from pathlib import Path

import pytest


def pytest_namespace():
    """
    This namespace is used to store global variables for
    tests. They can be accessed with `pytest.<variable_name>`
    e.g. `pytest.user`
    """
    return {
        "server": "mail.gandi.net",
        "user": "mickael@jmsinfo.co",
        "password": getenv("MICKAEL_JMSINFO_CO_PWD"),
        "file": Path(__file__).parent / "data" / "rules.ini",
    }


@pytest.fixture(autouse=True)
def no_warnings(recwarn):
    yield
    warnings = []
    for warning in recwarn:  # pragma: no cover
        message = str(warning.message)
        # ImportWarning: Not importing directory '...' missing __init__(.py)
        if not (
            isinstance(warning.message, ImportWarning)
            and message.startswith("Not importing directory ")
            and " missing __init__" in message
        ):
            warnings.append(f"{warning.filename}:{warning.lineno} {message}")
    assert not warnings
