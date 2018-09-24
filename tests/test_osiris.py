import pytest

from osiris.osiris import Osiris


def test_instanciation():
    with Osiris(file=pytest.file) as osiris:
        assert repr(osiris)


def test_1_client():
    with Osiris(file=pytest.file) as osiris:
        osiris.judge()
