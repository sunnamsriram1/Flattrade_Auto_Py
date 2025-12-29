
from NorenRestApiPy.NorenApi import NorenApi
import requests, hashlib, time, os, json
from datetime import datetime, time as dtime, date, timedelta
import pytz
import signal
import sys

os.system("clear")

# ================= CONFIG =================
USER_ID = "FZ3XXX1X"
PASSWORD = "ABXXXJX"
API_KEY = "0eb3fXXXXXX443aad2XXX0c1ecXXXXXXX552bec2e"
API_SECRET = "2025.0XXXXXXXXXf4924aXXXX65cf9056aaXXXXXXXX1b722ebbc3"

SYMBOL = "BANKNIFTY"
STRIKE_STEP = 100
QTY = 15

PAPER = True      # True for paper, False for Live
ENTRY_TIME = dtime(9, 20)

TARGET_POINTS = 100
STOPLOSS_POINTS = 70

TOKEN_FILE = "flattrade_token.json"
LOG_FILE = "strangle_bot_log.json"

TELEGRAM_BOT_TOKEN = "8559748137:AAXXXXXX06z-ChXXXXXXXXXLIoZdi9eqrI"
TELEGRAM_CHAT_ID = "57XXXXXX51XX29"
# =========================================

# ANSI Colors
RED_BOLD = "\033[1;31m"
GREEN_BOLD = "\033[1;32m"
RESET = "\033[0m"

logs = []

def send_telegram_message(message):
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
        try:
            d = json.load(open(TOKEN_FILE))
            if d.get("date") == str(date.today()):
                return d["token"]
        except:
            pass
    return None

def generate_token():
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    time_str = f"🕒 India Time : {now.strftime('%d-%m-%Y %I:%M:%S %p')}"
    print(time_str)
    day_str = f"📅 Day        : {now.strftime('%A')}"
    print(day_str)

    print("\n🔐 LOGIN:", f"https://auth.flattrade.in/?app_key={API_KEY}")
    try:
        rc = input("\n\nPaste request_code: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n⚠️ Input cancelled. Bot stopping safely...")
        sys.exit(0)

    if not rc:
        print("❌ Empty request_code. Bot stopped.")
        sys.exit(0)

    h = hashlib.sha256((API_KEY + rc + API_SECRET).encode()).hexdigest()

    try:
        r = requests.post(
            "https://authapi.flattrade.in/trade/apitoken",
            json={
                "api_key": API_KEY,
                "request_code": rc,
                "api_secret": h
            },
            timeout=30
        ).json()

        if r.get("stat") == "Ok":
            token = r["token"]
            json.dump({"token": token, "date": str(date.today())}, open(TOKEN_FILE, "w"))
            print("✅ Login Successful! Token saved for today.")
            send_telegram_message("✅ Login Successful! Bot ready.")
            return token
        else:
            print(f"❌ Login Failed: {r.get('emsg', 'Unknown error')}")
            send_telegram_message(f"❌ Login Failed: {r.get('emsg', 'Unknown error')}")
            sys.exit(0)
    except Exception as e:
        print(f"🌐 Network Error during login: {str(e)}")
        sys.exit(0)

def connect():
    api = FT()
    token = load_token() or generate_token()
    api.set_session(USER_ID, PASSWORD, token)

    now = datetime.now(pytz.timezone("Asia/Kolkata"))

    print(f"🕒 India Time : {now.strftime('%d-%m-%Y %I:%M:%S %p')}")
    print(f"📅 Day        : {now.strftime('%A')}")
    print("✅ Connected to FlatTrade_Server")
    print("🧪 PAPER MODE" if PAPER else "🔥 LIVE MODE — REAL MONEY")
    print(f"🎯 TARGET: {TARGET_POINTS} pts | 🛑 SL: {STOPLOSS_POINTS} pts")
    print()
    print("🚀 STRANGLE BOT STARTED")
    print("ℹ️ Exit Try Do HiT Ctrl + C")

    initial_message = (
        f"🕒 <b>{now.strftime('%d-%m-%Y %I:%M:%S %p')}</b>\n"
        f"📅 <b>{now.strftime('%A')}</b>\n"
        "✅ Connected\n"
        f"{'🧪 PAPER MODE' if PAPER else '🔥 LIVE MODE'}\n"
        f"🎯 TARGET: {TARGET_POINTS} pts | 🛑 SL: {STOPLOSS_POINTS} pts\n\n"
        "🚀 <b>STRANGLE BOT STARTED</b>"
    )
    send_telegram_message(initial_message)

    logs.append({"event": "time", "india_time": now.strftime("%d-%m-%Y %I:%M:%S %p")})
    logs.append({"event": "day", "day": now.strftime("%A")})
    logs.append({"event": "connection", "status": "Connected to FlatTrade_Server"})
    logs.append({"event": "mode", "mode": "PAPER MODE" if PAPER else "LIVE MODE — REAL MONEY"})
    logs.append({"event": "targets", "target_points": TARGET_POINTS, "stoploss_points": STOPLOSS_POINTS})
    logs.append({"event": "bot_started", "name": "STRANGLE BOT STARTED"})
    logs.append({"event": "exit_info", "info": "Exit చేయాలంటే Ctrl + C"})

    return api

