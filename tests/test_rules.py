from osiris.rules import Rules

from .constants import FILE, USER


def test_get_rules():
    rules = Rules(file=FILE)
    rules_mika = rules.get(USER)
    good = {
        "github_cherry_picked": ('"cherry picked from commit" in message', ["delete"]),
        "mms": (f'subject.startswith("mms") and "{USER}" in addr_from', ["move:Perso"]),
    }
    assert rules_mika == good
