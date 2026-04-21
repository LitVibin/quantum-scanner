import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Quantum Super", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .main {background-color: #0f172a;}
    h1 {color: #00E5FF; font-weight: 700;}
    .stTabs [data-baseweb="tab-list"] button {font-size: 1.1rem; font-weight: 600;}
    .stDataFrame {background-color: #1e2937; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Quantum Super")
st.markdown("**Weekly Trend Scanner med din exakta Quantum Trend**")

# Quantum-parametrar från din Pine Script
LSMA_LENGTH = 72
ALMA_LENGTH = 33
ALMA_OFFSET = 0.85
ALMA_SIGMA = 6
ATR_LENGTH = 14
ATR_MULTIPLIER = 0.35
MAX_DURATION = 50

# Stora fallback för att nå 500+ marknader
SP500_FALLBACK = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","LLY","AVGO","JPM","V","MA","XOM","UNH",
    "JNJ","PG","HD","MRK","COST","ABBV","AMD","NFLX","PEP","KO","CRM","ADBE","TMO","MCD","CSCO","ACN",
    "ABT","LIN","WMT","INTU","QCOM","NOW","AMGN","ISRG","BKNG","SPGI","INTC","VZ","UNP","HON","PFE",
    "RTX","CAT","GS","MS","BLK","AXP","SYK","ELV","MDT","PLD","ETN","DE","SCHW","REGN","LMT","T",
    "MO","BMY","GILD","ADI","PANW","KLAC","SNPS","CDNS","ANET","ADP","FI","CME","ICE","ZTS","SHW",
    "ITW","EOG","SLB","SO","DUK","NEE","PNC","USB","TGT","TJX","CSX","CL","MMM","GE","HCA","EMR",
    "BDX","APD","WM","AON","MPC","PSX","VLO","OXY","COP","CVX","HAL","BKR","FANG","DVN","EQT",
    "MRO","APA","CVS","CI","HUM","EL","LOW","ORCL","IBM","TXN","AMAT","MU","LRCX","ASML","ARM",
    "CRWD","PLTR","SNOW","DDOG","ZS","NET","MDB","TEAM","OKTA","DOCU","WDAY","ADSK","FTNT","CYBR",
    "SPLK","ESTC","HUBS","TWLO","SHOP","MELI","PDD","JD","BABA","BIDU","NTES","SE","TTD","RBLX",
    "EA","TTWO","ATVI","UBER","LYFT","DASH","ABNB","BKNG","MAR","HLT","VICI","EXR","PSA","AVB",
    "EQR","ESS","MAA","CPT","UDR","INVH","AMH","SUI","ELS","KIM","FRT","REG","NNN","O","WPC","ADC",
    "EQIX","DLR","SBAC","AMT","CCI","D","AEP","XEL","ED","PEG","WEC","ES","AEE","CNP","CMS","LNT",
    "EVRG","NI","PNW","PPL","FE","ETR","AWK"
]

CRYPTO_TICKERS = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD","DOGE-USD","AVAX-USD","TRX-USD","DOT-USD","LINK-USD","MATIC-USD","TON11419-USD","SHIB-USD","LTC-USD","BCH-USD","UNI7083-USD","XLM-USD","ATOM-USD","ETC-USD","ICP-USD","FIL-USD","APT21794-USD","HBAR-USD","ARB11841-USD","NEAR-USD","OP-USD","CRO-USD"]
SWEDISH_TICKERS = ["^OMXS30","ABB.ST","ALFA.ST","ASSA-B.ST","ATCO-A.ST","ATCO-B.ST","AZN.ST","BOL.ST","ELUX-B.ST","ERIC-B.ST","ESSITY-B.ST","EVO.ST","GETI-B.ST","HEXA-B.ST","HM-B.ST","INVE-B.ST","KINV-B.ST","NDA-SE.ST","SAND.ST","SBB-B.ST","SEB-A.ST","SHB-A.ST","SINCH.ST","SKF-B.ST","SSAB-A.ST","SWED-A.ST","TEL2-B.ST","TELIA.ST","VOLV-B.ST"]
COMMODITIES_TICKERS = ["GC=F","SI=F","CL=F","NG=F","HG=F","PL=F"]
MAJOR_INDICES = ["^DJI","^IXIC","^RUT","^VIX","^GSPC","^FTSE","^N225"]

def get_all_tickers():
    all_t = SP500_FALLBACK + CRYPTO_TICKERS + SWEDISH_TICKERS + COMMODITIES_TICKERS + MAJOR_INDICES
    return sorted(set(all_t))

# ====================== QUANTUM TREND ======================
def calculate_quantum_trend(df):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    lsma = ta.linreg(close, length=LSMA_LENGTH, offset=0)
    trend_base = ta.alma(lsma, length=ALMA_LENGTH, offset=ALMA_OFFSET, sigma=ALMA_SIGMA)
    atr = ta.atr(high, low, close, length=ATR_LENGTH)

    band_offset = atr * ATR_MULTIPLIER
    upper = trend_base + band_offset
    lower = trend_base - band_offset

    direction = pd.Series(0, index=df.index)
    final_line = pd.Series(0.0, index=df.index)

    if len(df) > 0:
        final_line.iloc[0] = trend_base.iloc[0]
        direction.iloc[0] = 1 if close.iloc[0] >= trend_base.iloc[0] else -1

    for i in range(1, len(df)):
        if direction.iloc[i-1] == 1:
            if close.iloc[i] < lower.iloc[i]:
                direction.iloc[i] = -1
                final_line.iloc[i] = upper.iloc[i]
            else:
                direction.iloc[i] = 1
                final_line.iloc[i] = max(lower.iloc[i], final_line.iloc[i-1])
        else:
            if close.iloc[i] > upper.iloc[i]:
                direction.iloc[i] = 1
                final_line.iloc[i] = lower.iloc[i]
            else:
                direction.iloc[i] = -1
                final_line.iloc[i] = min(upper.iloc[i], final_line.iloc[i-1])

    return direction, final_line

# ====================== APP ======================
timeframe = st.radio("Välj tidsram", ["Veckobasis", "Dagbasis"], horizontal=True)
mode = "weekly" if timeframe == "Veckobasis" else "daily"

if "data" not in st.session_state or st.session_state.get("last_mode") != mode:
    with st.spinner("Scannar alla marknader..."):
        st.session_state.data = scan_trends(mode)
        st.session_state.last_mode = mode

df = st.session_state.data

st.success(f"✅ Scannade **{len(df)}** marknader")

def color_row(row):
    color = "#00E5FF20" if row["Trend"] == "STRONG UP-TREND" else "#D500F920"
    return [f"background-color: {color}"] * len(row)

tab1, tab2, tab3, tab4 = st.tabs(["🔥 Nya 1-veckors/dagars trendskiften", "₿ Krypto", "📈 Aktier", "🪙 Råvaror & Index"])

with tab1:
    st.subheader(f"🔥 NYA TRENDSKIFTEN (1 {timeframe.lower()})")
    one_unit = df[df["Weeks/Days in trend"] == 1]
    for _, row in one_unit.iterrows():
        prompt = f"Analysera {row['Ticker']} som precis flippat till **{row['Trend']}** i exakt 1 {timeframe.lower()}. Pris: {row['Price']}, Rörelse: {row['Rörelse (%)']}, Invalidering: {row['Invalidering (pris)']}. Ge support/resistens, entry, risk/reward och SL/TP."
        with st.expander(f"{row['Ticker']} | {row['Trend']} | {row['Rörelse (%)']}"):
            st.code(prompt, language="markdown")
            if st.button("Kopiera prompt", key=row['Ticker']):
                st.clipboard(prompt)
                st.success("✅ Kopierad!")

with tab2: st.subheader("₿ Krypto"); st.dataframe(df[df['Ticker'].str.contains("-USD")].style.apply(color_row, axis=1), column_config={"TV_URL": st.column_config.LinkColumn("Länk", display_text="🔗 TradingView")}, use_container_width=True, height=700, hide_index=True)
with tab3: st.subheader("📈 Aktier"); st.dataframe(df[~df['Ticker'].str.contains("-USD") & ~df['Ticker'].str.contains("=F")].style.apply(color_row, axis=1), column_config={"TV_URL": st.column_config.LinkColumn("Länk", display_text="🔗 TradingView")}, use_container_width=True, height=700, hide_index=True)
with tab4: st.subheader("🪙 Råvaror & Index"); st.dataframe(df[df['Ticker'].str.contains("=F") | df['Ticker'].str.startswith("^")].style.apply(color_row, axis=1), column_config={"TV_URL": st.column_config.LinkColumn("Länk", display_text="🔗 TradingView")}, use_container_width=True, height=700, hide_index=True)

st.divider()
st.markdown("Byggd med ❤️ för trendbaserad trading – Quantum Super")