api = connect()

# ================= UTILITIES =================
def market_open():
    current_time = datetime.now().time()
    return dtime(9, 15) <= current_time <= dtime(15, 30)

def get_nearest_expiry():
    today = date.today()
    if today.month == 12:
        next_month_first = date(today.year + 1, 1, 1)
    else:
        next_month_first = date(today.year, today.month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    days_back = (last_day.weekday() - 1) % 7
    expiry = last_day - timedelta(days=days_back)
    return expiry.strftime("%d%b%y").upper()

def search_token(search_text):
    try:
        r = api.searchscrip(exchange="NFO", searchtext=search_text)
    except:
        return None
    data = {"event": "search_result", "for": search_text, "result": r if 'r' in locals() else {"stat": "Error"}}
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
    if trade_done:
        return

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
    if trade_done:
        place(ce_sym, "B")
        place(pe_sym, "B")

    exit_data = {
        "event": "exit",
        "reason": reason,
        "final_pnl": round(pnl, 2)
    }
    logs.append(exit_data)
    print(json.dumps(exit_data, indent=4))
    send_telegram_message(json.dumps(exit_data, indent=4))
    sys.exit(0)

# ================= SAFE SHUTDOWN =================
def signal_handler(sig, frame):
    print("\n\n🛑 Graceful Shutdown Initiated...")
    int_data = {"event": "interrupt", "message": "Ctrl + C detected"}
    logs.append(int_data)
    print(json.dumps(int_data, indent=4))

    stop_data = {"event": "bot_stopped", "message": "STRANGLE BOT STOPPED SAFELY"}
    logs.append(stop_data)
    print(json.dumps(stop_data, indent=4))

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

    print(f"\n{GREEN_BOLD}📁 All Logs Saved to {LOG_FILE}{RESET}\n")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ================= MAIN LOOP =================
market_closed_message_shown = False

try:
    while True:
        try:
            now = datetime.now()
            current_time_str = now.strftime("%H:%M:%S")
            ts_data = {"event": "timestamp", "time": current_time_str}
            logs.append(ts_data)
            print(json.dumps(ts_data, indent=4))
            send_telegram_message(json.dumps(ts_data, indent=4))

            if not market_open():
                if not market_closed_message_shown:
                    closed_msg = f"{RED_BOLD}⏳ Market Closed - Waiting for Market Open (9:15 AM - 3:30 PM){RESET}"
                    print(closed_msg)

                    waiting_data = {
                        "event": "market_status",
                        "display": "RED_BOLD",
                        "status": "Closed - Bot Will Resume at Market Open"
                    }
                    logs.append(waiting_data)

                    green_json = f"{RED_BOLD}{json.dumps(waiting_data, indent=4)}{RESET}"
                    print(green_json)

                    send_telegram_message("<b>⏳ Market Closed</b>\nBot waiting for next market open")
                    market_closed_message_shown = True
                time.sleep(30)
                continue
            else:
                if market_closed_message_shown:
                    open_msg = "🟢 Market Opened - Bot Resumed!"
                    print(open_msg)
                    resumed_data = {"event": "market_status", "status": "Open - Bot resumed"}
                    logs.append(resumed_data)
                    print(json.dumps(resumed_data, indent=4))
                    send_telegram_message(open_msg)
                    market_closed_message_shown = False

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

except Exception as e:
    # Final fallback
    print(f"\n🔴 Unexpected error: {str(e)}")
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)
    sys.exit(1)
