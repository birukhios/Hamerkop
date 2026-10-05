#!/usr/bin/env python3
"""Build the Hamerkop Systems static site.

Sources live in src/:
  src/content.json   copy for solutions, products, services, industries, insights, Odoo
  src/pages/*.html   one-off pages (home, hubs, company, contact, ...), with a front-matter block

Run `python3 build.py` from the repo root. It writes the finished *.html files to the
repo root, which GitHub Pages serves as-is. Edit the sources, not the generated files.
"""

import hashlib
import json
import re
import shutil
import sys
from html import escape
from urllib.parse import urlencode
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DATA = json.loads((SRC / "content.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
CATEGORIES = {c["slug"]: c for c in DATA["insight_categories"]}
ARTICLES = sorted(DATA["articles"], key=lambda a: a["date"], reverse=True)


def asset_version(name):
    """Short content hash, so browsers fetch styles/scripts again whenever they change."""
    return hashlib.sha1((ROOT / name).read_bytes()).hexdigest()[:8]


CSS_V, JS_V = asset_version("styles.css"), asset_version("main.js")

ARROW = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M5 12h14M13 6l6 6-6 6"/></svg>'
)

NAV = [
    ("solutions", "Solutions"),
    ("products", "Products"),
    ("services", "Services"),
    ("industries", "Industries"),
    ("company", "Company"),
    ("insights", "Insights"),
]

# Dropdown entries under the main navigation items.
MENUS = {
    "solutions": [(s["slug"], s["name"]) for s in DATA["solutions"]],
    "products": [("product-eims", "Hamerkop EIMS")] + [(p["slug"], p["name"]) for p in DATA["products"]],
    "services": [(s["slug"], s["name"]) for s in DATA["services"]],
    "industries": [(i["slug"], i["name"]) for i in DATA["industries"]],
}

CHEVRON = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M6 9l6 6 6-6"/></svg>'
)

THEME_ICONS = (
    '<svg class="icon-moon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
    '<svg class="icon-sun" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
)

# --------------------------------------------------------------------------- design directions
# `python3 build.py --designs <folder>` renders the whole site once per direction for comparison.

FONTSHARE = '<link rel="preconnect" href="https://api.fontshare.com" />\n    <link rel="preconnect" href="https://cdn.fontshare.com" crossorigin />\n    '
GOOGLE = '<link rel="preconnect" href="https://fonts.googleapis.com" />\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n    '

DESIGNS = [
    {
        "key": "editorial", "name": "Editorial", "ref_name": "Wayfare", "ref": "https://touroperator.framer.website/",
        "fonts": FONTSHARE + '<link href="https://api.fontshare.com/v2/css?f[]=clash-grotesk@400,500,600&amp;f[]=general-sans@400,500,600&amp;display=swap" rel="stylesheet" />',
        "type": "Clash Grotesk + General Sans", "toggle": True,
        "swatches": ["#fafafa", "#ffffff", "#0a0a0a", "#ea580c", "#71717a"],
        "summary": "Editorial and photographic: full-bleed hero with blur-in headline, scroll-revealed statement, spec sheet with counters, hover-swap product list, industries scroller and two-row marquee.",
    },
    {
        "key": "noir", "name": "Noir", "ref_name": "Hedvig", "ref": "https://hedvig.framer.website/",
        "fonts": GOOGLE + '<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&amp;display=swap" rel="stylesheet" />',
        "type": "Figtree", "toggle": False, "image_heroes": True,
        "swatches": ["#0a0a0a", "#141414", "#fafafa", "#ea580c", "#71717a"],
        "summary": "Cinematic on brand ink: zooming full-bleed hero, scroll-scrubbed statement, portrait cards, full-screen cards that stack as you scroll, and a before/after comparison.",
    },
    {
        "key": "serene", "name": "Serene", "ref_name": "Solva", "ref": "https://solva-template.framer.website/",
        "fonts": FONTSHARE + GOOGLE + '<link href="https://api.fontshare.com/v2/css?f[]=sentient@300,400&amp;display=swap" rel="stylesheet" />\n    <link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&amp;display=swap" rel="stylesheet" />',
        "type": "Sentient + Onest", "toggle": False,
        "swatches": ["#fafafa", "#ffffff", "#0a0a0a", "#ea580c", "#a1a1aa"],
        "summary": "Calm and considered: light serif headlines that blur in, interface cards floating over photography, logo marquee, alternating feature rows and a tabbed product section.",
    },
    {
        "key": "bold", "name": "Bold", "ref_name": "NoveQ", "ref": "https://noveq.framer.website/",
        "fonts": GOOGLE + '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet" />',
        "type": "Plus Jakarta Sans + Inter", "toggle": False,
        "swatches": ["#f4f4f5", "#ffffff", "#0a0a0a", "#ea580c", "#a1a1aa"],
        "summary": "Confident and heavy: sticky dark hero with character-blur text, two-tone headlines, bento grid with counters, alternating service rows, step cards and a capabilities marquee.",
    },
]
ACTIVE = None  # the direction being rendered; None means the normal site build


# Area of Interest values on the contact form (must match its <option> text).
PRODUCT_INTEREST = {
    "product-eims": "Electronic Invoicing",
    "product-finance-suite": "Financial Technology",
    "product-identity": "Identity & Trust",
    "product-integrator": "Enterprise Integration",
    "product-insight": "Data, Analytics & AI",
}
SERVICE_INTEREST = {
    "service-systems-integration": "Enterprise Integration",
    "service-technology-consulting": "Technology Consulting",
    "service-managed-services": "Managed Services",
}


def e(text):
    return escape(text, quote=True)


def img(ref, width=1400):
    """Local asset paths pass through; bare Unsplash ids become full URLs."""
    if ref.startswith("./"):
        return ref
    return f"https://images.unsplash.com/photo-{ref}?auto=format&fit=crop&w={width}&q=80"


def contact_url(type=None, interest=None, industry=None, product=None):
    """Link to the consultation form with fields pre-selected."""
    params = [(k, v) for k, v in (("type", type), ("interest", interest), ("industry", industry), ("product", product)) if v]
    query = ("?" + urlencode(params)) if params else ""
    return e(f"./contact.html{query}#consult-form")


def odoo_dates():
    o = DATA["odoo"]
    return o.get("agreement_date"), o.get("silver_date")


# --------------------------------------------------------------------------- layout

def header(active, slug):
    items = []
    for key, label in NAV:
        cls = ' class="nav-link is-active"' if key == active else ' class="nav-link"'
        here = ' aria-current="page"' if key == slug else ""
        link = f'<a href="./{key}.html"{cls}{here}>{label}</a>'
        if key not in MENUS:
            items.append(f"          {link}")
            continue
        current = ' aria-current="page"'
        entries = "\n".join(
            f'              <a href="./{href}.html"{current if href == slug else ""}>{e(name)}</a>'
            for href, name in MENUS[key]
        )
        items.append(f"""          <div class="nav-item">
            {link}
            <button class="nav-sub-toggle" type="button" aria-expanded="false" aria-controls="menu-{key}" aria-label="{label} menu">{CHEVRON}</button>
            <div class="nav-menu" id="menu-{key}">
              <a class="nav-menu-all" href="./{key}.html">All {label.lower()}</a>
{entries}
            </div>
          </div>""")
    links = "\n".join(items)
    toggle = (
        f'<button class="theme-toggle" type="button" aria-label="Switch to dark theme">{THEME_ICONS}</button>'
        if not ACTIVE or ACTIVE["toggle"] else ""
    )
    return f"""      <header class="topbar">
        <div class="nav-shell">
          <a class="brand" href="./index.html" aria-label="Hamerkop System S.C. home">
            <img class="brand-logo logo-on-light" src="./assets/hamerkop-logo.svg" alt="Hamerkop System S.C." width="148" height="40" />
            <img class="brand-logo logo-on-dark" src="./assets/hamerkop-logo-white.svg" alt="Hamerkop System S.C." width="148" height="40" />
          </a>
          <nav id="site-nav" class="site-nav" aria-label="Primary">
{links}
            <a href="./contact.html" class="button nav-cta-mobile">Request a Consultation</a>
          </nav>
          <div class="nav-actions">
            {toggle}
            <a href="./contact.html" class="button nav-cta">Request a Consultation</a>
            <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Menu">
              <span></span><span></span>
            </button>
          </div>
        </div>
      </header>"""


