import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import timedelta

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="NSE Trends Dashboard", layout="wide")
st.title("NSE Participant Trend Dashboard")

BASE_URL = "https://nsearchives.nseindia.com/content/nsccl/"
headers = {"User-Agent": "Mozilla/5.0"}


# ---------------------------
# FETCH (CACHED)
# ---------------------------
@st.cache_data
def fetch_csv(date_str):
    url = BASE_URL + f"fao_participant_oi_{date_str}.csv"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return pd.read_csv(StringIO(res.text))
    except:
        pass

    return None


# ---------------------------
# CLEAN FUNCTION
# ---------------------------
def clean_nse(df):
    df = df.dropna(how='all').reset_index(drop=True)

    # Find header row
    header_row = None
    for i, row in df.iterrows():
        if row.astype(str).str.contains("Client Type", case=False).any():
            header_row = i
            break

    if header_row is None:
        return None

    df.columns = df.iloc[header_row]
    df = df[header_row + 1:].reset_index(drop=True)

    # Clean column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )

    # Remove TOTAL rows
    df = df[~df["client_type"].str.contains("total", case=False, na=False)]

    # Convert numeric columns
    for col in df.columns:
        if col != "client_type":
            df[col] = df[col].astype(str).str.replace(",", "")
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ---------------------------
# DATE INPUT
# ---------------------------
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

if start_date and end_date:

    if start_date > end_date:
        st.error("Start date must be before end date")
        st.stop()

    if (end_date - start_date).days > 31:
        st.warning("Max 1 month range allowed")
        st.stop()

    # ---------------------------
    # GENERATE DATE LIST
    # ---------------------------
    def get_dates(start, end):
        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%d%m%Y"))
            current += timedelta(days=1)
        return dates

    dates = get_dates(start_date, end_date)

    st.info("Fetching data...")

    all_data = []
    progress = st.progress(0)

    # ---------------------------
    # FETCH LOOP
    # ---------------------------
    for i, d in enumerate(dates):
        df_raw = fetch_csv(d)

        if df_raw is not None:
            df_clean = clean_nse(df_raw)

            if df_clean is not None:
                df_clean["date"] = pd.to_datetime(d, format="%d%m%Y")
                all_data.append(df_clean)

        progress.progress((i + 1) / len(dates))

    if not all_data:
        st.error("No data available for selected range")
        st.stop()

    full_df = pd.concat(all_data, ignore_index=True)

    # ---------------------------
    # AUTO CREATE NET COLUMNS
    # ---------------------------
    net_columns = []

    for col in full_df.columns:
        if col.endswith("_long"):
            base = col.replace("_long", "")
            short_col = base + "_short"

            if short_col in full_df.columns:
                net_col = base + "_net"

                full_df[net_col] = full_df[col] - full_df[short_col]
                net_columns.append(net_col)

    # ---------------------------
    # UI SELECTION
    # ---------------------------
    st.subheader("Filters")

    col1, col2 = st.columns(2)

    with col1:
        participant = st.selectbox(
            "Select Participant",
            sorted(full_df["client_type"].unique())
        )

    with col2:
        metric = st.selectbox(
            "Select Metric (Net Values)",
            sorted(net_columns)
        )

    # ---------------------------
    # FILTER DATA
    # ---------------------------
    df_filtered = full_df[full_df["client_type"] == participant]
    df_filtered = df_filtered.sort_values("date")

    # ---------------------------
    # GRAPH
    # ---------------------------
    st.subheader("Trend Graph")

    st.line_chart(
        df_filtered.set_index("date")[metric]
    )

    # ---------------------------
    # OPTIONAL TABLE
    # ---------------------------
    with st.expander("View Data"):
        st.dataframe(df_filtered, use_container_width=True)

    st.success("Done")
