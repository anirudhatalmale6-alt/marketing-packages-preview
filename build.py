#!/usr/bin/env python3
"""
Static site generator for the marketing-packages catalogue.

    python3 build.py

Reads data/packages.json, writes plain HTML into site/. No frameworks, no build
chain, no node_modules — the output is the deliverable and can be dropped onto
any host (or GitHub Pages) as-is.

Edit the copy in data/packages.json, re-run this, re-upload. That is the whole
workflow. The generated HTML is committed too, so the site works even if nobody
ever runs Python again.
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
PKGDIR = os.path.join(SITE, "packages")

with open(os.path.join(ROOT, "data", "packages.json")) as fh:
    DATA = json.load(fh)

S = DATA["site"]
PACKAGES = DATA["packages"]
BRAND = S["brand"]
BRAND_FULL = f'{S["brand"]} {S["brandSuffix"]}'.strip()
BASE = S["domain"].rstrip("/")
CUR = S["currency"]

e = html.escape


def money(n):
    return f"{CUR}{n:,}"


NUMWORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
            7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def count_word(cap=False):
    """The package count, spelled out.

    Hard-coding "six packages" in the hero meant that dropping a package left
    three separate places on the home page quietly lying. Anything that states
    the count now derives it.
    """
    n = len(PACKAGES)
    w = NUMWORDS.get(n, str(n))
    return w.capitalize() if cap else w


def pay_link(p, fallback_prefix=""):
    """A package's checkout destination.

    Drop the real Stripe / PayPal / Paddle payment link into "payLink" in
    data/packages.json and it is used verbatim. Until then every buy button
    lands on checkout.html, which explains the flow instead of 404-ing.
    `fallback_prefix` only applies to that stand-in page — an absolute payment
    URL is never rewritten.
    """
    link = (p.get("payLink") or "").strip()
    return link if link else f"{fallback_prefix}checkout.html?pkg={p['slug']}"


# --- shared chrome ---------------------------------------------------------

def fonts(prefix):
    """Self-hosted, subset webfonts — see tools/fetch_fonts.py.

    The two faces that render above the fold are preloaded; the rest arrive with
    the stylesheet. No request ever leaves the site's own domain.
    """
    return (
        f'<link rel="preload" href="{prefix}assets/fonts/bricolage-normal.woff2" as="font" '
        'type="font/woff2" crossorigin>'
        f'<link rel="preload" href="{prefix}assets/fonts/newsreader-normal.woff2" as="font" '
        'type="font/woff2" crossorigin>'
        f'<link rel="stylesheet" href="{prefix}assets/css/fonts.css">'
    )

ANALYTICS = """<!-- ANALYTICS
     Paste your GA4 or Plausible snippet here and every button on the site
     starts reporting automatically — the tracking calls in main.js detect
     whichever one is present. Nothing else needs changing.

<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
-->"""


def head(title, desc, path, prefix, extra_ld=""):
    canonical = f"{BASE}/{path}" if path else f"{BASE}/"
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#f6f3ec">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(BRAND_FULL)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
{fonts(prefix)}
<link rel="stylesheet" href="{prefix}assets/css/style.css">
{extra_ld}
{ANALYTICS}"""


