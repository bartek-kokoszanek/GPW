"""
Pobiera świeże dane finansowe dla spółek z data.json:
- aktualna cena (stooq.com - CSV)
- P/S (biznesradar.pl - "Cena / Przychody ze sprzedaży")
- zmiana zysku netto r/r za ostatni kwartał (biznesradar.pl - rachunek zysków i strat kwartalnie)

Uruchamiane co 15 minut przez GitHub Actions (.github/workflows/update.yml).
Skrypt jest defensywny: jeśli źródło nie odpowiada lub format się zmienił, dla danej spółki
zostawia poprzednią wartość i nie wywala całego procesu.
"""
import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA_PATH = Path(__file__).parent.parent / "data.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}

def jitter_sleep(base):
    """Losowy odstęp wokół `base` sekund, żeby ruch mniej przypominał bota."""
    time.sleep(base + random.uniform(0, base * 0.6))

# Mapowanie nazwa spółki -> ticker na biznesradar i stooq
# (czasami się różnią; sprawdzam ręcznie najpopularniejsze).
TICKERS = {
    "LPP": {"br": "LPP", "stooq": "lpp"},
    "Allegro": {"br": "ALE", "stooq": "ale"},
    "Benefit Systems": {"br": "BFT", "stooq": "bft"},
    "Kogeneracja": {"br": "KGN", "stooq": "kgn"},
    "Archicom": {"br": "ARH", "stooq": "arh"},
    "Asbis": {"br": "ASB", "stooq": "asb"},
    "Inter Cars": {"br": "CAR", "stooq": "car"},
    "Kruk": {"br": "KRU", "stooq": "kru"},
    "Digital Network": {"br": "DIG", "stooq": "dig"},
    "Dom Development": {"br": "DOM", "stooq": "dom"},
    "AB": {"br": "ABE", "stooq": "abe"},
    "NTT System": {"br": "NTT", "stooq": "ntt"},
    "Mo-Bruk": {"br": "MBR", "stooq": "mbr"},
    "Murapol": {"br": "MUR", "stooq": "mur"},
    "Kino Polska": {"br": "KPL", "stooq": "kpl"},
    "Atal": {"br": "1AT", "stooq": "1at"},
    "Toya": {"br": "TOA", "stooq": "toa"},
    "VRG": {"br": "VRG", "stooq": "vrg"},
    "Selena FM": {"br": "SEL", "stooq": "sel"},
    "Odlewnie Polskie": {"br": "ODL", "stooq": "odl"},
    "Agora": {"br": "AGO", "stooq": "ago"},
    "Mex Polska": {"br": "MEX", "stooq": "mex"},
    "Wirtualna Polska": {"br": "WPL", "stooq": "wpl"},
    "Cyfrowy Polsat": {"br": "CPS", "stooq": "cps"},
    "Elektrotim": {"br": "ELT", "stooq": "elt"},
    "Eurotel": {"br": "ETL", "stooq": "etl"},
    "MFO": {"br": "MFO", "stooq": "mfo"},
}


def fetch_price_stooq(ticker_stooq):
    """Pobiera aktualną cenę zamknięcia z stooq przez darmowy endpoint CSV.
    Adres: https://stooq.com/q/l/?s=<ticker>.pl&f=sd2t2ohlcv&h&e=csv
    WAŻNE: spółki GPW na stooq wymagają sufiksu „.pl" (np. „lpp.pl"), inaczej
    endpoint zwraca błąd/puste dane. Zwraca cenę jako float lub None."""
    url = f"https://stooq.com/q/l/?s={ticker_stooq}.pl&f=sd2t2ohlcv&h&e=csv"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        # Format: Symbol,Date,Time,Open,High,Low,Close,Volume\nLPP,...,20600.00,...
        lines = r.text.strip().split("\n")
        if len(lines) < 2:
            return None
        row = lines[1].split(",")
        if len(row) < 7:
            return None
        close = row[6]
        if close in ("N/D", "-"):
            return None
        return float(close)
    except (requests.RequestException, ValueError, IndexError) as exc:
        print(f"[stooq] {ticker_stooq}: {exc}", file=sys.stderr)
        return None


