class MikrotikMcpError(Exception):
    pass


class ConnectionError(MikrotikMcpError):
    pass


class NotFoundError(MikrotikMcpError):
    pass


class ValidationError(MikrotikMcpError):
    pass
