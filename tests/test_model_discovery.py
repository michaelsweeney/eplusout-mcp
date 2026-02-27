"""Tests for model discovery via catalog_path() and ModelMap."""

from src.model_data import catalog_path, get_model_map
from tests.conftest import EXAMPLE_DIR


def test_catalog_discovers_four_models(model_map):
    assert len(model_map.models) == 4


def test_complete_models_have_all_file_types(atlanta_model, buffalo_model):
    for model in [atlanta_model, buffalo_model]:
        assert model.epjson_data is not None
        assert model.sql_data is not None
        assert model.html_data is not None


def test_dd_models_lack_epjson(atlanta_dd_model):
    assert atlanta_dd_model.epjson_data is None
    assert atlanta_dd_model.sql_data is not None
    assert atlanta_dd_model.html_data is not None


def test_get_model_by_id_returns_correct_model(model_map):
    model = model_map.get_model_by_id("./ASHRAE901_HotelLarge_STD2013_Atlanta")
    assert model is not None
    assert model.stem == "ASHRAE901_HotelLarge_STD2013_Atlanta"


def test_get_model_by_id_nonexistent_returns_none(model_map):
    assert model_map.get_model_by_id("nonexistent/model") is None


def test_search_models_atlanta(model_map):
    results = model_map.search_models("Atlanta")
    assert len(results) == 2
    for r in results:
        assert "Atlanta" in r.model_id


def test_search_models_buffalo(model_map):
    results = model_map.search_models("Buffalo")
    assert len(results) == 2


def test_search_models_none_returns_all(model_map):
    results = model_map.search_models(None)
    assert len(results) == 4


def test_get_basic_attributes(atlanta_model):
    attrs = atlanta_model.get_basic_attributes()
    assert attrs["model_id"] == "./ASHRAE901_HotelLarge_STD2013_Atlanta"
    assert attrs["stem"] == "ASHRAE901_HotelLarge_STD2013_Atlanta"
    assert "epjson" in attrs["files"]
    assert "sql" in attrs["files"]
    assert "html" in attrs["files"]


def test_get_all_model_ids(model_map):
    ids = model_map.get_all_model_ids()
    assert len(ids) == 4
    assert "./ASHRAE901_HotelLarge_STD2013_Atlanta" in ids
    assert "./ASHRAE901_HotelLarge_STD2013_Buffalo" in ids
