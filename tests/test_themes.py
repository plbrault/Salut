import yaml

import pytest

from src.themes import (
    ThemeError,
    built_in_theme_styles,
    discover_themes,
    font_css_links,
    generate_theme_css,
    load_resolved_theme,
    load_theme,
    normalize_theme_config,
    palette_is_dark,
    resolve_theme,
    theme_chain,
    theme_static_dir,
    validate_theme,
)

FULL_THEME = {
    "colors": {
        "bg": "#ffffff",
        "card_bg": "#f0f0f0",
        "text": "#111111",
        "text_muted": "#666666",
        "text_faint": "#999999",
        "border": "#dddddd",
        "link": "#0000ee",
        "link_hover": "#0000cc",
        "code_bg": "#eeeeee",
        "accent": "#0000ee",
        "accent_hover": "#0000cc",
        "accent_contrast": "#ffffff",
        "danger": "#cc0000",
        "danger_hover": "#aa0000",
        "danger_contrast": "#ffffff",
    },
    "fonts": {
        "page_heading": "Georgia, serif",
        "card_heading": "Arial, sans-serif",
        "card_content": "Verdana, sans-serif",
    },
    "radius": {"card": "0.25rem"},
}


def _write_theme(root, name, data, raw=None):
    theme_dir = root / name
    theme_dir.mkdir(parents=True, exist_ok=True)
    content = raw if raw is not None else yaml.dump(data)
    (theme_dir / "theme.yml").write_text(content, encoding="utf-8")
    return theme_dir


class TestDiscoverThemes:
    def test_discovers_builtin_themes(self):
        names = discover_themes()
        assert "default-light" in names
        assert "default-dark" in names

    def test_discovers_custom_themes(self, tmp_path):
        _write_theme(tmp_path, "my-theme", FULL_THEME)
        assert discover_themes(tmp_path) == ["my-theme"]

    def test_ignores_directories_without_theme_yml(self, tmp_path):
        (tmp_path / "not-a-theme").mkdir()
        assert discover_themes(tmp_path) == []

    def test_returns_empty_for_missing_directory(self, tmp_path):
        assert discover_themes(tmp_path / "missing") == []


class TestLoadTheme:
    def test_loads_builtin_theme(self):
        data = load_theme("default-light")
        assert data["colors"]["bg"] == "#f3f4f6"
        assert data["fonts"]["page_heading"] == "'Inter', sans-serif"
        assert data["fonts"]["card_heading"] == "'Inter', sans-serif"
        assert data["fonts"]["card_content"] == "'Inter', sans-serif"
        assert data["radius"]["card"] == "0.5rem"

    def test_missing_theme_raises(self, tmp_path):
        with pytest.raises(ThemeError, match="not found"):
            load_theme("nope", tmp_path)

    def test_missing_theme_yml_raises(self, tmp_path):
        (tmp_path / "empty-theme").mkdir()
        with pytest.raises(ThemeError, match="theme.yml"):
            load_theme("empty-theme", tmp_path)

    def test_invalid_yaml_raises(self, tmp_path):
        _write_theme(tmp_path, "broken", None, raw="{")
        with pytest.raises(ThemeError, match="Invalid YAML"):
            load_theme("broken", tmp_path)

    def test_non_mapping_raises(self, tmp_path):
        _write_theme(tmp_path, "listy", None, raw="- a\n- b\n")
        with pytest.raises(ThemeError, match="mapping"):
            load_theme("listy", tmp_path)


