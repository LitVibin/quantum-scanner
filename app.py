import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import warnings
warnings.filterwarnings("ignore")

# ====================== CONFIG ======================
st.set_page_config(page_title="Weekly Trend Scanner", page_icon="📈", layout="wide")

st.title("📊 Weekly Trend Scanner")
st.markdown("**Quantum Super – med exakta färger & bred marknad**")

# Quantum Trend-parametrar
LSMA_LENGTH = 72
ALMA_LENGTH = 33
ALMA_OFFSET = 0.85
ALMA_SIGMA = 6
ATR_LENGTH = 14
ATR_MULTIPLIER = 0.35

SHOW_TOP = 50
MIN_DURATION = 1
MAX_DURATION = 50

# Ticker-listor med stor fallback
SP500_FALLBACK = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","LLY","AVGO","JPM","V","MA","XOM","UNH","JNJ","PG","HD","MRK","COST","ABBV","AMD","NFLX","PEP","KO","CRM","ADBE","TMO","MCD","CSCO","ACN","ABT","LIN","WMT","INTU","QCOM","NOW","AMGN","ISRG","BKNG","SPGI","INTC","VZ","UNP","HON","PFE","RTX","CAT","GS","MS","BLK","AXP","SYK","ELV","MDT","PLD","ETN","DE","SCHW","REGN","LMT","T","MO","BMY","GILD","ADI","PANW","KLAC","SNPS","CDNS","ANET","ADP","FI","CME","ICE","ZTS","SHW","ITW","EOG","SLB","SO","DUK","NEE","PNC","USB","TGT","TJX","CSX","CL","MMM","GE","HCA","EMR","BDX","APD","WM","AON","MPC","PSX","VLO","OXY","COP","CVX","HAL","BKR","FANG","DVN","EQT","MRO","APA"]
CRYPTO_TICKERS = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD","DOGE-USD","AVAX-USD","TRX-USD","DOT-USD","LINK-USD","MATIC-USD","TON11419-USD","SHIB-USD","LTC-USD","BCH-USD","UNI7083-USD","XLM-USD","ATOM-USD","ETC-USD","ICP-USD","FIL-USD","APT21794-USD","HBAR-USD","ARB11841-USD","NEAR-USD","OP-USD","CRO-USD"]
SWEDISH_TICKERS = ["^OMXS30","ABB.ST","ALFA.ST","ASSA-B.ST","ATCO-A.ST","ATCO-B.ST","AZN.ST","BOL.ST","ELUX-B.ST","ERIC-B.ST","ESSITY-B.ST","EVO.ST","GETI-B.ST","HEXA-B.ST","HM-B.ST","INVE-B.ST","KINV-B.ST","NDA-SE.ST","SAND.ST","SBB-B.ST","SEB-A.ST","SHB-A.ST","SINCH.ST","SKF-B.ST","SSAB-A.ST","SWED-A.ST","TEL2-B.ST","TELIA.ST","VOLV-B.ST"]
COMMODITIES_TICKERS = ["GC=F","SI=F","CL=F","NG=F","HG=F","PL=F"]
MAJOR_INDICES = ["^DJI","^IXIC","^RUT","^VIX","^GSPC","^FTSE","^N225"]

def get_all_tickers():
    all_t = SP500_FALLBACK + CRYPTO_TICKERS + SWEDISH_TICKERS + COMMODITIES_TICKERS + MAJOR_INDICES
    return sorted(set(all_t))

# ====================== SCANNER ======================
def normalize_columns(df):
    if df is None or df.empty:
        return pd.DataFrame()
    data = df.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
    data = data.rename(columns=str.lower)
    return data

def calculate_duration(direction):
    direction = direction.dropna()
    if len(direction) <= 1:
        return len(direction)
    current = direction.iloc[-1]
    duration = 1
    for i in range(2, len(direction)+1):
        if direction.iloc[-i] == current:
            duration += 1
        else:
            break
    return duration

def scan_trends(timeframe="weekly"):
    tickers = get_all_tickers()
    trends = []
    interval = "1wk" if timeframe == "weekly" else "1d"
    period = "3y" if timeframe == "weekly" else "1y"
    duration_name = "Weeks in trend" if timeframe == "weekly" else "Days in trend"

    for ticker in tickers:
        try:
            raw = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
            if raw is None or raw.empty or len(raw) < 20:
                continue

            data = normalize_columns(raw)
            if not {"open","high","low","close"}.issubset(data.columns):
                continue

            # QUANTUM TREND
            lsma = ta.linreg(data["close"], length=LSMA_LENGTH, offset=0)
            trend_base = ta.alma(lsma, length=ALMA_LENGTH, offset=ALMA_OFFSET, sigma=ALMA_SIGMA)
            atr = ta.atr(data["high"], data["low"], data["close"], length=ATR_LENGTH)
            band_offset = atr * ATR_MULTIPLIER
            upper = trend_base + band_offset
            lower = trend_base - band_offset

            direction = pd.Series(0, index=data.index)
            final_line = pd.Series(0.0, index=data.index)

            if len(data) > 0:
                final_line.iloc[0] = trend_base.iloc[0]
                direction.iloc[0] = 1 if data["close"].iloc[0] >= trend_base.iloc[0] else -1

            for i in range(1, len(data)):
                if direction.iloc[i-1] == 1:
                    if data["close"].iloc[i] < lower.iloc[i]:
                        direction.iloc[i] = -1
                        final_line.iloc[i] = upper.iloc[i]
                    else:
                        final_line.iloc[i] = max(lower.iloc[i], final_line.iloc[i-1])
                else:
                    if data["close"].iloc[i] > upper.iloc[i]:
                        direction.iloc[i] = 1
                        final_line.iloc[i] = lower.iloc[i]
                    else:
                        final_line.iloc[i] = min(upper.iloc[i], final_line.iloc[i-1])

            current_dir = direction.iloc[-1]
            trend_name = "STRONG UP-TREND" if current_dir == 1 else "STRONG DOWN-TREND"

            latest = data.iloc[-1]
            close = latest["close"]
            duration = calculate_duration(direction)

            if duration < MIN_DURATION or duration > MAX_DURATION:
                continue

            start_idx = max(0, len(data) - duration - 1)
            start_price = data["close"].iloc[start_idx]
            pct = ((close - start_price) / start_price * 100) if start_price != 0 else 0

            trends.append({
                "Ticker": ticker,
                "Namn": ticker,
                "Trend": trend_name,
                duration_name: duration,
                "Price": round(float(close), 4 if "-" in ticker or "=" in ticker else 2),
                "Rörelse (%)": f"{pct:+.1f}%",
                "Invalidering (pris)": round(float(close), 4 if "-" in ticker or "=" in ticker else 2),
                "TV_URL": f"https://www.tradingview.com/symbols/{ticker.replace('.ST','').replace('-USD','')}/"
            })
        except:
            continue

    if trends:
        df = pd.DataFrame(trends)
        df = df.sort_values(by=duration_name, ascending=True).head(SHOW_TOP).reset_index(drop=True)
        return df
    return pd.DataFrame()

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
    duration_col = df.columns[2]
    one_unit = df[df[duration_col] == 1]
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
st.markdown("Byggd med ❤️ för trendbaserad trading – Quantum Super (en fil)")
