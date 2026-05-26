"""Shared helpers for native provider playlist naming."""


def provider_playlist_display_name(wof_name: str) -> str:
    """Format WheelOfFish playlist name for provider display (D-08)."""
    return f"{wof_name} [WoF]"