class TestInheritance:
    def test_child_overrides_only_specified_keys(self, tmp_path):
        _write_theme(tmp_path, "parent", FULL_THEME)
        _write_theme(tmp_path, "child", {"extends": "parent", "colors": {"bg": "#fff7f5"}})

        resolved = resolve_theme("child", tmp_path)

        assert resolved["colors"]["bg"] == "#fff7f5"
        assert resolved["colors"]["text"] == "#111111"
        assert resolved["fonts"]["page_heading"] == "Georgia, serif"
        assert resolved["fonts"]["card_heading"] == "Arial, sans-serif"
        assert resolved["fonts"]["card_content"] == "Verdana, sans-serif"
        assert resolved["radius"]["card"] == "0.25rem"

    def test_multilevel_inheritance(self, tmp_path):
        _write_theme(tmp_path, "grandparent", FULL_THEME)
        _write_theme(tmp_path, "parent", {"extends": "grandparent", "colors": {"bg": "#eeeeee"}})
        _write_theme(tmp_path, "child", {"extends": "parent", "colors": {"bg": "#cccccc"}})

        resolved = resolve_theme("child", tmp_path)

        assert resolved["colors"]["bg"] == "#cccccc"
        assert resolved["colors"]["border"] == "#dddddd"
        assert resolved["colors"]["link"] == "#0000ee"

    def test_name_and_extends_not_inherited(self, tmp_path):
        _write_theme(tmp_path, "parent", {**FULL_THEME, "name": "Parent"})
        _write_theme(tmp_path, "child", {"extends": "parent"})

        resolved = resolve_theme("child", tmp_path)

        assert "name" not in resolved
        assert "extends" not in resolved

    def test_circular_inheritance_raises(self, tmp_path):
        _write_theme(tmp_path, "a", {"extends": "b"})
        _write_theme(tmp_path, "b", {"extends": "a"})

        with pytest.raises(ThemeError, match="Circular"):
            resolve_theme("a", tmp_path)

    def test_self_inheritance_raises(self, tmp_path):
        _write_theme(tmp_path, "a", {"extends": "a"})
        with pytest.raises(ThemeError, match="Circular"):
            resolve_theme("a", tmp_path)

    def test_missing_parent_raises(self, tmp_path):
        _write_theme(tmp_path, "child", {"extends": "ghost"})
        with pytest.raises(ThemeError, match="not found"):
            resolve_theme("child", tmp_path)

    def test_invalid_extends_type_raises(self, tmp_path):
        _write_theme(tmp_path, "child", {"extends": 42})
        with pytest.raises(ThemeError, match="extends"):
            resolve_theme("child", tmp_path)


class TestValidateTheme:
    def test_valid_theme_passes(self):
        validate_theme(FULL_THEME, "full")

    def test_missing_section_raises(self, tmp_path):
        _write_theme(tmp_path, "no-radius", {"colors": FULL_THEME["colors"], "fonts": FULL_THEME["fonts"]})
        with pytest.raises(ThemeError, match="radius"):
            load_resolved_theme("no-radius", tmp_path)

    def test_missing_value_raises(self, tmp_path):
        colors = {k: v for k, v in FULL_THEME["colors"].items() if k != "link"}
        _write_theme(tmp_path, "no-link", {**FULL_THEME, "colors": colors})
        with pytest.raises(ThemeError, match="colors.link"):
            load_resolved_theme("no-link", tmp_path)

    def test_empty_value_raises(self, tmp_path):
        _write_theme(tmp_path, "empty-font", {**FULL_THEME, "fonts": {**FULL_THEME["fonts"], "card_heading": ""}})
        with pytest.raises(ThemeError, match="fonts.card_heading"):
            load_resolved_theme("empty-font", tmp_path)

    def test_missing_font_role_raises(self, tmp_path):
        fonts = {k: v for k, v in FULL_THEME["fonts"].items() if k != "card_heading"}
        _write_theme(tmp_path, "no-card-heading", {**FULL_THEME, "fonts": fonts})
        with pytest.raises(ThemeError, match="fonts.card_heading"):
            load_resolved_theme("no-card-heading", tmp_path)

    def test_child_missing_inherited_keys_fails(self, tmp_path):
        _write_theme(tmp_path, "orphan", {"colors": {"bg": "#000000"}})
        with pytest.raises(ThemeError):
            load_resolved_theme("orphan", tmp_path)


