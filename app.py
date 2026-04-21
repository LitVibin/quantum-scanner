import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

APP_TITLE = "Quantum Super"
BULL_COLOR = "#00E5FF"
BEAR_COLOR = "#D500F9"
TEXT_ON_COLOR = "#001014"
MAX_TREND_BARS = 50
ATR_LEN = 14
ATR_MULT = 0.35
LSMA_LEN = 72
ALMA_LEN = 33
ALMA_OFFSET = 0.85
ALMA_SIGMA = 6

st.set_page_config(page_title=APP_TITLE, layout="wide")


@dataclass(frozen=True)
class Instrument:
    ticker: str
    name: str
    category: str
    timeframe: str  # '1wk' or '1d'
    yahoo_symbol: str
    tv_symbol: str


CRYPTO = [
    Instrument("BTC-USD", "Bitcoin", "Krypto", "1d", "BTC-USD", "BINANCE:BTCUSDT"),
    Instrument("ETH-USD", "Ethereum", "Krypto", "1d", "ETH-USD", "BINANCE:ETHUSDT"),
    Instrument("SOL-USD", "Solana", "Krypto", "1d", "SOL-USD", "BINANCE:SOLUSDT"),
    Instrument("XRP-USD", "XRP", "Krypto", "1d", "XRP-USD", "BINANCE:XRPUSDT"),
    Instrument("BNB-USD", "BNB", "Krypto", "1d", "BNB-USD", "BINANCE:BNBUSDT"),
    Instrument("DOGE-USD", "Dogecoin", "Krypto", "1d", "DOGE-USD", "BINANCE:DOGEUSDT"),
    Instrument("ADA-USD", "Cardano", "Krypto", "1d", "ADA-USD", "BINANCE:ADAUSDT"),
    Instrument("AVAX-USD", "Avalanche", "Krypto", "1d", "AVAX-USD", "BINANCE:AVAXUSDT"),
    Instrument("LINK-USD", "Chainlink", "Krypto", "1d", "LINK-USD", "BINANCE:LINKUSDT"),
    Instrument("DOT-USD", "Polkadot", "Krypto", "1d", "DOT-USD", "BINANCE:DOTUSDT"),
    Instrument("MATIC-USD", "Polygon", "Krypto", "1d", "MATIC-USD", "BINANCE:POLUSDT"),
    Instrument("LTC-USD", "Litecoin", "Krypto", "1d", "LTC-USD", "BINANCE:LTCUSDT"),
    Instrument("BCH-USD", "Bitcoin Cash", "Krypto", "1d", "BCH-USD", "BINANCE:BCHUSDT"),
    Instrument("ATOM-USD", "Cosmos", "Krypto", "1d", "ATOM-USD", "BINANCE:ATOMUSDT"),
    Instrument("TRX-USD", "TRON", "Krypto", "1d", "TRX-USD", "BINANCE:TRXUSDT"),
    Instrument("UNI7083-USD", "Uniswap", "Krypto", "1d", "UNI7083-USD", "BINANCE:UNIUSDT"),
    Instrument("ETC-USD", "Ethereum Classic", "Krypto", "1d", "ETC-USD", "BINANCE:ETCUSDT"),
    Instrument("ICP-USD", "Internet Computer", "Krypto", "1d", "ICP-USD", "BINANCE:ICPUSDT"),
]

