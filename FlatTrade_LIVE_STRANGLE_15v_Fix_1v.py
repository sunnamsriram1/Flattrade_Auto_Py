from NorenRestApiPy.NorenApi import NorenApi
import requests, hashlib, time, os, json
from datetime import datetime, time as dtime, date, timedelta
import pytz

os.system("clear")

# ================= CONFIG =================
USER_ID = "FZXX3X8"
PASSWORD = "AXXeXXXX"
API_KEY = "0eXXXXXXXXXX20c1ec552XXXXXXXXXXbec2e"
API_SECRET = "2025.03XXXXXXXX56aadcaecbdaXXXXXXXXX60d1b722ebbc3"

SYMBOL = "BANKNIFTY"
STRIKE_STEP = 100
QTY = 15

PAPER = True      # True for paper, False for live
ENTRY_TIME = dtime(9, 20)

TARGET_POINTS = 100
STOPLOSS_POINTS = 70

TOKEN_FILE = "flattrade_token.json"
LOG_FILE = "strangle_bot_log.json"

TELEGRAM_BOT_TOKEN = "855XXX81XX37:AAGXXXXXXXXiA58ZYyLXXXXXXIoZdi9eqrI"  # Replace with your token
TELEGRAM_CHAT_ID = "57XXX475XXXX129"      # Replace with your chat ID
# =========================================

logs = []  # Global list to collect all events for saving

def send_telegram_message(message):
    if TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here" or TELEGRAM_CHAT_ID == "your_telegram_chat_id_here":
        return  # Skip if not configured
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram send error: {str(e)}")

class FT(NorenApi):
    def __init__(self):
        super().__init__(
            host="https://piconnect.flattrade.in/PiConnectTP/",
            websocket="wss://piconnect.flattrade.in/PiConnectWSTp/"
        )

# ================= TOKEN =================
def load_token():
    if os.path.exists(TOKEN_FILE):
        d = json.load(open(TOKEN_FILE))
        if d.get("date") == str(date.today()):
            return d["token"]
    return None

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
    json.dump({"token": token, "date": str(date.today())}, open(TOKEN_FILE, "w"))
    return token


def connect():
    api = FT()
    token = load_token() or generate_token()
    api.set_session(USER_ID, PASSWORD, token)

    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    
    # First beautiful prints
    time_str = f"🕒 India Time : {now.strftime('%d-%m-%Y %I:%M:%S %p')}"
    print(time_str)
    day_str = f"📅 Day        : {now.strftime('%A')}"
    print(day_str)
    conn_str = "✅ Connected to FlatTrade_Server"
    print(conn_str)
    mode_str = "🔥 LIVE MODE — REAL MONEY" if not PAPER else "🧪 PAPER MODE"
    print(mode_str)
    target_str = f"🎯 TARGET: {TARGET_POINTS} pts | 🛑 SL: {STOPLOSS_POINTS} pts"
    print(target_str)
    print()
    bot_start_str = "🚀 STRANGLE BOT STARTED"
    print(bot_start_str)
    exit_info_str = "ℹ️ Exit చేయాలంటే Ctrl + C"
    print(exit_info_str)
    
    # Send initial to Telegram
    initial_message = f"{time_str}\n{day_str}\n{conn_str}\n{mode_str}\n{target_str}\n\n{bot_start_str}\n{exit_info_str}"
    send_telegram_message(initial_message)
    
    # Save to logs
    logs.append({"event": "time", "india_time": now.strftime("%d-%m-%Y %I:%M:%S %p")})
    logs.append({"event": "day", "day": now.strftime("%A")})
    logs.append({"event": "connection", "status": "Connected to FlatTrade_Server"})
    logs.append({"event": "mode", "mode": "LIVE MODE — REAL MONEY" if not PAPER else "PAPER MODE"})
    logs.append({"event": "targets", "target_points": TARGET_POINTS, "stoploss_points": STOPLOSS_POINTS})
    logs.append({"event": "bot_started", "name": "STRANGLE BOT STARTED"})
    logs.append({"event": "exit_info", "info": "Exit చేయాలంటే Ctrl + C"})

    return api

