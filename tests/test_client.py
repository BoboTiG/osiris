import imaplib

import pytest

from osiris.client import Client
from osiris.exceptions import MissingAuth


def test_bad_credentials():
    with Client(pytest.server, pytest.user, password="foo") as client:
        with pytest.raises(imaplib.IMAP4.error):
            client.connect()


def test_missing_password():
    with Client(pytest.server, pytest.user) as client:
        with pytest.raises(MissingAuth):
            client.connect()


def test_password_ok():
    with Client(pytest.server, pytest.user, password=pytest.password) as client:
        client.connect()

    with Client(pytest.server, pytest.user, password=pytest.password) as client:
        client.connect(secure=False)
