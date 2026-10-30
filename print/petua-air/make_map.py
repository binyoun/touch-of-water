"""Two print-ready A1 sheets of the MMU 2026 edition for Petua Air, hung side by side.

Left sheet: the campus map from OpenStreetMap data (osm-mmu.json) with the five
team sites from editions/mmu-2026/teams.json, and what happened on 24 June.
Right sheet: one QR code per team's AR page and one for the Water Atlas, kept in
the lower part of the sheet so they sit at hand height.

Writes left.html and right.html, then Chrome prints each to PDF.

    python3 print/petua-air/make_map.py
"""
import html
import json
import math
import subprocess
from pathlib import Path

import qrcode

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SITE = 'https://binyoun.github.io/touch-of-water'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# Same colours as map.html
TEAM_COLORS = {1: '#ff6b6b', 2: '#69db7c', 3: '#ffd43b', 4: '#cc5de8', 5: '#74c0fc'}

# Map window (degrees), centred on the five sites, and its size on the sheet (mm)
LAT_MIN, LAT_MAX = 2.9238, 2.92898
LNG_MIN, LNG_MAX = 101.6404, 101.6450
MAP_W = 534
M_PER_DEG_LNG = 111320 * math.cos(math.radians(2.926))
MAP_H = MAP_W * ((LAT_MAX - LAT_MIN) * 110570) / ((LNG_MAX - LNG_MIN) * M_PER_DEG_LNG)

# Label placement around each dot (dx, dy in mm, text-anchor), set by hand so
# the close sites (1, 3, 5) don't collide
LABELS = {1: (11, -7, 'start'), 2: (-11, -7, 'end'), 3: (11, -4, 'start'),
          4: (11, 13, 'start'), 5: (-11, 15, 'end')}

BASE_CSS = '''
  @page { size: 594mm 841mm; margin: 0; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 594mm; height: 841mm; background: #05080c; color: #e8eef5;
    font-family: 'Courier New', Courier, monospace; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .page { width: 594mm; height: 841mm; padding: 26mm 30mm 20mm; display: flex; flex-direction: column; }
  footer { margin-top: auto; font-size: 3.8mm; line-height: 1.6; color: #5d7084; }
'''