def header(prefix, current=""):
    def item(label, href, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    return f"""<header class="site-head">
  <div class="site-head__in">
    <a class="brand" href="{prefix}index.html">
      <b>{e(BRAND)}</b><i></i><small>{e(S["brandSuffix"])}</small>
    </a>
    <nav class="nav" id="nav" aria-label="Main">
      {item("Packages", prefix + "index.html#packages", "packages")}
      {item("How it works", prefix + "index.html#process", "process")}
      {item("Results", prefix + "index.html#proof", "proof")}
      {item("Questions", prefix + "index.html#faq", "faq")}
    </nav>
    <a class="btn head-cta" href="{prefix}index.html#packages"
       data-track="nav_cta_click" data-where="header"><span>Browse packages</span></a>
    <button class="burger" type="button" aria-label="Menu" aria-expanded="false" aria-controls="nav">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>"""


def footer(prefix):
    links = "".join(
        f'<li><a href="{prefix}packages/{p["slug"]}.html">{e(p["name"])}</a></li>' for p in PACKAGES
    )
    return f"""<footer class="site-foot">
  <div class="wrap">
    <div class="foot__grid">
      <div>
        <div class="foot__brand">{e(BRAND_FULL)}</div>
        <p>{e(S["tagline"])} — priced in public, delivered on a date.</p>
      </div>
      <div>
        <h4>Packages</h4>
        <ul>{links}</ul>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="{prefix}index.html#process">How it works</a></li>
          <li><a href="{prefix}index.html#proof">Results</a></li>
          <li><a href="{prefix}index.html#faq">Questions</a></li>
          <li><a href="{prefix}index.html#contact">Get in touch</a></li>
        </ul>
      </div>
      <div>
        <h4>Legal</h4>
        <ul>
          <li><a href="{prefix}terms.html">Terms</a></li>
          <li><a href="{prefix}privacy.html">Privacy</a></li>
        </ul>
      </div>
    </div>
    <div class="foot__base">
      <span>&copy; <span id="year">2026</span> {e(BRAND_FULL)}</span>
      <span>Secure card payments</span>
    </div>
  </div>
</footer>
<script src="{prefix}assets/js/main.js" defer></script>"""


def page(title, desc, path, prefix, body, current="", extra_ld=""):
    return f"""<!doctype html>
<html lang="en">
<head>
{head(title, desc, path, prefix, extra_ld)}
</head>
<body>
{header(prefix, current)}
<main id="main">
{body}
</main>
{footer(prefix)}
</body>
</html>
"""


# --- home page ------------------------------------------------------------

def card(p, prefix=""):
    inc = "".join(f"<li>{e(x)}</li>" for x in p["includes"][:4])
    tag = (
        f'<span class="card__tag{" card__tag--quiet" if p.get("tagStyle") != "signal" else ""}">{e(p["tag"])}</span>'
        if p.get("tag")
        else ""
    )
    return f"""<article class="card" data-rise="1" data-package-view="{e(p["name"])}">
  <div class="card__top">
    <span class="card__no">PKG {e(p["no"])}</span>{tag}
  </div>
  <div class="card__art">
    <img src="{prefix}assets/img/{p["slug"]}-card.svg" width="1200" height="750" loading="lazy"
         alt="{e(p["name"])} package artwork">
  </div>
  <h3>{e(p["name"])}</h3>
  <p class="card__sub">{e(p["oneLiner"])}</p>
  <ul class="card__inc">{inc}</ul>
  <div class="card__foot">
    <div class="price">{money(p["price"])}<small>{e(p["priceNote"])}</small></div>
    <div class="card__links">
      <a class="go" href="{prefix}packages/{p["slug"]}.html"
         data-track="view_package" data-package="{e(p["name"])}" data-where="catalogue">Details</a>
      <a class="buy" href="{pay_link(p, prefix + "packages/")}" rel="noopener"
         data-track="begin_checkout" data-package="{e(p["name"])}"
         data-price="{p["price"]}" data-where="catalogue">Buy now</a>
    </div>
  </div>
</article>"""


def home():
    cards = "".join(card(p) for p in PACKAGES)
    steps = "".join(
        f'<div class="step" data-rise="{min(i+1,4)}"><b>{i+1:02d}</b>'
        f"<h3>{e(t)}</h3><p>{e(d)}</p></div>"
        for i, (t, d) in enumerate(DATA["steps"])
    )
    stats = "".join(
        f'<div data-rise="{min(i+1,4)}"><div class="proof__n">{e(n)}</div>'
        f'<div class="proof__l">{e(l)}</div></div>'
        for i, (n, l) in enumerate(DATA["stats"])
    )
    quotes = "".join(
        f'<figure class="quote" data-rise="{min(i+1,4)}"><blockquote>{e(q)}</blockquote>'
        f"<cite>{e(src)}</cite></figure>"
        for i, (q, src) in enumerate(DATA["quotes"])
    )
    faqs = "".join(
        f"<details{' open' if i == 0 else ''}><summary>{e(q)}</summary><p>{e(a)}</p></details>"
        for i, (q, a) in enumerate(DATA["faq"])
    )
    ticker_words = [
        "Fixed prices",
        "No sales calls",
        "Pay by card",
        "Delivered on a date",
        f"{count_word(cap=True)} packages",
        "Start this week",
    ]
    ticker = "".join(f"<span>{e(w)}</span>" for w in ticker_words)

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{BASE}/#org",
                "name": BRAND_FULL,
                "url": f"{BASE}/",
                "description": S["tagline"],
            },
            {
                "@type": "WebSite",
                "@id": f"{BASE}/#site",
                "url": f"{BASE}/",
                "name": BRAND_FULL,
                "publisher": {"@id": f"{BASE}/#org"},
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in DATA["faq"]
                ],
            },
            {
                "@type": "ItemList",
                "name": "Marketing packages",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "url": f"{BASE}/packages/{p['slug']}.html",
                        "name": p["name"],
                    }
                    for i, p in enumerate(PACKAGES)
                ],
            },
        ],
    }

    body = f"""<section class="hero">
  <div class="wrap hero__grid">
    <div>
      <p class="eyebrow" data-boot="1">{e(S["tagline"])}</p>
      <h1 data-boot="2">Marketing that is <em>already built.</em><br>Pick it, pay it, run it.</h1>
      <p class="lede" data-boot="3">{count_word(cap=True)} packages with the price on the front and the deliverables
        written down. No discovery call, no proposal deck, no three weeks waiting on a quote.</p>
      <div class="hero__actions" data-boot="4" style="margin-top:2rem">
        <a class="btn btn--signal" href="#packages" data-track="hero_cta_click" data-where="hero">
          <span>See the {count_word()} packages</span> <span class="arr">→</span>
        </a>
        <a class="btn btn--ghost" href="#process" data-track="hero_secondary_click"><span>How it works</span></a>
      </div>
    </div>
    <dl class="hero__facts" data-boot="4">
      <div><dt>From</dt><dd>{money(min(p["price"] for p in PACKAGES))}</dd></div>
      <div><dt>Kick-off</dt><dd>48 hours</dd></div>
      <div><dt>Contract</dt><dd>None</dd></div>
    </dl>
  </div>
</section>

<div class="ticker" aria-hidden="true">
  <div class="ticker__track">{ticker}{ticker}</div>
</div>

<section class="sec" id="packages">
  <div class="wrap">
    <div class="sec__head">
      <div>
        <p class="eyebrow">The catalogue</p>
        <h2>Everything we sell, on one page</h2>
      </div>
      <p class="lede">Each package is a fixed scope at a fixed price. Open one to read the full
        deliverables, or buy straight from here if you already know what you need.</p>
    </div>
    <div class="cards">{cards}</div>
  </div>
</section>

<section class="sec" id="process" style="padding-top:0">
  <div class="wrap">
    <div class="sec__head">
      <div>
        <p class="eyebrow">How it works</p>
        <h2>Four steps, no meetings</h2>
      </div>
      <p class="lede">The whole point of a ready-made package is that the scoping has
        already happened. Here is everything that stands between you and the work starting.</p>
    </div>
    <div class="steps">{steps}</div>
  </div>
</section>

<section class="sec proof" id="proof">
  <div class="wrap">
    <div class="sec__head" style="margin-bottom:2.5rem">
      <div>
        <p class="eyebrow">By the numbers</p>
        <h2 style="color:var(--paper)">Boring, measurable, repeatable</h2>
      </div>
    </div>
    <div class="proof__grid">{stats}</div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec__head">
      <div>
        <p class="eyebrow">What clients say</p>
        <h2>In their words</h2>
      </div>
    </div>
    <div class="quotes">{quotes}</div>
  </div>
</section>

<section class="sec" id="faq" style="padding-top:0">
  <div class="wrap">
    <div class="sec__head">
      <div>
        <p class="eyebrow">Questions</p>
        <h2>The things people ask before paying</h2>
      </div>
      <p class="lede">If something is not answered here, send it over before you buy —
        we would rather turn work down than take money for the wrong package.</p>
    </div>
    <div class="faq">{faqs}</div>
  </div>
</section>

<section class="cta" id="contact">
  <div class="wrap sec cta__in">
    <div>
      <p class="eyebrow">Ready when you are</p>
      <h2>Pick a package and<br>we start this week.</h2>
      <p>Payment is a single card transaction on the package page. The intake form
        arrives in minutes and work begins the same working day.</p>
    </div>
    <a class="btn" href="#packages" data-track="footer_cta_click" data-where="closing">
      <span>Browse the catalogue</span> <span class="arr">→</span>
    </a>
  </div>
</section>"""

    ld_tag = f'<script type="application/ld+json">{json.dumps(ld, separators=(",", ":"))}</script>'
    return page(
        f"{BRAND_FULL} — {S['tagline']} with prices up front",
        "Six ready-made marketing packages with fixed prices and written deliverables. "
        "Pick one, pay by card, and work starts the same working day. No sales calls, no proposals.",
        "",
        "",
        body,
        current="packages",
        extra_ld=ld_tag,
    )