def footer():
    solutions = "\n".join(
        f'                <a href="./{s["slug"]}.html">{e(s["name"])}</a>' for s in DATA["solutions"]
    )
    return f"""      <footer class="site-footer">
        <div class="footer-inner">
          <div class="footer-grid">
            <div class="footer-brand">
              <a class="brand" href="./index.html" aria-label="Hamerkop System S.C. home">
                <img class="brand-logo logo-on-light" src="./assets/hamerkop-logo.svg" alt="Hamerkop System S.C." width="160" height="43" />
                <img class="brand-logo logo-on-dark" src="./assets/hamerkop-logo-white.svg" alt="Hamerkop System S.C." width="160" height="43" />
              </a>
              <p>
                Enterprise technology for organizations that require reliable operations, connected
                systems and stronger institutional control.
              </p>
              <div class="footer-cert">
                <div class="cert-logos">
                  <img src="./assets/insa.svg" alt="INSA certified" />
                  <img src="./assets/mor.svg" alt="Ministry of Revenue accredited" />
                  <a class="cert-odoo" href="./partnership-odoo.html">{odoo_mark()}</a>
                </div>
                <p>Certified by INSA and accredited by the Ethiopian Ministry of Revenue. All Hamerkop systems are inspected every 6 months. Odoo Silver Partner.</p>
              </div>
            </div>
            <div>
              <p class="footer-title">Solutions</p>
              <div class="footer-links">
{solutions}
              </div>
            </div>
            <div>
              <p class="footer-title">Company</p>
              <div class="footer-links">
                <a href="./company.html">About Hamerkop</a>
                <a href="./partnership-odoo.html">Odoo partnership</a>
                <a href="./industries.html">Industries</a>
                <a href="./insights.html">Insights</a>
                <a href="./contact.html">Contact</a>
              </div>
            </div>
            <div>
              <p class="footer-title">Talk to us</p>
              <div class="footer-links">
                <a href="mailto:{SITE["email"]}">{SITE["email"]}</a>
                <span>Addis Ababa, Ethiopia</span>
                <a href="./contact.html">Request a Consultation</a>
              </div>
            </div>
          </div>
          <div class="footer-bottom">
            <span>&copy; 2026 Hamerkop System S.C. All rights reserved.</span>
            <span class="footer-legal">
              <a href="./privacy.html">Privacy Policy</a>
              <a href="./terms.html">Terms of Use</a>
              <a href="./cookies.html">Cookie Notice</a>
            </span>
          </div>
        </div>
        <p class="footer-wordmark" aria-hidden="true">HAMERKOP</p>
      </footer>"""


def layout(title, description, nav, body, slug):
    full_title = "Hamerkop Systems — Enterprise Technology Solutions" if nav == "home" else f"{title} | Hamerkop Systems"
    url = SITE["url"] + ("" if slug == "index" else f"{slug}.html")
    # The 404 page is served at whatever path was requested, so pin its relative links to the site root.
    head_extra = (
        f'<base href="{SITE["url"]}" />\n    <meta name="robots" content="noindex" />'
        if slug == "404" else f'<link rel="canonical" href="{url}" />\n    <meta property="og:url" content="{url}" />'
    )
    design = ACTIVE or DESIGNS[0]
    fonts = design["fonts"]
    theme_script = (
        '<script>try{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}catch(e){}</script>'
        if design["toggle"] else ""
    )
    design_css = ""
    badge = ""
    if ACTIVE:
        head_extra = '<meta name="robots" content="noindex" />'
        if ACTIVE["key"] != "editorial":
            version = hashlib.sha1((SRC / "designs" / f'{ACTIVE["key"]}.css').read_bytes()).hexdigest()[:8]
            design_css = f'\n    <link rel="stylesheet" href="./design.css?v={version}" />'
        badge = (
            f'\n    <div class="design-badge"><a href="../index.html"><strong>{ACTIVE["name"]}</strong> <span>Compare designs &rarr;</span></a>'
            f'<button class="design-badge-close" type="button" aria-label="Hide design preview label">&times;</button></div>'
        )
    return optimise_images(f"""<!doctype html>
<!-- Generated by build.py from src/. Edit the source files, then run: python3 build.py -->
<html lang="en"{f' data-design="{ACTIVE["key"]}"' if ACTIVE else ""}>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{e(description)}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="Hamerkop Systems" />
    <meta property="og:title" content="{e(full_title)}" />
    <meta property="og:description" content="{e(description)}" />
    {head_extra}
    <title>{e(full_title)}</title>
    <link rel="preconnect" href="https://images.unsplash.com" crossorigin />
    {fonts}
    {theme_script}
    <link rel="icon" href="./assets/hamerkop-bird.svg" type="image/svg+xml" />
    <meta name="theme-color" content="#f5efe4" />
    <link rel="stylesheet" href="./styles.css?v={CSS_V}" />{design_css}
    <noscript><style>.reveal{{opacity:1;transform:none}}</style></noscript>
    <script defer src="./main.js?v={JS_V}"></script>
  </head>
  <body>
    <div class="page-shell">
      <a class="skip-link" href="#main">Skip to main content</a>
{header(nav, slug)}

      <main id="main" tabindex="-1">
{body.strip()}
      </main>
{footer()}
    </div>{badge}
  </body>
</html>
""")


# --------------------------------------------------------------------------- image optimisation

UNSPLASH = re.compile(r'<img\b([^>]*?)\bsrc="https://images\.unsplash\.com/photo-([0-9a-f-]+)\?([^"]*)"([^>]*?)\s*/?>')
FULL_BLEED = ("page-hero-bg", "nx-band-bg", "nx-stats-bg", "nx-cta-bg", "hero-bg", "sv-art-bg", "is-active")
EAGER = ("page-hero-bg", "hero-bg", "is-active", "brand-logo", "hero-zoom", "sv-art-bg")


def optimise_images(html):
    """Responsive srcset for Unsplash photos; lazy loading and async decoding below the fold."""

    def unsplash(m):
        before, pid, query, after = m.groups()
        attrs = before + after
        params = dict(kv.split("=", 1) for kv in query.replace("&amp;", "&").split("&") if "=" in kv)
        w = int(params.get("w", 1600))
        q = params.get("q", "75")
        widths = sorted({x for x in (480, 800, 1200, 1600, 2000) if x < w} | {w})
        base = f"https://images.unsplash.com/photo-{pid}?auto=format&amp;fit=crop&amp;q={q}"
        srcset = ", ".join(f"{base}&amp;w={x} {x}w" for x in widths)
        full = any(c in attrs for c in FULL_BLEED) or w >= 2000
        sizes = "100vw" if full else "(max-width: 900px) 100vw, 50vw"
        return f'<img{before}src="{base}&amp;w={w}" srcset="{srcset}" sizes="{sizes}"{after} />'

    html = UNSPLASH.sub(unsplash, html)

    def lazy(m):
        tag = m.group(0)
        hero = any(c in tag for c in EAGER)
        if hero and "page-hero-bg" in tag or 'class="is-active"' in tag:
            tag = tag.replace("<img", '<img fetchpriority="high"', 1)
        if "loading=" not in tag and not hero:
            tag = tag.replace("<img", '<img loading="lazy"', 1)
        if "decoding=" not in tag:
            tag = tag.replace("<img", '<img decoding="async"', 1)
        return tag

    return re.sub(r"<img\b[^>]*>", lazy, html)


# --------------------------------------------------------------------------- shared blocks

def page_hero(eyebrow, h1, lede, actions="", extra="", image=None, art=False):
    if image and ACTIVE and ACTIVE.get("image_heroes"):
        return f"""        <section class="hero page-hero has-image{" is-art" if art else ""}" data-pointer-parallax>
          <img class="page-hero-bg" src="{img(image, 2400)}" alt="" />
          <div class="hero-copy" data-scroll-out>
            <p class="eyebrow">{eyebrow}</p>
            {extra}<h1 data-anim="blur-in">{e(h1)}</h1>
            <p class="lede reveal">{e(lede)}</p>
            {actions}
          </div>
        </section>"""
    return f"""        <section class="hero page-hero">
          <div class="hero-copy reveal">
            <p class="eyebrow">{eyebrow}</p>
            {extra}<h1>{e(h1)}</h1>
            <p class="lede">{e(lede)}</p>
            {actions}
          </div>
        </section>"""


def actions(*buttons):
    out = []
    for i, (href, label) in enumerate(buttons):
        cls = "button button-dark" if i == 0 else "button button-ghost"
        out.append(f'<a class="{cls}" href="{href}">{e(label)}</a>')
    return '<div class="hero-actions">' + "".join(out) + "</div>"


def cta(eyebrow, title, text, button=("./contact.html", "Request a Consultation")):
    return f"""        <section class="cta">
          <div class="cta-content reveal">
            <p class="eyebrow">{e(eyebrow)}</p>
            <h2>{e(title)}</h2>
          </div>
          <div class="cta-side reveal">
            <p>{e(text)}</p>
            <a class="button button-dark" href="{button[0]}">{e(button[1])}</a>
          </div>
        </section>"""


