# VanRakshak AI — Frontend

**Protecting Forests Through Artificial Intelligence**

This is the static frontend foundation for VanRakshak AI: a single
responsive landing page built with pure HTML, CSS, and vanilla
JavaScript. No frameworks, no build step.

---

## 1. What This Is

A calm, editorial landing page introducing the platform — navigation,
hero, an "About" section with three capability cards, a technology
timeline, and a footer. It does **not** include upload functionality,
map functionality, or prediction cards; those are separate, later tasks
that will build on top of this shell.

---

## 2. Folder Structure

```
frontend/
├── index.html            # The landing page (semantic HTML5)
├── styles/
│   └── style.css          # Design tokens + all page styling
├── scripts/
│   └── main.js             # Nav toggle, scroll reveal, footer year
├── assets/
│   └── favicon.svg         # Brand mark used as the site favicon
└── README.md
```

---

## 3. Running It

No build step or server required — it's static HTML/CSS/JS.

Simplest option: open `index.html` directly in a browser.

Or serve it locally (recommended, avoids any browser file:// quirks):

```bash
cd frontend
python3 -m http.server 5500
```

Then visit `http://localhost:5500`.

---

## 4. Design System

Defined as CSS custom properties at the top of `styles/style.css`:

**Color palette**

| Token | Hex | Use |
|---|---|---|
| `--color-bg` | `#F7F3EA` | Page background (warm paper) |
| `--color-primary` | `#254D32` | Primary actions, links, accents |
| `--color-secondary` | `#6B8F71` | Supporting green, illustration rings |
| `--color-dark` | `#1F2A1F` | Headings, dark section background |
| `--color-accent` | `#D6C6A5` | Warm highlight, illustration accents |
| `--color-text` | `#2C2C2C` | Body copy |

**Typography**

- Display: `Cormorant Garamond` (headings — loaded from Google Fonts)
- Body: `Inter` (body copy, UI text — loaded from Google Fonts)

**Signature element**

The hero illustration is a hand-composed inline SVG: thin orbital rings
(satellite monitoring), topographic contour ellipses (land), and a
central branch with paired leaf veins (forest) — deliberately not a
realistic globe, gradient, or glow effect.

---

## 5. Accessibility & Motion Notes

- Skip-to-content link for keyboard users.
- Visible focus states on all interactive elements (`:focus-visible`).
- Decorative SVGs are `aria-hidden`; the hero illustration has a
  descriptive `<title>` for screen readers.
- All animation (fades, slide-ups, hover states, the slow rotating
  orbit ring) is CSS-only and respects `prefers-reduced-motion`.
- Layout is responsive down to small mobile widths, with a dedicated
  mobile navigation toggle below 640px.

---

## 6. What's Coming Next

This page is intentionally a shell. Planned, not yet built:

- Image upload interface, wired to the backend `/api/v1/predict` endpoint.
- Interactive map (location search, click-to-select).
- Prediction result cards and confidence visualization.
- Historical comparison and environmental report views.

None of the above exists in this codebase yet — this foundation is
structured so each can be added as its own page/section without
reworking the design system already in place.