# --- package pages --------------------------------------------------------

def package_page(p, idx):
    deliver = "".join(
        f"<li><b>{e(n)}</b><span>{e(t)}</span></li>" for n, t in p["deliverables"]
    )
    incl = "".join(f"<li>{e(x)}</li>" for x in p["includes"])
    faqs = "".join(
        f"<details{' open' if i == 0 else ''}><summary>{e(q)}</summary><p>{e(a)}</p></details>"
        for i, (q, a) in enumerate(p["faq"])
    )
    others = "".join(
        f'<a href="{o["slug"]}.html" data-track="cross_sell_click" data-package="{e(o["name"])}">'
        f'<b>{e(o["name"])}</b><em>{money(o["price"])} · {e(o["priceNote"])}</em></a>'
        for o in PACKAGES
        if o["slug"] != p["slug"]
    )

    ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["name"],
        "description": p["oneLiner"],
        "sku": f"PKG-{p['no']}",
        "brand": {"@type": "Brand", "name": BRAND_FULL},
        "image": f"{BASE}/assets/img/{p['slug']}-wide.svg",
        "offers": {
            "@type": "Offer",
            "price": p["price"],
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": f"{BASE}/packages/{p['slug']}.html",
        },
    }
    crumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Packages", "item": f"{BASE}/#packages"},
            {"@type": "ListItem", "position": 3, "name": p["name"]},
        ],
    }
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in p["faq"]
        ],
    }
    ld_tag = "".join(
        f'<script type="application/ld+json">{json.dumps(x, separators=(",", ":"))}</script>'
        for x in (ld, crumb_ld, faq_ld)
    )

    body = f"""<div class="wrap">
  <p class="crumb"><a href="../index.html">Home</a> / <a href="../index.html#packages">Packages</a> / {e(p["name"])}</p>
</div>

<section class="pkg-hero">
  <div class="wrap">
    <span class="pkg-hero__no" aria-hidden="true">{e(p["no"])}</span>
    <p class="eyebrow">{e(p.get("tag", "Package"))} · {e(p["turnaround"])}</p>
    <h1>{e(p["name"])}</h1>
    <p class="lede">{e(p["oneLiner"])}</p>
  </div>
</section>

<div class="wrap pkg-body">
  <div>
    <img class="pkg-shot" src="../assets/img/{p["slug"]}-wide.svg" width="1600" height="760"
         alt="{e(p["name"])} package artwork">
    <div class="prose">
      <p class="first">{e(p["summary"])}</p>

      <h2>Who this is for</h2>
      <p>{e(p["who"])}</p>

      <h2>What you get</h2>
      <p>Five deliverables, each with a name and a date. Nothing on this list is conditional.</p>
      <ul class="deliver">{deliver}</ul>

      <h2>How this one runs</h2>
      <p>You pay the link on this page. Within a few minutes you get a receipt and a short intake
        form — usually six or seven questions. The moment that comes back, the clock starts on the
        turnaround quoted at the top of this page, and you get a single point of contact who is
        also the person doing the work.</p>
      <blockquote>If we miss the date for a reason that is ours, you are not billed for the overrun
        and we say so before you have to ask.</blockquote>

      <h2>Questions about {e(p["name"])}</h2>
      <div class="faq">{faqs}</div>
    </div>
  </div>

  <aside class="buybox">
    <div class="buybox__top">
      <p class="eyebrow">Package {e(p["no"])}</p>
      <div class="buybox__price">{money(p["price"])} <sub>{e(p["priceNote"])}</sub></div>
    </div>
    <div class="buybox__body">
      <ul>{incl}</ul>
      <a class="btn btn--signal btn--block" href="{pay_link(p)}" rel="noopener"
         data-track="begin_checkout" data-package="{e(p["name"])}"
         data-price="{p["price"]}" data-where="buybox">
        <span>Pay {money(p["price"])}</span> <span class="arr">→</span>
      </a>
      <p class="buybox__note">{e(p["turnaround"])}<br>Card payment · receipt by email</p>
    </div>
    <div class="buybox__secure">Secure hosted checkout</div>
  </aside>
</div>

<section class="more">
  <div class="wrap">
    <p class="eyebrow" style="margin-bottom:1.25rem">Other packages</p>
    <div class="more__list">{others}</div>
  </div>
</section>

<section class="cta">
  <div class="wrap sec cta__in">
    <div>
      <p class="eyebrow">Not sure this is the right one?</p>
      <h2>Tell us the problem,<br>we will name the package.</h2>
      <p>We would rather point you at the cheaper package that fixes it than sell you the
        expensive one that does not.</p>
    </div>
    <a class="btn" href="../index.html#faq" data-track="footer_cta_click" data-where="package_page">
      <span>Read the questions</span> <span class="arr">→</span>
    </a>
  </div>
</section>"""

    return page(
        f"{p['name']} — {money(p['price'])} {p['priceNote']} | {BRAND_FULL}",
        f"{p['oneLiner']} {money(p['price'])} {p['priceNote']}, delivered in {p['turnaround'].lower()}. "
        "Fixed scope, written deliverables, pay by card.",
        f"packages/{p['slug']}.html",
        "../",
        body,
        extra_ld=ld_tag,
    )


