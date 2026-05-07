import requests
import time

# ── CONFIG ──────────────────────────────────────────────
BOT_TOKEN = "8547764565:AAHTWvHvc4Y1qb-HfJ6kbEqiaz8bveO_noc"
CHAT_ID   = "2020862907"
CHECK_INTERVAL = 60
# ────────────────────────────────────────────────────────

COINS = [
    "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
    "DOGEUSDT","ADAUSDT","TRXUSDT","AVAXUSDT","LINKUSDT",
    "DOTUSDT","MATICUSDT","LTCUSDT","BCHUSDT","UNIUSDT",
    "ATOMUSDT","ETCUSDT","XLMUSDT","FILUSDT","APTUSDT",
    "ARBUSDT","OPUSDT","NEARUSDT","INJUSDT","SUIUSDT",
    "SEIUSDT","TIAUSDT","STXUSDT","RUNEUSDT","LDOUSDT",
    "AAVEUSDT","SNXUSDT","MKRUSDT","COMPUSDT","CRVUSDT",
    "GRTUSDT","APEUSDT","SANDUSDT","MANAUSDT","AXSUSDT",
    "GALAUSDT","ENJUSDT","CHZUSDT","FLOWUSDT","ICPUSDT",
    "VETUSDT","HBARUSDT","ALGOUSDT","XTZUSDT","EGLDUSDT",
    "PEPEUSDT","WIFUSDT","BONKUSDT","FLOKIUSDT","SHIBUSDT",
    "DOGSUSDT","NOTUSDT","1000SATSUSDT","TURBOUSDT","MEMEUSDT",
    "WLDUSDT","FETUSDT","AGIXUSDT","OCEANUSDT","RENDERUSDT",
    "TAOUSDT","ARKMUSDT","PERPUSDT","GMXUSDT","DYDXUSDT",
    "BLURUSDT","LOOKSUSDT","MAGICUSDT","IMXUSDT","RNDRRNDR",
    "CFXUSDT","STGUSDT","CAKEUSDT","BALUSDT","YFIUSDT",
    "SUSHIUSDT","1INCHUSDT","ZRXUSDT","BANDUSDT","KNCUSDT",
    "CELOUSDT","ZILUSDT","ONTUSDT","IOTAUSDT","NEOUSDT",
    "WAVESUSDT","DASHUSDT","ZECUSDT","XMRUSDT","MINAUSDT",
    "ROSEUSDT","SKLUSDT","ANKRUSDT","CTSIUSDT","OGNUSDT",
    "STORJUSDT","COTIUSDT","REQUSDT","POWRUSDT","IDEXUSDT",
    "ASTRUSDT","ACAUSDT","KSMUSDT","PARAMUSDT","GLMRUSDT",
    "RVNUSDT","SCUSDT","DCRUSDT","LRCUSDT","BATUSDT",
    "ZENUSD","QTUMUSDT","IOSTUSDT","NKNUSDT","MTLUSDT",
    "RLCUSDT","WOOUSDT","LINAUSDT","FORTHUSDT","RADUSDT",
    "CELRUSDT","CVCUSDT","BELUSDT","HARDUSDT","WNXMUSDT",
    "JOEUSDT","MAGICUSDT","HIGHUSDT","ALPACAUSDT","MDXUSDT",
    "TUSDT","IDUSDT","CYBERUSDT","ARKUSDT","MAVUSDT",
    "PENDLEUSDT","WUSDT","JUPUSDT","STRKUSDT","DYMUSDT",
    "ALTUSDT","ZETAUSDT","PIXELUSDT","PORTALUSDT","MYROUSDT",
    "REZUSDT","BOMEUSDT","ENAUSDT","ETHFIUSDT","SAGAUSDT",
    "OMNIUSDT","RUNEUSD","BBUSDT","ZKUSDT","LISTAUSDT",
    "ZROUSDT","RENDERUSDT","TONUSDT","CATIUSDT","HMSTRUSDT",
    "EIGENUSDT","SCRUSDT","MOVEUSDT","MEUSDT","VIRTUALUSDT",
    "AIUSDT","ACTUSDT","PNUTUSDT","COWUSDT","GRASSUSDT",
    "GOATUSDT","MOODENGUSDT","CHILLGUYUSDT","SWARMSUSDT",
    "TRUMPUSDT","MELANIAUSDT","USDCUSDT","VINEUSDT","BROCCOLI"
]

