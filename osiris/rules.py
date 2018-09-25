import logging
from configparser import ConfigParser
from pathlib import Path
from typing import Union

from dataclasses import dataclass


log = logging.getLogger(__name__)


@dataclass
class Rules:
    file: Union[Path, str] = "rules.ini"

    def __post_init__(self):
        log.debug(f"Loading {type(self).__name__} ...")
        self.file = Path(self.file)
        if not self.file.is_file():
            raise FileNotFoundError(self.file)

    @property
    def parser(self) -> "TODO":
        if not hasattr(self, "_parser"):
            self._parser = ConfigParser()
            self._parser.read(self.file, encoding="utf-8")
        return self._parser

    @staticmethod
    def read_rule(option):
        actions = option.strip().splitlines()
        criterias = actions.pop(0)
        return criterias, actions

    def get(self, user: str):
        section = f"{user}:rules"
        rules = sorted(self.parser.items(section))
        return {k: self.read_rule(v) for k, v in rules}

    def server(self, user: str) -> str:
        return self.parser.get(user, "server")