SWEDISH_LARGE_CAP = [
    Instrument("ABB.ST", "ABB", "Aktier", "1wk", "ABB.ST", "OMXSTO:ABB"),
    Instrument("ALFA.ST", "Alfa Laval", "Aktier", "1wk", "ALFA.ST", "OMXSTO:ALFA"),
    Instrument("ASSA-B.ST", "ASSA ABLOY B", "Aktier", "1wk", "ASSA-B.ST", "OMXSTO:ASSA_B"),
    Instrument("ATCO-A.ST", "Atlas Copco A", "Aktier", "1wk", "ATCO-A.ST", "OMXSTO:ATCO_A"),
    Instrument("ATCO-B.ST", "Atlas Copco B", "Aktier", "1wk", "ATCO-B.ST", "OMXSTO:ATCO_B"),
    Instrument("AZN.ST", "AstraZeneca", "Aktier", "1wk", "AZN.ST", "OMXSTO:AZN"),
    Instrument("BOL.ST", "Boliden", "Aktier", "1wk", "BOL.ST", "OMXSTO:BOL"),
    Instrument("ELUX-B.ST", "Electrolux B", "Aktier", "1wk", "ELUX-B.ST", "OMXSTO:ELUX_B"),
    Instrument("ERIC-B.ST", "Ericsson B", "Aktier", "1wk", "ERIC-B.ST", "OMXSTO:ERIC_B"),
    Instrument("ESSITY-B.ST", "Essity B", "Aktier", "1wk", "ESSITY-B.ST", "OMXSTO:ESSITY_B"),
    Instrument("EVO.ST", "Evolution", "Aktier", "1wk", "EVO.ST", "OMXSTO:EVO"),
    Instrument("GETI-B.ST", "Getinge B", "Aktier", "1wk", "GETI-B.ST", "OMXSTO:GETI_B"),
    Instrument("HEXA-B.ST", "Hexagon B", "Aktier", "1wk", "HEXA-B.ST", "OMXSTO:HEXA_B"),
    Instrument("HM-B.ST", "H&M B", "Aktier", "1wk", "HM-B.ST", "OMXSTO:HM_B"),
    Instrument("INVE-B.ST", "Investor B", "Aktier", "1wk", "INVE-B.ST", "OMXSTO:INVE_B"),
    Instrument("KINV-B.ST", "Kinnevik B", "Aktier", "1wk", "KINV-B.ST", "OMXSTO:KINV_B"),
    Instrument("NDA-SE.ST", "Nordea", "Aktier", "1wk", "NDA-SE.ST", "OMXSTO:NDA_SE"),
    Instrument("SAND.ST", "Sandvik", "Aktier", "1wk", "SAND.ST", "OMXSTO:SAND"),
    Instrument("SCA-B.ST", "SCA B", "Aktier", "1wk", "SCA-B.ST", "OMXSTO:SCA_B"),
    Instrument("SEB-A.ST", "SEB A", "Aktier", "1wk", "SEB-A.ST", "OMXSTO:SEB_A"),
    Instrument("SHB-A.ST", "Handelsbanken A", "Aktier", "1wk", "SHB-A.ST", "OMXSTO:SHB_A"),
    Instrument("SKF-B.ST", "SKF B", "Aktier", "1wk", "SKF-B.ST", "OMXSTO:SKF_B"),
    Instrument("SWED-A.ST", "Swedbank A", "Aktier", "1wk", "SWED-A.ST", "OMXSTO:SWED_A"),
    Instrument("TEL2-B.ST", "Tele2 B", "Aktier", "1wk", "TEL2-B.ST", "OMXSTO:TEL2_B"),
    Instrument("TELIA.ST", "Telia", "Aktier", "1wk", "TELIA.ST", "OMXSTO:TELIA"),
    Instrument("VOLV-A.ST", "Volvo A", "Aktier", "1wk", "VOLV-A.ST", "OMXSTO:VOLV_A"),
    Instrument("VOLV-B.ST", "Volvo B", "Aktier", "1wk", "VOLV-B.ST", "OMXSTO:VOLV_B"),
]

