import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings("ignore")

# ====================== CONFIG ======================
st.set_page_config(page_title="Quantum Super", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .main {background-color: #0f172a;}
    .stApp {background-color: #0f172a;}
    h1, h2, h3 {color: #00E5FF; font-weight: 700; letter-spacing: -0.5px;}
    .stTabs [data-baseweb="tab-list"] button {font-size: 1.05rem; font-weight: 600;}
    .stDataFrame {background-color: #1e2937;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Quantum Super")
st.markdown("**Weekly Trend Scanner med Quantum Trend-logik**")

# ====================== PARAMETERS ======================
LSMA_LENGTH = 72
ALMA_LENGTH = 33
ALMA_OFFSET = 0.85
ALMA_SIGMA = 6
ATR_LENGTH = 14
ATR_MULTIPLIER = 0.35
MAX_DURATION = 50

# ====================== MARKETS ======================
SP500_FALLBACK = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","LLY","AVGO","JPM","V","MA","XOM","UNH","JNJ","PG","HD","MRK",
    "COST","ABBV","AMD","NFLX","PEP","KO","CRM","ADBE","TMO","MCD","CSCO","ACN","ABT","LIN","WMT","INTU","QCOM","NOW","AMGN",
    "ISRG","BKNG","SPGI","INTC","VZ","UNP","HON","PFE","RTX","CAT","GS","MS","BLK","AXP","SYK","ELV","MDT","PLD","ETN","DE",
    "SCHW","REGN","LMT","T","MO","BMY","GILD","ADI","PANW","KLAC","SNPS","CDNS","ANET","ADP","FI","CME","ICE","ZTS","SHW",
    "ITW","EOG","SLB","SO","DUK","NEE","PNC","USB","TGT","TJX","CSX","CL","MMM","GE","HCA","EMR","BDX","APD","WM","AON",
    "MPC","PSX","VLO","OXY","COP","CVX","HAL","BKR","FANG","DVN","EQT","MRO","APA","CVS","CI","HUM","EL","LOW","ORCL",
    "IBM","TXN","AMAT","MU","LRCX","ASML","CRWD","PLTR","SNOW","DDOG","ZS","NET","MDB","TEAM","OKTA","DOCU","WDAY","ADSK",
    "FTNT","CYBR","HUBS","TWLO","SHOP","MELI","PDD","JD","BABA","BIDU","NTES","SE","TTD","RBLX","EA","UBER","ABNB","MAR",
    "HLT","VICI","EXR","PSA","AVB","EQR","ESS","MAA","CPT","UDR","INVH","AMH","SUI","ELS","KIM","FRT","REG","NNN","O",
    "WPC","ADC","EQIX","DLR","SBAC","AMT","CCI","D","AEP","XEL","ED","PEG","WEC","ES","AEE","CNP","CMS","LNT","EVRG",
    "NI","PNW","PPL","FE","ETR","AWK"
]

CRYPTO_TICKERS = [
    "BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD","DOGE-USD","AVAX-USD","TRX-USD","DOT-USD","LINK-USD",
    "MATIC-USD","SHIB-USD","LTC-USD","BCH-USD","XLM-USD","ATOM-USD","ETC-USD","ICP-USD","FIL-USD","HBAR-USD","NEAR-USD",
    "OP-USD","CRO-USD"
]

SWEDISH_TICKERS = [
    "^OMXS30","ABB.ST","ALFA.ST","ASSA-B.ST","ATCO-A.ST","ATCO-B.ST","AZN.ST","BOL.ST","ELUX-B.ST","ERIC-B.ST","ESSITY-B.ST",
    "EVO.ST","GETI-B.ST","HEXA-B.ST","HM-B.ST","INVE-B.ST","KINV-B.ST","NDA-SE.ST","SAND.ST","SBB-B.ST","SEB-A.ST","SHB-A.ST",
    "SINCH.ST","SKF-B.ST","SSAB-A.ST","SWED-A.ST","TEL2-B.ST","TELIA.ST","VOLV-B.ST"
]

COMMODITIES_TICKERS = ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "PL=F"]
MAJOR_INDICES = ["^DJI", "^IXIC", "^RUT", "^VIX", "^GSPC", "^FTSE", "^N225"]

NAME_MAP = {
    "^OMXS30": "OMXS30",
    "^DJI": "Dow Jones",
    "^IXIC": "Nasdaq Composite",
    "^RUT": "Russell 2000",
    "^VIX": "VIX",
    "^GSPC": "S&P 500",
    "^FTSE": "FTSE 100",
    "^N225": "Nikkei 225",
    "GC=F": "Gold",
    "SI=F": "Silver",
    "CL=F": "Crude Oil",
    "NG=F": "Natural Gas",
    "HG=F": "Copper",
    "PL=F": "Platinum",
}

def get_all_tickers():
    return sorted(set(SP500_FALLBACK + CRYPTO_TICKERS + SWEDISH_TICKERS + COMMODITIES_TICKERS + MAJOR_INDICES))

def get_category(ticker: str) -> str:
    if ticker in CRYPTO_TICKERS:
        return "Krypto"
    if ticker in COMMODITIES_TICKERS or ticker in MAJOR_INDICES:
        return "Råvaror & Index"
    return "Aktier"

# ====================== INDICATORS ======================
def lsma(series: pd.Series, length: int) -> pd.Series:
    def calc(window):
        y = np.array(window, dtype=float)
        x = np.arange(len(y), dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        return intercept + slope * (len(y) - 1)
    return series.rolling(length).apply(calc, raw=False)

def alma(series: pd.Series, length: int, offset: float = 0.85, sigma: float = 6) -> pd.Series:
    m = offset * (length - 1)
    s = length / sigma
    weights = np.array([np.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(length)], dtype=float)
    weights /= weights.sum()

    def calc(window):
        arr = np.array(window, dtype=float)
        return np.dot(arr, weights)

    return series.rolling(length).apply(calc, raw=False)

def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(length).mean()

# ====================== QUANTUM TREND ======================
def calculate_quantum_trend(df: pd.DataFrame):
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)

    lsma_line = lsma(close, LSMA_LENGTH)
    trend_base = alma(lsma_line, ALMA_LENGTH, ALMA_OFFSET, ALMA_SIGMA)
    atr_line = atr(high, low, close, ATR_LENGTH)

    band_offset = atr_line * ATR_MULTIPLIER
    upper = trend_base + band_offset
    lower = trend_base - band_offset

    direction = pd.Series(index=df.index, dtype="float64")
    final_line = pd.Series(index=df.index, dtype="float64")

    start_idx = None
    for i in range(len(df)):
        if pd.notna(trend_base.iloc[i]) and pd.notna(upper.iloc[i]) and pd.notna(lower.iloc[i]):
            start_idx = i
            break

    if start_idx is None:
        return None, None

    direction.iloc[start_idx] = 1 if close.iloc[start_idx] >= trend_base.iloc[start_idx] else -1
    final_line.iloc[start_idx] = lower.iloc[start_idx] if direction.iloc[start_idx] == 1 else upper.iloc[start_idx]

    for i in range(start_idx + 1, len(df)):
        prev_dir = direction.iloc[i - 1]

        if prev_dir == 1:
            if close.iloc[i] < lower.iloc[i]:
                direction.iloc[i] = -1
                final_line.iloc[i] = upper.iloc[i]
            else:
                direction.iloc[i] = 1
                final_line.iloc[i] = max(lower.iloc[i], final_line.iloc[i - 1])
        else:
            if close.iloc[i] > upper.iloc[i]:
                direction.iloc[i] = 1
                final_line.iloc[i] = lower.iloc[i]
            else:
                direction.iloc[i] = -1
                final_line.iloc[i] = min(upper.iloc[i], final_line.iloc[i - 1])

    return direction.ffill(), final_line.ffill()

def count_bars_in_trend(direction: pd.Series) -> int:
    if direction is None or len(direction.dropna()) == 0:
        return 0
    last_dir = direction.dropna().iloc[-1]
    count = 0
    for value in reversed(direction.dropna().tolist()):
        if value == last_dir:
            count += 1
        else:
            break
    return count

# ====================== DATA FETCH ======================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ohlc(ticker: str, interval_mode: str) -> pd.DataFrame:
    if interval_mode == "weekly":
        period = "10y"
        interval = "1wk"
    else:
        period = "2y"
        interval = "1d"

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False
    )

    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    needed = ["Open", "High", "Low", "Close", "Volume"]
    cols = [c for c in needed if c in df.columns]
    df = df[cols].copy()
    df.dropna(subset=["High", "Low", "Close"], inplace=True)

    return df

def get_invalidation_price(last_direction: float, final_line: pd.Series) -> float | None:
    if final_line is None or final_line.dropna().empty:
        return None
    return float(final_line.dropna().iloc[-1])

def get_move_pct(df: pd.DataFrame, bars_in_trend: int) -> float | None:
    if df.empty or bars_in_trend <= 0 or len(df) < bars_in_trend:
        return None
    start_price = float(df["Close"].iloc[-bars_in_trend])
    last_price = float(df["Close"].iloc[-1])
    if start_price == 0:
        return None
    return ((last_price / start_price) - 1) * 100

def get_display_name(ticker: str) -> str:
    return NAME_MAP.get(ticker, ticker)

def build_tv_link(ticker: str) -> str:
    clean = ticker.replace("-", "").replace("=", "").replace("^", "")
    return f"https://www.tradingview.com/chart/?symbol={clean}"

# ====================== SCAN ======================
def analyze_ticker(ticker: str, mode: str):
    try:
        df = fetch_ohlc(ticker, mode)
        if df.empty or len(df) < 140:
            return None

        direction, final_line = calculate_quantum_trend(df)
        if direction is None or final_line is None:
            return None

        valid_dir = direction.dropna()
        if len(valid_dir) < 2:
            return None

        last_dir = int(valid_dir.iloc[-1])
        prev_dir = int(valid_dir.iloc[-2])
        bars_in_trend = count_bars_in_trend(direction)

        if bars_in_trend == 0:
            return None

        trend_label = "STRONG UP-TREND" if last_dir == 1 else "STRONG DOWN-TREND"
        trend_shift = last_dir != prev_dir
        last_price = float(df["Close"].iloc[-1])
        move_pct = get_move_pct(df, bars_in_trend)
        invalidation = get_invalidation_price(last_dir, final_line)

        return {
            "Ticker": ticker,
            "Namn": get_display_name(ticker),
            "Kategori": get_category(ticker),
            "Trend": trend_label,
            "Weeks/Days in trend": min(int(bars_in_trend), MAX_DURATION),
            "Price": round(last_price, 4),
            "Rörelse (%)": None if move_pct is None else round(move_pct, 2),
            "Invalidering (pris)": None if invalidation is None else round(invalidation, 4),
            "TradingView": build_tv_link(ticker),
            "TrendShiftNow": trend_shift,
        }

    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def scan_trends(mode: str) -> pd.DataFrame:
    tickers = get_all_tickers()
    rows = []

    for ticker in tickers:
        result = analyze_ticker(ticker, mode)
        if result is not None:
            rows.append(result)

    if not rows:
        return pd.DataFrame(columns=[
            "Ticker","Namn","Kategori","Trend","Weeks/Days in trend",
            "Price","Rörelse (%)","Invalidering (pris)","TradingView","TrendShiftNow"
        ])

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["Weeks/Days in trend", "Ticker"], ascending=[True, True]).reset_index(drop=True)
    return df

# ====================== UI HELPERS ======================
def color_row(row):
    bg = "#00E5FF20" if row["Trend"] == "STRONG UP-TREND" else "#D500F920"
    return [f"background-color: {bg}"] * len(row)

def show_table(data: pd.DataFrame, title: str):
    st.subheader(title)

    if data.empty:
        st.info("Inga träffar just nu.")
        return

    display_cols = [
        "Ticker", "Namn", "Trend", "Weeks/Days in trend",
        "Price", "Rörelse (%)", "Invalidering (pris)", "TradingView"
    ]

    styled = data[display_cols].style.apply(color_row, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        height=560,
        column_config={
            "TradingView": st.column_config.LinkColumn("TradingView", display_text="Öppna"),
            "Price": st.column_config.NumberColumn(format="%.4f"),
            "Rörelse (%)": st.column_config.NumberColumn(format="%.2f"),
            "Invalidering (pris)": st.column_config.NumberColumn(format="%.4f"),
        }
    )

def grok_prompt(row: pd.Series, mode_label: str) -> str:
    return f"""Analysera {row['Ticker']} ({row['Namn']}) som precis har gett ett nytt Quantum Super {mode_label.lower()} trendskifte.

Data:
- Trend: {row['Trend']}
- Duration: {row['Weeks/Days in trend']} {mode_label.lower()}
- Pris: {row['Price']}
- Rörelse sedan trendstart: {row['Rörelse (%)']}%
- Invalidering: {row['Invalidering (pris)']}

Ge mig:
1. Trendkvalitet
2. Viktiga stöd/motstånd
3. Risk/reward
4. Mest sannolika scenario kommande 1–4 {mode_label.lower()}
5. Vad som skulle invalidera caset
"""

# ====================== APP ======================
timeframe = st.radio("Välj tidsram", ["Veckobasis", "Dagbasis"], horizontal=True)
mode = "weekly" if timeframe == "Veckobasis" else "daily"
mode_label = "Weeks" if mode == "weekly" else "Days"

if "data" not in st.session_state or st.session_state.get("last_mode") != mode:
    with st.spinner("Scannar alla marknader..."):
        st.session_state.data = scan_trends(mode)
        st.session_state.last_mode = mode

df = st.session_state.data.copy()

st.success(f"✅ Scannade **{len(get_all_tickers())}** marknader | Hittade **{len(df)}** aktiva trender")

new_shifts = df[df["TrendShiftNow"] == True].copy()
crypto_df = df[df["Kategori"] == "Krypto"].copy()
stocks_df = df[df["Kategori"] == "Aktier"].copy()
macro_df = df[df["Kategori"] == "Råvaror & Index"].copy()

tab1, tab2, tab3, tab4 = st.tabs([
    "Nya 1-veckors/dagars trendskiften",
    "Krypto",
    "Aktier",
    "Råvaror & Index"
])

with tab1:
    show_table(new_shifts, "Nya trendskiften")

    if not new_shifts.empty:
        st.markdown("### Grok-prompts")
        for _, row in new_shifts.iterrows():
            with st.expander(f"{row['Ticker']} — {row['Trend']}"):
                st.code(grok_prompt(row, mode_label), language="markdown")

with tab2:
    show_table(crypto_df, "Krypto")

with tab3:
    show_table(stocks_df, "Aktier")

with tab4:
    show_table(macro_df, "Råvaror & Index")

st.divider()
st.markdown("Byggd med ❤️ för trendbaserad trading – Quantum Super")
