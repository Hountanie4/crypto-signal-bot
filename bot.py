import requests
import time

# ── CONFIG ──────────────────────────────────────────────
BOT_TOKEN = "8547764565:AAHTWvHvc4Y1qb-HfJ6kbEqiaz8bveO_noc"
CHAT_ID   = "2020862907"
CHECK_INTERVAL = 300

COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
    "DOGEUSDT", "XRPUSDT", "ADAUSDT", "ARBUSDT",
    "DOGSUSDT", "PEPEUSDT", "WIFUSDT", "NOTUSDT"
]
# ────────────────────────────────────────────────────────


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})


def get_klines(symbol, interval="1h", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    closes = [float(x[4]) for x in data]
    volumes = [float(x[5]) for x in data]
    return closes, volumes


def ma(data, period):
    return sum(data[-period:]) / period


def rsi(closes, period=14):
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
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
        price = closes[-1]

        ma7  = ma(closes, 7)
        ma25 = ma(closes, 25)
        ma99 = ma(closes, 99)
        rsi_val = rsi(closes)

        avg_vol = sum(volumes[-10:]) / 10
        cur_vol = volumes[-1]
        vol_ratio = cur_vol / avg_vol if avg_vol > 0 else 1

        signal = None
        reasons = []

        if (price > ma7 > ma25 and rsi_val > 50 and rsi_val < 70 and vol_ratio > 1.5):
            signal = "LONG"
            reasons = [
                "Price above MA7 & MA25",
                f"RSI: {rsi_val:.1f} (bullish)",
                f"Volume {vol_ratio:.1f}x above average"
            ]
        elif (price < ma7 < ma25 and rsi_val < 50 and rsi_val > 30 and vol_ratio > 1.5):
            signal = "SHORT"
            reasons = [
                "Price below MA7 & MA25",
                f"RSI: {rsi_val:.1f} (bearish)",
                f"Volume {vol_ratio:.1f}x above average"
            ]

        return signal, price, ma7, ma25, rsi_val, reasons

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None, 0, 0, 0, 0, []


def format_signal(symbol, signal, price, ma7, ma25, rsi_val, reasons):
    emoji = "🟢" if signal == "LONG" else "🔴"
    sl_pct = 0.05
    tp1_pct = 0.08
    tp2_pct = 0.15

    if signal == "LONG":
        sl  = price * (1 - sl_pct)
        tp1 = price * (1 + tp1_pct)
        tp2 = price * (1 + tp2_pct)
    else:
        sl  = price * (1 + sl_pct)
        tp1 = price * (1 - tp1_pct)
        tp2 = price * (1 - tp2_pct)

    msg = f"""
{emoji} *{signal} SIGNAL — {symbol}*

💰 Price: `{price:.8f}`
🛑 Stop Loss: `{sl:.8f}`
🎯 TP1: `{tp1:.8f}`
🎯 TP2: `{tp2:.8f}`

📊 *Indicators:*
• MA7: `{ma7:.8f}`
• MA25: `{ma25:.8f}`
• RSI: `{rsi_val:.1f}`

✅ *Why:*
{chr(10).join(f'• {r}' for r in reasons)}

⚙️ Leverage: 3x–5x | Risk: 1% only
⚠️ _Not financial advice. Trade at your own risk._
"""
    return msg.strip()


def main():
    send_message("🤖 *Signal Bot Started!*\nMonitoring " + str(len(COINS)) + " coins every 5 minutes...")
    print("Bot running...")

    alerted = {}

    while True:
        for symbol in COINS:
            signal, price, ma7, ma25, rsi_val, reasons = analyze(symbol)

            if signal:
                key = f"{symbol}_{signal}"
                last_alert = alerted.get(key, 0)

                if time.time() - last_alert > 14400:
                    msg = format_signal(symbol, signal, price, ma7, ma25, rsi_val, reasons)
                    send_message(msg)
                    alerted[key] = time.time()
                    print(f"Signal sent: {symbol} {signal}")

            time.sleep(1)

        print(f"Scan complete. Sleeping {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
