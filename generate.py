#!/usr/bin/env python3
"""Generates GitSkins-style solar system cards for a GitHub profile README.
Run locally:   python generate.py        (optionally: GITHUB_TOKEN=xxx python generate.py)
It pulls your avatar, repos, languages and contributions from GitHub when it can,
and falls back to the built-in data below when it can't."""
import json, os, base64, random, urllib.request, html
from datetime import date, timedelta

USER = "Mayurv10"
FALLBACK = {
    "name": "Mayur V", "followers": 0, "stars": 0,
    "tagline": "JavaScript developer. Working on FIREVERSE right now.",
    "repos": [
        {"name": "Mayurv10", "desc": "A project in progress.", "lang": None},
        {"name": "FIREVERSE", "desc": "A project in progress.", "lang": "JavaScript"},
        {"name": "Christ-ai-chatbot", "desc": "AI-powered Study Assistant for Moodle LMS with RAG, Milvus vector search, Gemini LLM...", "lang": "Python"},
        {"name": "ai-devsecops-demo", "desc": "ai devsecops", "lang": "Python"},
    ],
    "langs": [("JavaScript", 36), ("Python", 30), ("CSS", 13), ("PHP", 12), ("HTML", 8)],
    "days_in_orbit": 3, "longest": 3, "revolutions": 8,
    "active": [(3, 0), (3, 1), (11, 1), (25, 4), (25, 5)], "today": (25, 6),
}
HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = json.load(open(os.path.join(HERE, "icons.json")))   # {language: {path, hex}}
COL = {k: v["hex"] for k, v in ICONS.items()}
TOKEN = os.environ.get("GITHUB_TOKEN")
os.makedirs("assets", exist_ok=True)
random.seed(11)

