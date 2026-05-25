from wheeloffish.main import app


def test_app_title() -> None:
    assert app.title == "Wheel of Fish TV"
