# EnergyPlus Output Analysis Summary

## Model Information

- **epJSON File**: `ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd.epJSON`
- **SQL Database**: `ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd.sql`
- **HTML Report**: `ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd.table.htm`
- **Location**: `eplus_files\diff_filenames\`

---

## Component Sizing Summary

The model contains extensive component sizing data for a Large Hotel building with GSHP (Ground Source Heat Pump) system in Buffalo, NY (2025 ASHRAE 901 Standard).

### Key Building Systems:

#### 1. **DOAS (Dedicated Outdoor Air Systems)**

- **GRM_DOAS**: 2.05 m³/s supply air flow
- **PUB_DOAS**: 6.24 m³/s supply air flow

#### 2. **Packaged Single Zone (PSZ) Systems**

Multiple PSZ systems serving different zones:

- PSZ_BASEMENT: 2.47 m³/s
- PSZ_LAUNDRY_FLR_1: 3.84 m³/s
- PSZ_LOBBY_FLR_1: 5.43 m³/s (largest)
- PSZ_CORRIDOR_FLR_3: 1.57 m³/s
- PSZ_CORRIDOR_FLR_6: 0.851438 m³/s
- And 10 additional PSZ systems for various zones

#### 3. **VRF (Variable Refrigerant Flow) Systems**

Room-level VRF units for guest rooms:

- ROOM_1_FLR_3 through ROOM_6_FLR_3
- ROOM_1_FLR_6 through ROOM_3_MULT9_FLR_6
- Typical cooling coil capacity: 13-15 kW for single rooms
- Multiplied rooms (MULT19/MULT9): 77-92 kW

#### 4. **Major Equipment Sizing**

**Cooling Coils (Sample)**:
| Component | Air Flow (m³/s) | Total Cooling (W) | Sensible Cooling (W) | Water Flow (m³/s) |
|-----------|-----------------|-------------------|----------------------|-------------------|
| PSZ_LOBBY_FLR_1 | 5.43 | 139,357 | 97,005 | - |
| PSZ_LAUNDRY_FLR_1 | 3.84 | 61,061 | 46,534 | - |
| PSZ_BASEMENT | 2.47 | 56,112 | 41,207 | - |
| ROOM_4_MULT19_FLR_3 | 7.49 | 91,921 | 79,894 | 0.004204 |

**Heating Coils (Sample)**:
| Component | Air Flow (m³/s) | Heating Capacity (W) | Water Flow (m³/s) |
|-----------|-----------------|----------------------|-------------------|
| PSZ_LOBBY_FLR_1 | 5.43 | 123,012 | - |
| PSZ_LAUNDRY_FLR_1 | 3.84 | 55,169 | - |
| ROOM_4_MULT19_FLR_3 | 7.49 | 87,045 | 0.004204 |

**Supplemental Electric Heat Coils**:

- Largest: PSZ_LOBBY_FLR_1_SUPPHEATCOIL - 123,012 W
- Various room-level units: 2,933 - 14,821 W
- PSZ units: 3,599 - 84,177 W

#### 5. **Plant Loops**

**Service Water Heating System (SWHSYS1)**:

- Maximum Loop Flow Rate: 0.000375 m³/s
- Plant Loop Volume: 0.045004 m³
- Design Supply Temperature: 60°C
- Design Return Temperature: 55°C
- Pump Power: 47.91 W

**Condenser Loop (GSHP System)**:

- Maximum Loop Flow Rate: 0.036859 m³/s
- Condenser Loop Volume: 4.42 m³
- Design Supply Temperature: 15°C
- Design Return Temperature: 10°C
- Circulation Pump: 12,511 W
- Ground Loop Design Flow: 0.036859 m³/s

#### 6. **Fans**

- GRM_DOAS FAN: 2.05 m³/s
- PUB_DOAS FAN: 6.24 m³/s
- Various PSZ fans with electric power consumption ranging from 135 W to 6,497 W
- VRF terminal fans sized to match cooling coil airflow

#### 7. **Air Terminals**

Multiple direct air terminals and DOAS air terminals for all served zones, with flow rates matching zone requirements.

#### 8. **Outdoor Air Controllers**

- DOAS systems: Fixed outdoor air rates (2.05 m³/s and 6.24 m³/s)
- PSZ systems: Various outdoor air rates based on zone requirements
- One system (PSZ_NOTSPR_KITCHEN_FLR_6) has minimum OA: 0.367350 m³/s

---

## Hourly Reports in SQL Database

The SQL database contains **4 hourly report variables**:

1. **Electricity:Facility**
   - Number of instances: 1
   - Key: None (facility-level)
   - Tracks total facility electricity consumption

2. **ElectricityNet:Facility**
   - Number of instances: 1
   - Key: None (facility-level)
   - Tracks net facility electricity (includes any generation)

3. **NaturalGas:Facility**
   - Number of instances: 1
   - Key: None (facility-level)
   - Tracks total facility natural gas consumption

4. **Site Day Type Index**
   - Number of instances: 1
   - Key: Environment
   - Indicates the day type (weekday, weekend, holiday, etc.)

### Available Database Tables:

The SQL database contains the following tables for analysis:

- **Simulations**: Simulation metadata
- **EnvironmentPeriods**: Run period information
- **Time**: Timestamp data
- **Zones**: Zone definitions
- **ReportData/ReportDataDictionary**: Time-series data and variable definitions
- **ComponentSizes**: Autosized component data
- **SystemSizes/ZoneSizes**: HVAC system and zone sizing results
- **Surfaces**: Building envelope data
- **Nominal Equipment**: Lighting, people, equipment loads
- **TabularData**: Summary reports and tables

---

## Notes

1. This is a **design day simulation** (indicated by `.dd` suffix), not a full annual run
2. The facility uses a **ground source heat pump (GSHP)** system as indicated by filename
3. Building type: **Large Hotel** per ASHRAE 901-2025 Standard
4. Location: **Buffalo, NY** (cold climate)
5. Most energy data shows 0.00 because this is sizing-only simulation
6. The simulation includes both:
   - Central DOAS systems for ventilation
   - Distributed PSZ and VRF systems for heating/cooling

---

## Summary Statistics

- **Total Air Systems**: 16 PSZ systems + 2 DOAS systems + 9 VRF terminal units
- **Largest Air System**: PSZ_LOBBY_FLR_1 (5.43 m³/s, 139.4 kW cooling, 123.0 kW heating)
- **Total Zones Served**: 30+ zones across 6 floors plus basement
- **Primary Heating**: Electric resistance supplemental heat + GSHP
- **Primary Cooling**: DX cooling coils + GSHP
- **Ventilation**: Dedicated outdoor air systems with heat recovery
