import requests
import time

# ── CONFIG ──────────────────────────────────────────────
BOT_TOKEN = "8547764565:AAHTWvHvc4Y1qb-HfJ6kbEqiaz8bveO_noc"
CHAT_ID   = "2020862907"
CHECK_INTERVAL = 60  # scan all coins every 60s
# ────────────────────────────────────────────────────────


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")


def get_all_coins():
    try:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        r = requests.get(url, timeout=15)
        data = r.json()
        coins = [
            s["symbol"] for s in data["symbols"]
            if s["quoteAsset"] == "USDT"
            and s["status"] == "TRADING"
            and s["isSpotTradingAllowed"]
        ]
        print(f"Found {len(coins)} USDT coins on Binance")
        return coins
    except Exception as e:
        print(f"Failed to fetch coins: {e}")
        return []


def get_klines(symbol, interval="1h", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if not isinstance(data, list) or len(data) < 50:
        raise ValueError(f"Bad data: {data}")
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

        # LONG
        if price > ma7 > ma25 and 50 < rsi_val < 75 and vol_ratio > 1.3:
            signal  = "LONG"
            reasons = [
                "Price above MA7 & MA25",
                f"RSI: {rsi_val:.1f} (bullish)",
                f"Volume {vol_ratio:.1f}x avg"
            ]

        # SHORT
        elif price < ma7 < ma25 and 25 < rsi_val < 50 and vol_ratio > 1.3:
            signal  = "SHORT"
            reasons = [
                "Price below MA7 & MA25",
                f"RSI: {rsi_val:.1f} (bearish)",
                f"Volume {vol_ratio:.1f}x avg"
            ]

        return signal, price, ma7, ma25, rsi_val, reasons

    except Exception as e:
        print(f"Skip {symbol}: {e}")
        return None, 0, 0, 0, 0, []


def format_signal(symbol, signal, price, ma7, ma25, rsi_val, reasons):
    emoji = "🟢" if signal == "LONG" else "🔴"
    if signal == "LONG":
        sl  = price * 0.95
        tp1 = price * 1.08
        tp2 = price * 1.15
    else:
        sl  = price * 1.05
        tp1 = price * 0.92
        tp2 = price * 0.85

    msg = f"""
{emoji} *{signal} — {symbol}*

💰 `{price:.8f}`
🛑 SL: `{sl:.8f}`
🎯 TP1: `{tp1:.8f}`
🎯 TP2: `{tp2:.8f}`

• RSI: {rsi_val:.1f} | Vol: {reasons[2] if len(reasons) > 2 else ''}
{chr(10).join(f'• {r}' for r in reasons[:2])}

⚙️ 3x–5x lev | 1% risk only
⚠️ _Not financial advice._
"""
    return msg.strip()


def main():
    send_message("🤖 *Signal Bot v3 Started!*\nFetching ALL Binance USDT coins...")

    # Fetch all coins once at start
    COINS = get_all_coins()
    if not COINS:
        send_message("❌ Failed to fetch coins. Restarting...")
        time.sleep(30)
        COINS = get_all_coins()

    send_message(f"✅ Monitoring *{len(COINS)} coins* on Binance. Signals incoming!")
    print(f"Monitoring {len(COINS)} coins...")

    alerted    = {}
    scan_count = 0

    while True:
        scan_count += 1
        print(f"\n--- Scan #{scan_count} | {len(COINS)} coins ---")
        signals_found = 0

        for symbol in COINS:
            signal, price, ma7, ma25, rsi_val, reasons = analyze(symbol)

            if signal:
                key        = f"{symbol}_{signal}"
                last_alert = alerted.get(key, 0)

                if time.time() - last_alert > 14400:  # max 1 alert per 4h per coin
                    msg = format_signal(symbol, signal, price, ma7, ma25, rsi_val, reasons)
                    send_message(msg)
                    alerted[key] = time.time()
                    signals_found += 1
                    print(f"✅ {symbol} {signal}")

            time.sleep(0.3)  # avoid Binance rate limit

        print(f"Scan #{scan_count} done. {signals_found} signals sent.")

        # Heartbeat every 10 scans
        if scan_count % 10 == 0:
            send_message(f"💓 *Bot alive* — Scan #{scan_count} | Watching {len(COINS)} coins")

        # Refresh coin list every 24h (scan_count * interval / 3600)
        if scan_count % 1440 == 0:
            COINS = get_all_coins()
            send_message(f"🔄 Coin list refreshed: {len(COINS)} coins")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
