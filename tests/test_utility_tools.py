"""Tests for utility tools like get_associated_files_by_type."""


def test_get_err_file(atlanta_model):
    lines = atlanta_model.get_associated_files_by_type(".err")
    assert isinstance(lines, list)
    assert len(lines) > 0


def test_err_file_contains_version(atlanta_model):
    lines = atlanta_model.get_associated_files_by_type(".err")
    first_line = lines[0]
    assert "EnergyPlus" in first_line


def test_dd_model_no_epjson_returns_none(atlanta_dd_model):
    # dd model has no epjson_data, so get_associated_files_by_type returns None
    result = atlanta_dd_model.get_associated_files_by_type(".err")
    assert result is None


def test_nonexistent_extension(atlanta_model):
    result = atlanta_model.get_associated_files_by_type(".xyz_nonexistent")
    assert isinstance(result, str)
    assert "error" in result.lower()