def api(url, data=None):
    h = {"User-Agent": "gen", "Accept": "application/vnd.github+json"}
    if TOKEN: h["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=data, headers=h)
    return json.load(urllib.request.urlopen(req, timeout=20))

D = dict(FALLBACK); avatar_b64 = None
_local = os.path.join(HERE, "avatar.png")          # your own picture wins; just replace avatar.png
if os.path.exists(_local): avatar_b64 = base64.b64encode(open(_local, "rb").read()).decode()
try:
    u = api(f"https://api.github.com/users/{USER}")
    D["name"] = u.get("name") or USER; D["followers"] = u.get("followers", 0)
    if not avatar_b64: 
      try:
        req = urllib.request.Request(u["avatar_url"] + "&s=300", headers={"User-Agent": "gen"})
        avatar_b64 = base64.b64encode(urllib.request.urlopen(req, timeout=20).read()).decode()
      except Exception as e: print("avatar failed:", e)
    repos = [r for r in api(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed") if not r["fork"]]
    D["repos"] = [{"name": r["name"], "desc": (r["description"] or "A project in progress."), "lang": r["language"],
                   "stars": r["stargazers_count"], "forks": r["forks_count"]} for r in repos[:4]]
    D["stars"] = sum(r["stargazers_count"] for r in repos)
    tot = {}
    for r in repos:
        for k, v in api(r["languages_url"]).items(): tot[k] = tot.get(k, 0) + v
    s = sum(tot.values())
    if s: D["langs"] = [(k, round(v * 100 / s)) for k, v in sorted(tot.items(), key=lambda x: -x[1]) if k in ICONS][:5]
    D["tagline"] = f"{D['langs'][0][0]} developer. Working on {D['repos'][0]['name']} right now."
    print("live data loaded")
    if TOKEN:   # contribution calendar needs a token (the GitHub Action provides one)
        q = {"query": "query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount weekday date}}}}}}",
             "variables": {"u": USER}}
        cal = api("https://api.github.com/graphql", json.dumps(q).encode())["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        weeks = cal["weeks"][-26:]; act = []; flat = []
        for wi, wk in enumerate(weeks):
            for d in wk["contributionDays"]:
                flat.append(d["contributionCount"])
                if d["contributionCount"] > 0: act.append((wi, d["weekday"]))
        run = best = 0
        for c in flat:
            run = run + 1 if c > 0 else 0; best = max(best, run)
        last = weeks[-1]["contributionDays"][-1]
        D.update(active=act, today=(len(weeks) - 1, last["weekday"]), days_in_orbit=sum(1 for c in flat if c > 0),
                 longest=best, revolutions=cal["totalContributions"])
        print("contributions loaded")
except Exception as e:
    print("using fallback data:", e)

esc = html.escape
STARS = lambda w, h, n: "".join(
    f'<circle cx="{random.randint(8,w-8)}" cy="{random.randint(8,h-8)}" r="{random.choice([.7,1,1.2])}" fill="#fff" opacity="{random.uniform(.2,.65):.2f}"/>'
    for _ in range(n))
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "'Segoe UI',system-ui,-apple-system,Helvetica,Arial,sans-serif"

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            '<defs><linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d1030"/><stop offset="1" stop-color="#05060f"/></linearGradient>'
            '<radialGradient id="glow"><stop offset="0" stop-color="#f5d36b" stop-opacity=".55"/><stop offset="1" stop-color="#f5d36b" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="tail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/></linearGradient>'
            f'<clipPath id="av"><circle cx="860" cy="125" r="74"/></clipPath><clipPath id="sunclip"><circle cx="500" cy="290" r="40"/></clipPath></defs>'
            f'{body}</svg>')

def card(w, h, x=0, y=0, rx=22):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#cg)"/>'

def icon(lang, x, y, s=30):
    c = COL.get(lang, "#8b949e"); p = ICONS.get(lang, {}).get("path")
    g = f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s*0.22:.0f}" fill="{c}" fill-opacity=".18" stroke="{c}" stroke-width="2"/>'
    if p:
        k = s * 0.6 / 24
        g += f'<path transform="translate({x+s*0.2:.1f},{y+s*0.2:.1f}) scale({k:.3f})" d="{p}" fill="{c}"/>'
    return g

def label(x, y, t): return f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="13" font-weight="700" letter-spacing="4" fill="#f5d36b">{t}</text>'

# 1) hero solar system (animated)
W, H, cx, cy = 1000, 560, 500, 290
b = [card(W, H), STARS(W, H, 90)]
b.append(f'<text x="30" y="40" font-family="{MONO}" font-size="13" letter-spacing="3" fill="#c9d1d9">SOLAR SYSTEM · @{USER.upper()}</text>')
b.append(f'<text x="30" y="{H-22}" font-family="{MONO}" font-size="11" fill="#8b949e">github.com/{USER}</text>')
b.append(f'<text x="{W-30}" y="{H-22}" font-family="{MONO}" font-size="11" fill="#8b949e" text-anchor="end">planets = languages · moons = repos · comets = recent pushes</text>')
orbits = [150, 205, 260, 315, 370]; durs = [70, 90, 110, 140, 170]; begs = [-10, -30, -60, -20, -100]
for rx in orbits: b.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{rx*.52:.1f}" fill="none" stroke="#fff" stroke-opacity=".13" stroke-dasharray="3 5"/>')
for i, (lang, pct) in enumerate(D["langs"]):
    rx = orbits[i]; ry = rx * .52; c = COL.get(lang, "#888"); r = 14 + pct * .35
    path = f"M{cx+rx},{cy} a{rx},{ry:.1f} 0 1,0 {-2*rx},0 a{rx},{ry:.1f} 0 1,0 {2*rx},0"
    b.append(f'<g><animateMotion dur="{durs[i]}s" begin="{begs[i]}s" repeatCount="indefinite" path="{path}"/>'
             f'<circle r="{r:.1f}" fill="{c}"/><circle r="{r:.1f}" fill="none" stroke="#fff" stroke-opacity=".25"/>'
             f'<path transform="translate({-r*.55:.1f},{-r*.55:.1f}) scale({r*1.1/24:.3f})" d="{ICONS[lang]["path"]}" fill="#0b0d1a"/>'
             f'<text y="{r+16:.0f}" font-family="{MONO}" font-size="11" font-weight="700" text-anchor="middle" fill="#e6edf3">{lang} {pct}%</text></g>')
b.append(f'<circle cx="{cx}" cy="{cy}" r="110" fill="url(#glow)"/><circle cx="{cx}" cy="{cy}" r="46" fill="#f5d36b"/>')
if avatar_b64: b.append(f'<image href="data:image/png;base64,{avatar_b64}" x="460" y="250" width="80" height="80" clip-path="url(#sunclip)" preserveAspectRatio="xMidYMid slice"/>')
else: b.append(f'<circle cx="{cx}" cy="{cy}" r="40" fill="#e23b1f"/><text x="500" y="302" font-family="{SANS}" font-size="34" font-weight="800" text-anchor="middle" fill="#2a0a05">M</text>')
def comet(lbl, y0, y1, dur, beg):
    b.append(f'<g><animateTransform attributeName="transform" type="translate" values="-100 {y0};1100 {y1}" dur="{dur}s" begin="{beg}s" repeatCount="indefinite"/>'
             f'<rect x="-80" y="-1" width="80" height="2" fill="url(#tail)" transform="rotate(-14)"/><circle r="4" fill="#fff"/>'
             f'<text x="12" y="-8" font-family="{MONO}" font-size="11" fill="#e6edf3">{esc(lbl)}</text></g>')
for i, r in enumerate(D["repos"][:2]): comet(r["name"], [200, 120][i], [340, 60][i], [18, 24][i], [0, -8][i])
open("assets/hero.svg", "w").write(svg(W, H, "".join(b)))

# 2) the sun card
b = [card(1000, 250), STARS(1000, 250, 28), label(44, 62, "THE SUN"),
     f'<text x="44" y="126" font-family="{SANS}" font-size="46" font-weight="800" fill="#fff">{esc(D["name"])}</text>',
     f'<text x="44" y="170" font-family="{SANS}" font-size="20" fill="#c9d1d9">{esc(D["tagline"])}</text>',
     f'<text x="44" y="214" font-family="{MONO}" font-size="14" fill="#8b949e">{D["followers"]} followers · {len(D["repos"])} repositories · ★ {D["stars"]} stars</text>',
     '<circle cx="860" cy="125" r="80" fill="#f5d36b"/>']
if avatar_b64: b.append(f'<image href="data:image/png;base64,{avatar_b64}" x="786" y="51" width="148" height="148" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>')
else: b.append(f'<circle cx="860" cy="125" r="74" fill="#e23b1f"/><text x="860" y="145" font-family="{SANS}" font-size="64" font-weight="800" text-anchor="middle" fill="#2a0a05">M</text>')
open("assets/sun.svg", "w").write(svg(1000, 250, "".join(b)))

# 3) moons 2x2
b = [STARS(1000, 520, 45)]; ringc = {None: "#9aa3b2"}
for i, r in enumerate(D["repos"][:4]):
    x = (i % 2) * 505; y = (i // 2) * 265; c = ringc.get(r["lang"], COL.get(r["lang"], "#9aa3b2"))
    b.append(card(495, 235, x, y, 20)); b.append(label(x + 36, y + 56, f"MOON 0{i+1}"))
    px, py = x + 430, y + 50
    b.append(f'<circle cx="{px}" cy="{py}" r="10" fill="{c}"/><ellipse cx="{px}" cy="{py}" rx="19" ry="5" fill="none" stroke="#c9d1d9" stroke-opacity=".7" stroke-width="1.5"/>')
    b.append(f'<text x="{x+36}" y="{y+100}" font-family="{MONO}" font-size="22" font-weight="700" fill="#fff">{esc(r["name"])}</text>')
    d = r["desc"]; l1 = d[:44].rsplit(" ", 1)[0] if len(d) >= 46 else d
    l2 = d[len(l1):].strip(); l2 = (l2[:43].rstrip() + "…") if len(l2) > 44 else l2
    lines = [l1] + ([l2] if l2 else [])
    for j, ln in enumerate(lines): b.append(f'<text x="{x+36}" y="{y+134+j*23}" font-family="{SANS}" font-size="16" fill="#c9d1d9">{esc(ln)}</text>')
    b.append(f'<text x="{x+36}" y="{y+205}" font-family="{MONO}" font-size="15" fill="#8b949e">★ {r.get("stars",0)}    ⑂ {r.get("forks",0)}</text>')
    if r["lang"] in ICONS:
        b.append(icon(r["lang"], x + 150, y + 183, 28)); b.append(f'<text x="{x+188}" y="{y+205}" font-family="{MONO}" font-size="15" fill="#c9d1d9">{r["lang"]}</text>')
open("assets/moons.svg", "w").write(svg(1000, 500, "".join(b)))

# 4) planets bars
rows = D["langs"]; h = 130 + len(rows) * 52
b = [card(1000, h), STARS(1000, h, 30), label(44, 62, "PLANETS")]
for i, (lang, pct) in enumerate(rows):
    y = 100 + i * 52; c = COL.get(lang, "#888")
    b.append(icon(lang, 44, y, 34))
    b.append(f'<text x="92" y="{y+24}" font-family="{SANS}" font-size="20" font-weight="700" fill="#fff">{lang}</text>')
    b.append(f'<rect x="300" y="{y+7}" width="600" height="20" rx="10" fill="#242738"/><rect x="300" y="{y+7}" width="{600*pct/rows[0][1]:.0f}" height="20" rx="10" fill="{c}"/>')
    b.append(f'<text x="956" y="{y+24}" font-family="{MONO}" font-size="16" text-anchor="end" fill="#aab2c5">{pct}%</text>')
open("assets/planets.svg", "w").write(svg(1000, h, "".join(b)))

# 5) orbit log (26 weeks)
b = [card(1000, 270), STARS(1000, 270, 25), label(44, 60, "ORBIT LOG · 26 WEEKS")]
act = set(D["active"]); today = tuple(D["today"])
for wk in range(26):
    for d in range(7):
        c = "#1d2033"
        if (wk, d) in act: c = "#4b5bd1"
        if (wk, d) == today: c = "#f5d36b"
        b.append(f'<rect x="{44+wk*23}" y="{95+d*21}" width="17" height="17" rx="4" fill="{c}"/>')
for i, (k, v) in enumerate([("DAYS IN ORBIT", f"{D['days_in_orbit']} days"), ("LONGEST ORBIT", f"{D['longest']} days"), ("REVOLUTIONS THIS YEAR", str(D["revolutions"]))]):
    y = 100 + i * 62
    b.append(f'<text x="700" y="{y}" font-family="{MONO}" font-size="13" letter-spacing="2" fill="#8b949e">{k}</text><text x="700" y="{y+34}" font-family="{SANS}" font-size="30" font-weight="800" fill="#fff">{v}</text>')
open("assets/orbit.svg", "w").write(svg(1000, 270, "".join(b)))
print("done -> assets/")
