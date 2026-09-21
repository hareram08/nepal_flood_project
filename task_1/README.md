# Task 1 — Nepal flood ETL and report

ETL for the **August 2026 Nepal-Tibet (Lhende / Bhotekoshi-Trishuli) flash flood**.

```
Excel Source 1 ─┐
Excel Source 2 ─┤
Excel Source 3 ─┼──→ Python/Pandas
                     ↓
               Clean Data
                     ↓
              Remove Duplicates
                     ↓
              Handle NULL Values
                     ↓
             Combine / Merge
                     ↓
          compiled_flood_data.xlsx
```

## Layout

```
task_1/
├── data/
│   ├── raw/
│   │   ├── source_1.xlsx    Wikipedia workbook
│   │   ├── source_2.xlsx    NDRRMA / Nepal Police / RDNA compiled workbook
│   │   └── source_3.xlsx    Compact Wikipedia + ReliefWeb key-values
│   └── processed/
│       └── compiled_flood_data.xlsx
├── scripts/
│   ├── clean_data.py
│   ├── filter_data.py
│   └── inspect_data.py
└── README.md
```

## Setup

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python scripts/clean_data.py
python scripts/filter_data.py
python scripts/inspect_data.py
streamlit run app.py
```

The Streamlit app reads `data/processed/compiled_flood_data.xlsx` and charts district impact, casualty updates, nationality tables, damage, and source comparisons.

`clean_data.py` writes `data/processed/compiled_flood_data.xlsx` with:

| Sheet | What it is |
| --- | --- |
| `event_comparison` | Same facts from all 3 sources side by side |
| `compiled_indicators` | Long-format union of metrics |
| `district_compiled` | District deaths merged with RDNA impact |
| `locations` | Affected places |
| `casualties_nationality` | Deaths/missing by nationality |
| `damage` | Infrastructure and other damage |
| `timeline_compiled` | Event timeline plus official casualty updates |
| `source2_snapshot` | National snapshot indicators |
| `source3_key_values` | Source 3 key-values |
| `source_notes` | Citations and caveats |

## Notes

Casualty figures are **provisional** and use different cut-off dates. `event_comparison` is the sheet to use when sources disagree (for example Wikipedia 1,410 Nepal deaths vs Nepal Police 1,451 recovered bodies on 20 Sep 2026).
