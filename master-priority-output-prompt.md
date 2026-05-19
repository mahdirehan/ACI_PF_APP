
You are an infrastructure asset management engineer. I have multiple Excel input files, where the factor equations are already implemented and validated.

### CONTEXT

In a typical infrastructure asset management workflow, **each asset type lives in its own separate Excel file** — e.g., one file for road signs, another for road markings, another for footpath, another for barrier, etc. Each file contains the full inventory and condition/priority calculations for that asset type. **The core task here is to pull every asset from all of these separate files and combine them into a single master Excel file, ranked from highest Priority Factor (PF) to lowest PF**, so decision-makers can see the unified priority picture across all asset types in one place.

### YOUR TASK

Build a Python script (using openpyxl) that:

1. **Reads every input Excel file** from the uploaded files. Each file typically represents a different asset type (road sign, road marking, barrier, guardrails, etc.). Auto-detect which sheets contain asset data (look for column headers matching Asset ID, ACI, CF, FLF, RF, PF, and all other relevant column fields).

2. **Extracts all relevant fields per asset row**, including but not limited to:
   - Asset ID / Element ID
   - Asset Type / Category (infer from source filename or a column in the sheet if no explicit type column exists)
   - Location / Road Name / Chainage / Coordinates (whatever location fields exist)
   - Description / Component Name
   - Inspection Date (if present)
   - ACI value
   - CF value
   - FLF value
   - RF value
   - PF value
   - Any other metadata columns that exist — capture everything.

3. **Consolidates all assets into a single master DataFrame** with a unified schema. Since each source file may use slightly different column names for the same concept, normalize them to a single consistent name. Add a `Source_File` column tracking which input file each row came from.

4. **Sorts the entire dataset by PF descending** (highest priority first). Secondary sort by ACI ascending (worst condition first) as tiebreaker.

5. **Generates a professionally formatted .xlsx output** named `Master_Priority_Output.xlsx` with:

   **Sheet 1 — "Priority Ranking"** (the main deliverable):
   - Frozen header row with filter arrows on every column
   - Column order: Rank (1, 2, 3...), Asset ID, Asset Type, Location fields, Description, ACI, CF, FLF, RF, PF, then remaining metadata columns
   - **Conditional formatting on PF column**: Red gradient fill for high PF values, green for low (3-color scale: green → yellow → red)
   - **Conditional formatting on ACI column**: Red for low ACI (poor condition), green for high ACI (good condition) — inverse of PF
   - Number formatting: all factor columns to 2 decimal places
   - Auto-fit column widths (cap at 40 characters)
   - Professional font (Arial 10pt), bold headers with dark gray fill and white text
   - Alternating row shading (light gray / white) for readability
   - Rank column uses `=ROW()-1` formula (dynamic, not hardcoded)

   **Sheet 2 — "Summary Statistics"**:
   - Total asset count, count per asset type
   - Average, Min, Max, Median for each factor (ACI, CF, FLF, RF, PF) — use Excel formulas referencing Sheet 1, not hardcoded Python values
   - Count of assets per priority band:
     - Critical (PF ≥ X — determine threshold from the data or use top 10%)
     - High (top 10-25%)
     - Medium (25-50%)
     - Low (bottom 50%)
   - A small table showing top 10 highest-priority assets (Asset ID, Type, Location, PF)

   **Sheet 3 — "Source Mapping"**:
   - Table showing which source file each asset type came from
   - Row counts per source file
   - Date of generation

6. **After saving, run formula recalculation** using `python scripts/recalc.py Master_Priority_Output.xlsx` and verify zero errors.

### CRITICAL REQUIREMENTS

- Do NOT hardcode computed values. Use Excel formulas for Summary Statistics (SUM, AVERAGE, MIN, MAX, MEDIAN, COUNTIF, RANK).
- If a source file has columns the others don't, still include them — just leave cells blank for assets from other files.
- Handle edge cases: empty rows, merged cells in source files, header rows not on row 1, numeric values stored as text.
- If PF is not pre-computed in a source file but ACI/CF/FLF/RF are present, compute PF using the formula from the OAMP framework (flag these rows with a note).
- Print a processing summary to console: files processed, rows per file, total rows, any warnings.

### OUTPUT

Single file: `Master_Priority_Output.xlsx` saved to `/mnt/user-data/outputs/`

### INPUT FILES

The Excel files are @1. Calculations for Priority Index.xlsx, MASTER_EXCEL_E11.xlsx, and RoW Assets_ACI Sheet_20-05-2025.xlsx


