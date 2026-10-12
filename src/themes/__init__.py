import posixpath
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
    "fonts": ("page_heading", "card_heading", "card_content"),
    "radius": ("card",),
}


class ThemeError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ThemeStyles(NamedTuple):
    css: str
    font_css: str
    single: bool
    dark: bool
    light_css_texts: list
    light_js_urls: list
    dark_css_texts: list
    dark_js_urls: list


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


def _validate_includes(includes, name, themes_dir):
    """Validate the includes section of a theme."""
    if not isinstance(includes, dict):
        raise ThemeError(f"Theme '{name}': 'includes' must be a mapping.")
    for key in ("css", "js"):
        val = includes.get(key)
        if val is not None and not isinstance(val, list):
            raise ThemeError(f"Theme '{name}': 'includes.{key}' must be a list.")
        if val:
            for item in val:
                if not isinstance(item, str):
                    raise ThemeError(f"Theme '{name}': 'includes.{key}' items must be strings.")
    static_dir = theme_static_dir(name, themes_dir)
    for css_file in includes.get("css", []):
        if not (static_dir / css_file).is_file():
            raise ThemeError(f"Theme '{name}': CSS file not found: {css_file}")
    for js_file in includes.get("js", []):
        if not (static_dir / js_file).is_file():
            raise ThemeError(f"Theme '{name}': JS file not found: {js_file}")


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

    includes = data.get("includes")
    if includes is not None:
        _validate_includes(includes, name, themes_dir)
        data["includes"] = includes
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
        # Child themes do NOT inherit parent's includes
        resolved.pop("includes", None)
    else:
        resolved = {}

    for section in ("colors", "fonts", "radius"):
        values = raw.get(section)
        if values is None:
            continue
        if not isinstance(values, dict):
            raise ThemeError(f"Theme '{name}': '{section}' must be a mapping.")
        resolved.setdefault(section, {}).update(values)

    # Only include 'includes' if explicitly defined in this theme
    if "includes" in raw:
        resolved["includes"] = raw["includes"]

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


_CSS_URL_PATTERN = re.compile(r"url\(\s*(['\"]?)(.+?)\1\s*\)", re.IGNORECASE)


def _rewrite_relative_urls(css_text, theme_name):
    """Rewrite bare relative url() references to absolute theme static paths."""
    prefix = f"{THEMES_URL_PREFIX}/{theme_name}/"

    def replace(match):
        quote = match.group(1)
        url = match.group(2).strip()
        lowered = url.lower()
        if not url or lowered.startswith(("data:", "http://", "https://", "//", "/", "#")):
            return match.group(0)
        return f"url({quote}{posixpath.normpath(prefix + url)}{quote})"

    return _CSS_URL_PATTERN.sub(replace, css_text)


def font_css_text(names, themes_dir=None):
    """Return the concatenated fonts.css contents for the given themes' chains."""
    root = _themes_root(themes_dir)
    chunks = []
    seen = set()
    for name in names:
        for theme_name in theme_chain(name, themes_dir):
            css_path = root / theme_name / "static" / "fonts.css"
            if not css_path.is_file() or css_path in seen:
                continue
            seen.add(css_path)
            chunks.append(_rewrite_relative_urls(
                css_path.read_text(encoding="utf-8"), theme_name
            ))
    return "\n".join(chunks)


def include_css_texts(includes, theme_name, themes_dir=None):
    """Return the rewritten contents of each CSS file in a theme's includes."""
    root = _themes_root(themes_dir)
    texts = []
    for filename in includes.get("css", []):
        css_path = root / theme_name / "static" / filename
        texts.append(_rewrite_relative_urls(
            css_path.read_text(encoding="utf-8"), theme_name
        ))
    return texts


def generate_theme_css(theme_config, themes_dir=None):
    """Generate the CSS custom properties and font links for the configured themes."""
    selection = normalize_theme_config(theme_config)
    light = load_resolved_theme(selection["light"], themes_dir)
    dark = load_resolved_theme(selection["dark"], themes_dir)

    # Get includes from resolved themes (only the final theme in chain)
    light_includes = light.get("includes", {})
    dark_includes = dark.get("includes", {})

    css = "\n\n".join([
        _render_block([':root', '[data-theme="light"]'], light),
        _render_block(['[data-theme="dark"]'], dark),
    ])
    font_css = font_css_text([selection["light"], selection["dark"]], themes_dir)

    # Build absolute URLs for JS includes and inline text for CSS includes
    def build_js_urls(includes, theme_name):
        return [f"/themes/{theme_name}/{f}" for f in includes.get("js", [])]

    light_css_texts = include_css_texts(light_includes, selection["light"], themes_dir)
    dark_css_texts = include_css_texts(dark_includes, selection["dark"], themes_dir)
    light_js_urls = build_js_urls(light_includes, selection["light"])
    dark_js_urls = build_js_urls(dark_includes, selection["dark"])

    return ThemeStyles(
        css=css,
        font_css=font_css,
        single=selection["single"],
        dark=palette_is_dark(light),
        light_css_texts=light_css_texts,
        light_js_urls=light_js_urls,
        dark_css_texts=dark_css_texts,
        dark_js_urls=dark_js_urls,
    )


def built_in_theme_styles(themes_dir=None):
    """Generate styles from the built-in themes, used as a fallback for the error page."""
    try:
        return generate_theme_css(
            {"light": DEFAULT_LIGHT_THEME, "dark": DEFAULT_DARK_THEME}, themes_dir
        )
    except ThemeError:
        return ThemeStyles(
            css="", font_css="", single=False, dark=False,
            light_css_texts=[], light_js_urls=[], dark_css_texts=[], dark_js_urls=[],
        )
