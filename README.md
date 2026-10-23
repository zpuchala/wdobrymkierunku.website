# W Dobrym Kierunku — strona kanału

Statyczna strona kanału YouTube „W Dobrym Kierunku”. Pliki publikowane przez GitHub Pages znajdują się w `site/`; nie ma procesu kompilacji.

## Włączenie GitHub Pages

1. Otwórz repozytorium `zpuchala/wdobrymkierunku.website` na GitHubie.
2. Wejdź w **Settings → Pages**.
3. W sekcji **Build and deployment** ustaw **Source** na **GitHub Actions** i zapisz.
4. Wejdź w **Actions**, otwórz workflow **Deploy GitHub Pages** i uruchom ponownie nieudany przebieg albo użyj **Run workflow**.
5. Po udanym wdrożeniu strona będzie dostępna pod adresem `https://zpuchala.github.io/wdobrymkierunku.website/`.

Workflow publikuje katalog `site/`. Nie wymaga sekretów ani dodatkowych zależności. Jeśli konfiguracja Pages nie została jeszcze włączona w ustawieniach repozytorium, krok `configure-pages` zwróci `Get Pages site failed / Not Found`.

## Podłączenie własnej domeny w OVH

Najpierw dodaj domenę w **Settings → Pages → Custom domain** repozytorium i kliknij **Save**. Następnie w Panelu OVHcloud otwórz **Web Cloud → Domain names → [domena] → DNS zone**. Dodaj lub edytuj poniższe rekordy:

| Typ | Subdomena | Wartość |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `zpuchala.github.io.` |

Jeśli OVH dopisuje nazwę domeny do celu CNAME, końcowa kropka w `zpuchala.github.io.` temu zapobiega. Nie zmieniaj serwerów nazw i nie usuwaj rekordów MX ani TXT poczty. Usuń lub edytuj tylko istniejące rekordy `@`/`www`, które kolidują z powyższymi. Po propagacji DNS wróć do **Settings → Pages** i włącz **Enforce HTTPS**, gdy GitHub udostępni tę opcję.

## Podgląd lokalny

W katalogu repozytorium uruchom:

```sh
python3 -m http.server 8000 --directory site
```

Następnie otwórz `http://localhost:8000`.

## Aktualizacja treści

- Tekst, odcinki i metadane: `site/index.html`
- Wygląd i wersja mobilna: `site/styles.css`
- Ikona kanału i ilustracja mapy: `site/assets/`
- Grafika podglądu Orlej Perci: `site/assets/images/orla-perc-social.svg` (źródło) i `orla-perc-social.png` (1200 × 630 px, do udostępniania).

Publiczny GPX Orlej Perci jest kopią bez pomiarów tętna i kadencji; współrzędne, wysokości i znaczniki czasu są zachowane. Oryginał pozostaje lokalnie w `.local-backups/gpx/`, poza publikowanym katalogiem `site/`. Katalog kopii jest ignorowany przez Git.

Każdy push do `main` zawierający zmiany w `site/` uruchamia publikację.

## Automatyczne statystyki w media kicie

Workflow **Update channel stats** (`.github/workflows/update-stats.yml`) w każdy poniedziałek uruchamia `scripts/update_stats.py`, który pobiera dane z YouTube Analytics API i YouTube Data API i podmienia liczby w `site/media-kit.html` między znacznikami `<!-- stats:… -->`. Jeśli liczby się zmieniły, robi commit i uruchamia publikację strony. Można go też uruchomić ręcznie: **Actions → Update channel stats → Run workflow**.

Wymagane sekrety (Settings → Secrets and variables → Actions): `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` (z jednorazowego `python3 scripts/authorize.py`) oraz `YT_API_KEY` (klucz API ograniczony do YouTube Data API v3). Projekt Google Cloud: `wdk-youtube-analytics`.

Test bez dostępu do API: `python3 scripts/update_stats.py --fixture plik.json --dry-run`.
