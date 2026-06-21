"""
Aktualizuje cenę docelową i potencjał wzrostu dla spółek z pokryciem analityków na TradingView.
Uruchamiane raz dziennie przez GitHub Actions (.github/workflows/update.yml).

Pobiera ze strony https://pl.tradingview.com/symbols/GPW-<TICKER>/forecast/
wartość "cena docelowa" (consensus target) oraz przelicza potencjał wzrostu
względem aktualnej ceny zapisanej w data.json (price aktualizowane ręcznie / z innego źródła notowań).
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

DATA_PATH = Path(__file__).parent.parent / "data.json"

# Tickery spółek, dla których TradingView ma pokrycie analityków (konsensus cen docelowych).
# Pozostałe spółki w data.json nie mają pokrycia - pole target_source zostaje "brak pokrycia analityków".
COVERED_TICKERS = {
    "LPP": "LPP",
    "Allegro": "ALE",
    "Benefit Systems": "BFT",
    "Inter Cars": "CAR",
    "Kruk": "KRU",
    "Dom Development": "DOM",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

TARGET_RE = re.compile(r"cena docelowa[^0-9]*([\d\s,]+\.?\d*)\s*PLN", re.IGNORECASE)


def fetch_target_price(ticker: str) -> float | None:
    """Pobiera cenę docelową (konsensus analityków) ze strony forecast TradingView."""
    url = f"https://pl.tradingview.com/symbols/GPW-{ticker}/forecast/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[WARN] Nie udało się pobrać {ticker}: {exc}", file=sys.stderr)
        return None

    match = TARGET_RE.search(resp.text)
    if not match:
        print(f"[WARN] Nie znaleziono ceny docelowej dla {ticker} w treści strony.", file=sys.stderr)
        return None

    raw = match.group(1).replace(" ", "").replace("\u00a0", "")
    # Polskie liczby: "25 036,60" -> "25036.60"
    raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    for company in data["companies"]:
        ticker = COVERED_TICKERS.get(company["name"])
        if not ticker:
            continue  # spółka bez pokrycia - nie aktualizujemy

        target = fetch_target_price(ticker)
        time.sleep(2)  # uprzejmość wobec serwera

        if target is None:
            continue

        company["target_price"] = round(target, 2)
        price = company.get("price")
        if price:
            company["potential_pct"] = round((target - price) / price * 100, 2)
        company["target_source"] = "TradingView (konsensus analityków) - aktualizacja automatyczna"

    from datetime import date
    data["last_updated"] = date.today().isoformat()

    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("data.json zaktualizowane.")


if __name__ == "__main__":
    main()
