import pytest

from zomboid_modder.domain.ini import PzIni
from zomboid_modder.domain.mod import Mod
from zomboid_modder.domain.mod_list import ModList, ModListError


def _ini():
    return PzIni.parse("Mods=Foo;Bar\nWorkshopItems=111;222\n")


def test_list_pairs_by_index():
    ml = ModList(_ini())
    mods = ml.list()
    assert [m.id for m in mods] == ["Foo", "Bar"]
    assert [m.workshop_id for m in mods] == ["111", "222"]


def test_add_appends_both():
    ini = _ini()
    ml = ModList(ini)
    ml.add(Mod(id="Baz", workshop_id="333", name="Baz Mod"))
    assert ini.get("Mods") == "Foo;Bar;Baz"
    assert ini.get("WorkshopItems") == "111;222;333"


def test_add_duplicate_raises():
    ml = ModList(_ini())
    with pytest.raises(ModListError):
        ml.add(Mod(id="Foo", workshop_id="999"))


def test_remove_strips_both():
    ini = _ini()
    ml = ModList(ini)
    ml.remove("Foo")
    assert ini.get("Mods") == "Bar"
    assert ini.get("WorkshopItems") == "222"


def test_remove_missing_raises():
    ml = ModList(_ini())
    with pytest.raises(ModListError):
        ml.remove("Nope")


def test_reorder_swaps_both():
    ini = _ini()
    ml = ModList(ini)
    ml.reorder("Bar", 0)
    assert ini.get("Mods") == "Bar;Foo"
    assert ini.get("WorkshopItems") == "222;111"


def test_empty_ini():
    ini = PzIni.parse("")
    ml = ModList(ini)
    assert ml.list() == []
    ml.add(Mod(id="A", workshop_id="1"))
    assert ini.get("Mods") == "A"
    assert ini.get("WorkshopItems") == "1"
