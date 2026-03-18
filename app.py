import streamlit as st
import pandas as pd
import requests
from io import StringIO

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(
    page_title="NSE FII/DII Dashboard",
    layout="wide"
)

st.title("NSE Participant Data Dashboard")

# ---------------------------
# INPUT
# ---------------------------
date_input = st.text_input("Enter Date (DDMMYYYY)", "")

BASE_URL = "https://nsearchives.nseindia.com/content/nsccl/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# ---------------------------
# FETCH FUNCTION
# ---------------------------
def fetch_csv(url):
    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        elif response.status_code == 404:
            st.warning("Data not available for this date.")
        else:
            st.error(f"Failed with status code: {response.status_code}")

    except requests.exceptions.Timeout:
        st.error("Request timed out")

    except Exception as e:
        st.error(f"Error: {e}")

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
        st.error("Could not find header row")
        return None

    # Set correct header
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
# MAIN ACTION
# ---------------------------
if st.button("Fetch Data"):

    if not date_input:
        st.warning("Please enter a date")
    else:
        oi_url = BASE_URL + f"fao_participant_oi_{date_input}.csv"
        vol_url = BASE_URL + f"fao_participant_vol_{date_input}.csv"

        st.info("Fetching data from NSE...")

        df_oi_raw = fetch_csv(oi_url)
        df_vol_raw = fetch_csv(vol_url)

        if df_oi_raw is not None:
            df_oi = clean_nse(df_oi_raw)
            if df_oi is not None:
                st.subheader("Open Interest")
                st.dataframe(df_oi, use_container_width=True)

        if df_vol_raw is not None:
            df_vol = clean_nse(df_vol_raw)
            if df_vol is not None:
                st.subheader("Trading Volume")
                st.dataframe(df_vol, use_container_width=True)

        st.success("Done")
