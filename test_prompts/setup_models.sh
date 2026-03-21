#!/usr/bin/env bash
set -euo pipefail

# Creates 20 test model directories from available source simulations.
# Run this once before using prompt 03_multi_model_comparison.
#
# Sources:
#   - example-files/ in this repo (2 HotelLarge models)
#   - ~/Documents/prototype-testing/output/ (4 models, if available)
#
# If prototype-testing files aren't available, all 20 models will use
# the repo's example files as source data.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MODELS_DIR="$SCRIPT_DIR/models"
PROTO_DIR="$HOME/Documents/prototype-testing/output"

mkdir -p "$MODELS_DIR"

# Source files: [htm, sql]
ATL_HTM="$REPO_DIR/example-files/ASHRAE901_HotelLarge_STD2013_Atlanta.table.htm"
ATL_SQL="$REPO_DIR/example-files/ASHRAE901_HotelLarge_STD2013_Atlanta.sql"
BUF_HTM="$REPO_DIR/example-files/ASHRAE901_HotelLarge_STD2013_Buffalo.table.htm"
BUF_SQL="$REPO_DIR/example-files/ASHRAE901_HotelLarge_STD2013_Buffalo.sql"

# Prototype sources (optional)
APT_ABQ_HTM="$PROTO_DIR/ApartmentMidRise_Albuquerque/eplustbl.htm"
APT_ABQ_SQL="$PROTO_DIR/ApartmentMidRise_Albuquerque/eplusout.sql"
APT_MIA_HTM="$PROTO_DIR/ApartmentMidRise_Miami/eplustbl.htm"
APT_MIA_SQL="$PROTO_DIR/ApartmentMidRise_Miami/eplusout.sql"
HTL_ELP_HTM="$PROTO_DIR/HotelLarge_ElPaso/eplustbl.htm"
HTL_ELP_SQL="$PROTO_DIR/HotelLarge_ElPaso/eplusout.sql"
HTL_INF_HTM="$PROTO_DIR/HotelLarge_InternationalFalls/eplustbl.htm"
HTL_INF_SQL="$PROTO_DIR/HotelLarge_InternationalFalls/eplusout.sql"

copy_model() {
    local name="$1" htm="$2" sql="$3"
    local dest="$MODELS_DIR/$name"
    mkdir -p "$dest"
    cp "$htm" "$dest/eplustbl.htm"
    cp "$sql" "$dest/eplusout.sql"
    echo "  $name"
}

# Use prototype sources if available, otherwise fall back to repo files
if [[ -f "$APT_ABQ_HTM" ]]; then
    SRC_APT_COLD_HTM="$APT_ABQ_HTM"; SRC_APT_COLD_SQL="$APT_ABQ_SQL"
    SRC_APT_HOT_HTM="$APT_MIA_HTM";  SRC_APT_HOT_SQL="$APT_MIA_SQL"
    SRC_HTL_MID_HTM="$HTL_ELP_HTM";  SRC_HTL_MID_SQL="$HTL_ELP_SQL"
    SRC_HTL_COLD_HTM="$HTL_INF_HTM"; SRC_HTL_COLD_SQL="$HTL_INF_SQL"
    echo "Using prototype-testing sources + repo example files"
else
    SRC_APT_COLD_HTM="$BUF_HTM"; SRC_APT_COLD_SQL="$BUF_SQL"
    SRC_APT_HOT_HTM="$ATL_HTM";  SRC_APT_HOT_SQL="$ATL_SQL"
    SRC_HTL_MID_HTM="$ATL_HTM";  SRC_HTL_MID_SQL="$ATL_SQL"
    SRC_HTL_COLD_HTM="$BUF_HTM"; SRC_HTL_COLD_SQL="$BUF_SQL"
    echo "Prototype-testing not found, using repo example files only"
fi

echo "Creating 20 models in $MODELS_DIR:"

# Apartments — cold climate source
copy_model "ApartmentMidRise_Chicago"       "$SRC_APT_COLD_HTM" "$SRC_APT_COLD_SQL"
copy_model "ApartmentMidRise_Minneapolis"   "$SRC_APT_COLD_HTM" "$SRC_APT_COLD_SQL"
copy_model "ApartmentMidRise_SanFrancisco"  "$SRC_APT_COLD_HTM" "$SRC_APT_COLD_SQL"
copy_model "ApartmentHighRise_NewYork"      "$SRC_APT_COLD_HTM" "$SRC_APT_COLD_SQL"
copy_model "ApartmentHighRise_Denver"       "$SRC_APT_COLD_HTM" "$SRC_APT_COLD_SQL"

# Apartments — hot climate source
copy_model "ApartmentMidRise_Houston"       "$SRC_APT_HOT_HTM"  "$SRC_APT_HOT_SQL"
copy_model "ApartmentMidRise_Phoenix"       "$SRC_APT_HOT_HTM"  "$SRC_APT_HOT_SQL"
copy_model "ApartmentHighRise_Seattle"      "$SRC_APT_HOT_HTM"  "$SRC_APT_HOT_SQL"

# Hotels — warm climate (Atlanta source)
copy_model "HotelLarge_Houston"    "$ATL_HTM" "$ATL_SQL"
copy_model "HotelLarge_Phoenix"    "$ATL_HTM" "$ATL_SQL"
copy_model "HotelLarge_LosAngeles" "$ATL_HTM" "$ATL_SQL"
copy_model "HotelSmall_Miami"      "$ATL_HTM" "$ATL_SQL"

# Hotels — cold climate (Buffalo source)
copy_model "HotelLarge_Chicago"      "$BUF_HTM" "$BUF_SQL"
copy_model "HotelSmall_Chicago"      "$BUF_HTM" "$BUF_SQL"

# Hotels — mid/extreme climate (prototype sources)
copy_model "HotelLarge_Denver"       "$SRC_HTL_MID_HTM"  "$SRC_HTL_MID_SQL"
copy_model "HotelLarge_Minneapolis"  "$SRC_HTL_COLD_HTM" "$SRC_HTL_COLD_SQL"

# Other building types
copy_model "OfficeLarge_Chicago"          "$BUF_HTM" "$BUF_SQL"
copy_model "OfficeMedium_Atlanta"         "$ATL_HTM" "$ATL_SQL"
copy_model "RetailStandalone_Buffalo"     "$BUF_HTM" "$BUF_SQL"
copy_model "SchoolPrimary_Albuquerque"    "$SRC_HTL_MID_HTM" "$SRC_HTL_MID_SQL"

echo ""
echo "Done. $(ls -d "$MODELS_DIR"/*/ 2>/dev/null | wc -l) models created."