# --- supporting pages -----------------------------------------------------

def checkout_page():
    rows = "".join(
        f'<li><b>{e(p["no"])}</b><span>{e(p["name"])} — {money(p["price"])} {e(p["priceNote"])}</span></li>'
        for p in PACKAGES
    )
    body = f"""<div class="wrap">
  <p class="crumb"><a href="../index.html">Home</a> / Checkout</p>
</div>
<section class="pkg-hero">
  <div class="wrap">
    <p class="eyebrow">Payment step</p>
    <h1 id="pkg-title">Checkout</h1>
    <p class="lede" id="pkg-sub">This is the hand-off point to the payment provider.</p>
  </div>
</section>
<div class="wrap" style="padding-bottom:4rem;max-width:56rem">
  <div class="prose">
    <blockquote><b>Demo note for the site owner:</b> this page stands in for your live payment
      link. Paste your Stripe, PayPal or Paddle link into <code>payLink</code> for the package in
      <code>data/packages.json</code>, rebuild, and every Buy button on the site goes straight to a
      real hosted checkout instead of here. Nothing else needs changing.</blockquote>
    <h2>What the live flow looks like</h2>
    <p>Customer clicks <em>Buy now</em> on a package, lands on the provider's secure hosted
      checkout page with the amount and package name already filled in, pays by card, and is
      returned to a thank-you page on this site. The provider emails the receipt. You get the
      notification. No cart, no account, no extra steps.</p>
    <h2>Packages and prices currently live</h2>
    <ul class="deliver">{rows}</ul>
    <p style="margin-top:2rem">
      <a class="btn btn--ghost" href="../index.html#packages"><span>Back to the catalogue</span></a>
      <a class="btn btn--signal" href="../thank-you.html" style="margin-left:.5rem"
         data-track="demo_payment_simulated"><span>Simulate a successful payment</span> <span class="arr">→</span></a>
    </p>
  </div>
</div>
<script>
(function () {{
  var packages = {json.dumps({p["slug"]: {"name": p["name"], "price": money(p["price"]), "note": p["priceNote"]} for p in PACKAGES}, separators=(",", ":"))};
  var slug = new URLSearchParams(location.search).get('pkg');
  var p = packages[slug];
  if (p) {{
    document.getElementById('pkg-title').textContent = p.name;
    document.getElementById('pkg-sub').textContent = p.price + ' ' + p.note +
      ' — this is where the live payment link takes over.';
    document.title = 'Checkout: ' + p.name;
  }}
}})();
</script>"""
    return page(
        f"Checkout | {BRAND_FULL}",
        "Secure payment hand-off for your chosen marketing package.",
        "packages/checkout.html",
        "../",
        body,
    )


