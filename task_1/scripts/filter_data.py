"""Filter compiled flood tables (districts, corridor, casualties, dates)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
COMPILED = PROCESSED / "compiled_flood_data.xlsx"

NEPAL_FOCUS_DISTRICTS = {
    "rasuwa",
    "nuwakot",
    "dhading",
    "gorkha",
    "chitwan",
}


def _load_sheet(name: str) -> pd.DataFrame:
    if not COMPILED.exists():
        raise FileNotFoundError(f"Missing {COMPILED}. Run scripts/clean_data.py first.")
    return pd.read_excel(COMPILED, sheet_name=name)


def filter_nepal_districts(min_deaths: int = 0) -> pd.DataFrame:
    df = _load_sheet("district_compiled")
    out = df.copy()
    if "country" in out.columns:
        out = out[out["country"].astype(str).str.lower() == "nepal"]
    if "district" in out.columns:
        out = out[~out["district"].astype(str).str.contains("total", case=False, na=False)]
    if "deaths_recovered" in out.columns:
        deaths = pd.to_numeric(out["deaths_recovered"], errors="coerce").fillna(0)
        out = out[deaths >= min_deaths]
    return out.sort_values("deaths_recovered", ascending=False)


def filter_focus_corridor() -> pd.DataFrame:
    df = filter_nepal_districts()
    return df[df["district"].astype(str).str.lower().isin(NEPAL_FOCUS_DISTRICTS)]


def filter_timeline(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    df = _load_sheet("timeline_compiled")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if start:
        df = df[df["date"] >= pd.to_datetime(start)]
    if end:
        df = df[df["date"] <= pd.to_datetime(end)]
    return df.sort_values("date")


def filter_casualties(min_deaths: int = 1) -> pd.DataFrame:
    df = _load_sheet("casualties_nationality")
    deaths = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    return df[deaths >= min_deaths].sort_values("deaths", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter compiled flood data.")
    parser.add_argument("--min-deaths", type=int, default=0)
    parser.add_argument("--start", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=None, help="YYYY-MM-DD")
    args = parser.parse_args()

    districts = filter_nepal_districts(min_deaths=args.min_deaths)
    corridor = filter_focus_corridor()
    casualties = filter_casualties(min_deaths=max(args.min_deaths, 1))
    timeline = filter_timeline(start=args.start, end=args.end)

    districts.to_csv(PROCESSED / "filtered_district_deaths.csv", index=False)
    corridor.to_csv(PROCESSED / "filtered_focus_districts.csv", index=False)
    casualties.to_csv(PROCESSED / "filtered_casualties.csv", index=False)
    timeline.to_csv(PROCESSED / "filtered_timeline.csv", index=False)

    print(f"Nepal districts: {len(districts)}")
    print(f"Focus corridor (Rasuwa-Chitwan): {len(corridor)}")
    print(f"Nationalities with deaths >= {max(args.min_deaths, 1)}: {len(casualties)}")
    print(f"Timeline rows: {len(timeline)}")


if __name__ == "__main__":
    main()
