import streamlit as st
import pandas as pd

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Zerodha Instrument Finder", layout="wide")
st.title("🔍 Zerodha Instrument Token Finder")
st.markdown("Search for Stocks, Futures, and Options to find their **Instrument Token**.")

# --- 2. LOAD DATA (Cached for Speed) ---
@st.cache_data
def load_instruments():
    """
    Fetches the daily instrument dump from Zerodha public API.
    This file contains every single tradable symbol (Stocks, F/O, CDS, MCX).
    """
    url = "https://api.kite.trade/instruments"
    try:
        with st.spinner("Downloading Instrument List from Zerodha..."):
            df = pd.read_csv(url)
            return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df_master = load_instruments()

if not df_master.empty:
    # --- 3. SEARCH FILTERS ---
    col1, col2 = st.columns(2)
    
    with col1:
        # Filter by Exchange (NSE, NFO, BSE, MCX)
        exchanges = df_master['exchange'].unique().tolist()
        selected_exchange = st.selectbox("Select Exchange", options=["NSE", "NFO", "BSE", "MCX"], index=0)

    with col2:
        # Filter by Segment type if needed (Optional refinement)
        segment_options = df_master[df_master['exchange'] == selected_exchange]['segment'].unique()
        selected_segment = st.selectbox("Select Segment", options=segment_options)

    # --- 4. THE SEARCHABLE DROPDOWN ---
    # Filter the dataframe based on previous selections
    filtered_df = df_master[
        (df_master['exchange'] == selected_exchange) & 
        (df_master['segment'] == selected_segment)
    ]

    # Create a display label: "Symbol (Name)"
    # We use tradingsymbol for the search
    search_list = filtered_df['tradingsymbol'].tolist()
    
    st.divider()
    
    # The magic search box
    selected_symbol = st.selectbox(
        "Start typing to search for the Instrument (e.g., RELIANCE, NIFTY24JANFUT)", 
        options=search_list,
        index=None,
        placeholder="Type symbol here..."
    )

    # --- 5. DISPLAY RESULTS ---
    if selected_symbol:
        # Get the row for the selected symbol
        row = filtered_df[filtered_df['tradingsymbol'] == selected_symbol].iloc[0]
        
        st.success(f"✅ Found: {row['tradingsymbol']}")
        
        # Display Key Metrics in big text
        m1, m2, m3 = st.columns(3)
        m1.metric("Instrument Token", str(row['instrument_token']))
        m2.metric("Exchange", row['exchange'])
        m3.metric("Lot Size", row['lot_size'])

        # Show full details in a table
        with st.expander("See Full Instrument Details", expanded=True):
            st.json(row.to_dict())

else:
    st.warning("Could not load instrument data. Check your internet connection.")