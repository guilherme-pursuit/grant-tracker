import streamlit as st
import pandas as pd
from foundation_grants_scraper import fetch_foundation_grants

st.set_page_config(page_title="Grant Tracker MVP", layout="wide")
st.title("📊 Pursuit Grant Tracker (MVP)")

# Fetch live grants on load
df = fetch_foundation_grants()

# Sidebar filters
st.sidebar.header("Filters")
geos = ["All"] + sorted(df["Geography"].unique().tolist())
sel_geo = st.sidebar.selectbox("Geography", geos)
topics = ["All"] + sorted(df["Topic"].unique().tolist())
sel_topic = st.sidebar.selectbox("Topic", topics)
types = ["All"] + sorted(df["Funder Type"].unique().tolist())
sel_type = st.sidebar.selectbox("Funder Type", types)

# Apply filters
filtered = df.copy()
if sel_geo != "All":
    filtered = filtered[filtered["Geography"] == sel_geo]
if sel_topic != "All":
    filtered = filtered[filtered["Topic"] == sel_topic]
if sel_type != "All":
    filtered = filtered[filtered["Funder Type"] == sel_type]

# Display results
st.subheader(f"🔍 {len(filtered)} Grants Found")
st.dataframe(filtered)

# CSV download
st.download_button(
    "Download CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="pursuit_grants_mvp.csv",
    mime="text/csv"
)