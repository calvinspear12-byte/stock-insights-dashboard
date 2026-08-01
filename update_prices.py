# Lightweight intraday price refresh for the live dashboard.
# Fetches current quotes for the roster tickers + major indices from Yahoo (free)
# and writes prices.json, which the hosted page fetches through the trading day.
import os, json, re, urllib.request, urllib.parse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
OUT = os.path.join(HERE, "prices.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
INDICES = {"^GSPC": "SPX", "^IXIC": "NASDAQ", "^DJI": "DOW"}

def quote(sym):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(sym) + "?range=1d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.load(r)
    m = d["chart"]["result"][0]["meta"]
    price = m.get("regularMarketPrice")
    prev = m.get("chartPreviousClose") or m.get("previousClose")
    chg = round((price / prev - 1) * 100, 2) if (price is not None and prev) else None
    return (round(price, 2) if price is not None else None), chg

def tickers():
    html = open(INDEX, encoding="utf-8").read()
    seen = []
    for t in re.findall(r'ticker:"([A-Z.]{1,6})"', html):
        if t not in seen:
            seen.append(t)
    return seen

def main():
    quotes = {}
    for t in tickers():
        try:
            p, c = quote(t)
            if p is not None:
                quotes[t] = {"price": p, "chg": c}
        except Exception as e:
            print(t, "err", str(e)[:80])
    idx = {}
    for sym, name in INDICES.items():
        try:
            p, c = quote(sym)
            if p is not None:
                idx[name] = {"level": p, "chg": c}
        except Exception as e:
            print(sym, "err", str(e)[:80])
    out = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "quotes": quotes, "indices": idx,
    }
    open(OUT, "w").write(json.dumps(out))
    print("wrote prices.json:", len(quotes), "quotes,", len(idx), "indices")

if __name__ == "__main__":
    main()
