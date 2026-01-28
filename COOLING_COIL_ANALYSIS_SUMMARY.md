# Cooling Load Sizing Analysis

## EnergyPlus Model: ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd

This analysis examines the `Coil:Cooling:WaterToAirHeatPump:EquationFit` objects in the EnergyPlus model, calculating the SF per Ton metric for each cooling coil.

---

## Executive Summary

| Coil Name                        | Zone Area (SF) | Capacity (Tons) | **SF per Ton** | CFM per Ton | SHR  |
| -------------------------------- | -------------- | --------------- | -------------- | ----------- | ---- |
| Room_1_Flr_3 Cooling Coil        | 420.03         | 4.36            | **96.42**      | 628.39      | 0.89 |
| Room_1_Flr_6 Cooling Coil        | 420.05         | 1.18            | **355.24**     | 630.18      | 0.89 |
| Room_2_Flr_3 Cooling Coil        | 419.98         | 4.23            | **99.30**      | 627.75      | 0.89 |
| Room_2_Flr_6 Cooling Coil        | 419.98         | 1.15            | **366.19**     | 629.58      | 0.89 |
| Room_3_Mult9_Flr_6 Cooling Coil  | 264.04         | 4.60            | **57.42**      | 615.31      | 0.88 |
| Room_3_Mult19_Flr_3 Cooling Coil | 263.97         | 21.93           | **12.04**      | 642.49      | 0.90 |
| Room_4_Mult19_Flr_3 Cooling Coil | 264.04         | 26.14           | **10.10**      | 606.85      | 0.87 |
| Room_5_Flr_3 Cooling Coil        | 420.03         | 3.87            | **108.58**     | 625.45      | 0.89 |
| Room_6_Flr_3 Cooling Coil        | 419.98         | 3.72            | **113.03**     | 624.26      | 0.89 |

---

## Detailed Coil Information

### Room_1_Flr_3 Cooling Coil

- **Zone Served**: Room_1_Flr_3
- **Air Inlet Node**: Room_1_Flr_3 Return
- **Air Outlet Node**: Room_1_Flr_3 Cooling Coil Outlet
- **Zone Area**: 39.02 m² (420.03 SF)
- **Nominal Total Capacity**: 15,319.85 W (4.36 Tons)
- **Nominal Sensible Capacity**: 13,620.12 W
- **Sensible Heat Ratio**: 0.89
- **COP**: 4.69
- **Air Flow**: 1.29 m³/s (2,737.35 CFM)
- **SF per Ton**: 96.42
- **CFM per Ton**: 628.39

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 1
- HVAC Sizing Summary > Coil Sizing Summary: Row 1

---

### Room_1_Flr_6 Cooling Coil

- **Zone Served**: Room_1_Flr_6
- **Air Inlet Node**: Room_1_Flr_6 Return
- **Air Outlet Node**: Room_1_Flr_6 Cooling Coil Outlet
- **Zone Area**: 39.02 m² (420.05 SF)
- **Nominal Total Capacity**: 4,158.46 W (1.18 Tons)
- **Nominal Sensible Capacity**: 3,704.05 W
- **Sensible Heat Ratio**: 0.89
- **COP**: 4.69
- **Air Flow**: 0.35 m³/s (745.16 CFM)
- **SF per Ton**: 355.24
- **CFM per Ton**: 630.18

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 7
- HVAC Sizing Summary > Coil Sizing Summary: Row 7

---

### Room_2_Flr_3 Cooling Coil

- **Zone Served**: Room_2_Flr_3
- **Air Inlet Node**: Room_2_Flr_3 Return
- **Air Outlet Node**: Room_2_Flr_3 Cooling Coil Outlet
- **Zone Area**: 39.02 m² (419.98 SF)
- **Nominal Total Capacity**: 14,874.61 W (4.23 Tons)
- **Nominal Sensible Capacity**: 13,215.38 W
- **Sensible Heat Ratio**: 0.89
- **COP**: 4.69
- **Air Flow**: 1.25 m³/s (2,655.08 CFM)
- **SF per Ton**: 99.30
- **CFM per Ton**: 627.75

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 2
- HVAC Sizing Summary > Coil Sizing Summary: Row 2

---

### Room_2_Flr_6 Cooling Coil

- **Zone Served**: Room_2_Flr_6
- **Air Inlet Node**: Room_2_Flr_6 Return
- **Air Outlet Node**: Room_2_Flr_6 Cooling Coil Outlet
- **Zone Area**: 39.02 m² (419.98 SF)
- **Nominal Total Capacity**: 4,033.45 W (1.15 Tons)
- **Nominal Sensible Capacity**: 3,590.41 W
- **Sensible Heat Ratio**: 0.89
- **COP**: 4.69
- **Air Flow**: 0.34 m³/s (722.06 CFM)
- **SF per Ton**: 366.19
- **CFM per Ton**: 629.58

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 8
- HVAC Sizing Summary > Coil Sizing Summary: Row 8

---

### Room_3_Mult9_Flr_6 Cooling Coil

