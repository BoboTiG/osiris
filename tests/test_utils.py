from osiris.utils import parse


def test_empty_subject(load_email):
    data = load_email("issue-10")
    msg = parse(data)
    assert msg["subject"] == ""


def test_parse_email_header_attribute_error(load_email):
    """Ensure issue #11 is fixed on Python 3.7:

    File "/opt/osiris/osiris/utils.py", line 63, in <dictcomp>
      ret = {sanitize_header(k): v.lower() for k, v in msg.items()}
    AttributeError: 'Header' object has no attribute 'lower'
    """
    data = load_email("issue-11")
    assert parse(data)
