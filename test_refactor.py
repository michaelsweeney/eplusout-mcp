"""
Test script to verify the filename-agnostic refactoring works correctly.
"""

from src.model_data import (
    get_file_info,
    catalog_path,
    get_model_map,
    initialize_model_map_from_directory
)
from pathlib import Path
import json

def test_get_file_info():
    """Test that get_file_info extracts correct path components"""
    print("=" * 80)
    print("Test 1: get_file_info()")
    print("=" * 80)

    test_path = "C:/mydir/somemodel.epJSON"
    result = get_file_info(test_path)

    print(f"Input: {test_path}")
    print(f"Result: {json.dumps(result, indent=2)}")

    assert result['stem'] == 'somemodel', f"Expected stem 'somemodel', got '{result['stem']}'"
    assert result['extension'] == 'epJSON', f"Expected extension 'epJSON', got '{result['extension']}'"
    print("[PASS] Test passed!\n")

def test_catalog_path():
    """Test that catalog_path groups files correctly"""
    print("=" * 80)
    print("Test 2: catalog_path()")
    print("=" * 80)

    test_dir = "eplus_files/diff_filenames"
    result = catalog_path(test_dir)

    print(f"Scanning directory: {test_dir}")
    print(f"Number of models found: {len(result)}")
    print("\nModels discovered:")

    for model_id, file_info in result.items():
        print(f"\n  Model ID: {model_id}")
        print(f"    Directory: {file_info['directory']}")
        print(f"    Stem: {file_info['stem']}")
        print(f"    HTML: {'YES' if file_info['html'] else 'NO'}")
        print(f"    SQL: {'YES' if file_info['sql'] else 'NO'}")
        print(f"    epJSON: {'YES' if file_info['epjson'] else 'NO'}")

    # Check that singlesimfolder has 3 separate models
    singlesim_models = [k for k in result.keys() if 'singlesimfolder' in k]
    print(f"\n  Models in singlesimfolder: {len(singlesim_models)}")

    assert len(singlesim_models) == 3, f"Expected 3 models in singlesimfolder, got {len(singlesim_models)}"
    print("[PASS] Test passed!\n")

def test_get_model_map():
    """Test that get_model_map creates ModelMap correctly"""
    print("=" * 80)
    print("Test 3: get_model_map()")
    print("=" * 80)

    test_dir = "eplus_files/diff_filenames"
    grouped_models = catalog_path(test_dir)
    model_map = get_model_map(grouped_models)

    print(f"Number of models in ModelMap: {len(model_map.models)}")

    for model in model_map.models:
        attrs = model.get_basic_attributes()
        print(f"\n  Model: {attrs['model_id']}")
        print(f"    Display name: {attrs['display_name']}")
        print(f"    Files: {list(attrs['files'].keys())}")

    assert len(model_map.models) == len(grouped_models), \
        f"Expected {len(grouped_models)} models, got {len(model_map.models)}"
    print("[PASS] Test passed!\n")

def test_initialize_full():
    """Test full initialization with a real directory"""
    print("=" * 80)
    print("Test 4: initialize_model_map_from_directory()")
    print("=" * 80)

    test_dir = "eplus_files/diff_filenames"

    print(f"Initializing model map from: {test_dir}")
    model_map = initialize_model_map_from_directory(test_dir)

    print(f"Total models found: {len(model_map.models)}")
    print("\nSample of discovered models:")

    for i, model in enumerate(model_map.models[:5]):
        attrs = model.get_basic_attributes()
        print(f"\n  {i+1}. {attrs['model_id']}")
        print(f"     Files: {', '.join(attrs['files'].keys())}")

    # Verify that models with different stems in the same directory are separate
    singlesim_models = [m for m in model_map.models if 'singlesimfolder' in m.model_id]
    print(f"\n  Models in singlesimfolder: {len(singlesim_models)}")

    for model in singlesim_models:
        print(f"    - {model.stem}")

    assert len(singlesim_models) == 3, \
        f"Expected 3 separate models in singlesimfolder, got {len(singlesim_models)}"
    print("[PASS] Test passed!\n")

def test_search_models():
    """Test search functionality"""
    print("=" * 80)
    print("Test 5: search_models()")
    print("=" * 80)

    test_dir = "eplus_files/diff_filenames"
    model_map = initialize_model_map_from_directory(test_dir)

    # Search for models in singlesimfolder
    search_results = model_map.search_models('singlesimfolder')

    print(f"Search pattern: 'singlesimfolder'")
    print(f"Matching models: {len(search_results)}")

    for model in search_results:
        print(f"  - {model.model_id}")

    assert len(search_results) > 0, "Expected to find models with 'singlesimfolder' pattern"
    print("[PASS] Test passed!\n")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING FILENAME-AGNOSTIC REFACTORING")
    print("=" * 80 + "\n")

    try:
        test_get_file_info()
        test_catalog_path()
        test_get_model_map()
        test_initialize_full()
        test_search_models()

        print("=" * 80)
        print("ALL TESTS PASSED!")
        print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print("TEST FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