# Remove any invalid symbols
COINS = list(set(COINS))


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")


def get_klines(symbol, interval="1h", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if not isinstance(data, list) or len(data) < 50:
        raise ValueError(f"Bad data for {symbol}")
    closes  = [float(x[4]) for x in data]
    volumes = [float(x[5]) for x in data]
    return closes, volumes


def ma(data, period):
    if len(data) < period:
        return None
    return sum(data[-period:]) / period


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains  = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def analyze(symbol):
    try:
        closes, volumes = get_klines(symbol, "1h", 100)
        price   = closes[-1]
        ma7     = ma(closes, 7)
        ma25    = ma(closes, 25)
        ma99    = ma(closes, 99)
        rsi_val = rsi(closes)

        if None in [ma7, ma25, ma99, rsi_val]:
            return None, 0, 0, 0, 0, []

        avg_vol   = sum(volumes[-10:]) / 10
        cur_vol   = volumes[-1]
        vol_ratio = cur_vol / avg_vol if avg_vol > 0 else 1

        signal  = None
        reasons = []

        if price > ma7 > ma25 and 50 < rsi_val < 75 and vol_ratio > 1.3:
            signal  = "LONG"
            reasons = [
                "Price above MA7 & MA25",
                f"RSI: {rsi_val:.1f} (bullish)",
                f"Vol: {vol_ratio:.1f}x avg"
            ]
        elif price < ma7 < ma25 and 25 < rsi_val < 50 and vol_ratio > 1.3:
            signal  = "SHORT"
            reasons = [
                "Price below MA7 & MA25",
                f"RSI: {rsi_val:.1f} (bearish)",
                f"Vol: {vol_ratio:.1f}x avg"
            ]

        return signal, price, ma7, ma25, rsi_val, reasons

    except Exception as e:
        print(f"Skip {symbol}: {e}")
        return None, 0, 0, 0, 0, []


def format_signal(symbol, signal, price, ma7, ma25, rsi_val, reasons):
    emoji = "🟢" if signal == "LONG" else "🔴"
    if signal == "LONG":
        sl, tp1, tp2 = price*0.95, price*1.08, price*1.15
    else:
        sl, tp1, tp2 = price*1.05, price*0.92, price*0.85

    return f"""
{emoji} *{signal} — {symbol}*
💰 `{price:.8f}`
🛑 SL: `{sl:.8f}`
🎯 TP1: `{tp1:.8f}`
🎯 TP2: `{tp2:.8f}`
📊 RSI: {rsi_val:.1f} | {reasons[2] if len(reasons)>2 else ''}
⚙️ 3x–5x lev | 1% risk only
⚠️ _Not financial advice._
""".strip()


def main():
    send_message(f"🤖 *Signal Bot v4 Started!*\nMonitoring *{len(COINS)} coins* every 60s...")
    print(f"Bot v4 running — {len(COINS)} coins")

    alerted    = {}
    scan_count = 0

    while True:
        scan_count += 1
        signals_found = 0

        for symbol in COINS:
            signal, price, ma7, ma25, rsi_val, reasons = analyze(symbol)
            if signal:
                key = f"{symbol}_{signal}"
                if time.time() - alerted.get(key, 0) > 14400:
                    send_message(format_signal(symbol, signal, price, ma7, ma25, rsi_val, reasons))
                    alerted[key] = time.time()
                    signals_found += 1
                    print(f"✅ {symbol} {signal}")
            time.sleep(0.3)

        print(f"Scan #{scan_count} done. {signals_found} signals.")

        if scan_count % 10 == 0:
            send_message(f"💓 *Bot alive* — Scan #{scan_count} | {len(COINS)} coins watched")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
