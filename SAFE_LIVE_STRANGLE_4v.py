from NorenRestApiPy.NorenApi import NorenApi
import requests, hashlib, pyotp, time, csv, os, json
from datetime import datetime, time as dtime, date
import os

os.system('clear')


# ================= CONFIG =================
USER_ID = "FZxxxxxx"
PASSWORD = "AbXXXXXXX"
API_KEY = "0eb3fed7140c443aaXXXXXXXXXXad20c1ec552bec2"
API_SECRET = "2025.032152fXXXXXXXXXXXXXXXXXa60d1b722ebbc3"
TOTP_SECRET = "4QPZT6XXXXXXXXXXXXXXXH764V4YNA7R74X7BLX5"

SYMBOL = "BANKNIFTY"
STRIKE_STEP = 100
QTY = 15

PAPER = True           # False = LIVE
ENTRY_TIME = dtime(9, 20)

TARGET_POINTS = 100
STOPLOSS_POINTS = 70

CSV_FILE = "strangle_trades.csv"
TOKEN_FILE = "flattrade_token.json"

# Telegram (optional)
TG_ENABLE = False     # True = SendMessage
TG_BOT_TOKEN = "YOUR_BOT_TOKEN"
TG_CHAT_ID = "YOUR_CHAT_ID"
# =========================================


class FT(NorenApi):
    def __init__(self):
        super().__init__(
            host="https://piconnect.flattrade.in/PiConnectTP/",
            websocket="wss://piconnect.flattrade.in/PiConnectWSTp/"
        )


def telegram(msg):
    if not TG_ENABLE:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg})


# ================= TOKEN =================

def load_token():
    if os.path.exists(TOKEN_FILE):
        data = json.load(open(TOKEN_FILE))
        if data.get("date") == str(date.today()):
            return data.get("token")
    return None



def generate_token():
    from datetime import datetime, date
    import pytz, json, hashlib, requests

    # ================= India Time =================
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    print("🕒 India Time :", now.strftime("%d-%m-%Y %I:%M:%S %p"))
    print("📅 Day        :", now.strftime("%A"))
    print("🔐 LOGIN URL  :", f"https://auth.flattrade.in/?app_key={API_KEY}")

    # ================ Request Code Input ================
    rc = input("Paste request_code: ").strip()

    # ================ Token Hash ================
    h = hashlib.sha256((API_KEY + rc + API_SECRET).encode()).hexdigest()

    # ================ API Call ================
    r = requests.post(
        "https://authapi.flattrade.in/trade/apitoken",
        json={
            "api_key": API_KEY,
            "request_code": rc,
            "api_secret": h
        }
    ).json()

    # ================ Token Extract ================
    token = r["token"]

    # ================ Save Token with India Time + Day ================
    json.dump(
        {
            "token": token,
            "date": str(date.today()),
            "time_ist": now.strftime("%I:%M:%S %p"),
            "day": now.strftime("%A")
        },
        open(TOKEN_FILE, "w"),
        indent=2
    )

    print("✅ TOKEN GENERATED SUCCESSFULLY")
    return token


"""
def generate_token():
    print("🔐 LOGIN:", f"https://auth.flattrade.in/?app_key={API_KEY}")
    rc = input("Paste request_code: ").strip()

    h = hashlib.sha256((API_KEY + rc + API_SECRET).encode()).hexdigest()

    r = requests.post(
        "https://authapi.flattrade.in/trade/apitoken",
        json={
            "api_key": API_KEY,
            "request_code": rc,
            "api_secret": h
        }
    ).json()

    token = r["token"]
    json.dump(
        {"token": token, "date": str(date.today())},
        open(TOKEN_FILE, "w")
    )
    return token
"""




def connect():
    from datetime import datetime, date
    import pytz, json, hashlib, requests
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    print("🕒 India Time :", now.strftime("%d-%m-%Y %I:%M:%S %p"))
    print("📅 Day        :", now.strftime("%A"))

    api = FT()
    token = load_token() or generate_token()
    api.set_session(USER_ID, PASSWORD, token)
    print("\n✅ Connected to FlatTrade_Server")
    return api


api = connect()

# ================= MODE INFO =================
if PAPER:
    print("🧪 RUNNING IN SAFE PAPER MODE")
else:
    print("🔥 LIVE MODE — REAL MONEY")

print(f"🎯 TARGET: {TARGET_POINTS} pts | 🛑 SL: {STOPLOSS_POINTS} pts")


