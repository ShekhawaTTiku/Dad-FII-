import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="NSE Trends Dashboard", layout="wide")
st.title("NSE Participant Trends Dashboard")

BASE_URL = "https://nsearchives.nseindia.com/content/nsccl/"
headers = {"User-Agent": "Mozilla/5.0"}

# ---------------------------
# FETCH FUNCTION (CACHED)
# ---------------------------
@st.cache_data
def fetch_csv(date_str):
    url = BASE_URL + f"fao_participant_oi_{date_str}.csv"

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        else:
            return None

    except:
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

    # Remove totals
    if "client_type" in df.columns:
        df = df[~df["client_type"].str.contains("total", case=False, na=False)]

    # Convert numeric columns
    for col in df.columns:
        if col != "client_type":
            df[col] = df[col].astype(str).str.replace(",", "")
            df[col] = pd.to_numeric(df[col], errors='coerce')

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
        st.warning("Please select max 1 month range")
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
    # CREATE NET METRICS
    # ---------------------------
    if "index_futures_long" in full_df.columns and "index_futures_short" in full_df.columns:
        full_df["net_futures"] = (
            full_df["index_futures_long"] - full_df["index_futures_short"]
        )

    # ---------------------------
    # UI SELECTIONS
    # ---------------------------
    st.subheader("Filters")

    col1, col2 = st.columns(2)

    with col1:
        participants = full_df["client_type"].unique()
        selected_participant = st.selectbox("Select Participant", participants)

    with col2:
        numeric_cols = full_df.select_dtypes(include=["number"]).columns.tolist()
        selected_metric = st.selectbox("Select Metric", numeric_cols)

    # ---------------------------
    # FILTER DATA
    # ---------------------------
    filtered_df = full_df[full_df["client_type"] == selected_participant]

    # ---------------------------
    # PLOT
    # ---------------------------
    st.subheader("Trend")

    plot_df = filtered_df.sort_values("date")

    st.line_chart(
        plot_df.set_index("date")[selected_metric]
    )

    # ---------------------------
    # SHOW TABLE (OPTIONAL)
    # ---------------------------
    with st.expander("View Raw Data"):
        st.dataframe(filtered_df, use_container_width=True)

    st.success("Done")