MACRO = [
    Instrument("GC=F", "Guld", "Råvaror & Index", "1wk", "GC=F", "COMEX:GC1!"),
    Instrument("SI=F", "Silver", "Råvaror & Index", "1wk", "SI=F", "COMEX:SI1!"),
    Instrument("CL=F", "WTI-olja", "Råvaror & Index", "1wk", "CL=F", "NYMEX:CL1!"),
    Instrument("BZ=F", "Brent-olja", "Råvaror & Index", "1wk", "BZ=F", "ICEEUR:BRN1!"),
    Instrument("NG=F", "Naturgas", "Råvaror & Index", "1wk", "NG=F", "NYMEX:NG1!"),
    Instrument("HG=F", "Koppar", "Råvaror & Index", "1wk", "HG=F", "COMEX:HG1!"),
    Instrument("ZC=F", "Majs", "Råvaror & Index", "1wk", "ZC=F", "CBOT:ZC1!"),
    Instrument("ZW=F", "Vete", "Råvaror & Index", "1wk", "ZW=F", "CBOT:ZW1!"),
    Instrument("SB=F", "Socker", "Råvaror & Index", "1wk", "SB=F", "ICEUS:SB1!"),
    Instrument("^GSPC", "S&P 500 Index", "Råvaror & Index", "1wk", "^GSPC", "SP:SPX"),
    Instrument("^NDX", "Nasdaq 100", "Råvaror & Index", "1wk", "^NDX", "NASDAQ:NDX"),
    Instrument("^DJI", "Dow Jones", "Råvaror & Index", "1wk", "^DJI", "DJ:DJI"),
    Instrument("^RUT", "Russell 2000", "Råvaror & Index", "1wk", "^RUT", "RUSSELL:RUT"),
    Instrument("^FTSE", "FTSE 100", "Råvaror & Index", "1wk", "^FTSE", "INDEX:UKX"),
    Instrument("^GDAXI", "DAX", "Råvaror & Index", "1wk", "^GDAXI", "XETR:DAX"),
    Instrument("^FCHI", "CAC 40", "Råvaror & Index", "1wk", "^FCHI", "TVC:CAC40"),
    Instrument("^N225", "Nikkei 225", "Råvaror & Index", "1wk", "^N225", "TVC:NI225"),
    Instrument("^HSI", "Hang Seng", "Råvaror & Index", "1wk", "^HSI", "HSI:HSI"),
    Instrument("^VIX", "VIX", "Råvaror & Index", "1wk", "^VIX", "CBOE:VIX"),
]

SP500_FALLBACK = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "GOOGL": "Alphabet A",
    "GOOG": "Alphabet C",
    "BRK-B": "Berkshire Hathaway B",
    "JPM": "JPMorgan Chase",
    "LLY": "Eli Lilly",
    "V": "Visa",
    "XOM": "Exxon Mobil",
    "UNH": "UnitedHealth",
    "MA": "Mastercard",
    "COST": "Costco",
    "AVGO": "Broadcom",
    "HD": "Home Depot",
    "PG": "Procter & Gamble",
    "JNJ": "Johnson & Johnson",
    "MRK": "Merck",
    "ABBV": "AbbVie",
    "PEP": "PepsiCo",
    "KO": "Coca-Cola",
    "BAC": "Bank of America",
    "WMT": "Walmart",
    "CVX": "Chevron",
    "ADBE": "Adobe",
    "CRM": "Salesforce",
    "AMD": "AMD",
    "NFLX": "Netflix",
    "CSCO": "Cisco",
    "ACN": "Accenture",
    "MCD": "McDonald's",
    "TMO": "Thermo Fisher",
    "ABT": "Abbott Laboratories",
    "ORCL": "Oracle",
    "LIN": "Linde",
    "DHR": "Danaher",
    "WFC": "Wells Fargo",
    "INTU": "Intuit",
    "IBM": "IBM",
    "QCOM": "Qualcomm",
    "TXN": "Texas Instruments",
    "CAT": "Caterpillar",
    "GE": "GE Aerospace",
    "DIS": "Walt Disney",
    "AMGN": "Amgen",
    "PFE": "Pfizer",
    "INTC": "Intel",
    "GS": "Goldman Sachs",
}


def lsma(series: pd.Series, length: int) -> pd.Series:
    x = np.arange(length, dtype=float)
    x_mean = x.mean()
    denom = ((x - x_mean) ** 2).sum()

    def _calc(y: np.ndarray) -> float:
        y_mean = y.mean()
        slope = ((x - x_mean) * (y - y_mean)).sum() / denom
        intercept = y_mean - slope * x_mean
        return intercept + slope * (length - 1)

    return series.rolling(length, min_periods=length).apply(_calc, raw=True)



def alma(series: pd.Series, length: int, offset: float = ALMA_OFFSET, sigma: float = ALMA_SIGMA) -> pd.Series:
    m = offset * (length - 1)
    s = length / sigma
    weights = np.exp(-((np.arange(length) - m) ** 2) / (2 * s * s))
    weights /= weights.sum()
    return series.rolling(length, min_periods=length).apply(lambda x: float(np.dot(x, weights)), raw=True)



