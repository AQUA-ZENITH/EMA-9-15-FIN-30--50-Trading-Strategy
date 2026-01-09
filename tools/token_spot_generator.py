import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Zerodha Instrument Finder",
    layout="wide"
)

st.title("Zerodha Instrument Token Finder")
st.markdown("Search Stocks, Futures, and Options")

@st.cache_data
def load_instruments():
    url = "https://api.kite.trade/instruments"
    return pd.read_csv(url)

df = load_instruments()

col1, col2 = st.columns(2)

with col1:
    exchange = st.selectbox(
        "Exchange",
        ["NSE", "NFO", "BSE", "MCX"]
    )

with col2:
    segments = df[df["exchange"] == exchange]["segment"].unique()
    segment = st.selectbox("Segment", segments)

filtered = df[
    (df["exchange"] == exchange) &
    (df["segment"] == segment)
]

symbol = st.selectbox(
    "Search Instrument",
    filtered["tradingsymbol"].tolist(),
    index=None
)

if symbol:
    row = filtered[filtered["tradingsymbol"] == symbol].iloc[0]
    st.success(f"Found: {symbol}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Instrument Token", row["instrument_token"])
    c2.metric("Exchange", row["exchange"])
    c3.metric("Lot Size", row["lot_size"])

    with st.expander("Full Details"):
        st.json(row.to_dict())
