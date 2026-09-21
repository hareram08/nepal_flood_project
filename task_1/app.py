"""Streamlit visual report for compiled 2026 Nepal-Tibet flood data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
COMPILED = ROOT / "data" / "processed" / "compiled_flood_data.xlsx"

DISTRICT_COORDS = {
    "Chitwan": (27.53, 84.35),
    "Rasuwa": (28.12, 85.30),
    "Nawalparasi East": (27.67, 84.14),
    "Nawalparasi West": (27.55, 83.68),
    "Nuwakot": (27.91, 85.17),
    "Gorkha": (28.00, 84.63),
    "Dhading": (27.87, 84.93),
    "Tanahun": (27.95, 84.25),
    "Kathmandu": (27.72, 85.32),
}

LOCATION_COORDS = {
    "Langtang Lirung": (28.26, 85.51),
    "Gyirong Port / Rasuwagadhi": (28.28, 85.38),
    "Dhunche": (28.11, 85.30),
    "Bidur": (27.90, 85.15),
    "Syafrubesi": (28.16, 85.35),
    "Trishuli Bazar": (27.91, 85.15),
    "Malekhu": (27.81, 84.84),
    "Devghat": (27.71, 84.42),
}

PALETTE = ["#0B3D91", "#1D7A8C", "#E07A3D", "#C0392B", "#5B4B8A", "#2E8B57"]
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,250,252,0.6)",
    font=dict(family="Source Sans 3, Segoe UI, sans-serif", color="#1B2430"),
    margin=dict(l=40, r=20, t=50, b=40),
    autosize=True,
)


@st.cache_data
def load_sheets() -> dict[str, pd.DataFrame]:
    if not COMPILED.exists():
        raise FileNotFoundError(
            "compiled_flood_data.xlsx not found. Run: python scripts/clean_data.py"
        )
    xl = pd.ExcelFile(COMPILED)
    return {name: pd.read_excel(COMPILED, sheet_name=name) for name in xl.sheet_names}


def snapshot_value(snapshot: pd.DataFrame, indicator: str) -> str:
    match = snapshot[snapshot["indicator"].astype(str).str.lower() == indicator.lower()]
    if match.empty:
        return "—"
    return str(match.iloc[0]["value"])


def apply_chart(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E6EEF4")
    return fig


def show_chart(fig: go.Figure) -> None:
    st.plotly_chart(apply_chart(fig), width="stretch", config={"responsive": True})


def show_table(df: pd.DataFrame) -> None:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = pd.to_datetime(out[col], errors="coerce").dt.strftime("%Y-%m-%d")
        else:
            out[col] = out[col].astype("string")
    st.dataframe(out, width="stretch", hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="Nepal Flood 2026 Report",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.2rem; max-width: 1400px;}
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #f4f8fb 0%, #eaf1f6 100%);
            border: 1px solid #d5e3ee;
            border-radius: 14px;
            padding: 12px 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    sheets = load_sheets()
    districts = sheets["district_compiled"].copy()
    casualties = sheets["casualties_nationality"].copy()
    damage = sheets["damage"].copy()
    timeline = sheets["timeline_compiled"].copy()
    timeline["date"] = pd.to_datetime(timeline["date"], errors="coerce")
    comparison = sheets["event_comparison"].copy()
    snapshot = sheets["source2_snapshot"].copy()
    locations = sheets["locations"].copy()
    notes = sheets["source_notes"].copy()

    st.sidebar.title("Report")
    st.sidebar.caption("Compiled from source_1, source_2, source_3")
    page = st.sidebar.radio(
        "Section",
        ["Overview", "Districts", "People", "Damage & places", "Sources"],
    )
    provinces = ["All"] + sorted(districts["province"].dropna().astype(str).unique().tolist())
    province = st.sidebar.selectbox("Province", provinces)
    min_deaths = st.sidebar.slider(
        "Minimum recovered deaths", 0, int(districts["deaths_recovered"].max()), 0
    )
    top_n = st.sidebar.slider("Nationalities to show", 5, 20, 10)

    filtered = districts.copy()
    if province != "All":
        filtered = filtered[filtered["province"] == province]
    filtered = filtered[filtered["deaths_recovered"].fillna(0) >= min_deaths]

    st.title("2026 Nepal–Tibet flood situation report")
    st.caption(
        "Flash flood and debris flow from 26 August 2026 along the Lhende / Bhotekoshi–Trishuli corridor. "
        "Figures are provisional. Different sources use different cut-off dates."
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Recovered deaths", snapshot_value(snapshot, "Deaths_confirmed_recovered"))
    k2.metric("Missing (NDRRMA)", snapshot_value(snapshot, "Missing_NDRRMA"))
    k3.metric("Rescued", snapshot_value(snapshot, "Rescued"))
    k4.metric("People affected (RDNA)", snapshot_value(snapshot, "People_affected_RDNA"))
    k5.metric("Houses damaged (RDNA)", snapshot_value(snapshot, "Houses_damaged_RDNA"))

    if page == "Overview":
        left, right = st.columns((1.15, 1))
        with left:
            cas = timeline.dropna(subset=["deaths"]).sort_values("date")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cas["date"], y=cas["deaths"], name="Deaths", mode="lines+markers", line=dict(color="#C0392B", width=3)))
            fig.add_trace(go.Scatter(x=cas["date"], y=cas["missing"], name="Missing", mode="lines+markers", line=dict(color="#E07A3D", width=3)))
            fig.add_trace(go.Scatter(x=cas["date"], y=cas["rescued"], name="Rescued", mode="lines+markers", line=dict(color="#1D7A8C", width=3)))
            fig.update_layout(title="Official casualty updates over time", legend=dict(orientation="h"))
            show_chart(fig)
        with right:
            compare_deaths = comparison[comparison["fact"].isin(["nepal_deaths", "nepal_missing", "tibet_deaths"])]
            long = compare_deaths.melt(id_vars="fact", var_name="source", value_name="reported")
            long["value_num"] = pd.to_numeric(
                long["reported"].astype(str).str.extract(r"([\d.]+)")[0], errors="coerce"
            )
            fig = px.bar(
                long.dropna(subset=["value_num"]),
                x="fact",
                y="value_num",
                color="source",
                barmode="group",
                color_discrete_sequence=PALETTE,
                title="Same facts, three sources",
                labels={"value_num": "Reported figure", "fact": ""},
            )
            show_chart(fig)
        st.subheader("Timeline")
        show_table(timeline.sort_values("date")[["date", "event", "location", "details", "deaths", "missing", "source"]])

    if page == "Districts":
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(
                filtered.sort_values("deaths_recovered"),
                x="deaths_recovered",
                y="district",
                color="province",
                orientation="h",
                title="Recovered bodies by district (Nepal Police, 20 Sep)",
                color_discrete_sequence=PALETTE,
                hover_data=["notes", "share_of_national_pct"],
                labels={"deaths_recovered": "Recovered deaths", "district": ""},
            )
            show_chart(fig)
        with c2:
            rdna = filtered.dropna(subset=["rdna_houses_damaged"])
            fig = px.bar(
                rdna.sort_values("rdna_houses_damaged"),
                x="rdna_houses_damaged",
                y="district",
                color="rdna_people_affected",
                orientation="h",
                title="RDNA houses damaged vs people affected",
                color_continuous_scale="Teal",
                labels={"rdna_houses_damaged": "Houses damaged", "district": "", "rdna_people_affected": "People"},
            )
            show_chart(fig)

        map_df = filtered.copy()
        map_df["lat"] = map_df["district"].map(lambda d: DISTRICT_COORDS.get(d, (None, None))[0])
        map_df["lon"] = map_df["district"].map(lambda d: DISTRICT_COORDS.get(d, (None, None))[1])
        map_df = map_df.dropna(subset=["lat", "lon"])
        fig = px.scatter_geo(
            map_df,
            lat="lat",
            lon="lon",
            size="deaths_recovered",
            color="province",
            hover_name="district",
            hover_data={"deaths_recovered": True, "rdna_houses_damaged": True, "lat": False, "lon": False},
            size_max=40,
            title="District impact (marker size = recovered deaths)",
            color_discrete_sequence=PALETTE,
        )
        fig.update_geos(
            projection_type="natural earth",
            center=dict(lat=27.9, lon=84.7),
            projection_scale=28,
            showland=True,
            landcolor="#EEF4F8",
            showcountries=True,
            showlakes=True,
        )
        show_chart(fig)
        show_table(filtered)
        st.caption(
            "RDNA blanks on Nawalparasi, Tanahun, and Kathmandu mean those districts were outside the five-district RDNA caseload, not zero damage."
        )

    if page == "People":
        top = casualties.sort_values("deaths", ascending=False).head(top_n)
        long = top.melt(
            id_vars="nationality",
            value_vars=["deaths", "missing"],
            var_name="measure",
            value_name="count",
        )
        fig = px.bar(
            long,
            x="nationality",
            y="count",
            color="measure",
            barmode="group",
            title=f"Top {top_n} nationalities in the Nepal-side casualty table",
            color_discrete_map={"deaths": "#C0392B", "missing": "#E07A3D"},
        )
        fig.update_xaxes(tickangle=-35)
        show_chart(fig)
        c1, c2 = st.columns(2)
        with c1:
            pie = casualties[casualties["deaths"] > 0].nlargest(8, "deaths")
            fig = px.pie(
                pie,
                names="nationality",
                values="deaths",
                title="Share of recorded deaths by nationality",
                color_discrete_sequence=PALETTE,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            show_chart(fig)
        with c2:
            st.subheader("How to read this table")
            st.markdown(
                """
                These counts are **nationality of people recorded in Nepal-side tables**,
                not Nepal's national death total. China appearing first does not mean
                China had more flood deaths than Nepal overall.
                """
            )
            show_table(casualties.sort_values(["deaths", "missing"], ascending=False))

    if page == "Damage & places":
        compact = damage.copy()
        compact = compact[compact["value"].fillna(0) < 20_000]
        compact = compact[~compact["metric"].astype(str).str.lower().str.contains("debris")]
        fig = px.bar(
            compact.sort_values("value", ascending=False).head(15),
            x="value",
            y="metric",
            color="category",
            orientation="h",
            title="Physical damage indicators (very large currency figures excluded)",
            color_discrete_sequence=PALETTE,
            hover_data=["unit", "area", "notes"],
        )
        show_chart(fig)

        loc = locations.copy()
        loc["lat"] = loc["location"].map(lambda n: LOCATION_COORDS.get(n, (None, None))[0])
        loc["lon"] = loc["location"].map(lambda n: LOCATION_COORDS.get(n, (None, None))[1])
        mapped = loc.dropna(subset=["lat", "lon"])
        fig = px.scatter_geo(
            mapped,
            lat="lat",
            lon="lon",
            hover_name="location",
            color="country_region",
            hover_data={"role_impact": True, "administrative_area": True, "lat": False, "lon": False},
            title="Named locations along the corridor",
            color_discrete_sequence=PALETTE,
        )
        fig.update_traces(marker=dict(size=12))
        fig.update_geos(
            projection_type="natural earth",
            center=dict(lat=28.0, lon=85.1),
            projection_scale=40,
            showland=True,
            landcolor="#EEF4F8",
            showcountries=True,
        )
        show_chart(fig)
        show_table(locations)
        with st.expander("Full damage table"):
            show_table(damage)

    if page == "Sources":
        st.subheader("Event facts compared")
        show_table(comparison)
        st.subheader("National snapshot (source 2)")
        show_table(snapshot)
        st.subheader("Notes and citations")
        show_table(notes)
        st.info(f"Data file: `{COMPILED}`")


if __name__ == "__main__":
    main()
