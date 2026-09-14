# W Dobrym Kierunku — strona kanału

Statyczna strona kanału YouTube „W Dobrym Kierunku”. Nie wymaga frameworka ani procesu kompilacji; pliki publikowane przez GitHub Pages znajdują się w `site/`.

## Publikacja w GitHub Pages

1. Otwórz repozytorium `zpuchala/wdobrymkierunku.website` na GitHubie.
2. Wejdź w **Settings → Pages**.
3. W sekcji **Build and deployment** ustaw **Source** na **GitHub Actions**.
4. W zakładce **Actions** sprawdź przebieg workflow **Deploy GitHub Pages**. Uruchamia się po zmianach w `main`; można go też uruchomić ręcznie.
5. Po udanym wdrożeniu strona będzie dostępna pod adresem:

   <https://zpuchala.github.io/wdobrymkierunku.website/>

Workflow publikuje zawartość katalogu `site/`. Do uruchomienia go nie są potrzebne sekrety ani dodatkowe zależności.

## Podgląd lokalny

W katalogu repozytorium uruchom:

```sh
python3 -m http.server 8000 --directory site
```

Następnie otwórz <http://localhost:8000>.

## Aktualizacja treści

- Tekst i metadane: `site/index.html`
- Wygląd i wersja mobilna: `site/styles.css`
- Ilustracje wektorowe: `site/assets/`

Każdy push do `main` zawierający zmiany w `site/` uruchomi publikację.
