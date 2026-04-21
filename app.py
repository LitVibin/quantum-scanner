import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import warnings

warnings.filterwarnings("ignore")

# ====================== CONFIG ======================
st.set_page_config(page_title="Quantum Super", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .main {background-color: #0f172a;}
    .stApp {background-color: #0f172a;}
    h1 {color: #00E5FF; font-weight: 700; letter-spacing: -1px;}
    .stTabs [data-baseweb="tab-list"] button {font-size: 1.05rem; font-weight: 600;}
    .stDataFrame {background-color: #1e2937; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Quantum Super")
st.caption("Quantum Trend – LSMA 72 + ALMA 33 + ATR 14 × 0.35")

# ====================== PARAMETRAR ======================
LSMA_LENGTH = 72
ALMA_LENGTH = 33
ALMA_OFFSET = 0.85
ALMA_SIGMA = 6
ATR_LENGTH = 14
ATR_MULTIPLIER = 0.35
MAX_DURATION = 50

BULL_COLOR = "#00E5FF"
BEAR_COLOR = "#D500F9"

# ====================== TICKERS ======================
SP500_FALLBACK = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","LLY","AVGO","JPM","V","MA","XOM","UNH","JNJ","PG","HD","MRK",
    "COST","ABBV","AMD","NFLX","PEP","KO","CRM","ADBE","TMO","MCD","CSCO","ACN","ABT","LIN","WMT","INTU","QCOM","NOW","AMGN",
    "ISRG","BKNG","SPGI","INTC","VZ","UNP","HON","PFE","RTX","CAT","GS","MS","BLK","AXP","SYK","ELV","MDT","PLD","ETN","DE",
    "SCHW","REGN","LMT","T","MO","BMY","GILD","ADI","PANW","KLAC","SNPS","CDNS","ANET","ADP","FI","CME","ICE","ZTS","SHW",
    "ITW","EOG","SLB","SO","DUK","NEE","PNC","USB","TGT","TJX","CSX","CL","MMM","GE","HCA","EMR","BDX","APD","WM","AON",
    "MPC","PSX","VLO","OXY","COP","CVX","HAL","BKR","FANG","DVN","EQT","MRO","APA","CVS","CI","HUM","EL","LOW","ORCL",
    "IBM","TXN","AMAT","MU","LRCX","ASML","CRWD","PLTR","SNOW","DDOG","ZS","NET","MDB","TEAM","OKTA","DOCU","WDAY","ADSK",
    "FTNT","CYBR","HUBS","TWLO","SHOP","MELI","PDD","JD","BABA","BIDU","NTES","SE","TTD","RBLX","EA","TTWO","UBER","ABNB",
    "MAR","HLT","VICI","EXR","PSA","AVB","EQR","ESS","MAA","CPT","UDR","INVH","AMH","SUI","ELS","KIM","FRT","REG","NNN",
    "O","WPC","ADC","EQIX","DLR","SBAC","AMT","CCI","D","AEP","XEL","ED","PEG","WEC","ES","AEE","CNP","CMS","LNT","EVRG",
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

def get_display_name(ticker: str) -> str:
    return NAME_MAP.get(ticker, ticker)

def build_tv_link(ticker: str) -> str:
    symbol = ticker
    if ticker.endswith(".ST"):
        symbol = f"OMXSTO:{ticker.replace('.ST', '')}"
    elif ticker == "^OMXS30":
        symbol = "OMXSTO:OMXS30"
    elif ticker == "^GSPC":
        symbol = "SP:SPX"
    elif ticker == "^DJI":
        symbol = "DJ:DJI"
    elif ticker == "^IXIC":
        symbol = "NASDAQ:IXIC"
    elif ticker == "^RUT":
        symbol = "RUSSELL:RUT"
    elif ticker == "^FTSE":
        symbol = "INDEX:UKX"
    elif ticker == "^N225":
        symbol = "INDEX:NI225"
    elif ticker == "^VIX":
        symbol = "CBOE:VIX"
    return f"https://www.tradingview.com/chart/?symbol={symbol}"

# ====================== INDIKATORER ======================
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
    weights = np.exp(-((np.arange(length) - m) ** 2) / (2 * s * s))
    weights = weights / weights.sum()

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
        return None, None, None

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

    return direction.ffill(), final_line.ffill(), trend_base

def count_bars_in_trend(direction: pd.Series) -> int:
    clean = direction.dropna()
    if clean.empty:
        return 0
    last_dir = clean.iloc[-1]
    count = 0
    for v in reversed(clean.tolist()):
        if v == last_dir:
            count += 1
        else:
            break
    return count

# ====================== DATA ======================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ohlc(ticker: str, mode: str) -> pd.DataFrame:
    if mode == "weekly":
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

    wanted = ["Open", "High", "Low", "Close", "Volume"]
    keep = [c for c in wanted if c in df.columns]
    df = df[keep].copy()
    df.dropna(subset=["High", "Low", "Close"], inplace=True)
    return df

def get_move_pct(df: pd.DataFrame, bars_in_trend: int) -> float | None:
    if df.empty or bars_in_trend <= 0 or len(df) < bars_in_trend:
        return None
    start_price = float(df["Close"].iloc[-bars_in_trend])
    end_price = float(df["Close"].iloc[-1])
    if start_price == 0:
        return None
    return ((end_price / start_price) - 1) * 100.0

def create_mini_chart(df: pd.DataFrame, final_line: pd.Series, ticker: str):
    if df.empty or final_line is None:
        return None

    chart_df = pd.DataFrame({
        "Close": df["Close"],
        "TrendLine": final_line
    }).dropna().tail(80)

    if chart_df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df["Close"],
        mode="lines",
        name="Pris",
        line=dict(width=2)
    ))
    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df["TrendLine"],
        mode="lines",
        name="Quantum Trend",
        line=dict(width=2, color=BULL_COLOR)
    ))

    fig.update_layout(
        title=ticker,
        height=180,
        margin=dict(l=10, r=10, t=35, b=10),
        template="plotly_dark",
        showlegend=False
    )
    return fig

def grok_prompt(row: pd.Series, bar_label: str) -> str:
    return f"""Analysera {row['Ticker']} ({row['Namn']}) som precis har gett ett nytt Quantum Super-trendskifte.

Data:
- Trend: {row['Trend']}
- Duration: {row['Weeks/Days in trend']} {bar_label.lower()}
- Pris: {row['Price']}
- Rörelse sedan trendstart: {row['Rörelse (%)']}%
- Invalidering: {row['Invalidering (pris)']}

Ge mig:
1. Trendkvalitet
2. Viktiga stöd/motstånd
3. Risk/reward
4. Mest sannolika scenario kommande 1–4 {bar_label.lower()}
5. Vad som invaliderar caset
"""

def analyze_ticker(ticker: str, mode: str):
    try:
        df = fetch_ohlc(ticker, mode)
        if df.empty or len(df) < 140:
            return None

        direction, final_line, trend_base = calculate_quantum_trend(df)
        if direction is None or final_line is None:
            return None

        clean_dir = direction.dropna()
        if len(clean_dir) < 2:
            return None

        last_dir = int(clean_dir.iloc[-1])
        prev_dir = int(clean_dir.iloc[-2])
        bars_in_trend = count_bars_in_trend(direction)
        if bars_in_trend <= 0:
            return None

        last_price = float(df["Close"].iloc[-1])
        move_pct = get_move_pct(df, bars_in_trend)
        invalidation = float(final_line.dropna().iloc[-1])

        return {
            "Ticker": ticker,
            "Namn": get_display_name(ticker),
            "Kategori": get_category(ticker),
            "Trend": "Bull" if last_dir == 1 else "Bear",
            "Weeks/Days in trend": min(bars_in_trend, MAX_DURATION),
            "Price": round(last_price, 4),
            "Rörelse (%)": None if move_pct is None else round(move_pct, 2),
            "Invalidering (pris)": round(invalidation, 4),
            "TradingView": build_tv_link(ticker),
            "TrendShiftNow": last_dir != prev_dir,
            "ChartDF": df.tail(120).copy(),
            "FinalLine": final_line.tail(120).copy()
        }
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def scan_trends(mode: str) -> pd.DataFrame:
    rows = []
    for ticker in get_all_tickers():
        row = analyze_ticker(ticker, mode)
        if row is not None:
            rows.append(row)

    if not rows:
        return pd.DataFrame(columns=[
            "Ticker", "Namn", "Kategori", "Trend", "Weeks/Days in trend",
            "Price", "Rörelse (%)", "Invalidering (pris)", "TradingView",
            "TrendShiftNow", "ChartDF", "FinalLine"
        ])

    df = pd.DataFrame(rows)
    df = df.sort_values(["Weeks/Days in trend", "Ticker"], ascending=[True, True]).reset_index(drop=True)
    return df

# ====================== UI ======================
def color_row(row):
    bg = "#00E5FF20" if row["Trend"] == "Bull" else "#D500F920"
    return [f"background-color: {bg}"] * len(row)

def show_styled_table(data: pd.DataFrame, key: str):
    if data.empty:
        st.info("Inga träffar just nu.")
        return

    table_df = data[[
        "Ticker", "Namn", "Trend", "Weeks/Days in trend",
        "Price", "Rörelse (%)", "Invalidering (pris)", "TradingView"
    ]].copy()

    styled = table_df.style.apply(color_row, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        key=key,
        column_config={
            "TradingView": st.column_config.LinkColumn("TradingView", display_text="Öppna"),
            "Price": st.column_config.NumberColumn(format="%.4f"),
            "Rörelse (%)": st.column_config.NumberColumn(format="%.2f"),
            "Invalidering (pris)": st.column_config.NumberColumn(format="%.4f"),
        }
    )

# ====================== APP ======================
timeframe = st.radio("Välj tidsram", ["Veckobasis", "Dagbasis"], horizontal=True)
mode = "weekly" if timeframe == "Veckobasis" else "daily"
bar_label = "Weeks" if mode == "weekly" else "Days"

if "data" not in st.session_state or st.session_state.get("last_mode") != mode:
    with st.spinner("Scannar alla marknader..."):
        st.session_state.data = scan_trends(mode)
        st.session_state.last_mode = mode

df = st.session_state.data.copy()

st.success(f"✅ Scannade **{len(get_all_tickers())}** marknader")

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
    st.subheader("Nya trendskiften")
    show_styled_table(new_shifts, "new_shifts_table")

    if not new_shifts.empty:
        st.markdown("### Charts & Grok-prompts")
        for i, (_, row) in enumerate(new_shifts.iterrows()):
            with st.expander(f"{row['Ticker']} • {row['Trend']} • {row['Weeks/Days in trend']} {bar_label.lower()}"):
                fig = create_mini_chart(row["ChartDF"], row["FinalLine"], row["Ticker"])
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{row['Ticker']}_{i}")

                prompt = grok_prompt(row, bar_label)
                st.code(prompt, language="text")

with tab2:
    st.subheader("Krypto")
    show_styled_table(crypto_df, "crypto_table")

with tab3:
    st.subheader("Aktier")
    show_styled_table(stocks_df, "stocks_table")

with tab4:
    st.subheader("Råvaror & Index")
    show_styled_table(macro_df, "macro_table")

st.divider()
st.markdown("Byggd med ❤️ för trendbaserad trading – Quantum Super")