def default_cta(href="./contact.html#consult-form"):
    return cta(
        "Start a conversation",
        "Start with the operation you need to improve.",
        "Whether the requirement is ERP, electronic invoicing, financial technology, identity, "
        "integration or data, the conversation begins with the current operation and the systems around it.",
        (href, "Request a Consultation"),
    )


def info_cards(items, cls="feature-grid"):
    cards = "\n".join(
        f"""          <article class="feature-card reveal">
            <h3>{e(t)}</h3>
            <p>{e(d)}</p>
          </article>"""
        for t, d in items
    )
    return f'        <section class="page-band {cls}">\n{cards}\n        </section>'


def section_heading(eyebrow, title, text=""):
    p = f"\n            <p>{e(text)}</p>" if text else ""
    return f"""          <div class="section-heading reveal">
            <p class="eyebrow">{e(eyebrow)}</p>
            <h2>{e(title)}</h2>{p}
          </div>"""


def link_card(href, image, alt, kicker, title, text, link_label):
    return f"""          <a class="feature-card reveal" href="{href}">
            <div class="service-visual"><img src="{img(image, 1200)}" alt="{e(alt)}" loading="lazy" /></div>
            <p class="service-kicker">{e(kicker)}</p>
            <h3>{e(title)}</h3>
            <p>{e(text)}</p>
            <span class="card-link">{e(link_label)} {ARROW}</span>
          </a>"""


def odoo_note():
    """Small callout linking ERP pages to the Odoo partnership."""
    return f"""        <section class="page-band">
          <a class="odoo-note reveal" href="./partnership-odoo.html">
            {odoo_mark()}
            <span>
              <strong>Hamerkop is an Odoo Silver Partner.</strong>
              Odoo forms part of our ERP implementation capability alongside Hamerkop products and client-specific integrations.
            </span>
            <span class="card-link">Read the story {ARROW}</span>
          </a>
        </section>"""


# --------------------------------------------------------------------------- generated card sets

def solution_cards():
    return "\n".join(
        link_card(f'./{s["slug"]}.html', s["image"], s["alt"], s["name"], s["headline"], s["summary"], "Explore")
        for s in DATA["solutions"]
    )


def product_card(p):
    return f"""          <a class="feature-card reveal" href="./{p["slug"]}.html">
            <div class="service-visual"><img src="{img(p["image"], 1200)}" alt="{e(p["name"])}" loading="lazy" /></div>
            <p class="service-kicker">{e(p["label"])}</p>
            <h3>{e(p["name"])}</h3>
            <p>{e(p["summary"])}</p>
            <span class="card-link">Explore {ARROW}</span>
          </a>"""


def products_by(family):
    return "\n".join(product_card(p) for p in DATA["products"] if p["family"] == family)


def service_cards():
    return "\n".join(
        link_card(f'./{s["slug"]}.html', s["image"], s["name"], f'Service {s["number"]}', s["name"], s["summary"], "Explore")
        for s in DATA["services"]
    )


def industry_cards():
    return "\n".join(
        link_card(f'./{i["slug"]}.html', i["image"], i["alt"], f'Industry {i["number"]}', i["name"], i["summary"], "Explore")
        for i in DATA["industries"]
    )


def home_industry_cards():
    """The six sectors featured on the homepage, with their shorter homepage copy."""
    cards = []
    for i in DATA["industries"]:
        if "home_summary" not in i:
            continue
        cards.append(f"""            <a class="team-card industry-card reveal" href="./{i["slug"]}.html">
              <div class="industry-photo"><img src="{img(i["image"], 1000)}" alt="{e(i["alt"])}" loading="lazy" /></div>
              <h3>{e(i.get("short", i["name"]))}</h3>
              <p>{e(i["home_summary"])}</p>
            </a>""")
    return "\n".join(cards)


def delivery_steps(long=False):
    return "\n".join(
        f"""            <article class="step reveal">
              <span class="step-index">0{n}</span>
              <h3>{e(name)}</h3>
              <p>{e(full if long else short)}</p>
            </article>"""
        for n, (name, short, full) in enumerate(DATA["delivery"], 1)
    )


def fmt_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    return f"{d} {months[m - 1]} {y}"


def read_minutes(a):
    words = 0
    for block in a["body"]:
        if isinstance(block, str):
            words += len(block.split())
        else:
            words += sum(len(str(x).split()) for v in block.values() for x in (v if isinstance(v, list) else [v]))
    return max(1, round(words / 200))


def article_image(a):
    """Abstract art in image-hero directions (Noir), the article photo elsewhere."""
    if ACTIVE and ACTIVE.get("image_heroes") and a.get("art"):
        return a["art"]
    return a.get("image")


def article_card(a):
    media = (
        f'<div class="journal-media"><img src="{img(article_image(a), 1200)}" alt="" loading="lazy" /></div>\n            '
        if article_image(a) else ""
    )
    return f"""          <a class="journal-card reveal" href="./article-{a["slug"]}.html">
            {media}<p class="journal-meta">{e(CATEGORIES[a["category"]]["name"])} <span aria-hidden="true">&bull;</span> {read_minutes(a)} min read</p>
            <h3>{e(a["title"])}</h3>
            <p>{e(a["summary"])}</p>
          </a>"""


def category_card(c, home=False):
    count = sum(1 for a in ARTICLES if a["category"] == c["slug"])
    status = f"{count} article{'s' if count != 1 else ''}" if count else "Articles coming soon"
    text = c.get("home_description", c["description"]) if home else c["description"]
    return f"""          <a class="feature-card insight-card reveal" href="./{c["slug"]}.html">
            <p class="service-kicker">Insights</p>
            <h3>{e(c["name"])}</h3>
            <p>{e(text)}</p>
            <span class="soon-tag">{status}</span>
          </a>"""


def insight_cards():
    return "\n".join(category_card(c) for c in DATA["insight_categories"])


def latest_articles():
    if not ARTICLES:
        return ""
    cards = "\n".join(article_card(a) for a in ARTICLES[:6])
    return f"""        <section class="page-band">
{section_heading("Latest", "Recent articles")}
          <div class="journal-grid">
{cards}
          </div>
        </section>"""


def home_insights():
    """Latest article previews once articles exist; topic categories until then."""
    if ARTICLES:
        return "\n".join(article_card(a) for a in ARTICLES[:3])
    return "\n".join(category_card(c, home=True) for c in DATA["insight_categories"] if "home_description" in c)


def category_page(c):
    articles = [a for a in ARTICLES if a["category"] == c["slug"]]
    if articles:
        listing = '        <section class="page-band journal-grid">\n' + "\n".join(article_card(a) for a in articles) + "\n        </section>"
    else:
        listing = f"""        <section class="page-band">
          <div class="detail-card empty-state reveal">
            <p class="service-kicker">Coming soon</p>
            <h2>Articles on {e(c["name"])} are in preparation.</h2>
            <p>In the meantime, our team is glad to discuss these questions directly.</p>
            <div class="hero-actions"><a class="button button-dark" href="./contact.html#consult-form">Request a Consultation</a><a class="button button-ghost" href="./insights.html">All insights</a></div>
          </div>
        </section>"""
    others = "\n".join(category_card(o) for o in DATA["insight_categories"] if o is not c)
    body = "\n".join([
        page_hero('<a href="./insights.html">Insights</a> &middot; Category', c["name"], c["description"],
                  image=next((a.get("art") for a in articles if a.get("art")), None), art=True),
        listing,
        '        <section class="page-band">\n' + section_heading("More topics", "Other Insights categories")
        + '\n          <div class="feature-grid">\n' + others + "\n          </div>\n        </section>",
    ])
    return layout(c["name"], c["description"], "insights", body, c["slug"])


