#!/usr/bin/env python3
"""Aktualizuje liczby na stronie site/media-kit.html danymi z YouTube.

Źródła:
- YouTube Analytics API (OAuth, zakres yt-analytics.readonly): wyświetlenia,
  czas oglądania, subskrybenci, wiek, płeć, kraje, urządzenia.
- YouTube Data API v3 (klucz API): łączne wyświetlenia kanału i filmów.

Zmienne środowiskowe: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, YT_API_KEY.
Do testów: --fixture plik.json zamiast zapytań do API.

Skrypt podmienia wyłącznie fragmenty między znacznikami
<!-- stats:nazwa --> ... <!-- /stats:nazwa -->. Jeśli którekolwiek zapytanie się nie
powiedzie, plik nie jest zmieniany.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request

CHANNEL_ID = 'UCufnvFcp2-PePAYYd6QPjKA'
CHANNEL_START = '2026-08-01'
VIDEOS = ['4hKhfTYWHQ0', 'WBMHq4xDD6U', 'hs5wtevaPq4']
PAGE = os.path.join(os.path.dirname(__file__), '..', 'site', 'media-kit.html')

NBSP = ' '


# ---------- formatowanie po polsku ----------

def fmt_int(n):
    s = f'{int(round(n)):,}'.replace(',', NBSP)
    return s


def fmt_tys(n, decimals=1):
    """243 812 -> '243,8 tys.'; poniżej 10 000 pełna liczba."""
    if n < 10_000:
        return fmt_int(n)
    v = n / 1000
    s = f'{v:.{decimals}f}'.replace('.', ',') if decimals else f'{round(v):d}'
    return f'{s}{NBSP}tys.'


def fmt_pct(x, decimals=1):
    return f'{x:.{decimals}f}'.replace('.', ',') + '%'


def fmt_date(d):
    return d.strftime('%d.%m.%Y')


# ---------- API ----------

def http_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def access_token():
    body = urllib.parse.urlencode({
        'client_id': os.environ['YT_CLIENT_ID'],
        'client_secret': os.environ['YT_CLIENT_SECRET'],
        'refresh_token': os.environ['YT_REFRESH_TOKEN'],
        'grant_type': 'refresh_token',
    }).encode()
    return http_json('https://oauth2.googleapis.com/token', data=body)['access_token']


def analytics(token, start, end, metrics, dimensions=None, sort=None):
    q = {'ids': 'channel==MINE', 'startDate': start, 'endDate': end, 'metrics': metrics}
    if dimensions:
        q['dimensions'] = dimensions
    if sort:
        q['sort'] = sort
    url = 'https://youtubeanalytics.googleapis.com/v2/reports?' + urllib.parse.urlencode(q)
    return http_json(url, headers={'Authorization': f'Bearer {token}'})


def data_api(path, params):
    params = dict(params, key=os.environ['YT_API_KEY'])
    return http_json(f'https://www.googleapis.com/youtube/v3/{path}?' + urllib.parse.urlencode(params))


def fetch(end):
    """Pobiera surowe dane. Zwraca słownik w tym samym kształcie co plik --fixture."""
    start28 = (end - dt.timedelta(days=27)).isoformat()
    e = end.isoformat()
    tok = access_token()
    raw = {
        'end': e,
        'totals28': analytics(tok, start28, e, 'views,estimatedMinutesWatched,subscribersGained,subscribersLost'),
        'subsLifetime': analytics(tok, CHANNEL_START, e, 'subscribersGained,subscribersLost'),
        'age': analytics(tok, start28, e, 'viewerPercentage', 'ageGroup'),
        'gender': analytics(tok, start28, e, 'viewerPercentage', 'gender'),
        'countries': analytics(tok, CHANNEL_START, e, 'views', 'country', '-views'),
        'devices': analytics(tok, start28, e, 'estimatedMinutesWatched', 'deviceType'),
        'channel': data_api('channels', {'part': 'statistics', 'id': CHANNEL_ID}),
        'videos': data_api('videos', {'part': 'statistics', 'id': ','.join(VIDEOS)}),
    }
    return raw


# ---------- przetwarzanie ----------

def rows(report):
    return report.get('rows') or []


def compute(raw):
    end = dt.date.fromisoformat(raw['end'])
    t = rows(raw['totals28'])[0]
    views28, minutes28, gained28, lost28 = t
    sl = rows(raw['subsLifetime'])[0]
    subs_total = sl[0] - sl[1]

    age_map = {'age13-17': '13–17', 'age18-24': '18–24', 'age25-34': '25–34', 'age35-44': '35–44',
               'age45-54': '45–54', 'age55-64': '55–64', 'age65-': '65+'}
    age = {age_map[k]: v for k, v in rows(raw['age']) if k in age_map}
    gender = {k: v for k, v in rows(raw['gender'])}

    ctry = rows(raw['countries'])
    total_ctry = sum(v for _, v in ctry) or 1
    pl_share = 100 * sum(v for k, v in ctry if k == 'PL') / total_ctry

    dev_names = {'TV': 'Telewizory', 'MOBILE': 'Telefony', 'DESKTOP': 'Komputery', 'TABLET': 'Tablety'}
    dev = {dev_names[k]: v for k, v in rows(raw['devices']) if k in dev_names}
    dev_total = sum(v for _, v in rows(raw['devices'])) or 1
    devices = sorted(((k, 100 * v / dev_total) for k, v in dev.items()), key=lambda x: -x[1])

    channel_views = int(raw['channel']['items'][0]['statistics']['viewCount'])
    video_views = {it['id']: int(it['statistics']['viewCount']) for it in raw['videos']['items']}

    return {
        'end': end, 'views28': views28, 'hours28': minutes28 / 60, 'subs_total': subs_total,
        'subs28': gained28 - lost28, 'age': age, 'female': gender.get('female', 0.0),
        'male': gender.get('male', 0.0), 'pl_share': pl_share, 'devices': devices,
        'channel_views': channel_views, 'video_views': video_views,
    }


# ---------- generowanie fragmentów HTML ----------

def render(s, today):
    b = {}
    b['meta'] = (f'<p class="mk-meta">Dane z YouTube Analytics · ostatnie 28 dni do {fmt_date(s["end"])}, '
                 f'o ile nie zaznaczono inaczej</p>')
    floor10k = (s['channel_views'] // 10_000) * 10
    b['intro'] = (f'<p class="mk-sub">Kanał istnieje od sierpnia 2026. Filmy i Shorty zebrały dotąd ponad '
                  f'{floor10k}{NBSP}tys. wyświetleń.</p>')
    b['reach'] = (
        '<div class="mk-stats">\n'
        f'          <div class="mk-stat"><b>{fmt_tys(s["views28"])}</b><span>wyświetleń w 28 dni</span></div>\n'
        f'          <div class="mk-stat"><b>{fmt_tys(s["channel_views"])}</b><span>wyświetleń od początku kanału</span></div>\n'
        f'          <div class="mk-stat"><b>{fmt_int(s["subs_total"])}</b><span>subskrybentów · '
        f'<em>{"+" if s["subs28"] >= 0 else "−"}{fmt_int(abs(s["subs28"]))}</em> w 28 dni</span></div>\n'
        f'          <div class="mk-stat"><b>{fmt_tys(s["hours28"])} h</b><span>czasu oglądania w 28 dni</span></div>\n'
        '        </div>')
    for vid in VIDEOS:
        b[f'video-{vid}'] = f'<b>{fmt_tys(s["video_views"].get(vid, 0), 0)}</b> wyświetleń'

    order = ['18–24', '25–34', '35–44', '45–54', '55–64', '65+']
    mx = max([s['age'].get(k, 0) for k in order] + [0.0001])
    lis = []
    for k in order:
        v = s['age'].get(k, 0.0)
        dim = ' dim' if v < mx * 0.3 else ''
        lis.append(f'              <li><span class="lbl">{k}</span><span class="track"><span class="fill{dim}" '
                   f'style="width:{round(100 * v / mx)}%"></span></span><span class="val">{fmt_pct(v)}</span></li>')
    b['age'] = '<ul class="mk-bars">\n' + '\n'.join(lis) + '\n            </ul>'

    b['gender-country'] = (
        f'<div class="mk-big"><b>{round(s["male"])}%</b><span>mężczyźni · {round(s["female"])}% kobiety</span></div>\n'
        f'            <div class="mk-big"><b>{round(s["pl_share"])}%</b><span>wyświetleń z Polski (od początku kanału)</span></div>')

    colors = ['var(--accent)', 'rgba(var(--accent-rgb),.6)', 'rgba(var(--accent-rgb),.32)', '#5d6668']
    devs = s['devices'][:4]
    label = ', '.join(f'{k.lower() if i else k} {fmt_pct(v)}' for i, (k, v) in enumerate(devs))
    bars = ''.join(f'<i style="width:{v:.1f}%;background:{colors[i]}"></i>' for i, (k, v) in enumerate(devs))
    legend = '\n'.join(f'              <li style="--c:{colors[i]}">{k} {fmt_pct(v)}</li>' for i, (k, v) in enumerate(devs))
    b['devices'] = (f'<div class="mk-split" role="img" aria-label="{label}">\n              {bars}\n            </div>\n'
                    f'            <ul class="mk-legend">\n{legend}\n            </ul>')

    b['source'] = (f'<p class="mk-src">Źródło danych: YouTube Analytics API i YouTube Data API, kanał W Dobrym '
                   f'Kierunku. Aktualizacja automatyczna: {fmt_date(today)}.</p>')
    return b


def apply(html, blocks, today):
    for name, content in blocks.items():
        pat = re.compile(r'(<!-- stats:' + re.escape(name) + r' -->).*?(<!-- /stats:' + re.escape(name) + r' -->)', re.S)
        if len(pat.findall(html)) != 1:
            raise SystemExit(f'Brak lub zdublowany znacznik stats:{name} w media-kit.html')
        html = pat.sub(lambda m: m.group(1) + content + m.group(2), html)
    html = re.sub(r'("dateModified":")\d{4}-\d{2}-\d{2}(")', r'\g<1>' + today.isoformat() + r'\g<2>', html, count=1)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fixture', help='plik JSON z surowymi danymi zamiast zapytań do API')
    ap.add_argument('--dry-run', action='store_true', help='nie zapisuj pliku, wypisz tylko podsumowanie')
    a = ap.parse_args()

    today = dt.date.today()
    end = today - dt.timedelta(days=2)  # dane Analytics są kompletne z ok. 2-dniowym opóźnieniem
    raw = json.load(open(a.fixture, encoding='utf-8')) if a.fixture else fetch(end)
    s = compute(raw)
    html = open(PAGE, encoding='utf-8').read()
    new = apply(html, render(s, today), today)

    print(f'Wyświetlenia 28 dni: {s["views28"]}, subskrybenci: {s["subs_total"]} ({s["subs28"]:+d} w 28 dni), '
          f'kanał łącznie: {s["channel_views"]}, filmy: {s["video_views"]}')
    if a.dry_run:
        return
    if new != html:
        open(PAGE, 'w', encoding='utf-8').write(new)
        print('media-kit.html zaktualizowany')
    else:
        print('Bez zmian')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f'Błąd API {e.code}: {e.read().decode()[:500]}', file=sys.stderr)
        sys.exit(1)
