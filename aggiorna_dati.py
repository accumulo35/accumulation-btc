# -*- coding: utf-8 -*-
"""
Aggiorna data.json per la Console di Accumulazione BTC.
Fonti: CoinGecko (prezzo), bitcoin-data.com/BGeometrics (metriche on-chain),
Blockchain.com (hash rate per le hash ribbons).
Eseguito 3 volte al giorno da GitHub Actions.
"""
import urllib.request, json, sys
from datetime import datetime, timezone

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (console-accumulo)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

dati = {"aggiornato": datetime.now(timezone.utc).isoformat(timespec="seconds")}
errori = []

# --- prezzo (CoinGecko) ---
try:
    p = get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
    dati["price"] = float(p["bitcoin"]["usd"])
except Exception as e:
    errori.append(f"prezzo: {e}")

# --- metriche on-chain (bitcoin-data.com) ---
mappa = {"mvrvZ": ("mvrv-zscore", "mvrvZscore"),
         "puell": ("puell-multiple", "puellMultiple"),
         "sopr": ("sopr", "sopr"),
         "reserveRisk": ("reserve-risk", "reserveRisk")}
for chiave, (endpoint, campo) in mappa.items():
    try:
        d = get(f"https://bitcoin-data.com/v1/{endpoint}/last")
        dati[chiave] = float(d[campo])
    except Exception as e:
        errori.append(f"{chiave}: {e}")

# --- hash ribbons (Blockchain.com, SMA 30/60 giorni) ---
try:
    d = get("https://api.blockchain.info/charts/hash-rate?timespan=90days&format=json&sampled=false")
    vals = [pt["y"] for pt in d["values"]]
    if len(vals) >= 60:
        sma30 = sum(vals[-30:]) / 30
        sma60 = sum(vals[-60:]) / 60
        dati["hashRibbonCapitulation"] = bool(sma30 < sma60)
        dati["hashRibbonCrossover"] = bool(sma30 > sma60)
    else:
        raise ValueError(f"solo {len(vals)} punti hash rate")
except Exception as e:
    errori.append(f"hashRibbons: {e}")

# --- salvataggio: non sovrascrivere se troppi errori ---
if errori:
    print("AVVISI:", "; ".join(errori))
if len(errori) >= 3:
    print("Troppe fonti in errore: data.json NON aggiornato per non degradare i dati.")
    sys.exit(1)

with open("data.json", "w") as f:
    json.dump(dati, f, indent=2)
print("data.json aggiornato:", json.dumps(dati, indent=2))
