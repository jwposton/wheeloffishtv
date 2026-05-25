class ProviderError(Exception):
    """Base exception for media provider failures."""

    code: str = "provider_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)


class ProviderUnreachable(ProviderError):
    code = "unreachable"


class ProviderUnauthorized(ProviderError):
    code = "unauthorized"


class ProviderSSLError(ProviderError):
    code = "ssl_error"


class ProviderDisabled(ProviderError):
    code = "provider_disabled"


class ProviderWrongType(ProviderError):
    code = "wrong_type"
