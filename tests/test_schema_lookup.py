"""Tests for EnergyPlus schema lookup."""

from src.server import get_eplus_object_schema


def test_exact_match():
    result = get_eplus_object_schema("Building")
    assert result["object_type"] == "Building"
    assert result["group"] == "Simulation Parameters"
    assert len(result["fields"]) == 7
    assert result["schema_version"] == "24.1"


def test_case_insensitive_match():
    result = get_eplus_object_schema("building")
    assert result["object_type"] == "Building"


def test_not_found_returns_suggestions():
    result = get_eplus_object_schema("Coil:Cooling")
    assert "error" in result
    assert len(result["suggestions"]) > 0
    assert any("Coil:Cooling" in s for s in result["suggestions"])


def test_complex_object_fields():
    result = get_eplus_object_schema("Coil:Cooling:WaterToAirHeatPump:EquationFit")
    assert result["group"] == "Coils"
    assert len(result["fields"]) == 21
    # Check a field has expected structure
    rated_air = next(f for f in result["fields"] if f["name"] == "rated_air_flow_rate")
    assert "number" in rated_air["type"]  # "number/string" because field accepts "Autosize"
    assert rated_air["units"] == "m3/s"


def test_nonexistent_object():
    result = get_eplus_object_schema("TotallyFakeObject:DoesNotExist")
    assert "error" in result
    assert result["suggestions"] == []