def xy(lat, lng):
    return ((lng - LNG_MIN) / (LNG_MAX - LNG_MIN) * MAP_W,
            (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * MAP_H)


def path_d(geom, close=False):
    pts = [xy(p['lat'], p['lon']) for p in geom]
    d = 'M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in pts)
    return d + (' Z' if close else '')


def campus_svg(osm):
    roads = {'primary': 3.2, 'primary_link': 2.2, 'secondary': 2.6, 'secondary_link': 1.8,
             'tertiary': 2.0, 'tertiary_link': 1.4, 'residential': 1.3, 'unclassified': 1.3,
             'service': 0.8}
    layers = {'green': [], 'water': [], 'drain': [], 'building': [], 'road': [], 'foot': []}
    for e in osm['elements']:
        t = e.get('tags', {})
        if e['type'] == 'relation':
            geoms = [m['geometry'] for m in e.get('members', []) if m.get('role') == 'outer' and 'geometry' in m]
        else:
            geoms = [e['geometry']] if 'geometry' in e else []
        for g in geoms:
            if t.get('natural') == 'water':
                layers['water'].append(f'<path d="{path_d(g, True)}"/>')
            elif 'waterway' in t:
                layers['drain'].append(f'<path d="{path_d(g)}"/>')
            elif 'leisure' in t:
                layers['green'].append(f'<path d="{path_d(g, True)}"/>')
            elif 'building' in t:
                layers['building'].append(f'<path d="{path_d(g, True)}"/>')
            elif t.get('highway') in roads:
                layers['road'].append(f'<path d="{path_d(g)}" stroke-width="{roads[t["highway"]]}"/>')
            elif t.get('highway') in ('footway', 'path', 'steps', 'pedestrian'):
                layers['foot'].append(f'<path d="{path_d(g)}"/>')
    return f'''
  <g fill="#11231c" stroke="none">{''.join(layers['green'])}</g>
  <g fill="none" stroke="#2a3b4c" stroke-linecap="round" stroke-linejoin="round">{''.join(layers['road'])}</g>
  <g fill="none" stroke="#26384a" stroke-width="0.45" stroke-dasharray="1.2 1.2">{''.join(layers['foot'])}</g>
  <g fill="#17222d" stroke="#35475a" stroke-width="0.35">{''.join(layers['building'])}</g>
  <g fill="none" stroke="#2f7fb8" stroke-width="0.9" stroke-linecap="round">{''.join(layers['drain'])}</g>
  <g fill="#123b5c" stroke="#4aa3e0" stroke-width="0.8">{''.join(layers['water'])}</g>'''


def qr_svg(url, size_mm):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=4)
    q.add_data(url)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    cells = ''.join(f'M{x},{y}h1v1h-1z' for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return (f'<svg class="qr" viewBox="0 0 {n} {n}" width="{size_mm}mm" height="{size_mm}mm" '
            f'shape-rendering="crispEdges"><rect width="{n}" height="{n}" fill="#fff"/>'
            f'<path d="{cells}" fill="#000"/></svg>')


def map_svg(teams, osm):
    pts = {t['id']: xy(t['lat'], t['lng']) for t in teams}
    walk = ' L'.join(f'{x:.2f},{y:.2f}' for x, y in pts.values())
    dots = []
    for t in teams:
        x, y = pts[t['id']]
        c = TEAM_COLORS[t['id']]
        dx, dy, anchor = LABELS[t['id']]
        dots.append(f'''
  <circle cx="{x:.2f}" cy="{y:.2f}" r="11" fill="{c}" opacity="0.18"/>
  <circle cx="{x:.2f}" cy="{y:.2f}" r="6" fill="#05080c" stroke="{c}" stroke-width="1.3"/>
  <text x="{x:.2f}" y="{y + 2.6:.2f}" class="num" fill="{c}">{t['id']}</text>
  <text x="{x + dx:.2f}" y="{y + dy:.2f}" class="lbl" text-anchor="{anchor}" fill="{c}">{html.escape(t['name'])}</text>''')
    scale_len = 100 / ((LNG_MAX - LNG_MIN) * M_PER_DEG_LNG) * MAP_W
    return f'''<svg class="map" viewBox="0 0 {MAP_W} {MAP_H:.2f}" width="{MAP_W}mm" height="{MAP_H:.2f}mm">
  <rect width="{MAP_W}" height="{MAP_H:.2f}" fill="#070b10"/>
  {campus_svg(osm)}
  <path d="M{walk}" fill="none" stroke="#ffffff" stroke-opacity="0.55" stroke-width="0.8" stroke-dasharray="2.4 4.5"/>
  {''.join(dots)}
  <g class="north" transform="translate({MAP_W - 20},22)">
    <path d="M0,-10 L4.5,6 L0,2.5 L-4.5,6 Z" fill="#cfd8e3"/><text y="16" text-anchor="middle">N</text>
  </g>
  <g class="scale" transform="translate(18,{MAP_H - 16:.2f})">
    <path d="M0,0 h{scale_len:.2f}" stroke="#cfd8e3" stroke-width="0.9"/>
    <text y="-3.5">100 m</text>
  </g>
</svg>'''


def left_sheet(teams, edition, osm):
    credits = '<br>'.join(html.escape(c) for c in edition['credits'])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Touch of Water · Petua Air · left (map)</title>
<style>{BASE_CSS}
  header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 11mm; }}
  h1 {{ font-size: 36mm; font-weight: 400; letter-spacing: -0.5mm; line-height: 0.9; }}
  .sub {{ font-size: 7mm; color: #9fb3c8; margin-top: 5mm; }}
  .where {{ text-align: right; font-size: 6mm; line-height: 1.45; color: #9fb3c8; }}
  .where b {{ color: #e8eef5; font-weight: 400; }}
  .map {{ display: block; border: 0.4mm solid #26323e; }}
  .map .num {{ font: 700 7.4px 'Courier New', monospace; text-anchor: middle; }}
  .map .lbl {{ font: 400 8px 'Courier New', monospace; }}
  .map .north text, .map .scale text {{ font: 5.5px 'Courier New', monospace; fill: #cfd8e3; }}
  .intro {{ margin-top: 10mm; font-size: 6mm; line-height: 1.5; columns: 2; column-gap: 14mm; }}
  .intro p + p {{ margin-top: 3mm; }}
  footer {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 10mm; }}
  .arrow {{ color: #9fb3c8; font-size: 5mm; white-space: nowrap; }}
</style></head>
<body><div class="page">
  <header>
    <div>
      <h1>Touch of Water</h1>
      <p class="sub">Memory-Mapping with AR and Sound Journal</p>
    </div>
    <div class="where"><b>{html.escape(edition['venue'])}</b><br>{html.escape(edition['city'])} · {html.escape(edition['date'])}<br>Petua Air · 2026</div>
  </header>

  {map_svg(teams, osm)}

  <section class="intro">
    <p>On 24 June 2026, five teams walked this campus looking for water they remembered: rain that made them stop, the hiss of a coffee machine, mud after a storm. Each team chose a site, recorded its sound, and turned an object from it into a 3D model.</p>
    <p>The dotted line is the path between them: the memory map of one afternoon. The sites are a few minutes' walk from here. Scan a team's code to see and hear what they found.</p>
  </section>

  <footer>
    <span>{credits}<br>Map data © OpenStreetMap contributors</span>
    <span class="arrow">Scan the codes →</span>
  </footer>
</div></body></html>'''


PHOTOS = ['mmu-11.jpg', 'mmu-12.jpg', 'mmu-14.jpg']


def right_sheet(teams):
    photos = ''.join(f'<img src="{(ROOT / "editions/mmu-2026/images/workshop" / f).as_uri()}" alt="">' for f in PHOTOS)
    cells = []
    for t in teams:
        url = f"{SITE}/ar.html?edition=mmu-2026&team={t['id'] - 1}"
        native = (f'<p class="native">{html.escape(t["textNative"])}'
                  f'<span class="lang"> · {html.escape(t["lang"])}</span></p>') if t.get('textNative') else ''
        cells.append(f'''
    <article class="card" style="--c:{TEAM_COLORS[t['id']]}">
      <div class="card-head"><span class="badge">{t['id']}</span><h3>{html.escape(t['name'])}</h3></div>
      {qr_svg(url, 90)}
      <p class="members">{html.escape(t['members'])}</p>
      <p class="en">{html.escape(t['textEn'])}</p>
      {native}
    </article>''')
    cells.append(f'''
    <article class="card atlas" style="--c:#74c0fc">
      <div class="card-head"><h3>Add your water</h3></div>
      {qr_svg(f'{SITE}/atlas.html?src=petua-air', 90)}
      <p class="en">Which water do you remember? A river, a tap, a monsoon, a bowl at home. Send a photo of it, the place it comes from, and one sentence in English and your own language.</p>
      <p class="native">It becomes a dot on the Water Atlas, shared across Jakarta, Kuala Lumpur and Ho Chi Minh City.</p>
    </article>''')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Touch of Water · Petua Air · right (codes)</title>
<style>{BASE_CSS}
  .page {{ justify-content: space-between; }}
  h2 {{ font-size: 22mm; font-weight: 400; line-height: 1; letter-spacing: -0.3mm; }}
  .lead {{ font-size: 7mm; color: #9fb3c8; margin: 5mm 0 10mm; }}
  .how {{ font-size: 6.8mm; line-height: 1.5; color: #9fb3c8; padding-left: 8mm; }}
  .how li + li {{ margin-top: 2mm; }}
  .how strong {{ color: #e8eef5; font-weight: 400; }}
  .photos {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6mm; }}
  .photos img {{ width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block; }}
  .caption {{ font-size: 4.2mm; color: #5d7084; margin-top: 3mm; }}
  .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); column-gap: 12mm; row-gap: 12mm; }}
  .card {{ border-top: 1.4mm solid var(--c); padding-top: 5mm; font-size: 4.3mm; line-height: 1.45; }}
  .card-head {{ display: flex; align-items: center; gap: 3.5mm; margin-bottom: 5mm; }}
  .badge {{ width: 11mm; height: 11mm; border-radius: 50%; border: 0.6mm solid var(--c); color: var(--c);
    display: inline-flex; align-items: center; justify-content: center; font-size: 6mm; font-weight: 700; flex: none; }}
  .card h3 {{ font-size: 7.5mm; font-weight: 400; color: var(--c); line-height: 1.1; }}
  .qr {{ display: block; margin-bottom: 5mm; }}
  .members {{ color: #7d90a4; margin-bottom: 3mm; }}
  .native {{ color: #9fb3c8; font-style: italic; margin-top: 2.5mm; }}
  .lang {{ font-style: normal; color: #5d7084; }}
  .atlas {{ background: #0a1520; outline: 0.5mm solid #4aa3e0; outline-offset: 0; padding: 5mm 6mm 6mm; }}
  .atlas .native {{ font-style: normal; }}
  footer {{ margin-top: 0; }}
</style></head>
<body><div class="page">
  <div>
  <h2>Scan to enter</h2>
  <p class="lead">Each code opens one team's water, here or at its site.</p>
  <ol class="how">
    <li><strong>Scan a code</strong> with your phone camera.</li>
    <li><strong>Allow the camera.</strong> The world turns blue, as if seen through water.</li>
    <li><strong>Tap to place</strong> the object. Drag to turn it.</li>
    <li><strong>Pinch to resize.</strong> Its size is the volume of the sound. Headphones help.</li>
  </ol>
  </div>

  <figure>
    <div class="photos">{photos}</div>
    <figcaption class="caption">The workshop, MMU, 24 June 2026: walking the campus in the rain, recording, and building the AR.</figcaption>
  </figure>

  <section class="cards">{''.join(cells)}
  </section>

  <footer>binyoun.github.io/touch-of-water</footer>
</div></body></html>'''


def print_pdf(page, name):
    src = HERE / f'{name}.html'
    src.write_text(page)
    pdf = HERE / f'touch-of-water-petua-air-A1-{name}.pdf'
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={pdf}', src.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(pdf)


def main():
    teams = [t for t in json.loads((ROOT / 'editions/mmu-2026/teams.json').read_text()) if not t.get('placeholder')]
    edition = next(e for e in json.loads((ROOT / 'editions.json').read_text()) if e['id'] == 'mmu-2026')
    osm = json.loads((HERE / 'osm-mmu.json').read_text())
    print_pdf(left_sheet(teams, edition, osm), 'left')
    print_pdf(right_sheet(teams), 'right')


if __name__ == '__main__':
    main()