def atr(df: pd.DataFrame, length: int) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(length, min_periods=length).mean()



def calculate_quantum_trend(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["LSMA"] = lsma(out["Close"], LSMA_LEN)
    out["ALMA"] = alma(out["Close"], ALMA_LEN)
    out["ATR"] = atr(out, ATR_LEN)
    out["BUFFER"] = out["ATR"] * ATR_MULT
    out["BULL_LEVEL"] = out[["LSMA", "ALMA"]].max(axis=1) + out["BUFFER"]
    out["BEAR_LEVEL"] = out[["LSMA", "ALMA"]].min(axis=1) - out["BUFFER"]

    direction: List[int] = []
    active = 0
    invalidation: List[float] = []

    for _, row in out.iterrows():
        close = row["Close"]
        bull_level = row["BULL_LEVEL"]
        bear_level = row["BEAR_LEVEL"]
        ls = row["LSMA"]
        al = row["ALMA"]
        buf = row["BUFFER"]

        if np.isnan(close) or np.isnan(bull_level) or np.isnan(bear_level) or np.isnan(ls) or np.isnan(al) or np.isnan(buf):
            direction.append(0)
            invalidation.append(np.nan)
            continue

        if active <= 0 and close > bull_level:
            active = 1
        elif active >= 0 and close < bear_level:
            active = -1
        elif active == 0:
            active = 1 if al >= ls else -1

        direction.append(active)
        if active == 1:
            invalidation.append(float(min(ls, al) - buf))
        else:
            invalidation.append(float(max(ls, al) + buf))

    out["direction"] = direction
    out["invalidation"] = invalidation

    trend_age = []
    bars = 0
    prev = 0
    for d in out["direction"].fillna(0).astype(int):
        if d == 0:
            bars = 0
        elif d == prev:
            bars += 1
        else:
            bars = 1
        prev = d
        trend_age.append(min(bars, MAX_TREND_BARS))
    out["trend_bars"] = trend_age
    out["trend_change"] = out["direction"].ne(out["direction"].shift(1)) & out["direction"].ne(0)
    return out


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def fetch_sp500_constituents() -> Dict[str, str]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        symbols = df["Symbol"].astype(str).str.replace(".", "-", regex=False)
        names = df["Security"].astype(str)
        return dict(zip(symbols, names))
    except Exception:
        return SP500_FALLBACK.copy()


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def build_instruments() -> List[Instrument]:
    sp500 = [
        Instrument(ticker=s, name=n, category="Aktier", timeframe="1wk", yahoo_symbol=s, tv_symbol=s)
        for s, n in fetch_sp500_constituents().items()
    ]
    all_items = sp500 + SWEDISH_LARGE_CAP + CRYPTO + MACRO
    unique = {}
    for item in all_items:
        unique[(item.yahoo_symbol, item.timeframe, item.category)] = item
    return list(unique.values())


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def download_market_data(symbols: Tuple[str, ...], interval: str, period: str) -> Dict[str, pd.DataFrame]:
    result: Dict[str, pd.DataFrame] = {}
    chunk_size = 60
    for i in range(0, len(symbols), chunk_size):
        chunk = list(symbols[i:i + chunk_size])
        raw = yf.download(
            tickers=chunk,
            interval=interval,
            period=period,
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="ticker",
        )
        if raw.empty:
            continue

        if isinstance(raw.columns, pd.MultiIndex):
            for symbol in chunk:
                try:
                    df = raw[symbol].copy()
                except Exception:
                    continue
                df = df.rename(columns=str.title)
                df = df[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]].dropna(how="all")
                if not df.empty:
                    result[symbol] = df
        else:
            df = raw.rename(columns=str.title)
            df = df[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]].dropna(how="all")
            if len(chunk) == 1 and not df.empty:
                result[chunk[0]] = df
    return result



def tradingview_link(tv_symbol: str) -> str:
    return f"https://www.tradingview.com/chart/?symbol={quote_plus(tv_symbol)}"



def format_price(x: float) -> str:
    if pd.isna(x):
        return "-"
    if abs(x) >= 1000:
        return f"{x:,.2f}"
    if abs(x) >= 10:
        return f"{x:,.2f}"
    return f"{x:,.4f}"



