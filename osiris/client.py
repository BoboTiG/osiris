import imaplib
import logging
import re
from collections import defaultdict
from contextlib import suppress
from email import message_from_bytes
from email.header import decode_header
from email.utils import getaddresses
from typing import Any, Dict, List, Tuple, Union

from dataclasses import dataclass, field

from .exceptions import MissingAuth


UIDs = Union[bytes, List[bytes]]
log = logging.getLogger(__name__)


@dataclass
class Client:
    """Informations of a user that will be judged soon."""

    server: str
    user: str
    conn: imaplib.IMAP4 = field(default=None, init=False, repr=False)
    password: str = field(default=None, repr=False)
    stats: Dict[str, int] = field(default_factory=dict, repr=False)
    # BODY.PEEK to not alter the message state
    fetch_pattern: str = field(default="(BODY.PEEK[])", repr=False)

    def __post_init__(self):
        self.stats = defaultdict(int)

    def __enter__(self) -> "Client":
        log.debug(f"Loading {type(self).__name__} ...")
        return self

    def __exit__(self, *exc_info: Any) -> None:
        log.debug(f"Stopping {type(self).__name__}: {dict(self.stats.items())} ...")
        self.close()

    def close(self):
        """Ensure to close everything correctly."""
        if getattr(self, "conn", None):
            if self.conn.state == "SELECTED":
                self.conn.logout()
            with suppress(OSError):
                self.conn.shutdown()
            del self.conn

    def connect(self, secure: bool = True, *args: Any, **kwargs: Any) -> None:
        """args and kwargs are optional additional parameters forwarded
        to IMAP.connect()."""

        if not self.password:
            raise MissingAuth()

        imap = imaplib.IMAP4_SSL if secure else imaplib.IMAP4
        self.conn = imap(self.server, *args, **kwargs)
        self.conn.login(self.user, self.password)
        # self.conn.enable("UTF8=ACCEPT")
        self.conn.select()
        log.debug(f"Added {self}")

    @staticmethod
    def dec(header):
        if isinstance(header, bytes):
            header = header.decode("latin-1")

        val, encoding = decode_header(header)[0]
        if isinstance(val, bytes):
            try:
                val = val.decode(encoding or "latin-1")
            except UnicodeDecodeError:
                val = val.decode("latin-1")
        return val

    def emails(self, full: bool = False) -> List[str]:
        """Retreive emails."""

        search = "(ALL)" if full else "(NOT DELETED)"
        typ, dat = self.conn.uid("search", None, search)
        if typ != "OK":
            raise dat[0]

        uids = dat[0].split()
        if not uids:
            return {}

        typ, dat = self.conn.uid("fetch", b",".join(uids), self.fetch_pattern)
        if typ != "OK":
            raise dat[0]

        ret = {}
        # reg_from = re.compile(b"<(.+)>")
        reg_uid = re.compile(br"UID (\d+)")

        for raw_data in dat:
            if len(raw_data) == 1:  # Invalid chunk?!
                continue

            command, data = raw_data
            uid = reg_uid.findall(command)[0]
            ret[uid] = self.get_body(data)

        return ret

    def get_body(self, data):
        ret = {}
        msg = message_from_bytes(data)
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get("Content-Disposition", ""))

                # Skip any text/plain attachments
                if ctype == "text/plain" and "attachment" not in cdispo:
                    body = part.get_payload(decode=True)
                    break
        else:
            # Not multipart - i.e. plain text, no attachments, keeping fingers crossed
            body = msg.get_payload(decode=True)

        ret["addr_from"] = ", ".join(
            (
                f"{self.dec(person)} <{addr}>" if person else addr
                for person, addr in getaddresses(msg.get_all("From"))
            )
        )
        ret["addr_to"] = ", ".join(
            (
                f"{self.dec(person)} <{addr}>" if person else addr
                for person, addr in getaddresses(msg.get_all("To"))
            )
        )
        ret["message"] = self.dec(body)
        ret["subject"] = self.dec(msg["Subject"])

        return ret

    # Actions

    @staticmethod
    def actions() -> List[Tuple[str, str]]:
        """Return a list of all available actions."""

        doable = []
        for attr in vars(Client):
            if attr.startswith("action_"):
                action = attr.replace("action_", "")
                doc = getattr(Client, attr).__doc__
                doable.append((action, doc.strip()))
        return doable

    def action_copy(self, uids: UIDs, folder: str, **kwargs) -> None:
        """COPY email(s) to the given *folder*."""

        if isinstance(uids, list):
            uids = b",".join(set(uids))

        if "inner" not in kwargs:
            plural = "s" if b"," in uids else ""
            log.info(f"[{self.user}] Copying email{plural} {uids!r} to {folder!r}")

        typ, dat = self.conn.uid("copy", uids, folder)
        if typ != "OK":
            raise dat[0]

        if "inner" not in kwargs:
            self.stats["copy"] += uids.count(b",") + 1

    def action_delete(self, uids: UIDs, **kwargs) -> None:
        """Delete email(s)."""

        if isinstance(uids, list):
            uids = b",".join(set(uids))

        if "inner" not in kwargs:
            plural = "s" if b"," in uids else ""
            log.info(f"[{self.user}] Deleting email{plural} {uids!r}")

        # STORE the Deleted flag on the given email(s)
        typ, dat = self.conn.uid("store", uids, "+FLAGS", "\\Deleted")
        if typ != "OK":
            raise dat[0]

        if "inner" not in kwargs:
            self.stats["delete"] += uids.count(b",") + 1

        self.conn.expunge()

    def action_move(self, uids: UIDs, folder: str, **kwargs) -> None:
        """Move email(s) to the *folder*."""

        if isinstance(uids, list):
            uids = b",".join(set(uids))

        plural = "s" if b"," in uids else ""
        log.info(f"[{self.user}] Moving email{plural} {uids!r} to {folder!r}")

        # There is no explicit MOVE command for IMAP so we have to
        # make a copy into the destination folder and delete the original.
        self.action_copy(uids, folder, inner=True)
        self.action_delete(uids, inner=True)

        self.stats["move"] += uids.count(b",") + 1
