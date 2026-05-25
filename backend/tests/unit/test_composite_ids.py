import pytest

from wheeloffish.domain.ids import canonical_composite_id, format_composite_id, parse_composite_id


def test_format_and_parse_round_trip() -> None:
    connection_id = "conn-uuid"
    provider = "plex"
    native_id = "com.plexapp.agents.thetvdb://123"

    composite = format_composite_id(connection_id, provider, native_id)
    parts = composite.split(":", 2)
    assert len(parts) == 3
    assert parts[0] == connection_id
    assert parts[1] == provider

    parsed = parse_composite_id(composite)
    assert parsed == (connection_id, provider, native_id)


def test_format_url_encodes_native_id() -> None:
    native_id = "com.plexapp.agents.thetvdb://123/1/1"
    composite = format_composite_id("conn-uuid", "plex", native_id)
    assert composite.count(":") >= 2
    assert parse_composite_id(composite)[2] == native_id


def test_canonical_composite_id_normalizes_decoded_guid() -> None:
    connection_id = "conn-uuid"
    encoded = format_composite_id(connection_id, "plex", "plex://show/abc123")
    decoded = f"{connection_id}:plex:plex://show/abc123"
    assert canonical_composite_id(decoded) == encoded
    assert canonical_composite_id(encoded) == encoded


@pytest.mark.parametrize(
    "value",
    [
        "",
        "only-two:parts",
        ":missing:leading",
        "missing:trailing:",
    ],
)
def test_parse_rejects_bad_format(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid composite ID"):
        parse_composite_id(value)
