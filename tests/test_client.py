import imaplib

import pytest

from osiris.client import Client
from osiris.exceptions import MissingAuth

from .constants import PASSWORD, SERVER, USER


def test_bad_credentials():
    with Client(SERVER, USER, password="foo") as client:
        with pytest.raises(imaplib.IMAP4.error):
            client.connect()


def test_missing_password():
    with Client(SERVER, USER) as client:
        with pytest.raises(MissingAuth):
            client.connect()


def test_password_ok():
    with Client(SERVER, USER, password=PASSWORD) as client:
        client.connect()

    with Client(SERVER, USER, password=PASSWORD) as client:
        client.connect(secure=False)
