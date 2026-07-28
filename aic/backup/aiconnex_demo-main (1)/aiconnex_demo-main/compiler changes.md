# Compiler Changes Required for Multi-Sensor & Multi-Device Datasets

## Problem Statement

The current AIConnex ZIP Compiler (`aiconnex_zip_compiler/`) handles **relational datasets** well (e.g., Solar: Generation CSV + Weather CSV joined on `PLANT_ID + DATE_TIME`). But it **fails** on datasets like NASA IGBT where:

1. **Multiple single-column CSV files** represent different sensors from the **same test run** (same row count, no shared timestamp column header — just aligned by row index).
2. **Multiple device folders** (Device 2, Device 3, Device 4, Device 5) contain the **same schema** and need to be **stacked vertically** with a `device_id` column.

The compiler currently dumps all 59 files into one `"default"` group, picks the largest file, and skips everything else. Result: a single-column CSV (`collector_current` only) instead of a rich multi-sensor, multi-device dataset.

---

## Root Cause Analysis (3 Gaps)

### Gap 1: No Index-Based Join (Row-Aligned Sensor Merging)
**Where**: [relational_joiner.py](file:///X:/TAS/AICONNEX/aiconnex_zip_compiler/relational_joiner.py) (Lines 70–121)

**Current behavior**: The joiner ONLY merges tables using explicit column-name-based keys (`date_time`, `plant_id`). If a dimension table doesn't have a matching key column, it gets skipped with a warning.

**What's missing**: When multiple CSV files from the **same parent folder** have the **exact same row count** and each contain a single numeric column, they are clearly **parallel sensor signals recorded at the same timestamps**. They should be joined **by row index** (column-concatenation), not by column-name keys.

**Example**: In `Thermal Overstress Aging with DC at gate/`:
- `COLLECTOR_CURRENT.csv` → 301,680 rows × 1 col
- `COLLECTOR_VOLTAGE.csv` → 301,680 rows × 1 col  
- `GATE_VOLTAGE.csv` → 301,680 rows × 1 col
- `GATE_CURRENT.csv` → 301,680 rows × 1 col
- `PACKAGE_TEMP.csv` → 301,680 rows × 1 col
- `HEAT_SINK_TEMP.csv` → 301,680 rows × 1 col
- `TIME.csv` → 301,680 rows × 1 col

All 7 files have identical row counts → **index-join them side-by-side into 1 table (301,680 × 7)**.

---

### Gap 2: No Folder-Aware Grouping (Directory = Entity Group)
**Where**: [discovery.py](file:///X:/TAS/AICONNEX/aiconnex_zip_compiler/discovery.py) (Lines 189–204)

**Current behavior**: Grouping is based on a detected `primary_group_col` value inside the CSV data. If no entity column is found, ALL files go into a single `"default"` group — regardless of which subfolder they came from.

**What's missing**: The directory hierarchy itself carries semantic meaning:
- `Device 2/` → all files inside belong to Device 2
- `Device 3/` → all files inside belong to Device 3
- `Thermal Overstress Aging with DC at gate/` → one experiment track
- `Thermal Overstress Aging with Square Signal at gate/` → another experiment track

When CSV files lack an explicit entity column, the compiler should **use the parent folder name as the group ID**.

---

### Gap 3: No Vertical Stacking (Multi-Entity Concat)
**Where**: [compiler.py](file:///X:/TAS/AICONNEX/aiconnex_zip_compiler/compiler.py) (Lines 68–123) and [handoff.py](file:///X:/TAS/AICONNEX/aiconnex_zip_compiler/handoff.py)

**Current behavior**: Each group produces its own `group_{id}_merged.csv`. Groups are never combined vertically.

**What's missing**: When multiple groups share the **same column schema** (same column names/types), they should be **vertically stacked (concatenated)** into one combined dataset with an added `group_id` / `device_id` column. This is essential for multi-entity ML tasks like RUL prediction across devices.

**Example**: After Gap 2 groups files by folder:
- Group `device_2` → `Device2  1.csv` (3 cols: transient, steadyState, report)
- Group `device_3` → `Device3  1.csv` (3 cols: transient, steadyState, report)
- Group `device_4` → `Device4  1.csv` (3 cols: transient, steadyState, report)
- Group `device_5` → `Device5  1.csv` (3 cols: transient, steadyState, report)

Since all 4 groups share the same schema → **stack them vertically into 1 table with a `device_id` column**.

---

## Proposed Changes Summary

| # | File to Change | Change Description |
|---|---|---|
| **1** | [discovery.py](file:///X:/TAS/AICONNEX/aiconnex_zip_compiler/discovery.py) | Add **folder-aware grouping** fallback: when no entity column is detected, use `parent_folder_name` as the group ID instead of dumping everything into `"default"`. |
| **2** | [relational_joiner.py](file:///X:/TAS/AICONNEX/aiconnex_zip_compiler/relational_joiner.py) | Add **index-based join** rule: before attempting key-based merges, check if multiple single-column CSVs in the same group share the exact same `row_count`. If yes, `pd.concat([...], axis=1)` them by row index. |
| **3** | [compiler.py](file:///X:/TAS/AICONNEX/aiconnex_zip_compiler/compiler.py) | Add **vertical stacking** step after Layer 3: after all groups are merged individually, detect groups with matching column schemas and `pd.concat([...], axis=0)` them with an added `group_id` column. |
| **4** | [handoff.py](file:///X:/TAS/AICONNEX/aiconnex_zip_compiler/handoff.py) | Update handoff export to emit the vertically-stacked combined CSV alongside per-group CSVs. |

---

## Verification Plan

### Test Case 1: IGBT Dataset (Index Join + Folder Grouping + Vertical Stack)
- **Input**: `IGBTAgingData_04022009.zip`
- **Expected Output**:
  - `group_dc_gate_merged.csv`: 301,680 rows × 7 columns (all sensors from `20080429T135531` index-joined)
  - `group_device_2_merged.csv`, `group_device_3_merged.csv`, etc.: Per-device aging data
  - `all_devices_combined.csv`: Vertical stack of Device 2–5 with `device_id` column

### Test Case 2: Solar Dataset (Existing Key-Based Join — Regression Test)
- **Input**: Solar Power Generation ZIP
- **Expected Output**: Same as before (no regression). Generation + Weather joined on `PLANT_ID + DATE_TIME`.

### Test Case 3: Algae Dataset (Mixed — Folder Grouping)
- **Input**: Algae Raceway ZIP (if zipped with per-raceway CSVs)
- **Expected Output**: Per-raceway CSVs grouped by folder, vertically stacked with `raceway_id`.
