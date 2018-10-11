import imaplib
import logging
import sqlite3
from collections import defaultdict
from datetime import datetime
from os import getenv
from pathlib import Path
from typing import Any, List, Union

from dataclasses import dataclass, field

from .client import Client
from .exceptions import InvalidAction, MissingEnvPassword
from .rules import Rules


log = logging.getLogger(__name__)


@dataclass
class Osiris:
    """The judge: it will instanciante clients and rules to perform actions."""

    file: Union[Path, str] = field(repr=False)
    full: bool = False
    rules: Rules = None
    clients: List[Client] = field(default_factory=list)

    def __enter__(self) -> "Osiris":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        log.debug(f"Stopping {type(self).__name__} ...")
        # Close all clients, preventing socket leaks
        for client in self.clients:
            client.close()

    def __post_init__(self):
        log.debug(f"Starting {type(self).__name__} ...")
        self.rules: Rules = Rules(self.file)
        for user in self.rules.parser.sections():
            if user.endswith(":rules"):
                continue

            server = self.rules.server(user)
            password = getenv(self.password_envar(user))
            if not password:
                raise MissingEnvPassword(user, self.password_envar(user))

            client = Client(server=server, user=user, password=password)
            self.clients.append(client)

        self.db = sqlite3.connect("statistics.db")
        c = self.db.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS osiris("
            "       id     INTEGER PRIMARY KEY,"
            "       run_at DATE,"
            "       user   TEXT,"
            "       action TEXT,"
            "       count  INT"
            ")"
        )

    def judge(self) -> None:
        """Judgement day: apply actions on emails based on rules."""

        run_at = datetime.now().replace(second=0, microsecond=0)

        for client in self.clients:
            with client:
                client.connect()
                emails = client.emails(full=self.full)
                if not emails:
                    log.debug(f"[{client.user}] No emails")
                    continue

                todo = defaultdict(list)
                rules = self.rules.get(client.user)
                for name, (criterias, actions) in rules.items():
                    for uid, data in list(emails.items()):
                        # Check if the email meets critierias of that rule
                        if not eval(criterias, None, data):
                            continue

                        log.debug(
                            f"[{client.user}] Rule {name!r} applies for {data} (uid={int(uid)})"
                        )

                        # Regroup actions for efficiency
                        for action in actions:
                            todo[action].append(uid)

                        emails.pop(uid, None)

                # Batch mode (deelte several UIDs, ... )
                for action, uids in todo.items():
                    if getenv("DEBUG"):
                        log.debug(f"Applying {action!r} action to {uids} UIDs")
                        continue

                    if ":" in action:
                        action, folder = action.split(":", 1)
                    else:
                        folder = None

                    try:
                        getattr(client, f"action_{action}")(uids, folder=folder)
                    except AttributeError as exc:
                        log.error(exc)
                        raise InvalidAction(action)
                    except imaplib.IMAP4.abort:
                        log.error("Error happened, will retry later")

                if client.stats:
                    self.save_stats(run_at, client)

    @staticmethod
    def password_envar(user: str) -> str:
        """Format the required envar name for a given user."""
        envar = f"{user.upper()}_PWD"
        for char in {"@", ".", "+", "-"}:
            envar = envar.replace(char, "_")
        return envar

    def save_stats(self, run_at: datetime, client: Client) -> None:
        """Save client statistics in the local dataase."""
        user = client.user
        c = self.db.cursor()
        sql = "INSERT INTO osiris(run_at, user, action, count) VALUES(?,?,?,?)"
        for action, count in client.stats.items():
            c.execute(sql, (run_at, user, action, count))
        self.db.commit()