def article_page(a):
    c = CATEGORIES[a["category"]]
    blocks = []
    for block in a["body"]:
        if isinstance(block, str):
            blocks.append(f"<p>{e(block)}</p>")
        elif "h2" in block:
            blocks.append(f"<h2>{e(block['h2'])}</h2>")
        elif "list" in block:
            blocks.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in block["list"]) + "</ul>")
        elif "quote" in block:
            blocks.append(f'<blockquote class="pull-quote">{e(block["quote"])}</blockquote>')
    author = f' &middot; {e(a["author"])}' if a.get("author") else ""
    image = (
        f'        <figure class="article-image reveal"><img src="{img(a["image"], 1800)}" alt="" /></figure>\n'
        if a.get("image") and not (ACTIVE and ACTIVE.get("image_heroes")) else ""
    )
    art_hero = ACTIVE and ACTIVE.get("image_heroes") and a.get("art")
    related = [x for x in ARTICLES if x["category"] == a["category"] and x is not a][:3]
    related_html = (
        '        <section class="page-band">\n' + section_heading("Related", f'More on {c["name"]}')
        + '\n          <div class="journal-grid">\n' + "\n".join(article_card(x) for x in related) + "\n          </div>\n        </section>\n"
        if related else ""
    )
    hero_open = (
        f'<header class="hero page-hero has-image is-art" data-pointer-parallax>\n            <img class="page-hero-bg" src="{img(a["art"], 2400)}" alt="" />\n            <div class="hero-copy" data-scroll-out>'
        if art_hero else '<header class="hero page-hero">\n            <div class="hero-copy reveal">'
    )
    body = f"""        <article class="article">
          {hero_open}
              <p class="eyebrow"><a href="./insights.html">Insights</a> &middot; <a href="./{c["slug"]}.html">{e(c["name"])}</a></p>
              <h1>{e(a["title"])}</h1>
              <p class="lede">{e(a["summary"])}</p>
              <p class="article-meta"><time datetime="{a["date"]}">{fmt_date(a["date"])}</time>{author} &middot; {read_minutes(a)} min read</p>
            </div>
          </header>
{image}          <div class="article-body reveal">
            {"".join(blocks)}
          </div>
        </article>
{related_html}{default_cta()}"""
    return layout(a["title"], a["summary"], "insights", body, f'article-{a["slug"]}')


def odoo_mark():
    """The official badge once supplied; until then the Odoo logo with a Silver Partner label."""
    badge = DATA["odoo"].get("badge")
    if badge:
        return f'<img class="odoo-mark" src="{badge}" alt="Odoo Silver Partner" />'
    return (
        '<span class="odoo-mark" role="img" aria-label="Odoo Silver Partner">'
        '<img src="./assets/partners/odoo.svg" alt="" /><span>Silver Partner</span></span>'
    )


def gallery_items(limit=None):
    photos = DATA["odoo"]["photos"][:limit] if limit else DATA["odoo"]["photos"]
    return "\n".join(
        f"""              <button type="button" class="gallery-item" data-lightbox data-caption="{e(p["caption"])}">
                <img src="{p["src"]}" alt="{e(p["caption"])}" loading="lazy" />
              </button>"""
        for p in photos
    )


# Galleries render only once real signing photos are listed in content.json.
def odoo_gallery_home():
    if not DATA["odoo"]["photos"]:
        return ""
    return f"""            <div class="milestone-gallery reveal" aria-label="Partnership signing photos">
{gallery_items(3)}
            </div>"""


def odoo_gallery_section():
    if not DATA["odoo"]["photos"]:
        return ""
    return f"""        <section class="section-pad">
          <div class="section-heading reveal">
            <p class="eyebrow">Gallery</p>
            <h2>The partnership signing.</h2>
          </div>
          <div class="photo-grid reveal">
{gallery_items()}
          </div>
        </section>"""


def odoo_timeline():
    agreement, silver = odoo_dates()
    days = DATA["odoo"]["days"]
    steps = [
        ("Partnership agreement signed", agreement, "Hamerkop Systems formally entered the Odoo partner network."),
        ("Team enablement & delivery", None, "Our ERP team aligned delivery, localization and support practices with the Odoo partner program."),
        ("Silver Partner grade awarded", silver, f"Hamerkop reached Odoo Silver Partner grade within {days} days of signing the partnership agreement."),
    ]
    out = []
    for n, (title, date, text) in enumerate(steps, 1):
        date_html = f'<span class="timeline-date">{e(date)}</span>' if date else ""
        out.append(f"""            <li class="timeline-step reveal">
              <span class="step-index">0{n}</span>
              <div>
                {date_html}<h3>{e(title)}</h3>
                <p>{e(text)}</p>
              </div>
            </li>""")
    return "\n".join(out)


def odoo_stats():
    return f"""            <div class="milestone-stats">
              <div><strong>{DATA["odoo"]["days"]} days</strong><span>from partnership agreement to Silver grade</span></div>
              <div><strong>Silver</strong><span>Odoo partner grade</span></div>
              <div><strong>ERP</strong><span>Odoo alongside Hamerkop ERP products</span></div>
            </div>"""


# --------------------------------------------------------------------------- homepage components

def home_solution_cards():
    """The three priority solutions as tall photo cards."""
    picks = {"solution-erp": "./assets/erp.jpg", "solution-e-invoicing": "./assets/invoice.jpg", "solution-integration": "./assets/data.jpg"}
    cards = []
    for s in DATA["solutions"]:
        if s["slug"] not in picks:
            continue
        cards.append(f"""            <a class="photo-card reveal" href="./{s["slug"]}.html">
              <img src="{picks[s["slug"]]}" alt="" loading="lazy" />
              <span class="photo-chip">Solution {s["number"]}</span>
              <span class="photo-card-body">
                <span class="photo-card-kicker">{e(s["name"])}</span>
                <span class="photo-card-title">{e(s["headline"])}</span>
                <span class="photo-card-cta">Explore {ARROW}</span>
              </span>
            </a>""")
    return "\n".join(cards)


SHOWCASE = [
    ("./products.html#erp-family", "ERP Family", "ERP Lite, ERP Business, ERP Enterprise and ERP for Government provide different levels of operational scope and control.", "1497215842964-222b430dc094"),
    ("./product-eims.html", "Hamerkop EIMS", "Electronic invoice and receipt processing connected with the systems that create, record and report the transaction.", "./assets/invoice.jpg"),
    ("./product-finance-suite.html", "Finance Suite", "A financial workflow platform for institutions managing collections, reconciliation and settlement.", "./assets/fintech.jpg"),
    ("./product-identity.html", "Identity", "Institutional identity and access for verified users, controlled roles and secure application access.", "1555949963-aa79dcee981c"),
    ("./product-integrator.html", "Integrator", "A managed integration layer for applications, APIs and legacy environments.", "./assets/data.jpg"),
    ("./product-insight.html", "Insight", "A reporting and analytics layer built around institutional data.", "1460925895917-afdab827c52f"),
]


def product_showcase():
    """Numbered product list; hovering or focusing a row swaps the photo beside it."""
    rows = "\n".join(
        f"""              <li>
                <a class="showcase-row{" is-active" if n == 1 else ""}" href="{href}" data-image="{img(image, 1400)}">
                  <span class="showcase-index">0{n}</span>
                  <span class="showcase-name">{e(name)}</span>
                  <span class="showcase-text">{e(text)}</span>
                </a>
              </li>"""
        for n, (href, name, text, image) in enumerate(SHOWCASE, 1)
    )
    first = img(SHOWCASE[0][3], 1400)
    return f"""          <div class="showcase">
            <figure class="showcase-media reveal"><img src="{first}" alt="" /></figure>
            <ol class="showcase-list">
{rows}
            </ol>
          </div>"""


def industry_scroller():
    cards = "\n".join(
        f"""              <a class="scroll-card" href="./{i["slug"]}.html">
                <img src="{img(i["image"], 900)}" alt="" loading="lazy" />
                <span class="scroll-card-body">
                  <span class="photo-card-kicker">Industry {i["number"]}</span>
                  <span class="scroll-card-title">{e(i.get("short", i["name"]))}</span>
                </span>
              </a>"""
        for i in DATA["industries"]
    )
    return f"""          <div class="scroller" data-scroller>
            <div class="scroller-track" tabindex="0" aria-label="Industries">
{cards}
            </div>
            <div class="scroller-controls">
              <button type="button" class="round-button" data-scroll="-1" aria-label="Previous industries">{ARROW}</button>
              <button type="button" class="round-button" data-scroll="1" aria-label="Next industries">{ARROW}</button>
            </div>
          </div>"""


def spec_sheet():
    rows = [
        ("Headquarters", "Addis Ababa"),
        ("Solution areas", str(len(DATA["solutions"]))),
        ("Products", str(len(DATA["products"]) + 1)),
        ("Industries served", str(len(DATA["industries"]))),
        ("Delivery stages", str(len(DATA["delivery"]))),
        ("Odoo partner grade", "Silver"),
    ]
    items = "\n".join(
        f'              <div class="spec-row"><dt>{e(k)}</dt><dd{f" data-count={chr(34)}{v}{chr(34)}" if v.isdigit() else ""}>{e(v)}</dd></div>'
        for k, v in rows
    )
    return f"""            <dl class="spec-sheet reveal">
{items}
              <p class="spec-note">From discovery to go-live, stabilization and continuous improvement.</p>
            </dl>"""


def marquee(items, extra_class="", speed=40):
    """Infinite marquee. The second copy is hidden from assistive technology."""
    track = "".join(items)
    return (
        f'<div class="marquee {extra_class}" style="--marquee-speed:{speed}s">'
        f'<div class="marquee-track">{track}<span class="marquee-copy" aria-hidden="true" style="display:contents">{track}</span></div></div>'
    )