def grok_prompt(row: pd.Series) -> str:
    return (
        f"Analysera {row['Namn']} ({row['Ticker']}) som precis har ett nytt {row['Trend'].lower()}-trendskifte "
        f"på {row['Timeframe label'].lower()} enligt Quantum Trend (LSMA 72, ALMA 33, ATR 14 * 0.35). "
        f"Nuvarande pris är {row['Price']}, trendlängd {row['Weeks/Days in trend']}, rörelse {row['Rörelse (%)']} %, "
        f"och invalidering {row['Invalidering']}. Ge mig: 1) trendkvalitet, 2) viktigaste stödnivå/motstånd, "
        f"3) sannolikt nästa scenario, 4) risk/reward för swing-trade, 5) tydlig slutsats i punktform."
    )



def scan_markets(instruments: List[Instrument]) -> pd.DataFrame:
    by_timeframe: Dict[str, List[Instrument]] = {"1wk": [], "1d": []}
    for item in instruments:
        by_timeframe[item.timeframe].append(item)

    datasets = {
        "1wk": download_market_data(tuple(i.yahoo_symbol for i in by_timeframe["1wk"]), "1wk", "5y"),
        "1d": download_market_data(tuple(i.yahoo_symbol for i in by_timeframe["1d"]), "1d", "18mo"),
    }

    rows = []
    for timeframe, items in by_timeframe.items():
        for item in items:
            df = datasets.get(timeframe, {}).get(item.yahoo_symbol)
            if df is None or len(df) < max(LSMA_LEN, ALMA_LEN, ATR_LEN) + 5:
                continue

            try:
                calc = calculate_quantum_trend(df)
                last = calc.dropna(subset=["LSMA", "ALMA", "ATR", "direction"]).iloc[-1]
            except Exception:
                continue

            direction = int(last["direction"])
            if direction == 0:
                continue

            age = int(last["trend_bars"])
            start_idx = max(len(calc) - age, 0)
            trend_start_close = float(calc.iloc[start_idx]["Close"]) if start_idx < len(calc) else float(last["Close"])
            current_close = float(last["Close"])
            move_pct = ((current_close / trend_start_close) - 1.0) * 100 if trend_start_close else np.nan
            timeframe_label = "Days" if timeframe == "1d" else "Weeks"

            rows.append(
                {
                    "Ticker": item.ticker,
                    "Namn": item.name,
                    "Kategori": item.category,
                    "Trend": "Bull" if direction == 1 else "Bear",
                    "Weeks/Days in trend": min(age, MAX_TREND_BARS),
                    "Price": round(current_close, 4),
                    "Rörelse (%)": round(move_pct, 2) if not pd.isna(move_pct) else np.nan,
                    "Invalidering": round(float(last["invalidation"]), 4),
                    "TradingView": tradingview_link(item.tv_symbol),
                    "Timeframe": timeframe,
                    "Timeframe label": timeframe_label,
                }
            )

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    out["sort_timeframe"] = out["Timeframe"].map({"1d": 0, "1wk": 1}).fillna(2)
    out = out.sort_values(["Weeks/Days in trend", "sort_timeframe", "Ticker"], ascending=[True, True, True]).reset_index(drop=True)
    return out



