class OsirisError(Exception):
    """Mother exception."""

    def __str__(self) -> str:
        return repr(self)


class InvalidAction(OsirisError):
    """An action defined in the rules file is not implemented."""

    def __init__(self, action: str) -> None:
        self.action = action

    def __repr__(self) -> str:
        return f"Unknown action {self.action!r}."


class MissingEnvPassword(OsirisError):
    """The password envar for a given user is not set."""

    def __init__(self, account: str, envar: str) -> None:
        self.account = account
        self.envar = envar

    def __repr__(self) -> str:
        return f"You need to provide a password via the envar {self.envar!r} for the account {self.account!r}."


class MissingAuth(OsirisError):
    """The password is missing from the class attributes,
    most lilely it was not setted before  in the code."""

    def __repr__(self) -> str:
        return "You need to provide a password."
