# RTA Asset Management - Testing Guide

This guide explains how to test the Master Priority Output implementation, which calculates ACI, factors (CF, RF, FLF), and Priority Factor (PF), then aggregates all assets into a sorted Excel file.

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Unit Tests](#1-unit-tests)
3. [Running the Master Generator](#2-running-the-master-generator)
4. [Programmatic Testing](#3-programmatic-testing-with-custom-input)
5. [End-to-End Testing](#4-full-end-to-end-test)
6. [Output Verification Checklist](#5-output-verification-checklist)
7. [Quick Reference Commands](#quick-reference-commands)

---

## Testing Overview

The testing workflow validates:

1. **User Input** → Asset data from Excel files
2. **ACI Calculation** → Asset Condition Index (0-100)
3. **Factor Calculations**:
   - CF (Condition Factor) from ACI
   - RF (Risk Factor) from asset type
   - FLF (Functional Life Factor) from deterioration curves
4. **PF Calculation** → `PF = 0.6*CF + 0.2*RF + 0.2*FLF`
5. **Sorting** → By PF descending, then ACI ascending
6. **Aggregation** → All assets consolidated into `Master_Priority_Output.xlsx`

---

## 1. Unit Tests

The project includes pytest-based unit tests for each component.

### Running All Tests

```bash
cd rta-asset-management
pytest tests/ -v
```

### Running Specific Test Modules

```bash
# Test ACI calculation
pytest tests/test_aci.py -v

# Test Condition Factor
pytest tests/test_cf.py -v

# Test Risk Factor
pytest tests/test_rf.py -v

# Test Functional Life Factor
pytest tests/test_flf.py -v

# Test Priority Factor aggregation
pytest tests/test_pf.py -v
```

### Test Output

Tests automatically generate an Excel report in the project root:
- `test_report_YYYY-MM-DD_HHMMSS.xlsx`

---

## 2. Running the Master Generator

The main script `scripts/generate_master_priority.py` performs the complete workflow.

### Auto-Discovery Mode

Finds all `.xlsx` files in the parent directory:

```bash
cd rta-asset-management
python scripts/generate_master_priority.py
```

### Explicit Files Mode

Specify input files directly:

```bash
python scripts/generate_master_priority.py "path/to/file1.xlsx" "path/to/file2.xlsx"
```

### Custom Output Path

```bash
python scripts/generate_master_priority.py --output ./MyOutput.xlsx
```

### Full Example

```bash
python scripts/generate_master_priority.py ^
    "../RoW Assets_ACI Sheet_20-05-2025.xlsx" ^
    "../MASTER_EXCEL_E11.xlsx" ^
    "../1. Calculations for Priority Index.xlsx" ^
    --output "../Master_Priority_Output.xlsx"
```

---

## 3. Programmatic Testing with Custom Input

For testing specific asset calculations interactively:

```python
# test_workflow.py
import sys
sys.path.insert(0, 'rta-asset-management')

from domain.pf.aggregator import calculate_pf, calculate_pf_batch
from domain.aci import calculate_aci
from domain.models import DefectInput

# 1. Define test assets (asset_type, aci)
test_assets = [
    ("MANHOLE", 75),
    ("TRAFFIC_SIGNAL", 45),
    ("GUARDRAIL", 20),
    ("GANTRY", 90),
]

# 2. Calculate PF for each
print("=" * 60)
print("PF Calculation Results (sorted by PF descending)")
print("=" * 60)

results = []
for asset_type, aci in test_assets:
    pf_result = calculate_pf(asset_type, aci)
    results.append((asset_type, aci, pf_result))

# 3. Sort by PF descending
results.sort(key=lambda x: x[2].pf, reverse=True)

# 4. Display ranked output
print(f"{'Rank':<6}{'Asset Type':<20}{'ACI':<8}{'CF':<10}{'RF':<10}{'FLF':<10}{'PF':<10}")
print("-" * 74)
for rank, (asset_type, aci, r) in enumerate(results, 1):
    print(f"{rank:<6}{asset_type:<20}{aci:<8}{r.cf:<10.2f}{r.rf:<10.2f}{r.flf:<10.2f}{r.pf:<10.2f}")
```

### Expected Output

```
============================================================
PF Calculation Results (sorted by PF descending)
============================================================
Rank  Asset Type          ACI     CF        RF        FLF       PF        
--------------------------------------------------------------------------
1     GUARDRAIL           20      75.00     46.84     85.00     62.87     
2     TRAFFIC_SIGNAL      45      43.75     100.00    55.00     62.88     
3     MANHOLE             75      6.25      36.84     12.50     16.69     
4     GANTRY              90      0.00      73.68     0.00      22.11     
```

---

## 4. Full End-to-End Test

Generate the complete master Excel output:

```python
# test_e2e_master.py
from pathlib import Path
import sys
sys.path.insert(0, 'rta-asset-management')

from scripts.generate_master_priority import generate_master_priority

# Configure paths
input_dir = Path("c:/Users/User/Downloads/ECIL Summer 2026/application dev")
output_path = input_dir / "TEST_Master_Priority_Output.xlsx"

# Generate the master output
result_path = generate_master_priority(input_dir, output_path)

print(f"\nOutput generated: {result_path}")
print("Open the file to verify:")
print("  - Sheet 1: Priority Ranking (sorted by PF desc, then ACI asc)")
print("  - Sheet 2: Summary Statistics (formulas, not hardcoded)")
print("  - Sheet 3: Source Mapping (which files contributed)")
```

---

## 5. Output Verification Checklist

When you open `Master_Priority_Output.xlsx`, verify:

### Sheet 1: Priority Ranking

| Check | Description |
|-------|-------------|
| OK | Rows sorted by PF (highest priority first) |
| OK | Secondary sort by ACI ascending (worst condition first) |
| OK | Rank column uses formula `=ROW()-1` (not hardcoded) |
| OK | Conditional formatting on PF column (red = high, green = low) |
| OK | Conditional formatting on ACI column (red = low/poor, green = high/good) |
| OK | Header row frozen with filter arrows |
| OK | Factor columns (ACI, CF, FLF, RF, PF) formatted to 2 decimal places |
| OK | `PF_Computed` column shows `TRUE` for computed values |

### Sheet 2: Summary Statistics

| Check | Description |
|-------|-------------|
| OK | Factor statistics use Excel formulas (AVERAGE, MIN, MAX, MEDIAN) |
| OK | Asset count by type uses COUNTIF formulas |
| OK | Priority bands calculated from PERCENTILE formulas |
| OK | Top 10 assets reference Sheet 1 data |

### Sheet 3: Source Mapping

| Check | Description |
|-------|-------------|
| OK | Lists all source files processed |
| OK | Shows row count per source file |
| OK | Displays generation timestamp |

---

## Quick Reference Commands

```bash
# Navigate to project
cd "c:\Users\User\Downloads\ECIL Summer 2026\application dev\rta-asset-management"

# Run unit tests
pytest tests/ -v

# Run unit tests with coverage
pytest tests/ -v --cov=domain

# Generate master output (auto-discover files)
python scripts/generate_master_priority.py

# Generate master output with specific files
python scripts/generate_master_priority.py "../file1.xlsx" "../file2.xlsx" --output ../output.xlsx

# Run as module
python -m scripts.generate_master_priority
```

---

## Troubleshooting

### Common Issues

1. **"No .xlsx files found"**
   - Ensure input files are in the parent directory
   - Or specify files explicitly with full paths

2. **"No RF score found for asset type"**
   - The asset type key doesn't match lookup tables
   - Check `domain/lookups/` for valid asset type keys

3. **PF values missing**
   - Requires ACI + asset type to compute CF/RF/FLF
   - If source file has pre-computed PF, it's used directly

4. **Module import errors**
   - Run from `rta-asset-management` directory
   - Or add to Python path: `sys.path.insert(0, 'rta-asset-management')`

---

## File Structure

```
rta-asset-management/
├── domain/
│   ├── aci/           # ACI calculators
│   ├── pf/
│   │   ├── aggregator.py   # PF = CF*0.6 + RF*0.2 + FLF*0.2
│   │   ├── cf.py           # Condition Factor
│   │   ├── rf.py           # Risk Factor
│   │   └── flf.py          # Functional Life Factor
│   ├── lookups/       # RF scores, FLF curves
│   └── models.py      # Data models
├── scripts/
│   └── generate_master_priority.py   # Main generator
├── tests/
│   ├── test_aci.py
│   ├── test_cf.py
│   ├── test_rf.py
│   ├── test_flf.py
│   └── test_pf.py
└── TESTING_GUIDE.md   # This file
```

---

*Generated for RTA Asset Management System*
