import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Weekly Trend Scanner", page_icon="📈", layout="wide")

st.title("📊 Weekly Trend Scanner")
st.markdown("**Quantum Super – din trendscanner**")

timeframe = st.radio("Välj tidsram", ["Veckobasis", "Dagbasis"], horizontal=True)
mode = "weekly" if timeframe == "Veckobasis" else "daily"

st.success("Appen laddas... (testversion)")

# Enkel testtabell så du ser att den fungerar
data = {
    "Ticker": ["BTC-USD", "ETH-USD", "AAPL", "EVO.ST"],
    "Trend": ["STRONG UP-TREND", "STRONG DOWN-TREND", "STRONG UP-TREND", "STRONG UP-TREND"],
    "Weeks/Days": [3, 1, 2, 4],
    "Price": [65000, 3200, 227, 638],
    "Rörelse (%)": ["+2.3%", "-1.1%", "+4.5%", "+6.3%"]
}
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)

st.divider()
st.markdown("Byggd med ❤️ för trendbaserad trading")
