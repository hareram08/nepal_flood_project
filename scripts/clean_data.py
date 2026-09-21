"""
Excel Source 1, 2, 3
        -> Python/Pandas
        -> Clean Data
        -> Remove Duplicates
        -> Handle NULL Values
        -> Combine / Merge
        -> compiled_flood_data.xlsx
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

SOURCE_1 = RAW / "source_1.xlsx"
SOURCE_2 = RAW / "source_2.xlsx"
SOURCE_3 = RAW / "source_3.xlsx"

NOT_REPORTED = "Not reported"


def _snake(name: object) -> str:
    text = str(name).strip().lower()
    text = re.sub(r"[^\w]+", "_", text, flags=re.UNICODE)
    return text.strip("_")


def _clean_text(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    if not isinstance(value, str):
        return value
    text = value.replace("\xa0", " ").strip()
    text = text.replace("–", "-").replace("—", "-").replace("�", "-")
    text = re.sub(r"\s+", " ", text)
    return text if text else pd.NA


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [_snake(c) for c in out.columns]
    out = out.dropna(how="all").dropna(axis=1, how="all")
    for col in out.columns:
        if out[col].dtype == object or str(out[col].dtype) in {"string", "str"}:
            out[col] = out[col].map(_clean_text)
    return out.reset_index(drop=True)


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().reset_index(drop=True)


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    date_cols = {"date", "as_of_date", "report_date"}
    for col in out.columns:
        kind = str(out[col].dtype)
        if "datetime" in kind or col in date_cols:
            out[col] = pd.to_datetime(out[col], errors="coerce")
            continue
        if kind.startswith(("float", "int", "Int", "Float")):
            continue
        numeric = pd.to_numeric(out[col], errors="coerce")
        present = out[col].notna() & (out[col].astype(str).str.strip() != "")
        if present.any() and numeric[present].notna().all():
            out[col] = numeric
            continue
        out[col] = out[col].mask(out[col].astype(str).str.strip() == "", pd.NA)
        out[col] = out[col].fillna(NOT_REPORTED)
    return out


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    return handle_nulls(remove_duplicates(clean_frame(df)))


def _read_sheet_with_header(path: Path, sheet: str, header_row: int) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    header = [str(v) if pd.notna(v) else f"col_{i}" for i, v in enumerate(raw.iloc[header_row])]
    body = raw.iloc[header_row + 1 :].copy()
    body.columns = header
    body = body[body.iloc[:, 0].notna()]
    return body.reset_index(drop=True)


def load_source_1() -> dict[str, pd.DataFrame]:
    return {
        "event_summary": prepare(pd.read_excel(SOURCE_1, sheet_name="Event Summary")),
        "locations": prepare(pd.read_excel(SOURCE_1, sheet_name="Locations")),
        "casualties": prepare(pd.read_excel(SOURCE_1, sheet_name="Casualties by Nationality")),
        "damage": prepare(pd.read_excel(SOURCE_1, sheet_name="Damage Indicators")),
        "timeline": prepare(pd.read_excel(SOURCE_1, sheet_name="Timeline")),
        "chart": prepare(pd.read_excel(SOURCE_1, sheet_name="Chart Data")),
    }


def load_source_2() -> dict[str, pd.DataFrame]:
    snapshot = prepare(_read_sheet_with_header(SOURCE_2, "National Snapshot", 3))
    deaths = prepare(_read_sheet_with_header(SOURCE_2, "District Deaths", 3))
    rdna = prepare(_read_sheet_with_header(SOURCE_2, "RDNA District Impact", 3))
    rdna = rdna[rdna["country"].astype(str).str.lower() == "nepal"].copy()
    timeline = prepare(_read_sheet_with_header(SOURCE_2, "Casualty Timeline", 3))
    notes = prepare(_read_sheet_with_header(SOURCE_2, "Sources and Notes", 2))
    return {
        "national_snapshot": snapshot,
        "district_deaths": deaths,
        "rdna": rdna,
        "casualty_timeline": timeline,
        "source_notes": notes,
    }


def load_source_3() -> pd.DataFrame:
    return prepare(pd.read_excel(SOURCE_3))


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def build_indicators(
    s1: dict[str, pd.DataFrame],
    s2: dict[str, pd.DataFrame],
    s3: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, row in s1["event_summary"].iterrows():
        rows.append(
            {
                "source": "source_1",
                "table": "event_summary",
                "geography": "Nepal-Tibet",
                "metric": row.get("field"),
                "value_text": row.get("value"),
                "value_num": pd.to_numeric(row.get("value"), errors="coerce"),
                "unit": NOT_REPORTED,
                "as_of_date": pd.NaT,
                "notes": row.get("source_note", row.get("source_note", NOT_REPORTED)),
            }
        )

    for _, row in s1["chart"].iterrows():
        for metric in ("deaths", "missing"):
            rows.append(
                {
                    "source": "source_1",
                    "table": "chart_data",
                    "geography": row.get("region"),
                    "metric": metric,
                    "value_text": str(row.get(metric)),
                    "value_num": _to_num(pd.Series([row.get(metric)])).iloc[0],
                    "unit": "people",
                    "as_of_date": pd.NaT,
                    "notes": "Wikipedia chart totals",
                }
            )

    for _, row in s1["damage"].iterrows():
        rows.append(
            {
                "source": "source_1",
                "table": "damage",
                "geography": row.get("area"),
                "metric": row.get("metric"),
                "value_text": str(row.get("value")),
                "value_num": _to_num(pd.Series([row.get("value")])).iloc[0],
                "unit": row.get("unit"),
                "as_of_date": pd.NaT,
                "notes": row.get("notes"),
            }
        )

    for _, row in s2["national_snapshot"].iterrows():
        rows.append(
            {
                "source": "source_2",
                "table": "national_snapshot",
                "geography": "Nepal",
                "metric": row.get("indicator"),
                "value_text": str(row.get("value")),
                "value_num": _to_num(pd.Series([row.get("value")])).iloc[0],
                "unit": row.get("unit"),
                "as_of_date": pd.to_datetime(row.get("as_of_date"), errors="coerce"),
                "notes": row.get("source"),
            }
        )

    for _, row in s3.iterrows():
        metric = f"{row.get('data_category')} | {row.get('sub_category')}"
        rows.append(
            {
                "source": "source_3",
                "table": "event_key_values",
                "geography": str(row.get("sub_category")),
                "metric": metric,
                "value_text": row.get("details_value"),
                "value_num": _to_num(pd.Series([row.get("details_value")])).iloc[0],
                "unit": NOT_REPORTED,
                "as_of_date": pd.NaT,
                "notes": row.get("source"),
            }
        )

    out = pd.DataFrame(rows)
    return handle_nulls(remove_duplicates(out))


def merge_districts(s2: dict[str, pd.DataFrame]) -> pd.DataFrame:
    deaths = s2["district_deaths"].copy()
    deaths["district_key"] = deaths["district"].astype(str).str.lower().str.replace(
        "tanahu", "tanahun"
    )
    deaths = deaths[~deaths["district_key"].str.contains("total", na=False)]

    rdna = s2["rdna"].copy()
    rdna["district_key"] = rdna["district"].astype(str).str.lower()
    rdna = rdna[~rdna["district_key"].str.contains("total", na=False)]
    rdna_keep = rdna[
        [
            "district_key",
            "people_affected",
            "households_affected",
            "houses_damaged",
            "share_of_damaged_buildings_pct",
        ]
    ].rename(
        columns={
            "people_affected": "rdna_people_affected",
            "households_affected": "rdna_households_affected",
            "houses_damaged": "rdna_houses_damaged",
            "share_of_damaged_buildings_pct": "rdna_share_buildings_pct",
        }
    )

    merged = deaths.merge(rdna_keep, on="district_key", how="outer")
    merged = merged.drop(columns=["district_key"])
    for col in (
        "deaths_recovered",
        "share_of_national_pct",
        "rdna_people_affected",
        "rdna_households_affected",
        "rdna_houses_damaged",
        "rdna_share_buildings_pct",
    ):
        if col in merged.columns:
            merged[col] = _to_num(merged[col])
    merged = merged.sort_values("deaths_recovered", ascending=False, na_position="last")
    return handle_nulls(remove_duplicates(merged))


def merge_timeline(
    s1: dict[str, pd.DataFrame], s2: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    wiki = s1["timeline"].copy()
    wiki["source"] = "source_1"
    wiki["deaths"] = pd.NA
    wiki["missing"] = pd.NA
    wiki["rescued"] = pd.NA
    wiki["injured"] = pd.NA
    wiki["date"] = pd.to_datetime(wiki["date"], errors="coerce")
    wiki = wiki.rename(columns={"event": "event", "location": "location", "details": "details"})

    cas = s2["casualty_timeline"].copy()
    cas["source"] = "source_2"
    cas["event"] = "Official casualty update"
    cas["location"] = "Nepal"
    cas["details"] = cas.get("reporting_body", NOT_REPORTED)
    cas["date"] = pd.to_datetime(cas.get("report_date"), errors="coerce")
    for col in ("deaths", "missing", "rescued", "injured"):
        if col in cas.columns:
            cas[col] = _to_num(cas[col])

    cols = [
        "date",
        "event",
        "location",
        "details",
        "deaths",
        "missing",
        "rescued",
        "injured",
        "source",
    ]
    out = pd.concat([wiki.reindex(columns=cols), cas.reindex(columns=cols)], ignore_index=True)
    out = out.sort_values("date", na_position="last")
    return handle_nulls(remove_duplicates(out))


def merge_event_facts(
    s1: dict[str, pd.DataFrame],
    s2: dict[str, pd.DataFrame],
    s3: pd.DataFrame,
) -> pd.DataFrame:
    """Side-by-side comparison of overlapping facts from the three Excel sources."""
    s1_map = {
        str(r["field"]).strip().lower(): r["value"]
        for _, r in s1["event_summary"].iterrows()
    }
    s2_map = {
        str(r["indicator"]).strip().lower(): r["value"]
        for _, r in s2["national_snapshot"].iterrows()
    }
    s3_map = {
        f"{str(r['data_category']).strip().lower()}|{str(r['sub_category']).strip().lower()}": r[
            "details_value"
        ]
        for _, r in s3.iterrows()
    }

    facts = [
        {
            "fact": "event_name",
            "source_1": s1_map.get("event"),
            "source_2": s2_map.get("event_name"),
            "source_3": s3_map.get("event name|general"),
        },
        {
            "fact": "start_date",
            "source_1": s1_map.get("start date"),
            "source_2": s2_map.get("event_start_datetime"),
            "source_3": s3_map.get("date|general"),
        },
        {
            "fact": "nepal_deaths",
            "source_1": s1["chart"].loc[s1["chart"]["region"].str.lower() == "nepal", "deaths"].iloc[0]
            if not s1["chart"].empty
            else pd.NA,
            "source_2": s2_map.get("deaths_confirmed_recovered"),
            "source_3": s3_map.get("deaths|nepal"),
        },
        {
            "fact": "nepal_missing",
            "source_1": s1["chart"].loc[s1["chart"]["region"].str.lower() == "nepal", "missing"].iloc[0]
            if not s1["chart"].empty
            else pd.NA,
            "source_2": s2_map.get("missing_ndrrma"),
            "source_3": s3_map.get("missing|nepal"),
        },
        {
            "fact": "tibet_deaths",
            "source_1": s1["chart"]
            .loc[s1["chart"]["region"].str.lower().str.contains("tibet|china", na=False), "deaths"]
            .iloc[0]
            if s1["chart"]["region"].str.lower().str.contains("tibet|china", na=False).any()
            else pd.NA,
            "source_2": s2_map.get("china_tar_deaths_reported"),
            "source_3": s3_map.get("deaths|china (tibet)"),
        },
        {
            "fact": "houses_destroyed_or_damaged",
            "source_1": s1["damage"]
            .loc[s1["damage"]["metric"].str.lower().str.contains("houses destroyed", na=False), "value"]
            .iloc[0]
            if s1["damage"]["metric"].str.lower().str.contains("houses destroyed", na=False).any()
            else pd.NA,
            "source_2": s2_map.get("houses_damaged_rdna"),
            "source_3": NOT_REPORTED,
        },
    ]
    return handle_nulls(pd.DataFrame(facts))


def save_compiled(sheets: dict[str, pd.DataFrame]) -> Path:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out_xlsx = PROCESSED / "compiled_flood_data.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
            df.to_csv(PROCESSED / f"{name}.csv", index=False, encoding="utf-8")
    return out_xlsx


def main() -> None:
    if not SOURCE_1.exists() or not SOURCE_2.exists() or not SOURCE_3.exists():
        raise FileNotFoundError(
            f"Need {SOURCE_1.name}, {SOURCE_2.name}, {SOURCE_3.name} in data/raw/"
        )

    s1 = load_source_1()
    s2 = load_source_2()
    s3 = load_source_3()

    sheets = {
        "event_comparison": merge_event_facts(s1, s2, s3),
        "compiled_indicators": build_indicators(s1, s2, s3),
        "district_compiled": merge_districts(s2),
        "locations": s1["locations"],
        "casualties_nationality": s1["casualties"],
        "damage": s1["damage"],
        "timeline_compiled": merge_timeline(s1, s2),
        "source2_snapshot": s2["national_snapshot"],
        "source3_key_values": s3,
        "source_notes": s2["source_notes"],
    }

    path = save_compiled(sheets)
    print(f"Wrote {path}")
    for name, df in sheets.items():
        print(f"  {name}: {len(df)} rows x {len(df.columns)} cols")


if __name__ == "__main__":
    main()
