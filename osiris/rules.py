import logging
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, List, Tuple, Union

from dataclasses import dataclass


log = logging.getLogger(__name__)


@dataclass
class Rules:
    """A set of rules for each and every users."""

    file: Union[Path, str] = "rules.ini"

    def __post_init__(self):
        log.debug(f"Loading {type(self).__name__} ...")
        self.file = Path(self.file)
        if not self.file.is_file():
            raise FileNotFoundError(self.file)

    @property
    def parser(self) -> ConfigParser:
        """Parse the rule INI file or return the current parser."""
        if not hasattr(self, "_parser"):
            self._parser = ConfigParser()
            self._parser.read(self.file, encoding="utf-8")
        return self._parser

    @staticmethod
    def read_rule(section) -> Tuple[str, List[str]]:
        """Retreive rules of a given user."""
        actions = section.strip().splitlines()
        criterias = actions.pop(0)
        return criterias, actions

    def get(self, user: str) -> Dict[str, Tuple[str, List[str]]]:
        """"Retreive rules of all users."""
        section = f"{user}:rules"
        rules = sorted(self.parser.items(section))
        return {k: self.read_rule(v) for k, v in rules}

    def server(self, user: str) -> str:
        """Get the IMAP server."""
        return self.parser.get(user, "server")