class TestThemeChain:
    def test_builtin_chain(self):
        assert theme_chain("default-dark") == ["default-light", "default-dark"]
        assert theme_chain("default-light") == ["default-light"]

    def test_chain_detects_cycles(self, tmp_path):
        _write_theme(tmp_path, "a", {"extends": "b"})
        _write_theme(tmp_path, "b", {"extends": "a"})
        with pytest.raises(ThemeError, match="Circular"):
            theme_chain("a", tmp_path)


class TestNormalizeThemeConfig:
    def test_none_defaults_to_pair(self):
        selection = normalize_theme_config(None)
        assert selection == {"light": "default-light", "dark": "default-dark", "single": False}

    def test_string_is_single_theme(self):
        selection = normalize_theme_config("default-dark")
        assert selection == {"light": "default-dark", "dark": "default-dark", "single": True}

    def test_mapping_is_pair(self):
        selection = normalize_theme_config({"light": "default-light", "dark": "default-dark"})
        assert selection == {"light": "default-light", "dark": "default-dark", "single": False}

    def test_invalid_value_raises(self):
        with pytest.raises(ThemeError, match="theme"):
            normalize_theme_config(42)


class TestGenerateThemeCss:
    def test_single_theme_applies_to_both_modes(self):
        styles = generate_theme_css("default-light")
        assert styles.single is True
        assert styles.css.count("--bg: #f3f4f6;") == 2
        assert ':root,\n[data-theme="light"]' in styles.css
        assert '[data-theme="dark"]' in styles.css

    def test_single_light_theme_is_not_dark(self):
        styles = generate_theme_css("default-light")
        assert styles.single is True
        assert styles.dark is False

    def test_single_dark_theme_is_dark(self):
        styles = generate_theme_css("default-dark")
        assert styles.single is True
        assert styles.dark is True

    def test_pair_theme_is_not_dark(self):
        styles = generate_theme_css({"light": "default-light", "dark": "default-dark"})
        assert styles.single is False
        assert styles.dark is False

    def test_pair_theme_uses_distinct_palettes(self):
        styles = generate_theme_css({"light": "default-light", "dark": "default-dark"})
        assert styles.single is False
        assert "--bg: #f3f4f6;" in styles.css
        assert "--bg: #111827;" in styles.css

    def test_generated_variables_match_required_keys(self):
        styles = generate_theme_css(None)
        for var_name in (
            "--bg:", "--card-bg:", "--text:", "--text-muted:", "--text-faint:",
            "--border:", "--link:", "--link-hover:", "--code-bg:",
            "--accent:", "--accent-hover:", "--accent-contrast:",
            "--danger:", "--danger-hover:", "--danger-contrast:",
            "--font-page-heading:", "--font-card-heading:", "--font-card-content:", "--card-radius:",
        ):
            assert var_name in styles.css

    def test_defaults_when_config_missing(self):
        styles = generate_theme_css(None)
        assert styles.single is False
        assert "--bg: #111827;" in styles.css

    def test_font_links_cover_inheritance_chain(self):
        styles = generate_theme_css(None)
        assert styles.font_links == ["/themes/default-light/fonts.css"]

    def test_font_links_deduplicate_shared_parent(self, tmp_path):
        _write_theme(tmp_path, "parent", FULL_THEME)
        (tmp_path / "parent" / "static").mkdir()
        (tmp_path / "parent" / "static" / "fonts.css").write_text("@font-face {}", encoding="utf-8")
        _write_theme(tmp_path, "light", {"extends": "parent"})
        _write_theme(tmp_path, "dark", {"extends": "parent"})

        links = font_css_links(["light", "dark"], tmp_path)

        assert links == ["/themes/parent/fonts.css"]

    def test_font_links_skip_themes_without_fonts_css(self, tmp_path):
        _write_theme(tmp_path, "bare", FULL_THEME)
        assert not font_css_links(["bare"], tmp_path)

    def test_builtin_fallback_styles(self):
        styles = built_in_theme_styles()
        assert styles.single is False
        assert "--bg: #f3f4f6;" in styles.css
        assert "--bg: #111827;" in styles.css
        assert styles.font_links == ["/themes/default-light/fonts.css"]


