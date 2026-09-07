# NSE Participant Trend Dashboard

A Streamlit web app that visualizes trends in NSE (National Stock Exchange of India) F&O **Participant-wise Open Interest** data. It downloads daily CSV reports directly from the NSE archives, cleans and merges them for a selected date range, and lets you explore net long/short positioning trends by participant type (Client, DII, FII, Pro).

## Features

- 📅 Pick a custom start/end date range (capped at 31 days per query)
- 🌐 Automatically fetches and caches the corresponding daily CSV reports from NSE archives
- 🧹 Cleans raw NSE CSVs (finds header row, strips formatting, converts numeric columns)
- ➕ Auto-generates **net** columns (`long − short`) for every matching long/short metric pair
- 🎛️ Interactive filters for participant type and metric
- 📈 Line chart of the selected metric's trend over time
- 📋 Expandable raw data table for the filtered selection

## How It Works

1. **Date range input** — you choose a start and end date (max 31 days apart).
2. **Fetch loop** — for each date in the range, the app requests:
   `https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_<DDMMYYYY>.csv`
   Results are cached with `@st.cache_data` so repeated runs are fast.
3. **Cleaning** — each raw CSV is parsed to locate the actual header row (containing "Client Type"), column names are normalized (lowercase, underscores), "Total" rows are dropped, and numeric columns are coerced to numbers.
4. **Net columns** — for every column ending in `_long` that has a matching `_short` column, a `_net` column is computed.
5. **Filtering & visualization** — you select a participant type and a net metric, and the app plots the trend as a line chart with an optional data table view.

## Requirements

- Python 3.8+
- Internet access (the app fetches live data from NSE archives at runtime — no local dataset needed)

### Python packages

```
streamlit
pandas
requests
```

## Installation

```bash
git clone <your-repo-url>
cd <your-repo-folder>
pip install streamlit pandas requests
```

## Usage

```bash
streamlit run app.py
```

Then, in the browser tab that opens:

1. Select a **Start Date** and **End Date** (within a 31-day window).
2. Wait for the progress bar as data is fetched for each day.
3. Choose a **Participant** (e.g., Client, DII, FII, Pro) and a **Metric** (a net long/short column) from the dropdowns.
4. View the trend chart and, optionally, expand **View Data** to see the underlying table.

## Notes & Limitations

- NSE does not publish data for weekends/holidays, so those dates are silently skipped (no data available).
- If **no valid data** is found for the entire selected range, the app shows an error and stops.
- The date range is intentionally capped at 31 days to keep fetch times reasonable, since each day requires a separate HTTP request.
- Network or server errors during fetch are caught silently (`fetch_csv` returns `None` for that date) rather than crashing the app.
- This app relies on the NSE archive URL structure and CSV format remaining stable; if NSE changes their file naming or report layout, the fetch/clean logic may need updating.

## Data Source

Data is sourced directly from the [NSE India archives](https://nsearchives.nseindia.com/content/nsccl/) — specifically the daily **FAO Participant-wise Open Interest** reports.

## License

Add a license of your choice (e.g., MIT) here.
