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
    return f"""      <header class="topbar">
        <a class="brand" href="./index.html" aria-label="Hamerkop System S.C. home">
          <img class="brand-mark" src="./assets/hamerkop-bird.svg" alt="" />
          <span class="brand-name">
            <strong>Hamerkop</strong>
            <span>System S.C.</span>
          </span>
        </a>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Menu">
          <span></span><span></span><span></span>
        </button>
        <nav id="site-nav" class="site-nav" aria-label="Primary">
{links}
          <a href="./contact.html" class="nav-cta">Request a Consultation</a>
        </nav>
      </header>"""


def footer():
    solutions = "\n".join(
        f'                <a href="./{s["slug"]}.html">{e(s["name"])}</a>' for s in DATA["solutions"]
    )
    return f"""      <footer class="site-footer">
        <div class="footer-grid">
          <div class="footer-brand">
            <img class="footer-logo" src="./assets/hamerkop-logo.svg" alt="Hamerkop System S.C." />
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
            <p class="footer-title">Contact</p>
            <div class="footer-contact">
              <span>Addis Ababa, Ethiopia</span>
              <a href="mailto:{SITE["email"]}">{SITE["email"]}</a>
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
      </footer>"""


def layout(title, description, nav, body, slug):
    full_title = "Hamerkop Systems — Enterprise Technology Solutions" if nav == "home" else f"{title} | Hamerkop Systems"
    url = SITE["url"] + ("" if slug == "index" else f"{slug}.html")
    # The 404 page is served at whatever path was requested, so pin its relative links to the site root.
    head_extra = (
        f'<base href="{SITE["url"]}" />\n    <meta name="robots" content="noindex" />'
        if slug == "404" else f'<link rel="canonical" href="{url}" />\n    <meta property="og:url" content="{url}" />'
    )
    return f"""<!doctype html>
<!-- Generated by build.py from src/. Edit the source files, then run: python3 build.py -->
<html lang="en">
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
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@1,500;1,600&display=swap"
      rel="stylesheet"
    />
    <link rel="icon" href="./assets/hamerkop-bird.svg" type="image/svg+xml" />
    <meta name="theme-color" content="#f4ede6" />
    <link rel="stylesheet" href="./styles.css?v={CSS_V}" />
    <noscript><style>.reveal{{opacity:1;transform:none}}</style></noscript>
    <script defer src="./main.js?v={JS_V}"></script>
  </head>
  <body>
    <div class="page-shell">
      <a class="skip-link" href="#main">Skip to main content</a>
      <div class="ambient ambient-left"></div>
      <div class="ambient ambient-right"></div>
{header(nav, slug)}

      <main id="main" tabindex="-1">
{body.strip()}
      </main>
{footer()}
    </div>
  </body>
</html>
"""


# --------------------------------------------------------------------------- shared blocks

def page_hero(eyebrow, h1, lede, actions="", extra=""):
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


def article_card(a):
    media = (
        f'<div class="service-visual"><img src="{img(a["image"], 1200)}" alt="" loading="lazy" /></div>\n            '
        if a.get("image") else ""
    )
    return f"""          <a class="feature-card article-card reveal" href="./article-{a["slug"]}.html">
            {media}<p class="service-kicker">{e(CATEGORIES[a["category"]]["name"])}</p>
            <h3>{e(a["title"])}</h3>
            <p>{e(a["summary"])}</p>
            <p class="article-meta"><time datetime="{a["date"]}">{fmt_date(a["date"])}</time></p>
            <span class="card-link">Read article {ARROW}</span>
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
          <div class="feature-grid">
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
        listing = '        <section class="page-band feature-grid">\n' + "\n".join(article_card(a) for a in articles) + "\n        </section>"
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
        page_hero('<a href="./insights.html">Insights</a> &middot; Category', c["name"], c["description"]),
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
        if a.get("image") else ""
    )
    related = [x for x in ARTICLES if x["category"] == a["category"] and x is not a][:3]
    related_html = (
        '        <section class="page-band">\n' + section_heading("Related", f'More on {c["name"]}')
        + '\n          <div class="feature-grid">\n' + "\n".join(article_card(x) for x in related) + "\n          </div>\n        </section>\n"
        if related else ""
    )
    body = f"""        <article class="article">
          <header class="hero page-hero">
            <div class="hero-copy reveal">
              <p class="eyebrow"><a href="./insights.html">Insights</a> &middot; <a href="./{c["slug"]}.html">{e(c["name"])}</a></p>
              <h1>{e(a["title"])}</h1>
              <p class="lede">{e(a["summary"])}</p>
              <p class="article-meta"><time datetime="{a["date"]}">{fmt_date(a["date"])}</time>{author}</p>
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


def render_page(path):
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
    return layout(meta["title"], meta["description"], meta.get("nav", ""), body, path.stem)


def main():
    out = {}
    for p in sorted((SRC / "pages").glob("*.html")):
        out[p.name] = render_page(p)
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