class TestPaletteIsDark:
    @pytest.mark.parametrize("bg, expected", [
        ("#ffffff", False),
        ("#000000", True),
        ("#fff", False),
        ("#111827", True),
        ("#f3f4f6", False),
        ("white", False),
        ("black", True),
        ("rgb(17, 24, 39)", True),
        ("rgb(243, 244, 246)", False),
        ("rgba(17, 24, 39, 0.9)", True),
    ])
    def test_common_color_formats(self, bg, expected):
        assert palette_is_dark({"colors": {"bg": bg}}) is expected

    def test_missing_background_defaults_to_light(self):
        assert palette_is_dark({"colors": {}}) is False
        assert palette_is_dark({}) is False

    def test_unparseable_background_defaults_to_light(self):
        assert palette_is_dark({"colors": {"bg": "url(paper.png)"}}) is False


class TestThemeIncludes:
    def test_includes_parsing_valid(self, tmp_path):
        theme_data = {
            **FULL_THEME,
            "includes": {
                "css": ["theme.css", "animations/float.css"],
                "js": ["theme.js"],
                "description": "Test theme with effects",
            },
        }
        theme_dir = _write_theme(tmp_path, "test-theme", theme_data)
        static_dir = theme_dir / "static"
        static_dir.mkdir()
        (static_dir / "theme.css").write_text("/* test */", encoding="utf-8")
        (static_dir / "theme.js").write_text("export function init() {}", encoding="utf-8")
        (static_dir / "animations").mkdir()
        (static_dir / "animations" / "float.css").write_text("/* float */", encoding="utf-8")

        data = load_theme("test-theme", tmp_path)
        assert "includes" in data
        assert data["includes"]["css"] == ["theme.css", "animations/float.css"]
        assert data["includes"]["js"] == ["theme.js"]
        assert data["includes"]["description"] == "Test theme with effects"

    def test_includes_rejects_non_list_css(self, tmp_path):
        theme_data = {**FULL_THEME, "includes": {"css": "theme.css"}}
        _write_theme(tmp_path, "bad-theme", theme_data)
        with pytest.raises(ThemeError, match=r"must be a list"):
            load_theme("bad-theme", tmp_path)

    def test_includes_rejects_non_list_js(self, tmp_path):
        theme_data = {**FULL_THEME, "includes": {"js": "theme.js"}}
        _write_theme(tmp_path, "bad-theme", theme_data)
        with pytest.raises(ThemeError, match=r"must be a list"):
            load_theme("bad-theme", tmp_path)

    def test_includes_rejects_non_string_items(self, tmp_path):
        theme_data = {**FULL_THEME, "includes": {"css": ["theme.css", 42]}}
        _write_theme(tmp_path, "bad-theme", theme_data)
        with pytest.raises(ThemeError, match=r"items must be strings"):
            load_theme("bad-theme", tmp_path)

    def test_includes_rejects_missing_css_file(self, tmp_path):
        theme_data = {**FULL_THEME, "includes": {"css": ["missing.css"]}}
        _write_theme(tmp_path, "bad-theme", theme_data)
        with pytest.raises(ThemeError, match="CSS file not found: missing.css"):
            load_theme("bad-theme", tmp_path)

    def test_includes_rejects_missing_js_file(self, tmp_path):
        theme_data = {**FULL_THEME, "includes": {"js": ["missing.js"]}}
        _write_theme(tmp_path, "bad-theme", theme_data)
        with pytest.raises(ThemeError, match="JS file not found: missing.js"):
            load_theme("bad-theme", tmp_path)

    def test_includes_invalid_structure(self, tmp_path):
        theme_data = {**FULL_THEME, "includes": "not-a-dict"}
        _write_theme(tmp_path, "bad-theme", theme_data)
        with pytest.raises(ThemeError, match=r"must be a mapping"):
            load_theme("bad-theme", tmp_path)


