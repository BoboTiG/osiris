import logging
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
    file: Union[Path, str] = field(repr=False)
    fiorce: bool = False
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

    def judge(self) -> None:
        for client in self.clients:
            with client:
                client.connect()
                emails = client.emails(force=self.fiorce)
                if not emails:
                    log.debug(f"[{client.user}] No emails")
                    continue

                rules = self.rules.get(client.user)
                for name, (criterias, actions) in rules.items():
                    for uid, data in list(emails.items()):
                        # Check if the email meets critierias of that rule
                        if not eval(criterias, None, data):
                            continue

                        log.debug(f"[{client.user}] Rule {name!r} matches email {uid}")

                        # Apply actions
                        for action in actions:
                            folder = None
                            if ":" in action:
                                action, folder = action.split(":", 1)
                            try:
                                getattr(client, f"action_{action}")(uid, folder=folder)
                            except AttributeError as exc:
                                log.error(exc)
                                raise InvalidAction(action)
                            except:  # noqa
                                log.exception(
                                    f"Error handling action {action!r} on email {uid}"
                                )

                        emails.pop(uid, None)

    @staticmethod
    def password_envar(user: str) -> str:
        envar = f"{user.upper()}_PWD"
        for char in {"@", ".", "+", "-"}:
            envar = envar.replace(char, "_")
        return envar
