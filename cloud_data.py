# Cloud (GitHub Actions) refresh: Kronos ~1-month forecasts + weekly price history,
# injected straight into index.html. Cross-platform, no Claude, no PC. Free Yahoo OHLCV.
import os, sys, re, json, urllib.request, urllib.parse, datetime, platform
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
KRONOS_DIR = os.environ.get("KRONOS_DIR", os.path.join(HERE, "Kronos"))
sys.path.insert(0, KRONOS_DIR)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
BENCH = {"SPY": "S&P 500 ETF", "QQQ": "Nasdaq 100 ETF"}
PRED_LEN, LOOKBACK, SAMPLE_COUNT = 21, 256, 5

def maybe_ca():
    # Only needed behind the Windows/Verisk proxy; Linux runners use default certs.
    if platform.system() != "Windows":
        return
    import ssl
    bundle = os.path.join(HERE, "ca-bundle.pem")
    if not os.path.exists(bundle) or os.path.getsize(bundle) < 1000:
        certs = []
        for store in ("ROOT", "CA"):
            try:
                for cert, enc, trust in ssl.enum_certificates(store):
                    if enc == "x509_asn":
                        certs.append(ssl.DER_cert_to_PEM_cert(cert))
            except Exception:
                pass
        open(bundle, "w").write("\n".join(certs))
    for v in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE"):
        os.environ[v] = bundle

def fetch(ticker, rng="2y", itv="1d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?range={rng}&interval={itv}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    res = d["chart"]["result"][0]
    ts = res["timestamp"]; q = res["indicators"]["quote"][0]
    return res, ts, q

def tickers():
    html = open(INDEX, encoding="utf-8").read()
    seen = []
    for t in re.findall(r'ticker:"([A-Z.]{1,6})"', html):
        if t not in seen:
            seen.append(t)
    return seen[:14]

def inject(a, b, payload):
    html = open(INDEX, encoding="utf-8").read()
    pat = re.compile(re.escape(a) + r".*?" + re.escape(b), re.S)
    if pat.search(html):
        open(INDEX, "w", encoding="utf-8").write(pat.sub(a + payload + b, html))
        print("injected", a)
    else:
        print("marker not found", a)

def do_history():
    names = {}
    html = open(INDEX, encoding="utf-8").read()
    for nm, tk in re.findall(r'name:"([^"]+)",ticker:"([A-Z.]{1,6})"', html):
        names.setdefault(tk, nm)
    series = {}
    for tk, nm in list(names.items())[:14] + list(BENCH.items()):
        try:
            res, ts, q = fetch(tk, "2y", "1wk")
            data = [[datetime.date.fromtimestamp(t).isoformat(), round(float(c), 2)]
                    for t, c in zip(ts, q["close"]) if c is not None]
            if len(data) > 20:
                series[tk] = {"name": nm, "data": data}
        except Exception as e:
            print(tk, "hist err", str(e)[:60])
    inject("/*HISTORY_START*/", "/*HISTORY_END*/",
           json.dumps({"generated": datetime.date.today().isoformat(), "series": series}, separators=(",", ":")))

def do_forecasts():
    from model import Kronos, KronosTokenizer, KronosPredictor
    tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    mdl = Kronos.from_pretrained("NeoQuasar/Kronos-small")
    pred = KronosPredictor(mdl, tok, max_context=512)
    out = {}
    for t in tickers():
        try:
            res, ts, q = fetch(t, "2y", "1d")
            df = pd.DataFrame({"timestamps": pd.to_datetime(ts, unit="s"), "open": q["open"], "high": q["high"],
                               "low": q["low"], "close": q["close"], "volume": q["volume"]}).dropna().reset_index(drop=True)
            df["amount"] = df["close"] * df["volume"]
            if len(df) < 120:
                continue
            lb = min(LOOKBACK, len(df))
            x = df.iloc[-lb:][["open", "high", "low", "close", "volume", "amount"]].reset_index(drop=True)
            xts = df.iloc[-lb:]["timestamps"].reset_index(drop=True)
            yts = pd.Series(pd.bdate_range(df["timestamps"].iloc[-1] + pd.Timedelta(days=1), periods=PRED_LEN))
            p = pred.predict(df=x, x_timestamp=xts, y_timestamp=yts, pred_len=PRED_LEN, T=1.0, top_p=0.9, sample_count=SAMPLE_COUNT, verbose=False)
            last = float(df["close"].iloc[-1]); pc = float(p["close"].iloc[-1]); pct = (pc/last-1)*100
            out[t] = {"last_close": round(last, 2), "pred_close": round(pc, 2), "pct_change": round(pct, 1),
                      "direction": "up" if pct > 1 else "down" if pct < -1 else "flat",
                      "band_low": round((float(p["low"].min())/last-1)*100, 1),
                      "band_high": round((float(p["high"].max())/last-1)*100, 1),
                      "as_of": df["timestamps"].iloc[-1].strftime("%Y-%m-%d")}
            print(t, out[t]["pct_change"], out[t]["direction"])
        except Exception as e:
            print(t, "fc err", str(e)[:80])
    inject("/*KRONOS_START*/", "/*KRONOS_END*/",
           json.dumps({"generated": datetime.date.today().isoformat(), "model": "Kronos-small",
                       "horizon_days": PRED_LEN, "sample_count": SAMPLE_COUNT, "forecasts": out}, separators=(",", ":")))

if __name__ == "__main__":
    maybe_ca()
    do_history()
    do_forecasts()
    print("cloud_data done")