def capability_marquee(reverse=False):
    names = [s["name"] for s in DATA["solutions"]] + ["Hamerkop EIMS"] + [p["name"] for p in DATA["products"]]
    return marquee([f'<span class="marquee-item">{e(n)}</span>' for n in names], "marquee-reverse" if reverse else "", 55)


def industry_marquee():
    return marquee([f'<a class="marquee-item" href="./{i["slug"]}.html">{e(i["name"])}</a>' for i in DATA["industries"]], "marquee-reverse", 45)


LOGOS = [("odoo", "Odoo"), ("sap", "SAP"), ("postgresql", "PostgreSQL"), ("mysql", "MySQL"), ("googlecloud", "Google Cloud"), ("ubuntu", "Ubuntu")]


def logo_marquee():
    items = [f'<span class="marquee-item"><img src="./assets/partners/{f}.svg" alt="{n}" /></span>' for f, n in LOGOS]
    items += ['<span class="marquee-item"><img src="./assets/insa.svg" alt="INSA certified" /></span>',
              '<span class="marquee-item"><img src="./assets/mor.svg" alt="Ministry of Revenue accredited" /></span>']
    return marquee(items, "logo-strip", 35)


BEFORE = [
    "Spreadsheets and disconnected departmental tools",
    "Aging software that is hard to change",
    "Invoicing separated from the transaction behind it",
    "Information re-keyed manually between systems",
    "Management reports rebuilt by hand",
    "Unclear ownership of critical records",
]
AFTER = [
    "Finance, procurement, inventory, people and sales on one connected platform",
    "Electronic invoicing connected to ERP, finance, billing and POS",
    "Secure, monitored interfaces between critical systems",
    "Roles, permissions and traceable activity around every workflow",
    "Reporting built on information captured in daily operations",
    "Support from discovery through go-live and continuous improvement",
]


def compare_cards():
    before = "".join(f"<li>{e(x)}</li>" for x in BEFORE)
    after = "".join(f"<li>{e(x)}</li>" for x in AFTER)
    return f"""          <div class="compare-cards" data-stagger>
            <article class="compare-card">
              <p class="eyebrow">Before</p>
              <h3>Fragmented technology</h3>
              <ul>{before}</ul>
            </article>
            <article class="compare-card is-ours">
              <p class="eyebrow">With Hamerkop</p>
              <h3>Connected, governed systems</h3>
              <ul>{after}</ul>
            </article>
          </div>"""


MOCKS = {
    "invoices": ("EIMS · Invoice status", [("INV-0412", "Validated", ""), ("INV-0413", "Submitted", "is-info"), ("INV-0414", "Needs correction", "is-warn"), ("INV-0415", "Validated", "")]),
    "close": ("ERP · Month-end close", [("Purchase orders matched", "Done", ""), ("Stock reconciled", "Done", ""), ("Payroll posted", "In review", "is-info"), ("Management report", "Ready", "")]),
    "interfaces": ("Integrator · Interfaces", [("ERP ↔ EIMS", "Connected", ""), ("POS ↔ EIMS", "Connected", ""), ("Core banking ↔ Finance Suite", "Monitored", "is-info"), ("Legacy HR ↔ ERP", "Monitored", "is-info")]),
    "reconcile": ("Finance Suite · Reconciliation", [("Collections batch", "Matched", ""), ("Settlement file", "Matched", ""), ("Exceptions", "To review", "is-warn")]),
    "roles": ("Identity · Roles", [("Finance officer", "Approve invoices", "is-info"), ("Branch cashier", "Create receipts", "is-info"), ("Internal auditor", "Read only", "is-info")]),
    "reports": ("Insight · Executive reporting", [("Revenue by branch", "Updated", ""), ("Procurement spend", "Updated", ""), ("Budget vs actual", "Updated", "")]),
}


def ui_mock(key):
    """Illustrative interface card (workflow states only, no performance figures)."""
    title, rows = MOCKS[key]
    body = "".join(f'<div class="ui-row"><b>{e(a)}</b><span class="ui-status {c}">{e(b)}</span></div>' for a, b, c in rows)
    return f'<div class="ui-mock" aria-hidden="true"><div class="ui-mock-head">{e(title)}<span>Illustrative</span></div>{body}</div>'


TAGS = {
    "solution-erp": "Where operations connect",
    "solution-e-invoicing": "Where compliance lives",
    "solution-fintech": "Where transactions settle",
    "solution-identity": "Where trust begins",
    "solution-integration": "Where systems meet",
    "solution-data-ai": "Where decisions improve",
}


def bold_services():
    rows = []
    for n, sol in enumerate(DATA["solutions"]):
        bullets = "".join(f"<li>{e(t)}</li>" for t, _ in sol["capabilities"][:5])
        rows.append(f"""          <div class="bold-service{" is-flipped" if n % 2 else ""}">
            <article class="bold-service-card reveal">
              <span class="bold-tag">{e(TAGS[sol["slug"]])}</span>
              <h3>{e(sol["name"])}</h3>
              <p>{e(sol["summary"])}</p>
              <ul>{bullets}</ul>
              <a class="card-link" href="./{sol["slug"]}.html">Explore {e(sol["name"])} {ARROW}</a>
            </article>
            <figure class="bold-service-media reveal"><img src="{img(sol["image"], 1400)}" alt="" loading="lazy" /></figure>
          </div>""")
    return "\n".join(rows)


def bold_steps():
    return "\n".join(
        f"""            <article class="bold-step">
              <span class="bold-tag">Step 0{n}</span>
              <h3>{e(name)}</h3>
              <p>{e(full)}</p>
            </article>"""
        for n, (name, short, full) in enumerate(DATA["delivery"], 1)
    )


# ---------------------------------------------------------------- reference-faithful components

APPS = {
    "eims": ("Hamerkop EIMS", "Invoices", ["Dashboard", "Invoices", "Receipts", "Validation", "Reports", "Integrations", "Settings"],
             ["Document", "Source", "Status"],
             [("Sales invoice", "ERP · Head office", "Validated", ""), ("Sales invoice", "POS · Branch 01", "Validated", ""),
              ("Credit note", "ERP · Head office", "Submitted", "is-info"), ("Receipt", "POS · Branch 02", "Validated", ""),
              ("Sales invoice", "Billing", "Needs correction", "is-warn"), ("Receipt", "POS · Branch 03", "Submitted", "is-info"),
              ("Sales invoice", "ERP · Head office", "Validated", "")]),
    "erp": ("Hamerkop ERP", "Purchase requests", ["Dashboard", "Finance", "Purchase requests", "Inventory", "People", "Sales", "Reports"],
            ["Request", "Department", "Status"],
            [("Office supplies", "Administration", "Approved", ""), ("Laboratory reagents", "Operations", "In review", "is-info"),
             ("Vehicle maintenance", "Logistics", "Approved", ""), ("IT equipment", "Technology", "Awaiting budget", "is-warn"),
             ("Training services", "People", "Approved", ""), ("Packaging materials", "Production", "In review", "is-info")]),
}


def app_mock(kind):
    """A full application window (illustrative): sidebar navigation plus a document table."""
    product, current, nav, cols, rows = APPS[kind]
    side = "".join(f'<li{" class=is-current" if n == current else ""}>{e(n)}</li>' for n in nav)
    head = "".join(f"<span>{e(c)}</span>" for c in cols)
    body = "".join(
        f'<div class="app-row"><span><i>{e(a[:1])}</i>{e(a)}</span><span>{e(b)}</span><span><em class="ui-status {c}">{e(st)}</em></span></div>'
        for a, b, st, c in rows
    )
    return f"""<div class="app-window" aria-hidden="true">
              <aside class="app-side"><p class="app-brand"><img src="./assets/hamerkop-bird.svg" alt="" />{e(product)}</p><ul>{side}</ul></aside>
              <div class="app-main"><div class="app-top"><b>{e(current)}</b><span class="app-search">Search</span><span class="app-tag">Illustrative</span></div>
                <div class="app-row app-head">{head}</div>{body}</div>
            </div>"""


