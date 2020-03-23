from osiris.osiris import Osiris

from .constants import FILE


def test_instanciation():
    with Osiris(file=FILE) as osiris:
        assert repr(osiris)


def test_1_client():
    with Osiris(file=FILE) as osiris:
        osiris.judge()


def test_1_client_async():
    with Osiris(file=FILE) as osiris:
        osiris.judge_async()
