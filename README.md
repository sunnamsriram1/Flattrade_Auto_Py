# 📈 Flattrade Auto Strangle Bot
## (పూర్తి తెలుగు వివరణ – README.md)

---

## ⚠️ ముఖ్య గమనిక (Disclaimer)
ఈ ప్రాజెక్ట్ **విద్యా ప్రయోజనాల కోసం మాత్రమే**.

👉 Live trading లో వాడితే **డబ్బు నష్టం జరిగే అవకాశం ఉంది**.  
👉 మీ బాధ్యత మీదే Live mode ఉపయోగించాలి.  
👉 మొదట PAPER MODE లో పూర్తిగా test చేయండి.

---

## 📌 ఈ ప్రాజెక్ట్ ఏమిటి?

ఇది ఒక **BANKNIFTY Auto Strangle Trading Bot**.

ఈ బాట్:
- Flattrade (PiConnect / Noren API) ఉపయోగిస్తుంది
- ATM CE & PE options ని ఆటోమేటిక్‌గా SELL చేస్తుంది
- Target లేదా Stoploss వచ్చినప్పుడు ఆటోమేటిక్‌గా EXIT అవుతుంది
- Paper Trading & Live Trading రెండింటినీ support చేస్తుంది

---

## 🧠 Strangle Strategy అంటే ఏమిటి?

- ఒకే strike వద్ద:
  - 1 ATM CALL (CE) SELL
  - 1 ATM PUT (PE) SELL

👉 Market sideways లో ఉంటే లాభం వచ్చే strategy.

---

## 🧰 అవసరమైనవి (Requirements)

### 🔹 Software
- Python 3.9 లేదా అంతకంటే ఎక్కువ
- Flattrade Trading Account
- PiConnect API Access

### 🔹 Python Packages
```bash
pip install requests pyotp pytz
```

---

## ⚙️ Configuration (అత్యంత ముఖ్యమైన భాగం)

ఈ values మీ ఖాతా ప్రకారం మార్చాలి:

```python
USER_ID = "YOUR_USER_ID"
PASSWORD = "YOUR_PASSWORD"
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"
TOTP_SECRET = "YOUR_TOTP_SECRET"
```

⚠️ **GitHub లో upload చేసే ముందు తప్పనిసరిగా hide చేయాలి**

---

## 📊 Trading Settings

```python
SYMBOL = "BANKNIFTY"
STRIKE_STEP = 100
QTY = 15

PAPER = True        # True = Paper | False = Live
ENTRY_TIME = 09:20

TARGET_POINTS = 100
STOPLOSS_POINTS = 70
```

---

## 🔐 Token System (Login Process)

### 🔹 load_token()
- Token file (`flattrade_token.json`) ఉందా check చేస్తుంది
- అదే రోజు token అయితే reuse చేస్తుంది
- లేకపోతే కొత్త token generate చేస్తుంది

---

### 🔹 generate_token()
ఈ function లో జరిగేది:

1. India Time & Day print అవుతుంది
2. Flattrade Login URL చూపిస్తుంది
3. Browser లో login అవ్వాలి
4. `request_code` paste చేయాలి
5. SHA256 hash create అవుతుంది
6. API token generate అవుతుంది
7. Token file లో save అవుతుంది

### 📁 Token File Format
```json
{
  "token": "xxxxxxxx",
  "date": "2025-12-24",
  "time_ist": "06:05:23 PM",
  "day": "Tuesday"
}
```

---

## 🔌 API Connection

### 🔹 connect()
- Token load లేదా generate చేస్తుంది
- Flattrade server కి connect అవుతుంది
- Successful అయితే message print అవుతుంది

```text
✅ Connected to FlatTrade_Server
```

---

## 🕒 Market Related Functions

### 🔹 market_open()
- Market open ఉందా check చేస్తుంది
- Time: 9:15 AM – 3:30 PM

---

### 🔹 get_nearest_expiry()
- BANKNIFTY కి nearest weekly expiry తీస్తుంది

---

### 🔹 fut_ltp()
- BANKNIFTY Futures current price తీస్తుంది

---

### 🔹 atm_strike()
- Futures price ఆధారంగా ATM strike calculate చేస్తుంది

---

## 📈 Option Functions

### 🔹 option_symbols(atm)
- ATM CE & PE symbols generate చేస్తుంది

### 🔹 get_ltp(symbol)
- Option current LTP తీస్తుంది

---

## 📝 Order Placement

### 🔹 place(symbol, side)

| Mode | Action |
|----|----|
| PAPER | Print మాత్రమే |
| LIVE | Real order place |

SELL = `"S"`  
BUY = `"B"`

---

## 📊 Trading Logic

### 🔹 enter_trade()
- Entry time వచ్చినప్పుడు run అవుతుంది
- ATM CE & PE SELL చేస్తుంది
- Entry prices save చేస్తుంది

---

### 🔹 monitor_trade()
- ప్రతి few seconds కి PnL calculate చేస్తుంది

**PnL Formula:**
```
(Entry CE - Current CE) + (Entry PE - Current PE)
```

---

### 🔹 exit_trade()
- Target లేదా SL hit అయితే
- Both legs BUY back చేస్తుంది
- CSV లో trade save చేస్తుంది
- Program exit అవుతుంది

---

## 📁 CSV Logging

File: `strangle_trades.csv`

```csv
TIME, CE, PE, PNL
```

---

## 🔁 Main Loop

- Market open wait చేస్తుంది
- Entry time వచ్చినప్పుడు trade enter
- Exit అయ్యే వరకు monitor చేస్తుంది

Terminal output example:
```
⏳ 10:15:30
📊 PnL: 420
```

---

## 🧪 PAPER vs 🔥 LIVE MODE

| Feature | PAPER | LIVE |
|------|------|------|
| Money Risk | ❌ | ✅ |
| Orders | Fake | Real |
| Beginners | Best | Risky |

---

## 📲 Telegram Alerts (Optional)

```python
TG_ENABLE = True
TG_BOT_TOKEN = "YOUR_BOT_TOKEN"
TG_CHAT_ID = "YOUR_CHAT_ID"
```

---

## ▶️ Run చేయడం ఎలా?

```bash
python SAFE_LIVE_STRANGLE_4v.py
```

---

## 🚀 Future Improvements
- WebSocket live prices
- Trailing Stoploss
- Multi-lot trading
- Strategy customization
- Dashboard UI

---

## 👨‍💻 Author
**Sunnam Sriram**  
GitHub: https://github.com/sunnamsriram1

---

## ⭐ ముగింపు

ఈ ప్రాజెక్ట్:
- Algo Trading basics నేర్పుతుంది
- Real API usage చూపిస్తుంది
- GitHub portfolio కి చాలా మంచిది

👉 మీకు ఉపయోగపడితే ⭐ Star చేయండి