def thanks_page():
    body = f"""<section class="pkg-hero" style="padding-top:4rem">
  <div class="wrap" style="max-width:48rem">
    <p class="eyebrow">Payment received</p>
    <h1>Thank you — we have it.</h1>
    <p class="lede">A receipt is on its way to the address you paid with, and a short intake
      form will land in the same inbox within a few minutes.</p>
    <div class="prose" style="margin-top:2.5rem">
      <h2>What happens next</h2>
      <ul class="deliver">
        <li><b>01</b><span>Receipt from our payment provider — keep it, it is your invoice.</span></li>
        <li><b>02</b><span>Intake form, six or seven questions, five minutes to fill in.</span></li>
        <li><b>03</b><span>Work starts the same working day your form comes back.</span></li>
        <li><b>04</b><span>You get one named contact, who is also the person doing the work.</span></li>
      </ul>
      <p style="margin-top:2rem"><a class="btn btn--ghost" href="index.html"><span>Back to the site</span></a></p>
    </div>
  </div>
</section>"""
    return page(
        f"Thank you | {BRAND_FULL}",
        "Your payment was received. Here is what happens next.",
        "thank-you.html",
        "",
        body,
    )


def legal_page(slug, title, intro, blocks):
    inner = "".join(f"<h2>{e(h)}</h2><p>{e(t)}</p>" for h, t in blocks)
    body = f"""<section class="pkg-hero" style="padding-top:3rem">
  <div class="wrap" style="max-width:52rem">
    <p class="eyebrow">{e(title)}</p>
    <h1>{e(title)}</h1>
    <p class="lede">{e(intro)}</p>
  </div>
</section>
<div class="wrap" style="max-width:52rem;padding-bottom:4rem">
  <div class="prose">
    <blockquote><b>Placeholder:</b> this page is scaffolded so the links and SEO structure are
      complete. Replace the wording below with your own terms before launch.</blockquote>
    {inner}
  </div>
</div>"""
    return page(f"{title} | {BRAND_FULL}", intro, f"{slug}.html", "", body)


