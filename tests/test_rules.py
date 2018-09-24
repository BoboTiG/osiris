import pytest

from osiris.rules import Rules


def test_get_rules():
    rules = Rules(file=pytest.file)
    rules_mika = rules.get("mickael@jmsinfo.co")
    good = {
        "mms": (
            'subject.startswith("mms") and "mickael@jmsinfo.co" in addr_from',
            "move:Perso",
        )
    }
    assert rules_mika == good
