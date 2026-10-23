#!/usr/bin/env python3
"""Jednorazowa autoryzacja: zdobywa refresh token do YouTube Analytics API.

Użycie:
    python3 scripts/authorize.py                      # zapyta o Client ID i Client secret
    python3 scripts/authorize.py client_secret.json   # albo weźmie je z pobranego pliku JSON

Skrypt otworzy przeglądarkę. Zaloguj się na konto kanału i zgódź się na dostęp
(tylko odczyt statystyk). Na końcu skrypt wypisze trzy wartości do wklejenia jako
sekrety w GitHubie: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
Niczego nie zapisuje na dysku i nie wysyła poza serwery Google.
"""
import getpass
import http.server
import json
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

SCOPE = 'https://www.googleapis.com/auth/yt-analytics.readonly'


def main():
    if len(sys.argv) == 2:
        cfg = json.load(open(sys.argv[1], encoding='utf-8'))
        cfg = cfg.get('installed') or cfg.get('web') or cfg
        client_id, client_secret = cfg['client_id'], cfg['client_secret']
    else:
        client_id = input('Client ID (Identyfikator klienta): ').strip()
        client_secret = getpass.getpass('Client secret (Tajny klucz klienta, nie będzie widoczny): ').strip()
    if not client_id.endswith('.apps.googleusercontent.com') or not client_secret:
        sys.exit('Nieprawidłowy Client ID albo pusty Client secret.')

    state = secrets.token_urlsafe(16)
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get('state', [''])[0] != state:
                self.send_response(400); self.end_headers(); return
            result.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write('<h2>Gotowe. Możesz zamknąć tę kartę i wrócić do terminala.</h2>'.encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(('127.0.0.1', 0), Handler)
    redirect = f'http://127.0.0.1:{srv.server_port}/'
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode({
        'client_id': client_id, 'redirect_uri': redirect, 'response_type': 'code', 'scope': SCOPE,
        'access_type': 'offline', 'prompt': 'consent', 'state': state,
    })
    t = threading.Thread(target=srv.handle_request); t.start()
    print('Otwieram przeglądarkę. Jeśli się nie otworzy, wejdź na ten adres:\n' + url + '\n')
    webbrowser.open(url)
    t.join()
    srv.server_close()

    if 'code' not in result:
        sys.exit('Brak zgody: ' + result.get('error', 'nieznany błąd'))
    body = urllib.parse.urlencode({
        'code': result['code'], 'client_id': client_id, 'client_secret': client_secret,
        'redirect_uri': redirect, 'grant_type': 'authorization_code',
    }).encode()
    tok = json.loads(urllib.request.urlopen('https://oauth2.googleapis.com/token', data=body).read())
    if 'refresh_token' not in tok:
        sys.exit('Google nie zwrócił refresh tokena. Cofnij dostęp na myaccount.google.com/permissions i spróbuj ponownie.')

    print('Dodaj w GitHubie (repozytorium → Settings → Secrets and variables → Actions → New repository secret):\n')
    print(f'  YT_CLIENT_ID      = {client_id}')
    print(f'  YT_CLIENT_SECRET  = {client_secret}')
    print(f'  YT_REFRESH_TOKEN  = {tok["refresh_token"]}')
    print('\nNie udostępniaj tych wartości nikomu i nie wklejaj ich do czatu.')


if __name__ == '__main__':
    main()
