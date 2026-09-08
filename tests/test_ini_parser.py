from pathlib import Path

from zomboid_modder.domain.ini import PzIni

FIXTURE = Path(__file__).parent / "fixtures" / "servertest.ini"


def test_roundtrip_preserves_content():
    text = FIXTURE.read_text()
    ini = PzIni.parse(text)
    assert ini.serialize() == text


def test_get_returns_value():
    ini = PzIni.parse(FIXTURE.read_text())
    assert ini.get("PVP") == "true"
    assert ini.get("Mods") == "Foo;Bar"
    assert ini.get("Missing") is None


def test_set_updates_in_place():
    ini = PzIni.parse(FIXTURE.read_text())
    ini.set("PVP", "false")
    out = ini.serialize()
    assert "PVP=false" in out
    assert "PVP=true" not in out
    assert "# Project Zomboid server config (fixture)" in out


def test_set_appends_new_key():
    ini = PzIni.parse(FIXTURE.read_text())
    ini.set("NewKey", "hello")
    assert ini.get("NewKey") == "hello"
    assert "NewKey=hello" in ini.serialize()


def test_keys_excludes_comments_and_blanks():
    ini = PzIni.parse(FIXTURE.read_text())
    assert "PVP" in ini.keys()
    assert "Mods" in ini.keys()
    assert all(not k.startswith("#") for k in ini.keys())
