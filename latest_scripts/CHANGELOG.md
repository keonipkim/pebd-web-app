# Changelog

All notable changes to this project are documented here.

### [generate_pebd_statistics] - 2025-03-01

#### Added
- Detailed PEBD validation statistics generation in `generate_pebd_statistics.py`
- Asymmetric threshold support: separate configurable windows for positive (+ days) and negative (- days) differences
  - `PEBD_THRESHOLD_PLUS` and `PEBD_THRESHOLD_MINUS` (default ±3 days)
- Toggle `IGNORE_THRESHOLD` to bypass threshold checks (useful for full difference analysis or debugging)
- Human-readable, well-aligned report in `reports/statistics.txt`:
  - Fixed-width summary section with right-aligned numbers
  - Clean year-by-year breakdown table with proper column alignment and separator line
- Detailed mismatch export to `reports/pebd_stats_mismatch_tbl.csv`:
  - Only mismatched records (or all when threshold ignored)
  - Sorted by largest absolute difference
  - Added formatted date columns (`Reported PEBD`, `Calculated PEBD`) for easy comparison
- Robust handling of datetime parsing with `errors='coerce'` and NaT row dropping

#### Improved
- Fixed float/int type issues in pandas aggregation → explicit `.astype(int)` for count/sum columns
- Consistent right-aligned formatting for large numbers (with commas) in text output
- Added mode indicators in output files when threshold is ignored

#### Fixed
- ValueError in text report formatting caused by float counts (now safely cast to int)

This completes the core PEBD match/mismatch validation and reporting pipeline.


## [generate_pebd_statistics.py] – 2026-02-28

### Added
- Script to calculate statistics summary CSV:
  - Implemented `generate_pebd_statistics.py` to process multiple EDIPIs and generate detailed reports.
  - Included breakdown by reported PEBD year and excluded specific columns from the output.

### Known limitations (addressed in future versions)
- The script currently handles only basic data processing and reporting.
- Further enhancements may be required for more complex scenarios or performance optimizations.


## [v2026.2] – 2026-02-23

### Changed
- Updated `v2026.2_compute_creditable_service_reports.py` to accept an optional EDIPI argument from the command line, allowing either a single-target run or a full report when no EDIPI is provided. [web:125][web:131]
- Removed the previous limit of 500 EDIPIs when generating per-person text reports so that all matching EDIPIs now produce a `statement_of_service_*.txt` file. [web:124][web:126]

### Added
- Introduced a local Python 3.12 virtual environment (`.venv312`) on macOS for performance and stability, and configured Git to ignore this directory in version control. [web:79][web:82]

### Fixed
- Cleaned up Git repository layout so only the intended `latest_scripts` project directory is tracked, avoiding accidental Git initialization at higher-level folders. [web:130][web:134]

## [v2026.2] – 2026-02-22

### Added
- Implemented DODFMR 30/360 creditable‑service logic:
  - Added `compute_segment_days_30` with 30‑day‑month normalization for 31st and February end dates.[cite:27]
  - Used `total_creditable_days` (30/360 basis) as the driver for calculated PEBD.[cite:27]

- Introduced explicit as‑of and PRESENT handling:
  - Added `as_of` and `segment_30_with_present` to properly count open‑ended (PRESENT) segments.[cite:27][cite:30]
  - Standardized inclusive/exclusive as‑of behavior to reduce systematic +1/‑1 day PEBD differences.[cite:11][cite:12]

- Expanded lost‑time support:
  - Defined `lost_reasons` set (`UA/DES`, `CNFD`, `EXPECC`, `IHFA`, `IHCA`).[cite:41][cite:32]
  - Added `lost_time_days` and updated net calculations so Total Lost Time subtracts from Gross Creditable Service and is shown in report footers.[cite:32][cite:25]

### Changed
- Improved segment merge and per‑EDIPI aggregation:
  - Added `merge_creditable_segments` to collapse overlapping/back‑to‑back creditable spans per EDIPI, avoiding double‑counting.[cite:36][cite:28]
  - Kept non‑creditable rows (e.g., lost time) separate so they still print and contribute to lost‑time totals.[cite:28]

- Refined DEP and open‑ended period handling:
  - Excluded DEP from creditable service and omitted DEP rows from text reports.[cite:37][cite:38]
  - Preserved open‑ended ACT REG/RES periods and ensured they are counted and printed as PRESENT.[cite:38]

- Reporting behavior:
  - Continued to generate `output_detail.csv`, `output_summary.csv`, and per‑EDIPI Statement of Service `.txt` files with PEBD comparison and DODFMR footer.[cite:26][cite:30]
  - Limited text report generation to the first 500 EDIPIs to keep runtime manageable for large D188 inputs.[cite:35][cite:26]

### Fixed
- Resolved NaT/NaN and formatting issues:
  - Made merge logic NaT‑safe and avoided dropping open‑ended (PRESENT) rows while still preventing invalid date comparisons.[cite:37][cite:38]
  - Guarded casts of `segment_days_30` when printing, treating NaN as 0 instead of raising errors.[cite:39]

- Cleaned up indentation and function placement:
  - Corrected indentation for `segment_30_with_present`, merge, and reporting loops so they live inside `main()` with consistent structure.[cite:29][cite:31][cite:40]
  - Eliminated prior IndentationError and SyntaxError issues around the segment and lost‑time blocks.[cite:34][cite:40]

---

## [v2026.1] – 2026-02-21

### Added
- Initial PEBD audit pipeline for D188 extracts:
  - Loaded D188 data, parsed key date columns, and computed basic segment day counts.[cite:33]
  - Produced `output_detail.csv`, `output_summary.csv`, and per‑EDIPI Statement of Service `.txt` reports.[cite:33][cite:36]

### Known limitations (addressed in v2026.2)
- Used simple calendar‑day math instead of full DODFMR 30/360 normalization.[cite:33]
- Did not robustly handle PRESENT end dates or overlapping ACT service segments.[cite:36]
- Lost‑time logic was incomplete, with some Reason Cds not contributing to `TmLost` or net creditable days.[cite:41]