api = connect()



import time
time.sleep(5)

# ================= UTILITIES =================
def market_open():
    return dtime(9,15) <= datetime.now().time() <= dtime(15,30)

def get_nearest_expiry():
    today = date.today()
    if today.month == 12:
        next_month_first = date(today.year + 1, 1, 1)
    else:
        next_month_first = date(today.year, today.month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    days_back = (last_day.weekday() - 1) % 7  # 1 = Tuesday
    expiry = last_day - timedelta(days=days_back)
    return expiry.strftime("%d%b%y").upper()  # 30DEC25

def search_token(search_text):
    r = api.searchscrip(exchange="NFO", searchtext=search_text)
    data = {"event": "search_result", "for": search_text, "result": r}
    logs.append(data)
    json_str = json.dumps(data, indent=4)
    print(json_str)
    send_telegram_message(json_str)
    if not r or "values" not in r or len(r["values"]) == 0:
        return None
    return r["values"][0]["token"]

def get_ltp(search_text):
    token = search_token(search_text)
    if not token:
        raise Exception(f"LTP SYMBOL ERROR: {search_text}")
    q = api.get_quotes(exchange="NFO", token=token)
    if q and "lp" in q:
        return float(q["lp"])
    else:
        raise Exception(f"No LTP data for {search_text}")

def fut_ltp():
    return get_ltp("BANKNIFTY FUT")

def atm_strike():
    return int(round(fut_ltp() / STRIKE_STEP) * STRIKE_STEP)

def place(symbol, side):
    if PAPER:
        data = {"event": "paper_trade", "side": side, "symbol": symbol}
        logs.append(data)
        json_str = json.dumps(data, indent=4)
        print(json_str)
        send_telegram_message(json_str)
        return {"stat": "Ok", "result": "PAPER_ORDER"}

    try:
        ret = api.place_order(
            buy_or_sell=side,
            product_type="M",
            exchange="NFO",
            tradingsymbol=symbol,
            quantity=QTY,
            discloseqty=0,
            price_type="MKT",
            price=0,
            retention="DAY",
            remarks="STRANGLE_AUTO"
        )
        resp = {"request_time": datetime.now().strftime("%H:%M:%S %d-%m-%Y")}
        if ret and ret.get("stat") == "Ok":
            resp["stat"] = "Ok"
            resp["result"] = ret.get("norenordno", "UNKNOWN")
        else:
            resp["stat"] = "Not_Ok"
            resp["emsg"] = ret.get("emsg", "Unknown error")
        logs.append(resp)
        json_str = json.dumps(resp, indent=4)
        print(json_str)
        send_telegram_message(json_str)
        return ret
    except Exception as e:
        err_resp = {
            "request_time": datetime.now().strftime("%H:%M:%S %d-%m-%Y"),
            "stat": "Not_Ok",
            "emsg": str(e)
        }
        logs.append(err_resp)
        json_str = json.dumps(err_resp, indent=4)
        print(json_str)
        send_telegram_message(json_str)
        return None

# ================= STRANGLE =================
trade_done = False
ce_sym = pe_sym = ""
entry_ce = entry_pe = 0
exp = ""

def enter_trade():
    global trade_done, ce_sym, pe_sym, entry_ce, entry_pe, exp

    exp = get_nearest_expiry()
    atm = atm_strike()

    ce_sym = f"{SYMBOL}{exp}C{atm}"
    pe_sym = f"{SYMBOL}{exp}P{atm}"

    entry_ce = get_ltp(ce_sym)
    entry_pe = get_ltp(pe_sym)

    placing_ce = {"event": "placing_order", "leg": "CE", "symbol": ce_sym}
    logs.append(placing_ce)
    print(json.dumps(placing_ce, indent=4))
    send_telegram_message(json.dumps(placing_ce, indent=4))
    place(ce_sym, "S")

    placing_pe = {"event": "placing_order", "leg": "PE", "symbol": pe_sym}
    logs.append(placing_pe)
    print(json.dumps(placing_pe, indent=4))
    send_telegram_message(json.dumps(placing_pe, indent=4))
    place(pe_sym, "S")

    trade_done = True
    entry_data = {
        "event": "entry_done",
        "ce_sym": ce_sym, "entry_ce": entry_ce,
        "pe_sym": pe_sym, "entry_pe": entry_pe
    }
    logs.append(entry_data)
    print(json.dumps(entry_data, indent=4))
    send_telegram_message(json.dumps(entry_data, indent=4))

def monitor_trade():
    ce = get_ltp(ce_sym)
    pe = get_ltp(pe_sym)

    pnl_ce = (entry_ce - ce) * QTY
    pnl_pe = (entry_pe - pe) * QTY
    total_pnl = pnl_ce + pnl_pe

    pnl_data = {
        "event": "pnl",
        "ce_pnl": round(pnl_ce, 2),
        "pe_pnl": round(pnl_pe, 2),
        "total_pnl": round(total_pnl, 2)
    }
    logs.append(pnl_data)
    print(json.dumps(pnl_data, indent=4))
    send_telegram_message(json.dumps(pnl_data, indent=4))

    if total_pnl >= TARGET_POINTS * QTY:
        exit_trade("TARGET HIT", total_pnl)
    if total_pnl <= -STOPLOSS_POINTS * QTY:
        exit_trade("STOPLOSS HIT", total_pnl)

def exit_trade(reason, pnl):
    placing_ce_exit = {"event": "placing_order", "leg": "CE EXIT", "symbol": ce_sym}
    logs.append(placing_ce_exit)
    print(json.dumps(placing_ce_exit, indent=4))
    send_telegram_message(json.dumps(placing_ce_exit, indent=4))
    place(ce_sym, "B")

    placing_pe_exit = {"event": "placing_order", "leg": "PE EXIT", "symbol": pe_sym}
    logs.append(placing_pe_exit)
    print(json.dumps(placing_pe_exit, indent=4))
    send_telegram_message(json.dumps(placing_pe_exit, indent=4))
    place(pe_sym, "B")

    exit_data = {
        "event": "exit",
        "reason": reason,
        "final_pnl": round(pnl, 2)
    }
    logs.append(exit_data)
    print(json.dumps(exit_data, indent=4))
    send_telegram_message(json.dumps(exit_data, indent=4))
    exit()

# ================= MAIN LOOP =================
try:
    while True:
        try:
            now = datetime.now()
            ts_data = {"event": "timestamp", "time": now.strftime("%H:%M:%S")}
            logs.append(ts_data)
            print(json.dumps(ts_data, indent=4))
            send_telegram_message(json.dumps(ts_data, indent=4))

            if not market_open():
                time.sleep(30)
                continue

            if now.time() >= ENTRY_TIME and not trade_done:
                enter_trade()

            if trade_done:
                monitor_trade()

            time.sleep(5)

        except Exception as e:
            err_data = {"event": "error", "message": str(e)}
            logs.append(err_data)
            print(json.dumps(err_data, indent=4))
            send_telegram_message(json.dumps(err_data, indent=4))
            time.sleep(5)

except KeyboardInterrupt:
    int_data = {"event": "interrupt", "message": "Ctrl + C detected"}
    logs.append(int_data)
    print(json.dumps(int_data, indent=4))
    # No send here to avoid hang

    stop_data = {"event": "bot_stopped", "message": "STRANGLE BOT STOPPED SAFELY"}
    logs.append(stop_data)
    print(json.dumps(stop_data, indent=4))
    # No send here to avoid hang

    # Final save to file
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

    print(f"\n📁 All logs saved to {LOG_FILE}")
