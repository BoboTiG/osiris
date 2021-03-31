from osiris.utils import parse


def test_empty_subject(load_email):
    data = load_email("issue-10")
    msg = parse(data)
    assert msg
