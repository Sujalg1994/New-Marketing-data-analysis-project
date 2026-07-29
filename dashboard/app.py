"""Interactive Streamlit dashboard for the marketing analytics project."""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.generate_data import DEFAULT_OUTPUT, generate_dataset
from src.marketing_analysis import add_kpis, aggregate_performance

st.set_page_config(page_title="Marketing Performance Dashboard", layout="wide")
st.title("Marketing Campaign Performance Dashboard")
st.caption("Reproducible synthetic UK retail marketing data — portfolio demonstration only")

data_path = ROOT / DEFAULT_OUTPUT
if not data_path.exists():
    generate_dataset(data_path)

df = pd.read_csv(data_path, parse_dates=["date"])
df = add_kpis(df)

with st.sidebar:
    st.header("Filters")
    channels = st.multiselect("Channel", sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
    segments = st.multiselect(
        "Customer segment",
        sorted(df["customer_segment"].unique()),
        default=sorted(df["customer_segment"].unique()),
    )
    regions = st.multiselect("Region", sorted(df["region"].unique()), default=sorted(df["region"].unique()))
    date_range = st.date_input(
        "Date range",
        value=(df["date"].min().date(), df["date"].max().date()),
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date(),
    )

filtered = df[
    df["channel"].isin(channels)
    & df["customer_segment"].isin(segments)
    & df["region"].isin(regions)
].copy()

if len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[filtered["date"].between(start_date, end_date)]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

impressions = int(filtered["impressions"].sum())
clicks = int(filtered["clicks"].sum())
conversions = int(filtered["conversions"].sum())
spend = float(filtered["spend_gbp"].sum())
revenue = float(filtered["revenue_gbp"].sum())
ctr = clicks / impressions if impressions else 0
cvr = conversions / clicks if clicks else 0
roas = revenue / spend if spend else 0
cpa = spend / conversions if conversions else 0

kpi_columns = st.columns(6)
kpi_columns[0].metric("Revenue", f"£{revenue:,.0f}")
kpi_columns[1].metric("Spend", f"£{spend:,.0f}")
kpi_columns[2].metric("ROAS", f"{roas:.2f}x")
kpi_columns[3].metric("CPA", f"£{cpa:.2f}")
kpi_columns[4].metric("CTR", f"{ctr:.2%}")
kpi_columns[5].metric("Conversion rate", f"{cvr:.2%}")

st.subheader("Monthly revenue and spend")
monthly = filtered.assign(month=filtered["date"].dt.to_period("M").astype(str))
monthly = monthly.groupby("month", as_index=False)[["revenue_gbp", "spend_gbp"]].sum()
st.line_chart(monthly.set_index("month"))

left, right = st.columns(2)
with left:
    st.subheader("Channel performance")
    channel = aggregate_performance(filtered, ["channel"])
    st.dataframe(
        channel[["channel", "spend_gbp", "revenue_gbp", "roas", "cpa_gbp", "ctr", "conversion_rate"]],
        use_container_width=True,
        hide_index=True,
    )
with right:
    st.subheader("Revenue by customer segment")
    segment = aggregate_performance(filtered, ["customer_segment"])
    st.bar_chart(segment.set_index("customer_segment")["revenue_gbp"])

st.subheader("A/B variant performance")
variant = aggregate_performance(filtered, ["ab_variant"])
st.dataframe(
    variant[["ab_variant", "clicks", "conversions", "conversion_rate", "revenue_gbp", "roas"]],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Analyst recommendation")
best = channel.sort_values("roas", ascending=False).iloc[0]
worst = channel.sort_values("roas", ascending=True).iloc[0]
st.write(
    f"Prioritise **{best['channel']}** for controlled budget growth because it has the "
    f"highest filtered ROAS ({best['roas']:.2f}x). Review **{worst['channel']}** creative, "
    f"targeting and bid strategy before increasing spend."
)