# ================= UTILITIES =================

def market_open():
    now = datetime.now().time()
    return dtime(9, 15) <= now <= dtime(15, 30)


def get_nearest_expiry():
    r = api.searchscrip("NFO", SYMBOL)
    for v in r["values"]:
        if v["instname"] == "FUTIDX":
            return v["tsym"][len(SYMBOL):len(SYMBOL)+7]


def fut_ltp():
    exp = get_nearest_expiry()
    r = api.searchscrip("NFO", f"{SYMBOL}{exp}F")
    token = r["values"][0]["token"]
    q = api.get_quotes("NFO", token)
    return float(q["lp"])


def atm_strike():
    return int(round(fut_ltp() / STRIKE_STEP) * STRIKE_STEP)


def option_symbols(atm):
    exp = get_nearest_expiry()
    return (
        f"{SYMBOL}{exp}{atm}CE",
        f"{SYMBOL}{exp}{atm}PE"
    )


def get_ltp(symbol):
    r = api.searchscrip("NFO", symbol)
    token = r["values"][0]["token"]
    q = api.get_quotes("NFO", token)
    return float(q["lp"])


def place(symbol, side):
    if PAPER:
        print(f"📝 PAPER {side} {symbol}")
        return

    api.place_order(
        buy_or_sell=side,
        product_type="M",
        exchange="NFO",
        tradingsymbol=symbol,
        quantity=QTY,
        price_type="MKT",
        price=0,
        retention="DAY",
        remarks="STRANGLE_AUTO"
    )


def log_csv(row):
    new = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["TIME", "CE", "PE", "PNL"])
        w.writerow(row)


# ================= STRANGLE =================

trade_done = False
ce_sym = pe_sym = ""
entry_ce = entry_pe = 0


def enter_trade():
    global trade_done, ce_sym, pe_sym, entry_ce, entry_pe

    atm = atm_strike()
    ce_sym, pe_sym = option_symbols(atm)

    entry_ce = get_ltp(ce_sym)
    entry_pe = get_ltp(pe_sym)

    place(ce_sym, "S")
    place(pe_sym, "S")

    trade_done = True
    telegram(f"ENTRY DONE\n{ce_sym}\n{pe_sym}")
    print("✅ ENTRY DONE")


def monitor_trade():
    ce_ltp = get_ltp(ce_sym)
    pe_ltp = get_ltp(pe_sym)

    pnl = ((entry_ce - ce_ltp) + (entry_pe - pe_ltp)) * QTY
    print(f"📊 PnL: {round(pnl, 2)}")

    if pnl >= TARGET_POINTS * QTY:
        exit_trade("TARGET HIT", pnl)

    if pnl <= -STOPLOSS_POINTS * QTY:
        exit_trade("STOPLOSS HIT", pnl)


def exit_trade(reason, pnl):
    place(ce_sym, "B")
    place(pe_sym, "B")
    log_csv([datetime.now(), ce_sym, pe_sym, pnl])
    telegram(f"{reason}\nPnL: {pnl}")
    print(f"🏁 {reason} | PnL: {pnl}")
    exit()

# ================= MAIN LOOP =================

print("\n🚀 STRANGLE BOT STARTED")
print("ℹ️ Exit చేయాలంటే Ctrl + C నొక్కండి")

try:
    while True:
        try:
            now = datetime.now()
            print("⏳", now.strftime("%H:%M:%S"))

            if not market_open():
                time.sleep(30)
                continue

            if now.time() >= ENTRY_TIME and not trade_done:
                enter_trade()

            if trade_done:
                monitor_trade()

            time.sleep(5)

        except Exception as e:
            print("❌ ERROR:", e)
            time.sleep(5)

except KeyboardInterrupt:
    print("\n🛑 Ctrl + C detected")
    print("👋 STRANGLE BOT STOPPED SAFELY")
    exit()

# ================= MAIN LOOP =================
"""
print("\n🚀 STRANGLE BOT STARTED")

while True:
    try:
        now = datetime.now()
        print("⏳", now.strftime("%H:%M:%S"))

        if not market_open():
            time.sleep(30)
            continue

        if now.time() >= ENTRY_TIME and not trade_done:
            enter_trade()

        if trade_done:
            monitor_trade()

        time.sleep(5)

    except Exception as e:
        print("❌ ERROR:", e)
        time.sleep(5)
"""