def notfound_page():
    body = f"""<section class="pkg-hero" style="padding-top:5rem">
  <div class="wrap" style="max-width:44rem">
    <span class="pkg-hero__no" aria-hidden="true">404</span>
    <h1 style="margin-top:1rem">That page has moved on.</h1>
    <p class="lede">The packages have not. All six are one click away.</p>
    <p style="margin-top:2rem"><a class="btn btn--signal" href="{BASE}/">
      <span>See the catalogue</span> <span class="arr">→</span></a></p>
  </div>
</section>"""
    return page(f"Page not found | {BRAND_FULL}", "Page not found.", "404.html", "", body)


FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" fill="#141310"/>'
    '<circle cx="46" cy="18" r="7" fill="#e8431f"/>'
    '<text x="9" y="47" font-family="Arial Black,Arial,sans-serif" font-size="34" '
    'font-weight="900" fill="#f6f3ec">N</text></svg>'
)


def sitemap():
    urls = [("", "1.0"), ("thank-you.html", "0.3"), ("terms.html", "0.2"), ("privacy.html", "0.2")]
    urls += [(f"packages/{p['slug']}.html", "0.9") for p in PACKAGES]
    items = "".join(
        f"<url><loc>{BASE}/{u}</loc><changefreq>monthly</changefreq>"
        f"<priority>{pr}</priority></url>"
        for u, pr in urls
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>\n'


def robots():
    return f"User-agent: *\nAllow: /\nDisallow: /packages/checkout.html\n\nSitemap: {BASE}/sitemap.xml\n"


# --- write ----------------------------------------------------------------

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)


