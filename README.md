# Osiris

Osiris is a simple Python module to sort messages in your email box.

This is Python 3.6+, PEP8 compliant, multi-platform and easy to use.

## How?

For each and every account, define the appropriate environment variable to set its password.
For instance, let's define the password for the account `contact@example.com`:

    # Unix
    export CONTACT_EXAMPLE_COM_PWD="my_password"

    # Windows
    set CONTACT_EXAMPLE_COM_PWD=my_password

## Configuration File

See `rules.ini` for examples.

## Available Data

All data is converted to *lowercase string* to ease filtering.
Note that emails are not marked as read, Osiris will do a `BODY.PEEK` to not alter emails state.

- `addr_from`: The full FROM header value (can be a simple email address or something like "John Doe" <john@doe.com>).
- `addr_to`: The full TO header value (can be a simple email address or something like "John Doe" <john@doe.com>)..
- `message`: The email message.
- `subject`: The email subject.

## Automating

Cron job line:

    python -m osiris --config-file /path/to/rules.ini [--debug] [--full]

## Statistics

A simple SQLite3 database named `statistics.db` will be filled with actions done for each and every user.

## Developing

    python -m pip install pre-commit
    pre-commit install

## Testing

    python -m pip install tox
    tox
