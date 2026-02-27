"""Tests for epJSON file parsing."""


def test_get_data_returns_dict(atlanta_model):
    data = atlanta_model.epjson_data.get_data()
    assert isinstance(data, dict)


def test_top_level_object_count(atlanta_model):
    data = atlanta_model.epjson_data.get_data()
    assert len(data) == 129


def test_zone_count(atlanta_model):
    data = atlanta_model.epjson_data.get_data()
    assert "Zone" in data
    assert len(data["Zone"]) == 22


def test_building_properties(atlanta_model):
    data = atlanta_model.epjson_data.get_data()
    building = data["Building"]["HotelLarge"]
    assert building["terrain"] == "City"
    assert building["north_axis"] == 0


def test_dd_model_has_no_epjson(atlanta_dd_model):
    assert atlanta_dd_model.epjson_data is None


def test_buffalo_epjson_also_works(buffalo_model):
    data = buffalo_model.epjson_data.get_data()
    assert isinstance(data, dict)
    assert "Building" in data
    assert len(data) > 100