def prune():
    """Delete pages and artwork for packages that no longer exist.

    Without this, removing a package from packages.json leaves its page on disk.
    It drops out of the nav and the sitemap but stays reachable by URL, so search
    engines keep serving a product we no longer sell.
    """
    live = {p["slug"] for p in PACKAGES}
    gone = []

    if os.path.isdir(PKGDIR):
        for f in os.listdir(PKGDIR):
            slug, ext = os.path.splitext(f)
            if ext == ".html" and slug != "checkout" and slug not in live:
                os.remove(os.path.join(PKGDIR, f))
                gone.append(f"packages/{f}")

    imgdir = os.path.join(SITE, "assets", "img")
    if os.path.isdir(imgdir):
        for f in os.listdir(imgdir):
            if f == "favicon.svg" or not f.endswith(".svg"):
                continue
            slug = f.rsplit("-", 1)[0]
            if slug not in live:
                os.remove(os.path.join(imgdir, f))
                gone.append(f"assets/img/{f}")

    for g in gone:
        print(f"  pruned {g}")
    return gone


def main():
    import gen_art
    gen_art.build(PACKAGES)
    prune()

    w(os.path.join(SITE, "index.html"), home())
    for i, p in enumerate(PACKAGES):
        w(os.path.join(PKGDIR, f"{p['slug']}.html"), package_page(p, i))
    w(os.path.join(PKGDIR, "checkout.html"), checkout_page())
    w(os.path.join(SITE, "thank-you.html"), thanks_page())
    w(os.path.join(SITE, "404.html"), notfound_page())
    w(
        os.path.join(SITE, "terms.html"),
        legal_page(
            "terms",
            "Terms of service",
            "The rules that apply when you buy a package.",
            [
                ("Scope", "Each package lists its deliverables. Anything not listed is out of scope and quoted separately before it is started."),
                ("Payment", "Packages are paid in full before work begins, by card, through a hosted checkout. Monthly packages renew on the same date each month and can be cancelled after the stated minimum term."),
                ("Turnaround", "Turnaround runs from the day the completed intake form is received, not from the day of payment."),
                ("Ownership", "On final payment, all delivered work and source files transfer to you for unrestricted commercial use."),
                ("Refunds", "If work has not started, a full refund is available on request. Once work is underway, we will correct anything you are unhappy with within the stated scope."),
            ],
        ),
    )
    w(
        os.path.join(SITE, "privacy.html"),
        legal_page(
            "privacy",
            "Privacy policy",
            "What we collect, why, and how to get rid of it.",
            [
                ("What we collect", "The details you give us when you buy or enquire, and anonymous usage statistics about which pages and packages get viewed."),
                ("Payments", "Card details are never seen or stored by us. Payment is handled entirely by our payment provider on their own secure checkout."),
                ("Analytics", "We record aggregate page and package views to understand which packages people are interested in. No advertising profiles are built and nothing is sold on."),
                ("Your rights", "Ask us for a copy of what we hold, or ask us to delete it, and we will do so within 30 days."),
            ],
        ),
    )
    w(os.path.join(SITE, "assets", "img", "favicon.svg"), FAVICON)
    w(os.path.join(SITE, "sitemap.xml"), sitemap())
    w(os.path.join(SITE, "robots.txt"), robots())

    pages = 1 + len(PACKAGES) + 5
    print(f"built {pages} html pages + sitemap.xml + robots.txt -> {SITE}")


if __name__ == "__main__":
    main()