FAQ = [
    ("Getting started", "Where does an engagement with Hamerkop start?",
     "With the current operation: operational challenges, legacy system constraints, compliance and reporting requirements, existing systems and integration needs, and the sequence required to move to a stable working environment."),
    ("Getting started", "Who does Hamerkop work with?",
     "Organizations operating in complex or regulated environments, including private companies, financial institutions, government bodies, healthcare providers and development organizations."),
    ("Getting started", "What should we prepare before a consultation?",
     "Useful context includes your organization and sector, the operational challenge, existing systems, regulatory or reporting requirements, the number of entities, locations or users, important integration requirements and the expected timeline."),
    ("Delivery", "How does a Hamerkop implementation run?",
     "Every implementation moves through four stages: Discover, Design, Implement, and Stabilize & Improve, connecting the business requirement to architecture, go-live and continuous improvement."),
    ("Delivery", "Do you support systems after go-live?",
     "Yes. ERP Support covers incident resolution, maintenance, health reviews and continuous improvement, and Managed Services can operate defined technology environments through structured service arrangements."),
    ("Products", "Do you implement Odoo?",
     "Yes. Hamerkop is an Odoo Silver Partner, and Odoo forms part of our ERP implementation capability alongside Hamerkop ERP products and client-specific integrations."),
    ("Products", "Can Hamerkop EIMS work with our existing ERP or POS?",
     "EIMS manages electronic invoice and receipt processes while integrating them with ERP, accounting, billing and point-of-sale environments."),
]


def faq_items(tabs=False):
    groups = []
    for g, _, _ in FAQ:
        if g not in groups:
            groups.append(g)
    items = "\n".join(
        f"""            <details class="faq-item"{f' data-faq-group="{e(g)}"' if tabs else ""}{" hidden" if tabs and g != groups[0] else ""}>
              <summary>{e(q)}</summary>
              <p>{e(a)}</p>
            </details>"""
        for g, q, a in FAQ
    )
    if not tabs:
        return items
    buttons = "".join(
        f'<button type="button" data-faq-tab="{e(g)}" aria-pressed="{"true" if i == 0 else "false"}">{e(g)}</button>'
        for i, g in enumerate(groups)
    )
    return f'<div class="faq-tabs" role="group" aria-label="Question categories">{buttons}</div>\n{items}'


def editions_cards(featured="product-erp-business"):
    cards = []
    for p in DATA["products"]:
        if p["family"] != "erp" or p["slug"] == "product-erp-government":
            continue
        caps = "".join(f"<li>{e(c)}</li>" for c in p["capabilities"])
        hot = p["slug"] == featured
        demo = contact_url("demo", "Enterprise Systems & ERP", product=p["name"])
        cards.append(f"""            <article class="edition{" is-featured" if hot else ""}">
              <div class="edition-head"><span class="bold-tag">{e(p["name"])}</span>{'<span class="edition-flag">Most chosen</span>' if hot else ""}</div>
              <p class="edition-for">{e(p["designed_for"])}</p>
              <a class="button {"button-dark" if hot else "button-ghost"} edition-cta" href="{demo}">Request a Demo</a>
              <p class="edition-label">What's included</p>
              <ul>{caps}</ul>
            </article>""")
    return "\n".join(cards)


def dark_products():
    feature = next(p for p in DATA["products"] if p["slug"] == "product-erp-enterprise")
    chips = lambda caps: "".join(f"<span>{e(c)}</span>" for c in caps)
    eims_caps = ["Invoice workflows", "Validation", "Integration", "Traceability", "Reporting", "Access"]
    lead = f"""            <a class="glass-case glass-feature reveal" href="./product-eims.html">
              <div><h3>Hamerkop EIMS</h3><p class="glass-sub">Electronic Invoicing Management System</p>
                <p class="glass-text">Keep invoicing connected to the systems behind every transaction, from ERP and billing to point of sale.</p></div>
              <dl><div><dt>Category</dt><dd>Flagship product</dd></div><div><dt>Integrates with</dt><dd>ERP, finance, billing, POS</dd></div><div><dt>Delivery</dt><dd>Configuration, integration, rollout, training</dd></div></dl>
              <div class="glass-chips">{chips(eims_caps)}</div>
            </a>"""
    rows = []
    for slug in ["product-erp-enterprise", "product-integrator", "product-insight"]:
        p = next(x for x in DATA["products"] if x["slug"] == slug)
        rows.append(f"""            <a class="glass-case glass-row reveal" href="./{slug}.html">
              <div><p class="glass-sub">{e(p["eyebrow"])}</p><h3>{e(p["name"])}</h3><p class="glass-text">{e(p["headline"])}</p>
                <div class="glass-chips">{chips(p["capabilities"][:3])}</div></div>
              <img src="{img(p["image"], 800)}" alt="" loading="lazy" />
            </a>""")
    return lead + "\n" + "\n".join(rows)


def consult_form():
    """The consultation form from the contact page, for reuse on a homepage."""
    src = (SRC / "pages" / "contact.html").read_text(encoding="utf-8")
    start = src.index('<h2 id="form-title">')
    end = src.index("</div>", src.index('id="consult-success-text"')) + len("</div>")
    return src[start:end].replace("{{form_attrs}}", SNIPPETS["form_attrs"]())


# ---------------------------------------------------------------- Noir hub components

def noir_solution_explorer():
    """Huge numbered list; the pinned panel swaps photo and summary on hover/focus."""
    rows = "\n".join(
        f"""              <li>
                <a class="showcase-row{" is-active" if n == 0 else ""}" href="./{x["slug"]}.html" data-image="{img(x.get("hero", x["image"]), 1600)}">
                  <span class="showcase-index">{x["number"]}</span>
                  <span class="showcase-name">{e(x["name"])}</span>
                  <span class="showcase-text">{e(x["summary"])} <b>Explore &rarr;</b></span>
                </a>
              </li>"""
        for n, x in enumerate(DATA["solutions"])
    )
    first = DATA["solutions"][0]
    return f"""          <div class="showcase nx-explorer">
            <figure class="showcase-media"><img src="{img(first.get("hero", first["image"]), 1600)}" alt="" /></figure>
            <ol class="showcase-list">
{rows}
            </ol>
          </div>"""


def noir_service_track():
    cards = "\n".join(
        f"""              <a class="hs-card" href="./{x["slug"]}.html">
                <span class="hs-num">{x["number"]}</span>
                <figure><img src="{img(x.get("hero", x["image"]), 1200)}" alt="" loading="lazy" /></figure>
                <h3>{e(x["name"])}</h3>
                <p>{e(x["summary"])}</p>
                <span class="hs-more">Explore the service &rarr;</span>
              </a>"""
        for x in DATA["services"]
    )
    return f"""          <div class="hs-track">
{cards}
          </div>"""


def noir_timeline():
    steps = "\n".join(
        f"""            <li data-step>
              <span class="nx-step-dot" aria-hidden="true"></span>
              <span class="nx-step-num">0{n}</span>
              <h3>{e(name)}</h3>
              <p>{e(full)}</p>
            </li>"""
        for n, (name, short, full) in enumerate(DATA["delivery"], 1)
    )
    return f"""          <ol class="nx-timeline" data-progress-line>
{steps}
          </ol>"""


def noir_industry_mosaic():
    tiles = "\n".join(
        f"""            <a class="nx-tile nx-tile-{n}" href="./{x["slug"]}.html" data-tilt="5">
              <img src="{img(x["image"], 1200)}" alt="" loading="lazy" />
              <span class="nx-tile-body">
                <small>Industry {x["number"]}</small>
                <b>{e(x["name"])}</b>
                <em>{e(x["summary"])}</em>
              </span>
            </a>"""
        for n, x in enumerate(DATA["industries"], 1)
    )
    return f"""          <div class="nx-mosaic" data-stagger>
{tiles}
          </div>"""


SNIPPETS = {
    "solution_cards": solution_cards,
    "erp_products": lambda: products_by("erp"),
    "core_products": lambda: products_by("core"),
    "service_cards": service_cards,
    "industry_cards": industry_cards,
    "home_industry_cards": home_industry_cards,
    "delivery_steps": delivery_steps,
    "delivery_steps_long": lambda: delivery_steps(long=True),
    "insight_cards": insight_cards,
    "latest_articles": latest_articles,
    "home_insights": home_insights,
    "home_solution_cards": home_solution_cards,
    "product_showcase": product_showcase,
    "industry_scroller": industry_scroller,
    "spec_sheet": spec_sheet,
    "capability_marquee": capability_marquee,
    "capability_marquee_reverse": lambda: capability_marquee(True),
    "industry_marquee": industry_marquee,
    "logo_marquee": logo_marquee,
    "compare_cards": compare_cards,
    "bold_services": bold_services,
    "bold_steps": bold_steps,
    "app_eims": lambda: app_mock("eims"),
    "app_erp": lambda: app_mock("erp"),
    "faq_items": faq_items,
    "faq_tabbed": lambda: faq_items(True),
    "editions_cards": editions_cards,
    "dark_products": dark_products,
    "consult_form": consult_form,
    "noir_solution_explorer": noir_solution_explorer,
    "noir_service_track": noir_service_track,
    "noir_timeline": noir_timeline,
    "noir_industry_mosaic": noir_industry_mosaic,
    **{f"mock_{k}": (lambda k=k: ui_mock(k)) for k in MOCKS},
    "site_email": lambda: SITE["email"],
    "form_attrs": lambda: (
        f'data-email="{e(SITE["email"])}" data-routes="{e(json.dumps(SITE["routes"]))}"'
        + (f' data-endpoint="{e(SITE["form_endpoint"])}"' if SITE.get("form_endpoint") else "")
    ),
    "odoo_gallery_section": odoo_gallery_section,
    "odoo_gallery_home": odoo_gallery_home,
    "odoo_timeline": odoo_timeline,
    "odoo_stats": odoo_stats,
    "odoo_mark": odoo_mark,
    "odoo_days": lambda: str(DATA["odoo"]["days"]),
    "odoo_partner_link": lambda: (
        f'<a class="button button-ghost" href="{e(DATA["odoo"]["partner_url"])}" rel="noopener">View our Odoo partner listing</a>'
        if DATA["odoo"].get("partner_url") else ""
    ),
    "default_cta": default_cta,
    "arrow": lambda: ARROW,
}


