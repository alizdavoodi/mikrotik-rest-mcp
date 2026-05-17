class MikrotikMcpError(Exception):
    pass


class MikrotikConnectionError(MikrotikMcpError):
    pass


class MikrotikNotFound(MikrotikMcpError):
    """A specific RouterOS record was not found at the given submenu path."""

    def __init__(self, path: str, identifier: str | None = None) -> None:
        self.path = path
        self.identifier = identifier
        msg = f"RouterOS record not found: {path}"
        if identifier is not None:
            msg = f"{msg} (id={identifier!r})"
        super().__init__(msg)
