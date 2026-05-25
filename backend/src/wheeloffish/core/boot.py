from datetime import UTC, datetime

from sqlalchemy.orm import Session

from wheeloffish.core.config import Settings
from wheeloffish.db.models.connection import Connection


def sync_connection_from_env(db: Session, settings: Settings) -> Connection:
    """Upsert the single env-configured media server connection row."""
    now = datetime.now(UTC)
    connection = (
        db.query(Connection).filter(Connection.provider_type == settings.WOF_PROVIDER).one_or_none()
    )
    if connection is None:
        connection = Connection(
            provider_type=settings.WOF_PROVIDER,
            display_name=settings.WOF_MEDIA_SERVER_DISPLAY_NAME,
            base_url=settings.WOF_MEDIA_SERVER_URL,
            verify_ssl=settings.WOF_VERIFY_SSL,
            created_at=now,
            updated_at=now,
        )
        db.add(connection)
    else:
        connection.display_name = settings.WOF_MEDIA_SERVER_DISPLAY_NAME
        connection.base_url = settings.WOF_MEDIA_SERVER_URL
        connection.verify_ssl = settings.WOF_VERIFY_SSL
        connection.updated_at = now
    db.commit()
    db.refresh(connection)
    return connection
