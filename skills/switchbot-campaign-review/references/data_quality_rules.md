# Data Quality Rules

## Inventory first

List every supported file, workbook sheet, Markdown table, JSON table, and PDF page/table. Record source path, sheet or table name, row count, columns, date range, and read errors.

## Required checks

- Missing values in identifiers, dates, and base KPI fields
- Exact duplicate rows and suspected business duplicates
- Total or subtotal rows mixed with detail
- Invalid or mixed date formats
- Currency, tax, agency-fee, or attribution conflicts
- Explicit percentages mixed with decimals
- Cumulative values mixed with daily values
- Inconsistent channel, campaign, and product names
- Product values not exactly resolved through Product Knowledge
- Product aliases that map to multiple entities
- Missing or Critical Product Knowledge index when a product dimension is populated
- Formula error strings
- Different campaign durations or conversion definitions
- Current and comparison scope mismatches
- Unmapped fields and unsupported nested structures

## Repair policy

- Preserve source files and original values.
- Remove only exact duplicates automatically.
- Exclude clearly labeled totals from detail calculations and retain them in the audit.
- Normalize explicit values such as `2.5%` to `0.025`.
- Normalize numeric percentage columns only when the header and all non-null values make the scale unambiguous; otherwise flag for confirmation.
- Parse dates and numerics conservatively; retain failed values and report them.
- Never apply FX conversion without user-supplied rates and effective dates.
- Never silently ignore unmapped fields.

## Issue classification

Assign one repair class: `Auto-fixed`, `Needs confirmation`, `No material impact`, or `Material impact`. Assign severity `Info`, `Warning`, or `Critical`. Explain the affected conclusion and the action taken.
