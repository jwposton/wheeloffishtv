from pydantic import BaseModel


class ConnectionSummary(BaseModel):
    id: str
    provider: str
    display_name: str
    base_url: str


class InstallScheduleSummary(BaseModel):
    """Install-wide nightly rebuild window (D-01) for operator-facing UI copy."""

    install_timezone: str
    rebuild_cron: str


class AuthMeResponse(BaseModel):
    app_user_id: str
    provider_user_id: str
    provider_username: str | None
    connection: ConnectionSummary | None
    has_media_link: bool
    libraries_scoped: bool
    install_schedule: InstallScheduleSummary


class BootstrapSessionResponse(BaseModel):
    status: str


class LogoutResponse(BaseModel):
    status: str