class TestGenerateThemeCssIncludes:
    def test_generate_theme_css_returns_include_urls(self, tmp_path):
        theme_data = {
            **FULL_THEME,
            "includes": {"css": ["theme.css"], "js": ["theme.js"]},
        }
        theme_dir = _write_theme(tmp_path, "test-theme", theme_data)
        static_dir = theme_dir / "static"
        static_dir.mkdir()
        (static_dir / "theme.css").write_text("/* test */", encoding="utf-8")
        (static_dir / "theme.js").write_text("export function init() {}", encoding="utf-8")

        styles = generate_theme_css("test-theme", tmp_path)
        assert styles.light_css_urls == ["/themes/test-theme/theme.css"]
        assert styles.light_js_urls == ["/themes/test-theme/theme.js"]
        assert styles.dark_css_urls == ["/themes/test-theme/theme.css"]
        assert styles.dark_js_urls == ["/themes/test-theme/theme.js"]

    def test_generate_theme_css_light_dark_different_includes(self, tmp_path):
        light_data = {**FULL_THEME, "includes": {"css": ["light.css"], "js": ["light.js"]}}
        dark_data = {**FULL_THEME, "includes": {"css": ["dark.css"], "js": ["dark.js"]}}
        light_dir = _write_theme(tmp_path, "light-theme", light_data)
        dark_dir = _write_theme(tmp_path, "dark-theme", dark_data)
        for d in [light_dir, dark_dir]:
            static = d / "static"
            static.mkdir()
            (static / "light.css").write_text("/* */", encoding="utf-8")
            (static / "light.js").write_text("export function init() {}", encoding="utf-8")
            (static / "dark.css").write_text("/* */", encoding="utf-8")
            (static / "dark.js").write_text("export function init() {}", encoding="utf-8")

        styles = generate_theme_css({"light": "light-theme", "dark": "dark-theme"}, tmp_path)
        assert styles.light_css_urls == ["/themes/light-theme/light.css"]
        assert styles.light_js_urls == ["/themes/light-theme/light.js"]
        assert styles.dark_css_urls == ["/themes/dark-theme/dark.css"]
        assert styles.dark_js_urls == ["/themes/dark-theme/dark.js"]

    def test_generate_theme_css_single_theme(self, tmp_path):
        theme_data = {**FULL_THEME, "includes": {"css": ["theme.css"], "js": ["theme.js"]}}
        theme_dir = _write_theme(tmp_path, "single-theme", theme_data)
        static_dir = theme_dir / "static"
        static_dir.mkdir()
        (static_dir / "theme.css").write_text("/* */", encoding="utf-8")
        (static_dir / "theme.js").write_text("export function init() {}", encoding="utf-8")

        styles = generate_theme_css("single-theme", tmp_path)
        assert styles.single is True
        assert styles.light_css_urls == ["/themes/single-theme/theme.css"]
        assert styles.light_js_urls == ["/themes/single-theme/theme.js"]

    def test_includes_not_inherited(self, tmp_path):
        parent_data = {**FULL_THEME, "includes": {"css": ["parent.css"], "js": ["parent.js"]}}
        child_data = {"extends": "parent", "includes": {"css": ["child.css"], "js": ["child.js"]}}
        parent_dir = _write_theme(tmp_path, "parent", parent_data)
        child_dir = _write_theme(tmp_path, "child", child_data)
        for d in [parent_dir, child_dir]:
            static = d / "static"
            static.mkdir()
            (static / "parent.css").write_text("/* */", encoding="utf-8")
            (static / "parent.js").write_text("export function init() {}", encoding="utf-8")
            (static / "child.css").write_text("/* */", encoding="utf-8")
            (static / "child.js").write_text("export function init() {}", encoding="utf-8")

        styles = generate_theme_css("child", tmp_path)
        # Child's includes should replace parent's
        assert styles.light_css_urls == ["/themes/child/child.css"]
        assert styles.light_js_urls == ["/themes/child/child.js"]

    def test_no_includes_returns_empty(self):
        styles = generate_theme_css(None)
        assert styles.light_css_urls == []
        assert styles.light_js_urls == []
        assert styles.dark_css_urls == []
        assert styles.dark_js_urls == []

    def test_builtin_fallback_styles_has_new_fields(self):
        styles = built_in_theme_styles()
        assert styles.light_css_urls == []
        assert styles.light_js_urls == []
        assert styles.dark_css_urls == []
        assert styles.dark_js_urls == []


