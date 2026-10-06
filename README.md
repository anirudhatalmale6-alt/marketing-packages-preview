# Marketing packages website

A hand-coded catalogue site for selling ready-made marketing packages. Plain
HTML, CSS and JavaScript — no WordPress, no page builder, no framework, no
build step required to host it.

**Live preview:** https://anirudhatalmale6-alt.github.io/marketing-packages-preview/

> All copy, prices, package names and brand ("Mainstream Media") in this preview
> are placeholders written to show the layout. They are all replaced from one
> file — see *Changing the content* below.

---

## What is in here

```
site/                 ← this folder is the entire website. Upload it as-is.
  index.html            home + full catalogue
  packages/*.html       one page per package
  packages/checkout.html stand-in for the live payment link (see Payments)
  thank-you.html        post-payment landing page
  terms.html            placeholder legal copy
  privacy.html          placeholder legal copy
  404.html
  sitemap.xml           regenerated automatically
  robots.txt
  assets/css            style.css (the design) + fonts.css (generated)
  assets/js/main.js     mobile menu, scroll reveals, click tracking
  assets/fonts          self-hosted subset webfonts, 172 KB total
  assets/img            generated placeholder artwork (SVG)

data/packages.json    ← all content lives here
build.py              ← regenerates site/ from data/packages.json
gen_art.py            ← draws the placeholder artwork
tools/fetch_fonts.py  ← re-downloads + subsets the webfonts (rarely needed)
```

## Changing the content

Everything a non-developer would want to change — package names, prices,
descriptions, deliverables, FAQs, testimonials, the brand name — lives in
`data/packages.json`. Edit it, then:

```sh
python3 build.py
```

That rewrites every page in `site/`, including the sitemap. Re-upload `site/`.

The generated HTML is committed, so the site still works for anyone who never
runs Python.

## Payments

Each package has a `payLink` field in `data/packages.json`. Paste a Stripe
Payment Link (or PayPal / Paddle link) there and rebuild — every *Buy now*
button for that package goes straight to the provider's hosted checkout.

Until a real link is set, buttons land on `packages/checkout.html`, which
explains the flow instead of 404-ing. Nothing else in the code changes when the
real links arrive.

Card details never touch this site — the provider's hosted page handles them,
which is also what keeps PCI compliance out of scope.

## Analytics

Every meaningful click already pushes a named event to `window.dataLayer`:

| event | fired when |
|---|---|
| `view_package_card` | a package card scrolls into view (which packages get attention) |
| `view_package` | "Details" clicked |
| `begin_checkout` | "Buy now" / "Pay $X" clicked — carries package name and price |
| `hero_cta_click`, `nav_cta_click`, `footer_cta_click` | the main calls to action |
| `cross_sell_click` | another package clicked from a package page |

Paste a GA4 or Plausible snippet into the commented `<!-- ANALYTICS -->` block
in `build.py` and rebuild. `main.js` detects whichever one is present and the
events start flowing — no other change needed.

## SEO

Already in place on every page: unique `<title>` and meta description, canonical
URL, Open Graph and Twitter card tags, and JSON-LD structured data —
`Organization` + `WebSite` + `FAQPage` + `ItemList` on the home page, and
`Product` + `Offer` + `BreadcrumbList` + `FAQPage` on each package page, so
prices can show directly in Google results.

`sitemap.xml` and `robots.txt` are generated. Update the `domain` field in
`data/packages.json` when the real domain is connected — every canonical URL,
Open Graph URL and sitemap entry follows from it.

## Performance notes

- No framework, no jQuery, no CSS library. One 16 KB stylesheet, one 3 KB script.
- Fonts are self-hosted and subset to the characters the site renders (172 KB
  for four faces), so no request ever goes to a third party and nothing blocks
  on an external domain.
- Artwork is SVG drawn at build time — a few KB per image, sharp at any size.
  Replace with real photography by dropping files into `assets/img/`.
- Animations respect `prefers-reduced-motion`.

## Testing done

- 12 pages parsed under a strict HTML5 parser — no markup errors.
- 371 internal links resolved — none broken.
- Full buyer journey driven in a real browser (catalogue → package → checkout →
  thank-you), plus the mobile menu, FAQ, analytics events and tap-target sizes.
- Checked for horizontal overflow at 390 px on every page type.
