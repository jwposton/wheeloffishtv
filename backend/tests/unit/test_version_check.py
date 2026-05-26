from wheeloffish.core.version_check import is_newer_version, reset_release_cache


def test_is_newer_version_compares_semver() -> None:
    assert is_newer_version("0.1.3", "0.1.2")
    assert is_newer_version("0.2.0", "0.1.9")
    assert not is_newer_version("0.1.2", "0.1.2")
    assert not is_newer_version("0.1.1", "0.1.2")


def test_is_newer_version_accepts_v_prefix() -> None:
    assert is_newer_version("v0.1.3", "0.1.2")


def test_reset_release_cache_is_safe() -> None:
    reset_release_cache()
