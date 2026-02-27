import pytest
from pathlib import Path
from src.model_data import catalog_path, get_model_map, ModelMap, ModelFileData

EXAMPLE_DIR = str(Path(__file__).parent.parent / "example-files")


@pytest.fixture(scope="session")
def model_map() -> ModelMap:
    """Build model map from example-files directory."""
    catalog = catalog_path(EXAMPLE_DIR)
    return get_model_map(catalog)


@pytest.fixture(scope="session")
def atlanta_model(model_map) -> ModelFileData:
    """Full Atlanta model (epJSON + SQL + HTML)."""
    return model_map.get_model_by_id("./ASHRAE901_HotelLarge_STD2013_Atlanta")


@pytest.fixture(scope="session")
def buffalo_model(model_map) -> ModelFileData:
    """Full Buffalo model (epJSON + SQL + HTML)."""
    return model_map.get_model_by_id("./ASHRAE901_HotelLarge_STD2013_Buffalo")


@pytest.fixture(scope="session")
def atlanta_dd_model(model_map) -> ModelFileData:
    """Design-day Atlanta model (SQL + HTML only, no epJSON)."""
    return model_map.get_model_by_id("./ASHRAE901_HotelLarge_STD2013_Atlanta.dd")
