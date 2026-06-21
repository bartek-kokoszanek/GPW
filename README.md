# Spółki – poprawa wyników 2026

Strona z tabelą spółek GPW wytypowanych w analizie Przemysława Parzyszka
(Analizy Prezesa / PortalAnaliz.pl) jako kandydatów do poprawy wyników w 2026 roku.

## Pliki

- `index.html` – strona (dark mode, Tailwind), wczytuje dane z `data.json`
- `data.json` – dane spółek (ceny, C/Z, zmiana zysku, ocena szans, jakość zarządu)
- `scripts/update_targets.py` – scraper TradingView (cena docelowa / potencjał wzrostu)
- `.github/workflows/update.yml` – automatyczna codzienna aktualizacja `data.json`

## Jak wgrać na GitHub (ręcznie, przez stronę)

1. Wejdź na swoje repozytorium (albo stwórz nowe: **New repository**).
2. **Add file → Upload files** i wgraj WSZYSTKIE pliki z zachowaniem struktury folderów:
   - `index.html`
   - `data.json`
   - `scripts/update_targets.py`
   - `.github/workflows/update.yml`

   ⚠️ GitHub przy przeciąganiu plików przez przeglądarkę zachowuje strukturę folderów,
   jeśli przeciągniesz cały folder `repo` (a nie pojedyncze pliki) – najłatwiej spakować
   folder i wgrać przez `git`, patrz niżej.
3. **Commit changes**.
4. Włącz GitHub Pages: **Settings → Pages → Branch: main → Save**.
   Strona będzie dostępna pod `https://twojnick.github.io/nazwa-repo/`.
5. Włącz uprawnienia do automatycznego commitowania przez Actions:
   **Settings → Actions → General → Workflow permissions → Read and write permissions → Save**
   (bez tego krok "Commit i push zmian" w workflow nie zadziała).

## Jak wgrać przez terminal (Windows, Git)

```bash
git clone https://github.com/TWOJNICK/NAZWA-REPO.git
cd NAZWA-REPO
# skopiuj tu pliki index.html, data.json, scripts/, .github/
git add .
git commit -m "Dodanie tabeli spolek 2026 + automatyczna aktualizacja"
git push
```

## Automatyczna aktualizacja

Workflow `.github/workflows/update.yml` odpala się codziennie o 8:00 (czasu PL)
i raz na żądanie z zakładki **Actions → Aktualizacja cen docelowych → Run workflow**.
Aktualizuje tylko spółki z pokryciem analityków na TradingView (LPP, Allegro,
Benefit Systems, Inter Cars, Kruk, Dom Development) – resztę spółek TradingView
nie pokrywa rekomendacjami, więc te pola pokazują „brak pokrycia”.

## Uwagi co do danych

- **C/S** – nie występuje w źródłowej analizie, brak w `data.json` (`null`).
- **Jakość zarządu** – wzięta z treści PDF analityka; podana tylko tam, gdzie
  analityk się wprost wypowiedział (jedyny taki przypadek: Mex Polska).
- **Ocena szans** – opisowa ocena analityka (nie liczbowe %).
