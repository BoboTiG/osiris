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

- `addr_cc`: The full `Cc` header value.
- `addr_from`: The full `From` header value.
- `addr_to`: The full `To` header value.
- `delivered_to`: The full `Delivered-To` header value.
- `message`: The email body.
- `msgid`: The email `Message-ID`.
- `reply_to`: The full `Reply-To` header value.
- `subject`: The email subject.
- `ua`: The user-agent used to send the email.

Also all email headers are available under their "sanitized" form.
For instance, if you have a Gandi.net account and would like to filter out emails on the [X-GND-Status]() headers, you would use such rule:

    gandi_commercial =
        x_gnd_status == "mce"
        delete

The original header can be found in the lowercase form, and underscores are replaced with dashes: `X-GND-Status` -> `x_gnd_status`.

Each field containing email ID can have the following format:

- `john@doe.com`
- `John Doe <john@doe.com>`
- `John Doe <john@doe.com>, Jane Doe <jane@doe.com>, ... `
- `John Doe <john@doe.com>, jane@doe.com, ... `

## Automating

Cron job line:

    python -m osiris --config-file /path/to/rules.ini [--debug] [--full]

## Statistics

A simple SQLite3 database named `statistics.db` will be filled with actions done for each and every user.
There is also a shell script that can display the number of operations day by day:

    bash stats.sh [[LINES] [--all]]
    2018-10-08|delete|225
    2018-10-08|move|3
    2018-10-07|delete|14
    2018-10-07|move|7
    2018-10-06|delete|68
    2018-10-06|move|11
    2018-10-05|delete|526
    2018-10-05|move|17
    2018-10-04|delete|423
    2018-10-04|move|9
    2018-10-03|delete|419
    2018-10-03|move|8
    2018-10-02|delete|489
    2018-10-02|move|14
    2018-10-01|delete|554
    2018-10-01|move|7

    bash stats.sh --all
    delete|8156
    move|22

## Developing

    python -m pip install pre-commit
    pre-commit install

## Testing

    python -m pip install tox
    tox

You can set the `DEBUG` envar to `1` to print actions done instead of actually doing actions.