def fetch_ps_biznesradar(ticker_br):
    """Pobiera aktualne P/S (Cena/Przychody ze sprzedaży) z biznesradar.
    Wskaźnik znajduje się na stronie /wskazniki-wartosci-rynkowej/<TICKER>
    w wierszu 'Cena / Przychody ze sprzedaży' w ostatniej kolumnie."""
    url = f"https://www.biznesradar.pl/wskazniki-wartosci-rynkowej/{ticker_br},0"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        html = r.text
    except requests.RequestException as exc:
        print(f"[br P/S] {ticker_br}: {exc}", file=sys.stderr)
        return None

    # Szukam wiersza tabeli z linkiem CPCurrent (Cena/Przychody ze sprzedaży aktualne)
    # i wyciągam wartości liczbowe z komórek tego wiersza, biorąc ostatnią.
    match = re.search(
        r'Cena / Przychody ze sprzedaży.*?</tr>',
        html,
        re.DOTALL,
    )
    if not match:
        return None
    row_html = match.group(0)
    # Wyciągnij wszystkie liczby (np. "1,72", "2,30") z komórek wiersza
    nums = re.findall(r'>(\d+[.,]\d+)~branża', row_html)
    if not nums:
        # alternatywna struktura - bez tildy
        nums = re.findall(r'>(\d+[.,]\d+)<', row_html)
    if not nums:
        return None
    try:
        return float(nums[-1].replace(",", "."))
    except ValueError:
        return None


def fetch_profit_yoy_biznesradar(ticker_br):
    """Pobiera dynamikę r/r zysku netto za ostatni kwartał z biznesradar.
    Adres: /raporty-finansowe-rachunek-zyskow-i-strat/<TICKER>,Q,1
    Szuka wiersza 'Zysk netto' i wartości r/r z ostatniej kolumny."""
    url = f"https://www.biznesradar.pl/raporty-finansowe-rachunek-zyskow-i-strat/{ticker_br},Q,1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        html = r.text
    except requests.RequestException as exc:
        print(f"[br r/r] {ticker_br}: {exc}", file=sys.stderr)
        return None

    # Szukam wiersza "Zysk netto" (bez słów "akcjonariuszy", "udziałowców") z dynamiką r/r
    # biznesradar pokazuje wartości jak np. ">475 000<" oraz "r/r +42.22%"
    # Wybieram pierwsze trafienie i ostatnią wartość r/r (najświeższy kwartał).
    matches = re.finditer(
        r'<tr[^>]*>\s*<td[^>]*>\s*<a[^>]*>Zysk netto</a>.*?</tr>',
        html,
        re.DOTALL,
    )
    for m in matches:
        row = m.group(0)
        rr = re.findall(r'r/r\s+([+-]?\d+[.,]\d+)%', row)
        if rr:
            try:
                return float(rr[-1].replace(",", "."))
            except ValueError:
                continue
    return None


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    updated = 0
    failed = 0

    for company in data["companies"]:
        tickers = TICKERS.get(company["name"])
        if not tickers:
            continue

        # 1. Cena ze stooq
        price = fetch_price_stooq(tickers["stooq"])
        if price is not None:
            company["price"] = price
            # Jeśli mamy też cenę docelową, przelicz potencjał
            if company.get("target_price"):
                company["potential_pct"] = round(
                    (company["target_price"] - price) / price * 100, 2
                )

        time.sleep(0.5)  # uprzejmość wobec stooq

        # 2. P/S z biznesradar
        ps = fetch_ps_biznesradar(tickers["br"])
        if ps is not None:
            company["ps"] = ps
            company["ps_source"] = "biznesradar.pl (auto)"
            updated += 1
        else:
            failed += 1

        jitter_sleep(1.2)  # uprzejmość wobec biznesradar + utrudnia wykrycie jako bot

        # 3. Zmiana zysku netto r/r z biznesradar
        yoy = fetch_profit_yoy_biznesradar(tickers["br"])
        if yoy is not None:
            company["profit_yoy_pct"] = yoy
            company["profit_yoy_source"] = "biznesradar.pl - ostatni kwartał r/r (auto)"

        jitter_sleep(1.2)

    data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Zaktualizowano P/S dla {updated} spółek, {failed} nieudanych.")


if __name__ == "__main__":
    main()