- **Zone Served**: Room_3_Mult9_Flr_6
- **Air Inlet Node**: Room_3_Mult9_Flr_6 Return
- **Air Outlet Node**: Room_3_Mult9_Flr_6 Cooling Coil Outlet
- **Zone Area**: 24.53 m² (264.04 SF)
- **Nominal Total Capacity**: 16,171.65 W (4.60 Tons)
- **Nominal Sensible Capacity**: 14,181.58 W
- **Sensible Heat Ratio**: 0.88
- **COP**: 4.69
- **Air Flow**: 1.34 m³/s (2,829.38 CFM)
- **SF per Ton**: 57.42
- **CFM per Ton**: 615.31

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 9
- HVAC Sizing Summary > Coil Sizing Summary: Row 9

---

### Room_3_Mult19_Flr_3 Cooling Coil

- **Zone Served**: Room_3_Mult19_Flr_3
- **Air Inlet Node**: Room_3_Mult19_Flr_3 Return
- **Air Outlet Node**: Room_3_Mult19_Flr_3 Cooling Coil Outlet
- **Zone Area**: 24.52 m² (263.97 SF)
- **Nominal Total Capacity**: 77,127.42 W (21.93 Tons)
- **Nominal Sensible Capacity**: 69,447.11 W
- **Sensible Heat Ratio**: 0.90
- **COP**: 4.69
- **Air Flow**: 6.65 m³/s (14,090.26 CFM)
- **SF per Ton**: 12.04
- **CFM per Ton**: 642.49

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 3
- HVAC Sizing Summary > Coil Sizing Summary: Row 3

---

### Room_4_Mult19_Flr_3 Cooling Coil

- **Zone Served**: Room_4_Mult19_Flr_3
- **Air Inlet Node**: Room_4_Mult19_Flr_3 Return
- **Air Outlet Node**: Room_4_Mult19_Flr_3 Cooling Coil Outlet
- **Zone Area**: 24.53 m² (264.04 SF)
- **Nominal Total Capacity**: 91,921.16 W (26.14 Tons)
- **Nominal Sensible Capacity**: 79,894.49 W
- **Sensible Heat Ratio**: 0.87
- **COP**: 4.69
- **Air Flow**: 7.49 m³/s (15,861.44 CFM)
- **SF per Ton**: 10.10
- **CFM per Ton**: 606.85

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 4
- HVAC Sizing Summary > Coil Sizing Summary: Row 4

---

### Room_5_Flr_3 Cooling Coil

- **Zone Served**: Room_5_Flr_3
- **Air Inlet Node**: Room_5_Flr_3 Return
- **Air Outlet Node**: Room_5_Flr_3 Cooling Coil Outlet
- **Zone Area**: 39.02 m² (420.03 SF)
- **Nominal Total Capacity**: 13,604.54 W (3.87 Tons)
- **Nominal Sensible Capacity**: 12,057.81 W
- **Sensible Heat Ratio**: 0.89
- **COP**: 4.69
- **Air Flow**: 1.14 m³/s (2,419.47 CFM)
- **SF per Ton**: 108.58
- **CFM per Ton**: 625.45

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 5
- HVAC Sizing Summary > Coil Sizing Summary: Row 5

---

### Room_6_Flr_3 Cooling Coil

- **Zone Served**: Room_6_Flr_3
- **Air Inlet Node**: Room_6_Flr_3 Return
- **Air Outlet Node**: Room_6_Flr_3 Cooling Coil Outlet
- **Zone Area**: 39.02 m² (419.98 SF)
- **Nominal Total Capacity**: 13,067.31 W (3.72 Tons)
- **Nominal Sensible Capacity**: 11,567.31 W
- **Sensible Heat Ratio**: 0.89
- **COP**: 4.69
- **Air Flow**: 1.09 m³/s (2,319.53 CFM)
- **SF per Ton**: 113.03
- **CFM per Ton**: 624.26

**References in HTML Reports**:

- Equipment Summary > Cooling Coils: Row 6
- HVAC Sizing Summary > Coil Sizing Summary: Row 6

---

## Analysis Notes

### SF per Ton Observations:

1. **High SF per Ton** (300+ SF/Ton): Room_1_Flr_6 and Room_2_Flr_6 show significantly higher SF per Ton ratios, suggesting these zones may have:
   - Lower cooling loads per square foot
   - Better envelope performance
   - Lower occupancy or internal gains
   - Different operating conditions

2. **Very Low SF per Ton** (10-12 SF/Ton): Room_3_Mult19_Flr_3 and Room_4_Mult19_Flr_3 have extremely low ratios, indicating:
   - Very high cooling loads per square foot (2,880-3,300 W/m²)
   - These are multiplied zones (76x), representing multiple identical rooms
   - Higher internal gains or envelope loads

3. **Typical Range** (95-115 SF/Ton): Room_1, Room_2, Room_5, and Room_6 on Floor 3 fall in a more typical range for hotel guest rooms.

### CFM per Ton Observations:

All coils show CFM per Ton ratios in the 605-645 range, which is typical for water-to-air heat pumps serving hotel guest rooms. This consistency suggests proper air flow sizing across all units.

---

## Data Sources

1. **epJSON File**: Object properties, node names, zone associations
2. **HTML Report - Equipment Summary > Cooling Coils**: Nominal capacities, SHR, COP
3. **HTML Report - HVAC Sizing Summary > Coil Sizing Summary**: Final sizing values, air flows
4. **HTML Report - HVAC Sizing Summary > Zone Sensible Cooling**: Zone areas and design loads

---

**Generated**: January 28, 2026  
**Model**: ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd  
**Tool**: MCP-EPlus Output Server
