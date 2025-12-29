
from NorenRestApiPy.NorenApi import NorenApi
import json
import hashlib
import requests
import pyotp
from datetime import date, datetime
import sys
import os

# ===== CONFIG =====
USER_ID = "FZXX1X"
PASSWORD = "AXXde7XXX"
API_KEY = "0eb3fed7XXXXXXXd20c1ec5XXXXXX52bec2e"
API_SECRET = "2025.032152f6XXXXXXXX8c0f4924XXXXXXXXXXecbda60d1bXXX722ebbc3"
TOTP_SECRET = "4QPZXT6GXXXXX64V4XXXXXX74X7BXXXLX5"

TOKEN_FILE = "flattrade_Searchtoken.json"
RESULTS_FILE = "Search_Results.json"

class FT(NorenApi):
    def __init__(self):
        super().__init__(
            host="https://piconnect.flattrade.in/PiConnectTP/",
            websocket="wss://piconnect.flattrade.in/PiConnectWSTp/"
        )

# ================= TOKEN MANAGEMENT =================
def load_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
            if data.get("date") == str(date.today()) and data.get("token"):
                print("✅ Token loaded from flattrade_Searchtoken.json (Valid for today)")
                return data["token"]
            else:
                print("🗓️ Token expired or invalid. Generating new...")
        except Exception as e:
            print(f"⚠️ Token file error: {e}. Generating new...")
    return None

def save_token(token):
    data = {"token": token, "date": str(date.today())}
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("💾 Token saved to flattrade_Searchtoken.json")
    except Exception as e:
        print(f"⚠️ Could not save token: {e}")

def login():
    totp = pyotp.TOTP(TOTP_SECRET).now()

    token = load_token()
    if token:
        api = FT()
        api.set_session(USER_ID, PASSWORD, token)
        return api

    print("🔐 LOGIN REQUIRED")
    print(f"🌐 Open this link in browser: https://auth.flattrade.in/?app_key={API_KEY}")
    print("   → Enter User ID & Password")
    print("   → Complete any OTP if asked")
    print("   → After successful login, copy the 'request_code' from URL or page\n")

    try:
        rc = input("📋 Paste request_code here: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\n⚠️ Input cancelled by user. Exiting safely...")
        sys.exit(0)

    if not rc:
        print("❌ Empty request_code entered. Bot stopped.")
        sys.exit(0)

    h = hashlib.sha256((API_KEY + rc + API_SECRET).encode()).hexdigest()

    try:
        print("🔄 Generating token...")
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
            save_token(token)
            print("✅ Login Successful!")
            print("🔑 Token received and session created.\n")

            api = FT()
            api.set_session(USER_ID, PASSWORD, token)
            return api
        else:
            error_msg = r.get("emsg", "Unknown error")
            print(f"❌ Login Failed: {error_msg}")
            sys.exit(0)

    except requests.exceptions.RequestException as e:
        print(f"🌐 Network Error: {str(e)}")
        sys.exit(0)
    except Exception as e:
        print(f"⚠️ Unexpected error during login: {str(e)}")
        sys.exit(0)

# ================= MAIN =================
try:
    api = login()

    while True:
        try:
            search_text = input("\n🔍 Enter symbol to search (e.g., BANDHANBNK, RELIANCE, NIFTY): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️ Search cancelled. Exiting safely...")
            sys.exit(0)

        if not search_text:
            print("❌ No symbol entered. Try again...")
            continue

        print(f"\n🔍 Searching for: {search_text} in NFO...")
        res = api.searchscrip("NFO", search_text)

        # Load existing data
        existing_data = []
        if os.path.exists(RESULTS_FILE):
            try:
                with open(RESULTS_FILE, "r") as f:
                    existing_data = json.load(f)
            except:
                existing_data = []

        # New entry with timestamp
        now = datetime.now()
        new_entry = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "search_text": search_text,
            "results": res
        }

        existing_data.append(new_entry)

        # Save updated data
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump(existing_data, f, indent=4)
            print(f"\n📁 Data appended to {RESULTS_FILE} with timestamp")
        except Exception as e:
            print(f"⚠️ Save error: {e}")

        if res and res.get("stat") == "Ok" and res.get("values"):
            values = res["values"]
            print(f"\n✅ Found {len(values)} results:\n")

            # Clean JSON format first
            clean_list = []
            for item in values:
                clean_item = {
                    "exch": item.get("exch"),
                    "token": item.get("token"),
                    "tsym": item.get("tsym"),
                    "dname": item.get("dname"),
                    "optt": item.get("optt"),
                    "instname": item.get("instname"),
                    "symname": item.get("symname"),
                    "seg": item.get("seg"),
                    "exd": item.get("exd"),
                    "pp": item.get("pp"),
                    "ls": item.get("ls"),
                    "ti": item.get("ti")
                }
                clean_list.append(clean_item)

            print("Clean JSON format:")
            print(json.dumps(clean_list, indent=4))
            print("\n" + "=" * 80 + "\n")

            # Pretty formatted results next
            print("Pretty formatted results:\n")
            for item in values:
                tsym = item.get("tsym", "N/A")
                token = item.get("token", "N/A")
                exd = item.get("exd", "N/A")
                optt = item.get("optt", "XX")
                ls = item.get("ls", "N/A")
                print(f"   📌 {tsym}")
                print(f"      Token: {token} | Expiry: {exd} | Type: {optt} | Lot: {ls}")
                print("   ---")

        else:
            print("\n❌ No results found or error in search.\n")

except KeyboardInterrupt:
    print("\n\n🛑 Ctrl + C detected. Exiting safely...")
    sys.exit(0)
except Exception as e:
    print(f"\n🔴 Unexpected error: {str(e)}")
    sys.exit(1)
