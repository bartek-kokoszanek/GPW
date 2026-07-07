# Spółki – poprawa wyników 2026

Strona z tabelą spółek GPW wytypowanych w analizie Przemysława Parzyszka
(Analizy Prezesa / PortalAnaliz.pl) jako kandydatów do poprawy wyników w 2026 roku.

## Pliki

- `index.html` – strona (dark mode, Tailwind, sortowanie kolumn, dodawanie spółek lokalnie),
  wczytuje dane z `data.json`.
- `data.json` – dane spółek (ceny, C/Z, P/S, zmiana zysku r/r, ocena szans).
- `scripts/update_data.py` – scraper stooq.com (cena) + biznesradar.pl (P/S, zysk r/r).
- `.github/workflows/update.yml` – automatyczna aktualizacja `data.json` **co 15 minut**.

## Konfiguracja po wgraniu (jednorazowo)

Bez tych kroków automatyczna aktualizacja nie zadziała:

1. **Settings → Actions → General → Workflow permissions → Read and write permissions → Save**
   (pozwala botowi commitować zmiany do `data.json`).
2. **Settings → Pages → Branch: main → Save** (publiczny adres strony).
3. **Actions → I understand my workflows, go ahead and enable them** (jeśli GitHub pokazuje takie pytanie).
4. Pierwsze odpalenie ręcznie: **Actions → Aktualizacja danych GPW → Run workflow**.
   Po minucie zobaczysz commit „Auto-update: dane finansowe..." na liście commitów.

## Źródła danych

- **Aktualna cena**: stooq.com (CSV endpoint `https://stooq.com/q/l/?s=<ticker>&f=sd2t2ohlcv`)
- **P/S (Cena/Przychody ze sprzedaży)**: biznesradar.pl, strona „Wskaźniki wartości rynkowej",
  wiersz „Cena / Przychody ze sprzedaży", ostatnia kolumna.
- **Zmiana zysku netto r/r za ostatni kwartał**: biznesradar.pl, „Rachunek zysków i strat"
  w trybie kwartalnym, wiersz „Zysk netto", dynamika r/r z ostatniego kwartału.
- **Cena docelowa / Potencjał wzrostu**: TradingView (tylko dla spółek z pokryciem analityków;
  ręczna aktualizacja przy zmianie konsensusu).

## Limity i uwagi

- GitHub Actions cron działa „best effort" – przy obciążeniu kolejki opóźnienia 5-15 min są normalne,
  realny interwał to często 20-30 min zamiast obiecanych 15. Tak działa GitHub, nie da się tego obejść.
- Plan Free GitHub Actions: 2000 minut/mc dla repo prywatnego, **nieograniczone dla publicznego**.
  Każde uruchomienie naszego workflow zajmuje ~1-2 min, czyli ~6 min/godz = ~140 min/dzień – bezpiecznie zmieści się tylko jeśli repo jest publiczne lub konto ma plan Pro.
- Biznesradar może rate-limitować przy zbyt częstych zapytaniach – skrypt robi `sleep(1s)` między spółkami.
  Jeśli zacznie zwracać błędy, dla danej spółki zostaje poprzednia wartość w `data.json`.

## Jak wgrać na GitHub (jeśli jeszcze tego nie zrobiłeś)

Przez stronę:
1. Otwórz https://github.com/bartek-kokoszanek/GPW
2. **Add file → Upload files**, przeciągnij wszystkie pliki z tego folderu.
3. **Commit changes**.

Przez terminal:
```
git clone https://github.com/bartek-kokoszanek/GPW.git
cd GPW
# skopiuj zawartość tego folderu
git add .
git commit -m "Auto-aktualizacja co 15 min: stooq + biznesradar"
git push
```