# --------------------------------------------------------------------------- detail pages

def solution_page(s):
    designed = "".join(f"<li>{e(x)}</li>" for x in s["designed_for"])
    product_btn = [(f'./{s["product"][0]}.html', s["product"][1])] if s.get("product") else []
    body = "\n".join([
        page_hero(
            f'<a href="./solutions.html">Solutions</a> &middot; Solution {s["number"]}',
            s["headline"], s["lede"],
            actions((contact_url(interest=s["name"]), "Request a Consultation"), *product_btn),
            image=s.get("hero", s["image"]),
        ),
        f"""        <section class="page-band split-panel">
          <aside class="panel-dark reveal">
            <p class="eyebrow">Scope</p>
            <h2>{e(s["name"])}</h2>
            <p>{e(s["scope"])}</p>
          </aside>
          <div class="detail-card reveal">
            <p class="service-kicker">Designed for</p>
            <ul class="check-list">{designed}</ul>
          </div>
        </section>""",
        '        <section class="page-band">\n' + section_heading("Key capabilities", s["name"]) + "\n        </section>",
        info_cards(s["capabilities"]),
        odoo_note() if s.get("odoo") else "",
        default_cta(contact_url(interest=s["name"])),
    ])
    return layout(s["name"], s["summary"], "solutions", body, s["slug"])


def product_page(p):
    demo = contact_url("demo", PRODUCT_INTEREST.get(p["slug"], "Enterprise Systems & ERP"), product=p["name"])
    caps = "".join(f"<li>{e(c)}</li>" for c in p["capabilities"])
    designed = (
        f"""            <p class="service-kicker">Designed for</p>
            <p>{e(p["designed_for"])}</p>
""" if p.get("designed_for") else ""
    )
    body = "\n".join([
        page_hero(
            f'<a href="./products.html">Products</a> &middot; {e(p["label"])}',
            p["headline"], p["lede"],
            actions((demo, "Request a Demo"), ("./products.html", "All products")),
            extra=f'<p class="product-name">{e(p["eyebrow"])} &middot; {e(p["name"])}</p>\n            ',
        ),
        f"""        <section class="page-band split-panel">
          <div class="story-media reveal">
            <img src="{img(p["image"], 1600)}" alt="{e(p["name"])}" />
          </div>
          <div class="detail-card reveal">
{designed}            <p class="service-kicker">{e(p["focus_title"])}</p>
            <p>{e(p["focus"])}</p>
            <p class="service-kicker">Core capabilities</p>
            <ul class="pill-list">{caps}</ul>
          </div>
        </section>""",
        odoo_note() if p["family"] == "erp" else "",
        cta(p["name"], f'See {p["name"]} in your operating context.',
            "Tell us about your organization, current systems and requirements and we will arrange a focused demonstration.",
            (demo, "Request a Demo")),
    ])
    return layout(p["name"], p["lede"], "products", body, p["slug"])


def service_page(s):
    consult = contact_url(interest=SERVICE_INTEREST.get(s["slug"], "Enterprise Systems & ERP"))
    body = "\n".join([
        page_hero(
            f'<a href="./services.html">Services</a> &middot; Service {s["number"]}',
            s["headline"], s["lede"],
            actions((consult, "Request a Consultation"), ("./services.html", "All services")),
            extra=f'<p class="product-name">Hamerkop Services &middot; {e(s["name"])}</p>\n            ',
            image=s.get("hero", s["image"]),
        ),
        f"""        <section class="page-band split-panel">
          <div class="story-media reveal">
            <img src="{img(s["image"], 1600)}" alt="{e(s["name"])}" />
          </div>
          <div class="detail-card reveal">
            <p class="service-kicker">Service scope</p>
            <h2>{e(s["name"])}</h2>
            <p>{e(s["summary"])}</p>
          </div>
        </section>""",
        info_cards(s["scope"]),
        odoo_note() if s.get("odoo") else "",
        default_cta(consult),
    ])
    return layout(s["name"], s["summary"], "services", body, s["slug"])


def industry_page(i):
    consult = contact_url(industry=i["name"])
    caps = "".join(f"<li>{e(c)}</li>" for c in i["capabilities"])
    body = "\n".join([
        page_hero(
            f'<a href="./industries.html">Industries</a> &middot; Industry {i["number"]}',
            i["headline"], i["lede"],
            actions((consult, "Request a Consultation"), ("./industries.html", "All industries")),
            extra=f'<p class="product-name">{e(i["name"])}</p>\n            ',
            image=i.get("hero", i["image"]),
        ),
        f"""        <section class="page-band split-panel">
          <div class="story-media reveal">
            <img src="{img(i["image"], 1600)}" alt="{e(i["alt"])}" />
          </div>
          <div class="detail-card reveal">
            <p class="service-kicker">Relevant Hamerkop capabilities</p>
            <ul class="pill-list">{caps}</ul>
          </div>
        </section>""",
        '        <section class="page-band">\n' + section_heading("Operational focus", i["name"]) + "\n        </section>",
        info_cards(i["focus"]),
        default_cta(consult),
    ])
    return layout(i["name"], i["summary"], "industries", body, i["slug"])


# --------------------------------------------------------------------------- one-off pages

FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def render_page(path, slug=None):
    raw = path.read_text(encoding="utf-8")
    m = FRONT.match(raw)
    meta = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    body = raw[m.end():]

    def sub(match):
        key = match.group(1)
        if key not in SNIPPETS:
            raise KeyError(f"{path.name}: unknown snippet {{{{{key}}}}}")
        return SNIPPETS[key]()

    body = re.sub(r"\{\{(\w+)\}\}", sub, body)
    if ACTIVE and ACTIVE.get("image_heroes") and meta.get("hero_image") and '<section class="hero page-hero">' in body:
        body = body.replace(
            '<section class="hero page-hero">',
            f'<section class="hero page-hero has-image is-art" data-pointer-parallax>\n          <img class="page-hero-bg" src="{img(meta["hero_image"], 2400)}" alt="" />',
            1,
        ).replace('<div class="hero-copy reveal">', '<div class="hero-copy" data-scroll-out>', 1)
    return layout(meta["title"], meta["description"], meta.get("nav", ""), body, slug or path.stem)


def render_all():
    out = {}
    for p in sorted((SRC / "pages").glob("*.html")):
        override = SRC / "designs" / f'{ACTIVE["key"]}-{p.stem}.html' if ACTIVE else None
        out[p.name] = render_page(override if override and override.exists() else p, p.stem)
    if ACTIVE:
        home = SRC / "designs" / f'{ACTIVE["key"]}-home.html'
        if home.exists():
            out["index.html"] = render_page(home)
    for s in DATA["solutions"]:
        out[f'{s["slug"]}.html'] = solution_page(s)
    for p in DATA["products"]:
        out[f'{p["slug"]}.html'] = product_page(p)
    for s in DATA["services"]:
        out[f'{s["slug"]}.html'] = service_page(s)
    for i in DATA["industries"]:
        out[f'{i["slug"]}.html'] = industry_page(i)
    for c in DATA["insight_categories"]:
        out[f'{c["slug"]}.html'] = category_page(c)
    for a in ARTICLES:
        out[f'article-{a["slug"]}.html'] = article_page(a)
    return out


