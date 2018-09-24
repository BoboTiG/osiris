import imaplib
import logging
from collections import defaultdict
from contextlib import suppress
from email.header import decode_header
from typing import Any, Dict, List, Union

from dataclasses import dataclass, field

from .exceptions import MissingAuth


UIDs = Union[bytes, List[bytes]]
log = logging.getLogger(__name__)


@dataclass
class Client:
    server: str
    user: str
    conn: imaplib.IMAP4 = field(default=None, init=False, repr=False)
    password: str = field(default=None, repr=False)
    stats: Dict[str, int] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.stats = defaultdict(int)

    def __enter__(self) -> "Client":
        log.debug(f"Loading {type(self).__name__} ...")
        return self

    def __exit__(self, *exc_info: Any) -> None:
        log.debug(f"Stopping {type(self).__name__}: {dict(self.stats.items())} ...")
        self.close()

    def close(self):
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
        log.info(f"Added {self}")

    def emails(self, force: bool = False) -> List[str]:
        ret = {}
        # reg_from = re.compile(b"<(.+)>")

        search = "(ALL)" if force else "(UNSEEN)"
        typ, dat = self.conn.uid("search", None, search)
        if typ != "OK":
            raise dat[0]

        uids = dat[0].split()
        if not uids:
            return ret

        all_uids = b",".join(uids)

        #  BODY.PEEK to not alter the message state
        typ, dat = self.conn.uid(
            "fetch", all_uids, "(BODY.PEEK[HEADER.FIELDS (SUBJECT TO FROM)])"
        )
        if typ != "OK":
            raise dat[0]

        for uid, data in zip(uids, dat):
            data = b"".join(data[1:]).strip().splitlines()
            if not data:
                continue

            ret[uid] = {}
            for line in data:
                line = line.lower().strip()
                if not line:
                    continue

                if line.startswith(b"subject:"):
                    key = "subject"
                    val = line.partition(b"subject:")[2]
                elif line.startswith(b"to:"):
                    key = "addr_to"
                    val = line.partition(b"to:")[2]
                    # Only the email address
                    # address = reg_from.findall(val)
                    # if address:
                    #     val = address[0]
                elif line.startswith(b"from:"):
                    key = "addr_from"
                    val = line.partition(b"from:")[2]
                    # Only the email address
                    # address = reg_from.findall(val)
                    # if address:
                    #     val = address[0]

                if isinstance(val, bytes):
                    val, encoding = decode_header(val.decode("utf-8"))[0]
                    if not encoding:
                        encoding = "utf-8"
                    if isinstance(val, bytes):
                        try:
                            val = val.decode(encoding)
                        except UnicodeDecodeError:
                            val = val.decode("latin-1")

                ret[uid][key] = val.strip()

        return ret

    # Actions

    @staticmethod
    def actions():
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

        plural = "s" if b"," in uids else ""
        log.info(f"[{self.user}] Copying email{plural} {uids!r} to {folder!r}")
        typ, dat = self.conn.uid("copy", uids, folder)
        if typ != "OK":
            raise dat[0]

        if "no_stats" not in kwargs:
            self.stats["copy"] += 1

    def action_delete(self, uids: UIDs, **kwargs) -> None:
        """Delete email(s)."""

        if isinstance(uids, list):
            uids = b",".join(set(uids))

        plural = "s" if b"," in uids else ""
        log.info(f"[{self.user}] Deleting email{plural} {uids!r}")

        # STORE the Deleted flag on the given email(s)
        typ, dat = self.conn.uid("store", uids, "+FLAGS", "\\Deleted")
        if typ != "OK":
            raise dat[0]

        if "no_stats" not in kwargs:
            self.stats["delete"] += 1

        self.conn.expunge()

    def action_move(self, uids: UIDs, folder: str, **kwargs) -> None:
        """Move email(s) to the *folder*."""

        if isinstance(uids, list):
            uids = b",".join(set(uids))

        plural = "s" if b"," in uids else ""
        log.info(f"[{self.user}] Moving email{plural} {uids!r} to {folder!r}")

        # There is no explicit MOVE command for IMAP so we have to
        # make a copy into the destination folder and delete the original.
        self.action_copy(uids, folder, no_stats=True)
        self.action_delete(uids, no_stats=True)

        self.stats["move"] += 1
