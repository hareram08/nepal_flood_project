"""Inspect the three Excel sources and compiled_flood_data.xlsx."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
COMPILED = ROOT / "data" / "processed" / "compiled_flood_data.xlsx"

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)
pd.set_option("display.max_colwidth", 72)


def banner(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def inspect_frame(df: pd.DataFrame, label: str, head: int = 6) -> None:
    banner(label)
    print(f"shape: {df.shape[0]} rows x {df.shape[1]} cols")
    print("columns:", list(df.columns))
    missing = df.isna().sum()
    missing = missing[missing > 0]
    print("missing numeric/date cells:", "none" if missing.empty else "")
    if not missing.empty:
        print(missing.to_string())
    print(f"\nfirst {head} rows:")
    print(df.head(head).to_string(index=False))


def inspect_workbook(path: Path, title: str) -> None:
    if not path.exists():
        print(f"missing {path}")
        return
    xl = pd.ExcelFile(path)
    banner(f"{title}: {path.name} | sheets={xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        inspect_frame(df, f"{title} / {sheet}")


def main() -> None:
    inspect_workbook(RAW / "source_1.xlsx", "SOURCE 1")
    inspect_workbook(RAW / "source_2.xlsx", "SOURCE 2")
    inspect_workbook(RAW / "source_3.xlsx", "SOURCE 3")
    inspect_workbook(COMPILED, "COMPILED")
    print("\nDone.")


if __name__ == "__main__":
    main()