def render_html_table(df: pd.DataFrame, show_prompts: bool = False, table_key: str = "") -> None:
    if df.empty:
        st.info("Inga träffar just nu.")
        return

    display_df = df.copy()
    display_df["Price"] = display_df["Price"].apply(format_price)
    display_df["Invalidering"] = display_df["Invalidering"].apply(format_price)
    display_df["Rörelse (%)"] = display_df["Rörelse (%)"].map(lambda x: "-" if pd.isna(x) else f"{x:.2f}")

    html = [
        "<div style='overflow-x:auto;'>",
        "<table style='width:100%; border-collapse:collapse; font-size:14px;'>",
        "<thead><tr>",
    ]
    headers = ["Ticker", "Namn", "Trend", "Weeks/Days in trend", "Price", "Rörelse (%)", "Invalidering", "TradingView"]
    for h in headers:
        html.append(
            f"<th style='text-align:left; padding:10px; border-bottom:1px solid rgba(255,255,255,0.12);'>{h}</th>"
        )
    html.append("</tr></thead><tbody>")

    for _, row in display_df.iterrows():
        bg = BULL_COLOR if row["Trend"] == "Bull" else BEAR_COLOR
        html.append(f"<tr style='background:{bg}; color:{TEXT_ON_COLOR};'>")
        html.append(f"<td style='padding:9px 10px;'><strong>{row['Ticker']}</strong></td>")
        html.append(f"<td style='padding:9px 10px;'>{row['Namn']}</td>")
        html.append(f"<td style='padding:9px 10px;'><strong>{row['Trend']}</strong></td>")
        html.append(f"<td style='padding:9px 10px;'>{row['Weeks/Days in trend']}</td>")
        html.append(f"<td style='padding:9px 10px;'>{row['Price']}</td>")
        html.append(f"<td style='padding:9px 10px;'>{row['Rörelse (%)']}</td>")
        html.append(f"<td style='padding:9px 10px;'>{row['Invalidering']}</td>")
        html.append(
            f"<td style='padding:9px 10px;'><a href='{row['TradingView']}' target='_blank' style='color:{TEXT_ON_COLOR}; font-weight:700;'>Öppna</a></td>"
        )
        html.append("</tr>")
    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)

    if show_prompts:
        with st.expander("Grok-prompts för nya trendskiften"):
            for _, row in df.iterrows():
                st.markdown(f"**{row['Ticker']} — {row['Namn']}**")
                st.code(grok_prompt(row), language="text")



def main() -> None:
    st.title(APP_TITLE)
    st.caption(
        "Weekly Trend Scanner med Quantum Trend-logik: LSMA 72 + ALMA 33 + ATR 14 × 0.35 + stateful direction. "
        "Krypto körs på daglig data, övriga marknader på veckodata."
    )

    with st.sidebar:
        st.header("Inställningar")
        force_refresh = st.button("Uppdatera scan nu")
        if force_refresh:
            st.cache_data.clear()
            st.rerun()
        st.markdown(
            "- **Bull:** turkos `#00E5FF`\n"
            "- **Bear:** lila `#D500F9`\n"
            f"- Max trendlängd i visning: **{MAX_TREND_BARS}**"
        )

    instruments = build_instruments()
    st.subheader(f"Scannade {len(instruments)} marknader")

    with st.spinner("Hämtar marknadsdata och kör Quantum Trend-scan..."):
        df = scan_markets(instruments)

    if df.empty:
        st.error("Kunde inte hämta marknadsdata just nu. Försök igen om en stund.")
        return

    new_shifts = df[df["Weeks/Days in trend"] == 1].copy()
    crypto_df = df[df["Kategori"] == "Krypto"].copy()
    stocks_df = df[df["Kategori"] == "Aktier"].copy()
    macro_df = df[df["Kategori"] == "Råvaror & Index"].copy()

    tabs = st.tabs([
        "Nya 1-veckors/dagars trendskiften",
        "Krypto",
        "Aktier",
        "Råvaror & Index",
    ])

    with tabs[0]:
        st.write(f"Nya skiften just nu: **{len(new_shifts)}**")
        render_html_table(new_shifts, show_prompts=True, table_key="new")

    with tabs[1]:
        st.write(f"Krypto-trender: **{len(crypto_df)}**")
        render_html_table(crypto_df, table_key="crypto")

    with tabs[2]:
        st.write(f"Aktietrender: **{len(stocks_df)}**")
        render_html_table(stocks_df, table_key="stocks")

    with tabs[3]:
        st.write(f"Råvaror & index-trender: **{len(macro_df)}**")
        render_html_table(macro_df, table_key="macro")

    with st.expander("Teknisk notis"):
        st.markdown(
            "Den här versionen är byggd för att vara stabil på gratis hosting. För att minimera beroenden använder den egen Python-kod "
            "för LSMA, ALMA och ATR i stället för externa TA-paket. Om din Pine Script innehåller någon extra specialregel utöver "
            "LSMA 72 + ALMA 33 + ATR 14 × 0.35 + stateful direction, byt endast ut funktionen `calculate_quantum_trend()` i `app.py`."
        )


if __name__ == "__main__":
    main()