class TestHalloweenThemes:
    def test_halloween_themes_discovered(self):
        names = discover_themes()
        assert "halloween-light" in names
        assert "halloween-dark" in names

    def test_halloween_themes_declare_own_includes(self):
        for name in ("halloween-light", "halloween-dark"):
            resolved = load_resolved_theme(name)
            assert resolved["includes"] == {"css": ["theme.css"], "js": ["theme.js"]}

    def test_halloween_themes_use_creepster_headings(self):
        for name in ("halloween-light", "halloween-dark"):
            resolved = load_resolved_theme(name)
            assert resolved["fonts"]["page_heading"] == "'Creepster', 'Inter', sans-serif"
            assert resolved["fonts"]["card_heading"] == "'Creepster', 'Inter', sans-serif"
            assert resolved["fonts"]["card_content"] == "'Lato', 'Inter', sans-serif"

    def test_halloween_themes_inherit_radius(self):
        light = load_resolved_theme("halloween-light")
        assert light["radius"]["card"] == "0.5rem"

    def test_halloween_font_links_include_creepster(self):
        styles = generate_theme_css({"light": "halloween-light", "dark": "halloween-dark"})
        assert "/themes/halloween-light/fonts.css" in styles.font_links
        assert "/themes/halloween-dark/fonts.css" in styles.font_links
        assert "--font-page-heading: 'Creepster', 'Inter', sans-serif;" in styles.css
        assert "--font-card-heading: 'Creepster', 'Inter', sans-serif;" in styles.css
        assert "--font-card-content: 'Lato', 'Inter', sans-serif;" in styles.css

    def test_halloween_static_files_exist(self):
        for name in ("halloween-light", "halloween-dark"):
            static_dir = theme_static_dir(name)
            assert (static_dir / "theme.css").is_file()
            assert (static_dir / "theme.js").is_file()
            assert (static_dir / "fonts.css").is_file()
            assert (static_dir / "Creepster-Regular.woff2").is_file()
            assert (static_dir / "Lato-Regular.woff2").is_file()
            assert (static_dir / "Lato-Bold.woff2").is_file()
            fonts_css = (static_dir / "fonts.css").read_text(encoding="utf-8")
            assert "Creepster-Regular.woff2" in fonts_css
            assert "Lato-Regular.woff2" in fonts_css
            assert "Lato-Bold.woff2" in fonts_css

    def test_halloween_pair_emits_include_urls(self):
        styles = generate_theme_css({"light": "halloween-light", "dark": "halloween-dark"})
        assert styles.light_css_urls == ["/themes/halloween-light/theme.css"]
        assert styles.light_js_urls == ["/themes/halloween-light/theme.js"]
        assert styles.dark_css_urls == ["/themes/halloween-dark/theme.css"]
        assert styles.dark_js_urls == ["/themes/halloween-dark/theme.js"]

    def test_halloween_js_has_no_forbidden_global(self):
        for name in ("halloween-light", "halloween-dark"):
            source = (theme_static_dir(name) / "theme.js").read_text(encoding="utf-8")
            assert "themeInitConfig" not in source
            assert "prefers-reduced-motion" in source
            assert "pointerEvents" in source
            assert "requestAnimationFrame" in source
            assert "startFlyby();" in source
            assert "ghost" in source
            assert "witch" not in source
