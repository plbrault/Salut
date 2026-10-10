import re
from pathlib import Path
from typing import NamedTuple

import yaml

THEMES_DIR = Path(__file__).resolve().parent
THEMES_URL_PREFIX = "/themes"

DEFAULT_LIGHT_THEME = "default-light"
DEFAULT_DARK_THEME = "default-dark"

REQUIRED_KEYS = {
    "colors": (
        "bg", "card_bg", "text", "text_muted", "text_faint",
        "border", "link", "link_hover", "code_bg",
        "accent", "accent_hover", "accent_contrast",
        "danger", "danger_hover", "danger_contrast",
    ),
    "fonts": ("family",),
    "radius": ("card",),
}


class ThemeError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ThemeStyles(NamedTuple):
    css: str
    font_links: list
    single: bool
    dark: bool


def _themes_root(themes_dir=None):
    return Path(themes_dir) if themes_dir else THEMES_DIR


def theme_static_dir(name, themes_dir=None):
    """Return the static directory for a theme (where servable assets live)."""
    return _themes_root(themes_dir) / name / "static"


def discover_themes(themes_dir=None):
    """Return the names of all theme directories that contain a theme.yml file."""
    root = _themes_root(themes_dir)
    if not root.is_dir():
        return []
    return sorted(path.parent.name for path in root.glob("*/theme.yml"))


def load_theme(name, themes_dir=None):
    """Load the raw theme.yml data for a theme."""
    root = _themes_root(themes_dir)
    theme_dir = root / name
    if not theme_dir.is_dir():
        raise ThemeError(f"Theme '{name}' not found in {root}.")
    theme_path = theme_dir / "theme.yml"
    if not theme_path.is_file():
        raise ThemeError(f"Theme '{name}' is missing a theme.yml file.")
    with open(theme_path, "r", encoding="utf-8") as file:
        try:
            data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ThemeError(f"Invalid YAML in theme '{name}': {e}") from e
    if not isinstance(data, dict):
        raise ThemeError(f"Theme '{name}' must be a mapping of theme values.")
    return data


def resolve_theme(name, themes_dir=None, _chain=None):
    """Resolve a theme with its full inheritance chain into a single mapping."""
    chain = _chain or []
    if name in chain:
        cycle = chain[chain.index(name):] + [name]
        raise ThemeError(f"Circular theme inheritance: {' -> '.join(cycle)}.")

    raw = load_theme(name, themes_dir)

    parent = raw.get("extends")
    if parent is not None:
        if not isinstance(parent, str) or not parent:
            raise ThemeError(f"Theme '{name}': 'extends' must be a non-empty string.")
        resolved = resolve_theme(parent, themes_dir, chain + [name])
    else:
        resolved = {}

    for section in ("colors", "fonts", "radius"):
        values = raw.get(section)
        if values is None:
            continue
        if not isinstance(values, dict):
            raise ThemeError(f"Theme '{name}': '{section}' must be a mapping.")
        resolved.setdefault(section, {}).update(values)

    return resolved


def validate_theme(resolved, name):
    """Ensure a resolved theme provides every required value."""
    for section, keys in REQUIRED_KEYS.items():
        values = resolved.get(section)
        if not isinstance(values, dict):
            raise ThemeError(f"Theme '{name}' is missing required '{section}' section.")
        for key in keys:
            if values.get(key) in (None, ""):
                raise ThemeError(f"Theme '{name}' is missing required value '{section}.{key}'.")


def load_resolved_theme(name, themes_dir=None):
    """Load, resolve and validate a theme."""
    resolved = resolve_theme(name, themes_dir)
    validate_theme(resolved, name)
    return resolved


def theme_chain(name, themes_dir=None):
    """Return the theme names from the root ancestor down to the theme itself."""
    chain = []
    current = name
    while current:
        if current in chain:
            cycle = chain[chain.index(current):] + [current]
            raise ThemeError(f"Circular theme inheritance: {' -> '.join(cycle)}.")
        chain.append(current)
        current = load_theme(current, themes_dir).get("extends")
    return list(reversed(chain))


def normalize_theme_config(value):
    """Normalize the config `theme` field into light/dark theme names."""
    if value is None:
        return {"light": DEFAULT_LIGHT_THEME, "dark": DEFAULT_DARK_THEME, "single": False}
    if isinstance(value, str):
        return {"light": value, "dark": value, "single": True}
    if isinstance(value, dict):
        return {"light": value.get("light"), "dark": value.get("dark"), "single": False}
    raise ThemeError("'theme' must be a string or a mapping with 'light' and 'dark'.")


_HEX_COLOR = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB_COLOR = re.compile(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")
_NAMED_COLORS = {"white": (255, 255, 255), "black": (0, 0, 0)}


def _parse_color(value):
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    hex_match = _HEX_COLOR.match(value)
    if hex_match:
        digits = hex_match.group(1)
        if len(digits) == 3:
            digits = "".join(ch * 2 for ch in digits)
        return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))
    rgb_match = _RGB_COLOR.match(value)
    if rgb_match:
        return tuple(int(rgb_match.group(i)) for i in (1, 2, 3))
    return _NAMED_COLORS.get(value)


def palette_is_dark(resolved):
    """Return True when a resolved theme's background color is dark."""
    color = _parse_color(resolved.get("colors", {}).get("bg"))
    if color is None:
        return False
    red, green, blue = color
    return (0.299 * red + 0.587 * green + 0.114 * blue) < 128


def _css_variable_name(section, key):
    slug = key.replace("_", "-")
    if section == "fonts":
        return f"--font-{slug}"
    if section == "radius":
        return f"--{slug}-radius"
    return f"--{slug}"


def _render_block(selectors, resolved):
    lines = [",\n".join(selectors) + " {"]
    for section in ("colors", "fonts", "radius"):
        for key, value in resolved.get(section, {}).items():
            lines.append(f"    {_css_variable_name(section, key)}: {value};")
    lines.append("}")
    return "\n".join(lines)


def font_css_links(names, themes_dir=None):
    """Return the URLs of every fonts.css in the inheritance chains of the given themes."""
    root = _themes_root(themes_dir)
    links = []
    for name in names:
        for theme_name in theme_chain(name, themes_dir):
            static_dir = root / theme_name / "static"
            if not (static_dir / "fonts.css").is_file():
                continue
            url = f"{THEMES_URL_PREFIX}/{theme_name}/fonts.css"
            if url not in links:
                links.append(url)
    return links


def generate_theme_css(theme_config, themes_dir=None):
    """Generate the CSS custom properties and font links for the configured themes."""
    selection = normalize_theme_config(theme_config)
    light = load_resolved_theme(selection["light"], themes_dir)
    dark = load_resolved_theme(selection["dark"], themes_dir)

    css = "\n\n".join([
        _render_block([':root', '[data-theme="light"]'], light),
        _render_block(['[data-theme="dark"]'], dark),
    ])
    font_links = font_css_links([selection["light"], selection["dark"]], themes_dir)
    return ThemeStyles(
        css=css,
        font_links=font_links,
        single=selection["single"],
        dark=palette_is_dark(light),
    )


def built_in_theme_styles(themes_dir=None):
    """Generate styles from the built-in themes, used as a fallback for the error page."""
    try:
        return generate_theme_css(
            {"light": DEFAULT_LIGHT_THEME, "dark": DEFAULT_DARK_THEME}, themes_dir
        )
    except ThemeError:
        return ThemeStyles(css="", font_links=[], single=False, dark=False)
