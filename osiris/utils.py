from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from email.utils import getaddresses
from typing import Any, Dict, List, Tuple, Union


def decode(header: Union[bytes, str]) -> str:
    """Decode an email header, if necessary."""

    if isinstance(header, bytes):
        header = header.decode("latin-1")

    val, encoding = decode_header(header)[0]
    errors = "strict"
    if isinstance(val, bytes):
        if encoding == "unknown-8bit":
            encoding = "latin-1"
            errors = "ignore"
        try:
            val = val.decode(encoding or "latin-1", errors=errors)
        except UnicodeDecodeError:
            val = val.decode("latin-1")
    return val


def fmt_addr(msg: Message, header: List[Union[bytes, str]]) -> str:
    """Format address(es)."""
    return ", ".join(
        (
            f"{decode(person)} <{addr}>" if person else addr
            for person, addr in getaddresses(msg.get_all(header, []))
        )
    ).lower()


def is_spam(msg) -> bool:
    """Naive checks for spam."""

    spam = msg.get("X-Spam-Flag", "").lower() == "yes"
    if not spam:
        spam = msg.get("X-GND-Status", "").lower() == "spam"
    if not spam:
        # If it seems to be a spam, the value will be one or more plus (+).
        # When not a spam, the value is a slash (/).
        # Other associated headers are:
        #   X-Atmail-Spam-score (ie: 3.6)
        #   X-Atmail-Spam-score_int (ie: 36)
        spam = "+" in msg.get("X-Atmail-Spam-bar", "")

    return spam


def sanitize_header(value: str) -> str:
    """Sanitize email header names."""
    return value.lower().replace("-", "_")


def parse(data: Tuple[Any]) -> Dict[str, str]:
    """Parse an email."""

    msg = message_from_bytes(data)
    ret = {sanitize_header(k): v.lower() for k, v in msg.items()}
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

    ret["addr_cc"] = fmt_addr(msg, "Cc")
    ret["addr_from"] = fmt_addr(msg, "From")
    ret["addr_to"] = fmt_addr(msg, "To")
    ret["delivered_to"] = fmt_addr(msg, "Delivered-To")
    ret["is_spam"] = is_spam(msg)
    ret["message"] = decode(body).lower()
    ret["msgid"] = msg.get("Message-ID", "").lower()
    ret["reply_to"] = fmt_addr(msg, "Reply-To")
    ret["subject"] = decode(msg["Subject"] or b"").lower()
    ret["ua"] = msg.get("User-Agent", "").lower()

    return ret