def build_designs(target):
    """Render every page once per design direction, plus a comparison page."""
    global ACTIVE
    target = (ROOT / target).resolve()
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", target / "assets")
    shutil.copy(ROOT / "styles.css", target / "styles.css")
    shutil.copy(ROOT / "main.js", target / "main.js")
    total = 0
    for design in DESIGNS:
        ACTIVE = design
        folder = target / design["key"]
        folder.mkdir()
        if design["key"] != "editorial":
            shutil.copy(SRC / "designs" / f'{design["key"]}.css', folder / "design.css")
        for name, html in render_all().items():
            if name == "404.html":
                continue
            html = (html.replace('href="./styles.css', 'href="../styles.css')
                        .replace('src="./main.js', 'src="../main.js')
                        .replace('"./assets/', '"../assets/'))
            (folder / name).write_text(html, encoding="utf-8")
            total += 1
    ACTIVE = None
    (target / "index.html").write_text(compare_page(), encoding="utf-8")
    print(f"Built {total} pages across {len(DESIGNS)} design directions in {target}.")


def compare_page():
    cards = []
    options = "".join(f'<option value="{d["key"]}">{d["name"]}</option>' for d in DESIGNS)
    for d in DESIGNS:
        swatches = "".join(f'<span style="background:{c}" title="{c}"></span>' for c in d["swatches"])
        cards.append(f"""      <article class="dir">
        <a class="thumb" href="./{d["key"]}/index.html" aria-label="Open the {d["name"]} direction">
          <iframe src="./{d["key"]}/index.html" title="{d["name"]} homepage preview" loading="lazy" tabindex="-1" scrolling="no"></iframe>
        </a>
        <div class="dir-body">
          <div class="dir-head"><h2>{d["name"]}</h2><span class="swatches">{swatches}</span></div>
          <p>{e(d["summary"])}</p>
          <dl>
            <div><dt>Type</dt><dd>{e(d["type"])}</dd></div>
            <div><dt>Inspired by</dt><dd><a href="{d["ref"]}" target="_blank" rel="noopener">{d["ref_name"]} &#8599;</a></dd></div>
          </dl>
          <div class="dir-actions">
            <a class="btn" href="./{d["key"]}/index.html">Open full site</a>
            <a class="btn btn-ghost" href="./{d["key"]}/solution-erp.html">Inner page</a>
          </div>
        </div>
      </article>""")
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="robots" content="noindex" />
    <title>Design directions | Hamerkop Systems</title>
    <link rel="icon" href="./assets/hamerkop-bird.svg" type="image/svg+xml" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet" />
    <style>
      :root {{ --bg:#f4f4f2; --card:#fff; --ink:#151515; --muted:#666; --line:#e3e3e0; color-scheme: light; }}
      * {{ box-sizing: border-box; }}
      body {{ margin:0; font-family:Inter, system-ui, sans-serif; background:var(--bg); color:var(--ink); }}
      a {{ color:inherit; }}
      .wrap {{ width:min(1360px, calc(100vw - 32px)); margin:0 auto; padding:48px 0 80px; }}
      header {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:flex-end; gap:24px; margin-bottom:36px; }}
      .brand {{ display:flex; align-items:center; gap:10px; font-weight:600; }}
      .brand img {{ height:28px; }}
      h1 {{ margin:18px 0 8px; font-size:clamp(2rem, 4vw, 3.2rem); letter-spacing:-0.035em; line-height:1.05; }}
      header p {{ margin:0; max-width:60ch; color:var(--muted); line-height:1.6; }}
      .live {{ font-size:.92rem; color:var(--muted); }}
      .live a {{ font-weight:600; color:var(--ink); }}
      .grid {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:20px; }}
      .dir {{ overflow:hidden; border:1px solid var(--line); border-radius:20px; background:var(--card); }}
      .thumb {{ position:relative; display:block; aspect-ratio:16/10; overflow:hidden; border-bottom:1px solid var(--line); background:#ddd; }}
      .thumb iframe {{ position:absolute; top:0; left:0; width:1440px; height:900px; border:0; pointer-events:none; transform-origin:0 0; }}
      .dir-body {{ padding:22px; }}
      .dir-head {{ display:flex; justify-content:space-between; align-items:center; gap:12px; }}
      .dir h2 {{ margin:0; font-size:1.5rem; letter-spacing:-0.02em; }}
      .dir p {{ margin:10px 0 0; color:var(--muted); line-height:1.6; }}
      .swatches {{ display:flex; }}
      .swatches span {{ width:22px; height:22px; margin-left:-6px; border:2px solid #fff; border-radius:50%; box-shadow:0 0 0 1px var(--line); }}
      dl {{ display:flex; flex-wrap:wrap; gap:28px; margin:16px 0 0; }}
      dt {{ font-size:.75rem; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); }}
      dd {{ margin:4px 0 0; font-weight:500; }}
      .dir-actions {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:20px; }}
      .btn {{ display:inline-flex; align-items:center; min-height:42px; padding:0 18px; border-radius:999px; background:var(--ink); color:#fff; font-weight:500; font-size:.92rem; text-decoration:none; }}
      .btn-ghost {{ background:transparent; color:var(--ink); box-shadow:inset 0 0 0 1px var(--line); }}
      .compare {{ margin-top:56px; }}
      .compare-head {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:16px; margin-bottom:16px; }}
      .compare h2 {{ margin:0; font-size:1.6rem; letter-spacing:-0.02em; }}
      .controls {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; }}
      select {{ min-height:42px; padding:0 12px; border:1px solid var(--line); border-radius:10px; background:#fff; font:inherit; }}
      .panes {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
      .pane {{ position:relative; height:78vh; overflow:hidden; border:1px solid var(--line); border-radius:16px; background:#fff; }}
      .pane iframe {{ width:100%; height:100%; border:0; }}
      .pane-label {{ position:absolute; top:10px; left:10px; z-index:1; padding:4px 10px; border-radius:999px; background:rgba(21,21,21,.85); color:#fff; font-size:.8rem; }}
      @media (max-width: 900px) {{ .grid, .panes {{ grid-template-columns:1fr; }} .pane {{ height:70vh; }} }}
    </style>
  </head>
  <body>
    <div class="wrap">
      <header>
        <div>
          <span class="brand"><img src="./assets/hamerkop-bird.svg" alt="" /> Hamerkop Systems</span>
          <h1>Design directions</h1>
          <p>Four complete versions of the new Hamerkop website. Content and pages are identical; only the design system changes. Open any direction to browse the full site, or compare two side by side below.</p>
        </div>
        <p class="live">Current live site: <a href="{SITE["url"]}">{SITE["url"].replace("https://", "")}</a></p>
      </header>

      <section class="grid">
{chr(10).join(cards)}
      </section>

      <section class="compare" aria-labelledby="compare-title">
        <div class="compare-head">
          <h2 id="compare-title">Side by side</h2>
          <div class="controls">
            <label>Left <select id="left">{options}</select></label>
            <label>Right <select id="right">{options}</select></label>
            <label>Page <select id="page">
              <option value="index.html">Home</option>
              <option value="solution-erp.html">Solution page</option>
              <option value="product-eims.html">EIMS product</option>
              <option value="partnership-odoo.html">Odoo partnership</option>
              <option value="insights.html">Insights</option>
              <option value="contact.html">Contact</option>
            </select></label>
          </div>
        </div>
        <div class="panes">
          <div class="pane"><span class="pane-label" id="left-label"></span><iframe id="left-frame" title="Left design"></iframe></div>
          <div class="pane"><span class="pane-label" id="right-label"></span><iframe id="right-frame" title="Right design"></iframe></div>
        </div>
      </section>
    </div>
    <script>
      // Scale the 1440px-wide homepage previews to fit their cards.
      const fit = () => document.querySelectorAll(".thumb").forEach((t) => {{
        t.querySelector("iframe").style.transform = `scale(${{t.clientWidth / 1440}})`;
      }});
      fit();
      window.addEventListener("resize", fit);

      const left = document.getElementById("left"), right = document.getElementById("right"), page = document.getElementById("page");
      right.selectedIndex = 1;
      const show = () => {{
        for (const [select, side] of [[left, "left"], [right, "right"]]) {{
          document.getElementById(`${{side}}-frame`).src = `./${{select.value}}/${{page.value}}`;
          document.getElementById(`${{side}}-label`).textContent = select.options[select.selectedIndex].text;
        }}
      }};
      [left, right, page].forEach((el) => el.addEventListener("change", show));
      show();
    </script>
  </body>
</html>
"""


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--designs":
        build_designs(sys.argv[2])
        return
    out = render_all()

    # Search-engine files. The 404 page is left out of the sitemap.
    pages = sorted(n for n in out if n != "404.html")
    urls = "\n".join(
        f"  <url><loc>{SITE['url']}{'' if n == 'index.html' else n}</loc></url>" for n in pages
    )
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n',
        encoding="utf-8",
    )
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}sitemap.xml\n", encoding="utf-8")

    for name, html in out.items():
        (ROOT / name).write_text(html, encoding="utf-8")
    print(f"Built {len(out)} pages.")


if __name__ == "__main__":
    main()
