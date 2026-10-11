# Proposal: Theme Visual Effects

## Problem

The current theme system (colors, fonts, radius via `theme.yml`) handles design tokens well but **cannot express visual effects** that make a start page feel alive:

| Effect Type | Current Workaround | Pain |
|-------------|-------------------|------|
| Background images (seasonal, branded) | Hardcode in CSS via devtools, lost on reload | Not configurable, not portable |
| CSS animations (falling snow, pulsing glow) | Inline styles in template, not themeable | Tied to specific plugin/template |
| JS animations (canvas snow, interactive particles) | Not possible without custom plugin | Requires Python plugin for visual-only feature |
| Seasonal themes (Halloween pumpkins, autumn leaves, winter snow) | Duplicate entire theme + manual CSS | Maintenance burden, no inheritance |

Users who want a "Halloween" or "Winter" theme must either:
1. Fork a theme and add raw CSS/JS — loses inheritance, not shareable
2. Build a plugin — overkill for visual effects
3. Edit browser devtools — lost on reload

## Solution

Extend the theme system with an **`includes`** key in `theme.yml` that declares CSS and JavaScript files to load. Files live in the theme's `static/` directory and are served at `/themes/<name>/`.

### Theme Author Experience

```yaml
# src/themes/halloween/theme.yml
name: "Halloween"
extends: "default-dark"

includes:
  css:
    - "theme.css"
    - "animations/float.css"
  js:
    - "theme.js"
```

```
src/themes/halloween/
├── theme.yml
└── static/
    ├── theme.css              # backgrounds, CSS animations
    ├── theme.js               # canvas/JS animations (ES module)
    ├── pumpkin.svg            # referenced via url("pumpkin.svg") in CSS
    └── animations/
        └── float.css
```

### Runtime Behavior

| `includes` Entry | Injected As | Location |
|------------------|-------------|----------|
| `css: ["theme.css"]` | `<link rel="stylesheet" href="/themes/halloween/theme.css">` | `<head>` (after theme variables) |
| `js: ["theme.js"]` | `<script type="module" src="/themes/halloween/theme.js"></script>` | End of `<body>` |

## Non-Goals

- No changes to theme inheritance (child themes do NOT inherit parent's `includes`; each theme declares its own)
- No live theme switching without server reload (config change → reload)
- No built-in animation library — themes bring their own CSS/JS
- No validation of CSS/JS content — trust theme authors
- No `theme_options` config passthrough
- No `init()` function contract — themes run on load
- No `reducedMotion` / `prefers-reduced-motion` handling — themes handle themselves
- No `meta` object or `themeName` passthrough

## Why This Approach

| Alternative | Rejected Because |
|-------------|------------------|
| Declarative YAML for animations | Too limiting for canvas/WebGL/interactivity |
| Auto-discover `theme.css`/`theme.js` | Implicit behavior surprises users; explicit `includes` is clear |
| Template injection points (`{% block %}`) | Over-engineered; CSS/JS files are standard web pattern |
| Effect plugin system | New abstraction layer; CSS/JS files are simpler and portable |
| `init()` function contract | Themes are standard ES modules; they run on load |
| `theme_options` passthrough | Adds complexity; themes can read config from DOM if needed |

This follows the existing pattern: `static/` is mounted, `fonts.css` is declared in theme chain. `includes` is the natural extension for arbitrary CSS/JS.