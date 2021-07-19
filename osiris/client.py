import imaplib
import logging
import re
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass, field
from itertools import zip_longest
from typing import Any, Dict, List, Tuple, Union

from .exceptions import MissingAuth
from .utils import parse

UIDs = Union[bytes, List[bytes]]
log = logging.getLogger(__name__)


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks."""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


@dataclass
class Client:
    """Informations of a user that will be judged soon."""

    server: str
    user: str
    conn: imaplib.IMAP4 = field(default=None, init=False, repr=False)
    password: str = field(default=None, repr=False)
    folder: str = field(default=None)
    stats: Dict[str, int] = field(default_factory=dict, repr=False)
    # BODY.PEEK to not alter the message state
    fetch_pattern: str = field(default="(BODY.PEEK[])", repr=False)
    batch_size: int = field(default=256)
    commit_size: int = field(default=256 * 8)

    def __post_init__(self):
        self.stats = defaultdict(int)

    def __enter__(self) -> "Client":
        log.debug(f"Loading {self} ...")
        return self

    def __exit__(self, *_: Any) -> None:
        log.debug(f"Stopping {self} ...")
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
        if self.folder:
            self.conn.select(self.folder)
        else:
            self.conn.select()
        log.debug(f"Added {self}")

    def emails(self, full: bool = False) -> List[str]:
        """Retreive emails."""

        search = "(ALL)" if full else "(NOT DELETED)"
        typ, dat = self.conn.uid("search", None, search)
        if typ != "OK":
            raise dat[0]

        all_uids = dat[0].split()
        if not all_uids:
            return {}

        ret = {}
        reg_uid = re.compile(br"UID (\d+)")

        len_uids = len(all_uids)
        rounds = len_uids // self.batch_size + (1 if len_uids % self.batch_size else 0)
        log.debug(
            f"Retrieving {len_uids:,} emails "
            f"(batch size is {self.batch_size:,}, "
            f"commit size is {self.commit_size:,}, "
            f"round count is {rounds:,}) ..."
        )
        for batch, some_uids in enumerate(grouper(all_uids, self.batch_size), 1):
            # Filter out empty UIDs filled by grouper()
            uids = [u for u in some_uids if u is not None]

            log.debug(f"[round {batch}] Fetching {len(uids):,} emails ...")
            typ, dat = self.conn.uid("fetch", b",".join(uids), self.fetch_pattern)
            if typ != "OK":
                raise dat[0]

            for raw_data in dat:
                if len(raw_data) != 2:  # Invalid chunk?!
                    continue

                command, data = raw_data
                uid = reg_uid.findall(command)[0]
                try:
                    ret[uid] = parse(data)
                except TypeError:
                    # https://bugs.python.org/issue27513
                    log.exception("bpo-27513: Error when trying to decode email header")

            if len(ret) >= self.commit_size:
                yield ret
                ret = {}

        if ret:
            yield ret

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

        total = uids.count(b",") + 1

        if "inner" not in kwargs:
            plural = "s" if total > 1 else ""
            log.info(
                f"[{self.user}] Copying {total:,} email{plural} {uids!r} to {folder!r}"
            )

        typ, dat = self.conn.uid("copy", uids, folder)
        if typ != "OK":
            raise dat[0]

        if "inner" not in kwargs:
            self.stats["copy"] += total

    def action_delete(self, uids: UIDs, **kwargs) -> None:
        """Delete email(s)."""

        if isinstance(uids, list):
            uids = b",".join(set(uids))

        total = uids.count(b",") + 1

        if "inner" not in kwargs:
            plural = "s" if total > 1 else ""
            log.info(f"[{self.user}] Deleting {total:,} email{plural} {uids!r}")

        # STORE the Deleted flag on the given email(s)
        typ, dat = self.conn.uid("store", uids, "+FLAGS", "\\Deleted")
        if typ != "OK":
            raise dat[0]

        if "inner" not in kwargs:
            self.stats["delete"] += total

        self.conn.expunge()

    def action_move(self, uids: UIDs, folder: str, **kwargs) -> None:
        """Move email(s) to the *folder*."""

        if isinstance(uids, list):
            uids = b",".join(set(uids))

        total = uids.count(b",") + 1
        plural = "s" if total > 1 else ""
        log.info(f"[{self.user}] Moving {total:,} email{plural} {uids!r} to {folder!r}")

        # There is no explicit MOVE command for IMAP so we have to
        # make a copy into the destination folder and delete the original.
        self.action_copy(uids, folder, inner=True)
        self.action_delete(uids, inner=True)

        self.stats["move"] += total
