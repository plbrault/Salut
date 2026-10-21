import yaml

import pytest

from src.themes import (
    ThemeError,
    _rewrite_relative_urls,
    built_in_theme_styles,
    discover_themes,
    font_css_text,
    generate_theme_css,
    include_css_texts,
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

    def test_font_css_covers_inheritance_chain(self):
        styles = generate_theme_css(None)
        assert "font-family: 'Inter';" in styles.font_css
        assert "url('/themes/default-light/Inter-Variable.woff2')" in styles.font_css

    def test_font_css_deduplicates_shared_parent(self, tmp_path):
        _write_theme(tmp_path, "parent", FULL_THEME)
        (tmp_path / "parent" / "static").mkdir()
        (tmp_path / "parent" / "static" / "fonts.css").write_text(
            "@font-face { src: url('parent.woff2'); }", encoding="utf-8"
        )
        _write_theme(tmp_path, "light", {"extends": "parent"})
        _write_theme(tmp_path, "dark", {"extends": "parent"})

        text = font_css_text(["light", "dark"], tmp_path)

        assert text.count("parent.woff2") == 1
        assert "url('/themes/parent/parent.woff2')" in text

    def test_font_css_orders_parent_before_child(self, tmp_path):
        _write_theme(tmp_path, "parent", FULL_THEME)
        (tmp_path / "parent" / "static").mkdir()
        (tmp_path / "parent" / "static" / "fonts.css").write_text(
            "/* parent-fonts */", encoding="utf-8"
        )
        child_dir = _write_theme(tmp_path, "child", {"extends": "parent"})
        (child_dir / "static").mkdir()
        (child_dir / "static" / "fonts.css").write_text(
            "/* child-fonts */", encoding="utf-8"
        )

        text = font_css_text(["child"], tmp_path)

        assert text.index("parent-fonts") < text.index("child-fonts")

    def test_font_css_skips_themes_without_fonts_css(self, tmp_path):
        _write_theme(tmp_path, "bare", FULL_THEME)
        assert not font_css_text(["bare"], tmp_path)

    def test_builtin_fallback_styles(self):
        styles = built_in_theme_styles()
        assert styles.single is False
        assert "--bg: #f3f4f6;" in styles.css
        assert "--bg: #111827;" in styles.css
        assert "url('/themes/default-light/Inter-Variable.woff2')" in styles.font_css


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


class TestRewriteRelativeUrls:
    def test_rewrites_bare_relative_url(self):
        css = 'src: url(font.woff2);'
        assert _rewrite_relative_urls(css, "my-theme") == \
            "src: url(/themes/my-theme/font.woff2);"

    def test_rewrites_quoted_and_spaced_urls(self):
        assert _rewrite_relative_urls('src: url("a/b.woff2");', "t") == \
            'src: url("/themes/t/a/b.woff2");'
        assert _rewrite_relative_urls("src: url( 'c.woff2' );", "t") == \
            "src: url('/themes/t/c.woff2');"

    def test_leaves_non_relative_urls_untouched(self):
        for url in (
            "data:font/woff2;base64,AAA",
            "https://example.com/f.woff2",
            "http://example.com/f.woff2",
            "//example.com/f.woff2",
            "/themes/other/f.woff2",
            "#fragment",
        ):
            css = f"src: url({url});"
            assert _rewrite_relative_urls(css, "t") == css


class TestGenerateThemeCssIncludes:
    def test_include_css_texts_rewrite_relative_urls(self, tmp_path):
        theme_dir = _write_theme(tmp_path, "art", FULL_THEME)
        static_dir = theme_dir / "static"
        static_dir.mkdir()
        (static_dir / "theme.css").write_text(
            '.bg { background-image: url("pumpkin.svg"); }', encoding="utf-8"
        )

        texts = include_css_texts({"css": ["theme.css"]}, "art", tmp_path)

        assert texts == ['.bg { background-image: url("/themes/art/pumpkin.svg"); }']

    def test_include_css_texts_preserve_file_order(self, tmp_path):
        theme_dir = _write_theme(
            tmp_path, "multi",
            {**FULL_THEME, "includes": {"css": ["one.css", "two.css"]}},
        )
        static_dir = theme_dir / "static"
        static_dir.mkdir()
        (static_dir / "one.css").write_text("/* one */", encoding="utf-8")
        (static_dir / "two.css").write_text("/* two */", encoding="utf-8")

        texts = include_css_texts({"css": ["one.css", "two.css"]}, "multi", tmp_path)

        assert texts == ["/* one */", "/* two */"]

    def test_generate_theme_css_returns_include_texts(self, tmp_path):
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
        assert styles.light_css_texts == ["/* test */"]
        assert styles.light_js_urls == ["/themes/test-theme/theme.js"]
        assert styles.dark_css_texts == ["/* test */"]
        assert styles.dark_js_urls == ["/themes/test-theme/theme.js"]

    def test_generate_theme_css_light_dark_different_includes(self, tmp_path):
        light_data = {**FULL_THEME, "includes": {"css": ["light.css"], "js": ["light.js"]}}
        dark_data = {**FULL_THEME, "includes": {"css": ["dark.css"], "js": ["dark.js"]}}
        light_dir = _write_theme(tmp_path, "light-theme", light_data)
        dark_dir = _write_theme(tmp_path, "dark-theme", dark_data)
        for d in [light_dir, dark_dir]:
            static = d / "static"
            static.mkdir()
            (static / "light.css").write_text("/* light */", encoding="utf-8")
            (static / "light.js").write_text("export function init() {}", encoding="utf-8")
            (static / "dark.css").write_text("/* dark */", encoding="utf-8")
            (static / "dark.js").write_text("export function init() {}", encoding="utf-8")

        styles = generate_theme_css({"light": "light-theme", "dark": "dark-theme"}, tmp_path)
        assert styles.light_css_texts == ["/* light */"]
        assert styles.light_js_urls == ["/themes/light-theme/light.js"]
        assert styles.dark_css_texts == ["/* dark */"]
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
        assert styles.light_css_texts == ["/* */"]
        assert styles.light_js_urls == ["/themes/single-theme/theme.js"]

    def test_includes_not_inherited(self, tmp_path):
        parent_data = {**FULL_THEME, "includes": {"css": ["parent.css"], "js": ["parent.js"]}}
        child_data = {"extends": "parent", "includes": {"css": ["child.css"], "js": ["child.js"]}}
        parent_dir = _write_theme(tmp_path, "parent", parent_data)
        child_dir = _write_theme(tmp_path, "child", child_data)
        for d in [parent_dir, child_dir]:
            static = d / "static"
            static.mkdir()
            (static / "parent.css").write_text("/* parent */", encoding="utf-8")
            (static / "parent.js").write_text("export function init() {}", encoding="utf-8")
            (static / "child.css").write_text("/* child */", encoding="utf-8")
            (static / "child.js").write_text("export function init() {}", encoding="utf-8")

        styles = generate_theme_css("child", tmp_path)
        # Child's includes should replace parent's
        assert styles.light_css_texts == ["/* child */"]
        assert styles.light_js_urls == ["/themes/child/child.js"]

    def test_no_includes_returns_empty(self):
        styles = generate_theme_css(None)
        assert styles.light_css_texts == []
        assert styles.light_js_urls == []
        assert styles.dark_css_texts == []
        assert styles.dark_js_urls == []

    def test_builtin_fallback_styles_has_new_fields(self):
        styles = built_in_theme_styles()
        assert styles.light_css_texts == []
        assert styles.light_js_urls == []
        assert styles.dark_css_texts == []
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

    def test_halloween_dark_extends_halloween_light(self):
        assert theme_chain("halloween-dark") == ["default-light", "halloween-light", "halloween-dark"]

    def test_halloween_light_sets_font_roles(self):
        resolved = load_resolved_theme("halloween-light")
        assert resolved["fonts"]["page_heading"] == "'Creepster', 'Inter', sans-serif"
        assert resolved["fonts"]["card_heading"] == "'Creepster', 'Inter', sans-serif"
        assert resolved["fonts"]["card_content"] == "'Lato', 'Inter', sans-serif"

    def test_halloween_dark_inherits_fonts(self):
        resolved = load_resolved_theme("halloween-dark")
        assert resolved["fonts"]["page_heading"] == "'Creepster', 'Inter', sans-serif"
        assert resolved["fonts"]["card_heading"] == "'Creepster', 'Inter', sans-serif"
        assert resolved["fonts"]["card_content"] == "'Lato', 'Inter', sans-serif"

    def test_halloween_dark_pins_danger_colors(self):
        resolved = load_resolved_theme("halloween-dark")
        assert resolved["colors"]["danger"] == "#ef4444"
        assert resolved["colors"]["danger_hover"] == "#f87171"
        assert resolved["colors"]["danger_contrast"] == "#111827"

    def test_halloween_themes_inherit_radius(self):
        light = load_resolved_theme("halloween-light")
        assert light["radius"]["card"] == "0.5rem"

    def test_halloween_font_css_inlines_creepster(self):
        styles = generate_theme_css({"light": "halloween-light", "dark": "halloween-dark"})
        assert "Creepster" in styles.font_css
        assert "url('/themes/halloween-light/Creepster-Regular.woff2')" in styles.font_css
        assert "url('/themes/default-light/Inter-Variable.woff2')" in styles.font_css
        assert styles.font_css.index("Inter-Variable") < styles.font_css.index("Creepster")
        assert "--font-page-heading: 'Creepster', 'Inter', sans-serif;" in styles.css
        assert "--font-card-heading: 'Creepster', 'Inter', sans-serif;" in styles.css
        assert "--font-card-content: 'Lato', 'Inter', sans-serif;" in styles.css
        assert "--danger: #ef4444;" in styles.css

    def test_halloween_static_files_exist(self):
        static_dir = theme_static_dir("halloween-light")
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

    def test_halloween_dark_has_no_duplicated_font_files(self):
        static_dir = theme_static_dir("halloween-dark")
        assert (static_dir / "theme.css").is_file()
        assert (static_dir / "theme.js").is_file()
        assert not (static_dir / "fonts.css").exists()
        assert not (static_dir / "Creepster-Regular.woff2").exists()
        assert not (static_dir / "Lato-Regular.woff2").exists()
        assert not (static_dir / "Lato-Bold.woff2").exists()

    def test_halloween_pair_inlines_include_css(self):
        styles = generate_theme_css({"light": "halloween-light", "dark": "halloween-dark"})
        assert len(styles.light_css_texts) == 1
        assert len(styles.dark_css_texts) == 1
        assert "radial-gradient" in styles.light_css_texts[0]
        assert "body .card" in styles.dark_css_texts[0]
        assert styles.light_js_urls == ["/themes/halloween-light/theme.js"]
        assert styles.dark_js_urls == ["/themes/halloween-dark/theme.js"]

    def test_halloween_js_has_no_forbidden_global(self):
        for name in ("halloween-light", "halloween-dark"):
            source = (theme_static_dir(name) / "theme.js").read_text(encoding="utf-8")
            assert "themeInitConfig" not in source
            assert "runSky" in source

    def test_halloween_engine_holds_flight_behavior(self):
        source = (theme_static_dir("halloween-light") / "engine.js").read_text(encoding="utf-8")
        assert "themeInitConfig" not in source
        assert "prefers-reduced-motion" in source
        assert "pointerEvents" in source
        assert "requestAnimationFrame" in source
        assert "startFlyby();" in source
        assert "ghost" in source
        assert "witch" not in source
        assert "entered" in source
        assert "measureText" in source
        assert source.index("ctx.font = ") < source.index("measureText")

    def test_halloween_dark_card_border_beats_base_rule(self):
        css = (theme_static_dir("halloween-dark") / "theme.css").read_text(encoding="utf-8")
        assert "body .card" in css
        assert "border-color: rgba(249, 115, 22, 0.35);" in css

    def test_halloween_dark_imports_shared_engine(self):
        light_entry = (theme_static_dir("halloween-light") / "theme.js").read_text(encoding="utf-8")
        assert 'import { runSky } from "./engine.js";' in light_entry
        assert "runSky({ ghost: [0.16, 0.16], bat: [0.22, 0.2] });" in light_entry
        dark_entry = (theme_static_dir("halloween-dark") / "theme.js").read_text(encoding="utf-8")
        assert 'import { runSky } from "/themes/halloween-light/engine.js";' in dark_entry
        assert "runSky({ ghost: [0.22, 0.2], bat: [0.3, 0.25] });" in dark_entry


class TestNeubrutalistThemes:
    def test_neubrutalist_themes_discovered(self):
        names = discover_themes()
        assert "neubrutalist-light" in names
        assert "neubrutalist-dark" in names

    def test_neubrutalist_themes_declare_own_css_only_includes(self):
        for name in ("neubrutalist-light", "neubrutalist-dark"):
            resolved = load_resolved_theme(name)
            assert resolved["includes"] == {"css": ["theme.css"]}

    def test_neubrutalist_dark_extends_neubrutalist_light(self):
        assert theme_chain("neubrutalist-dark") == [
            "default-light",
            "neubrutalist-light",
            "neubrutalist-dark",
        ]

    def test_neubrutalist_light_sets_font_roles(self):
        resolved = load_resolved_theme("neubrutalist-light")
        assert resolved["fonts"]["page_heading"] == "'Archivo Black', 'Inter', sans-serif"
        assert resolved["fonts"]["card_heading"] == "'Archivo Black', 'Inter', sans-serif"
        assert resolved["fonts"]["card_content"] == "'Inter', sans-serif"

    def test_neubrutalist_dark_inherits_fonts(self):
        resolved = load_resolved_theme("neubrutalist-dark")
        assert resolved["fonts"]["page_heading"] == "'Archivo Black', 'Inter', sans-serif"
        assert resolved["fonts"]["card_heading"] == "'Archivo Black', 'Inter', sans-serif"
        assert resolved["fonts"]["card_content"] == "'Inter', sans-serif"

    def test_neubrutalist_light_owns_full_palette(self):
        resolved = load_resolved_theme("neubrutalist-light")
        assert resolved["colors"]["bg"] == "#fffbeb"
        assert resolved["colors"]["border"] == "#000000"
        assert resolved["colors"]["accent"] == "#ffe14d"
        assert resolved["colors"]["accent_contrast"] == "#111111"
        assert palette_is_dark(resolved) is False

    def test_neubrutalist_dark_overrides_full_palette(self):
        resolved = load_resolved_theme("neubrutalist-dark")
        assert resolved["colors"]["bg"] == "#141414"
        assert resolved["colors"]["border"] == "#e5e5e5"
        assert resolved["colors"]["accent_contrast"] == "#141414"
        assert resolved["colors"]["danger"] == "#ff6b6b"
        assert palette_is_dark(resolved) is True

    def test_neubrutalist_themes_squarish_cards(self):
        for name in ("neubrutalist-light", "neubrutalist-dark"):
            assert load_resolved_theme(name)["radius"]["card"] == "0"

    def test_neubrutalist_font_css_inlines_archivo_black(self):
        styles = generate_theme_css({"light": "neubrutalist-light", "dark": "neubrutalist-dark"})
        assert "Archivo Black" in styles.font_css
        assert "url('/themes/neubrutalist-light/ArchivoBlack-Regular.woff2')" in styles.font_css
        assert "url('/themes/default-light/Inter-Variable.woff2')" in styles.font_css
        assert styles.font_css.index("Inter-Variable") < styles.font_css.index("ArchivoBlack")
        assert "--font-page-heading: 'Archivo Black', 'Inter', sans-serif;" in styles.css
        assert "--font-card-content: 'Inter', sans-serif;" in styles.css
        assert "--card-radius: 0;" in styles.css
        assert "--border: #000000;" in styles.css

    def test_neubrutalist_static_files_exist(self):
        static_dir = theme_static_dir("neubrutalist-light")
        assert (static_dir / "theme.css").is_file()
        assert (static_dir / "fonts.css").is_file()
        assert (static_dir / "ArchivoBlack-Regular.woff2").is_file()
        fonts_css = (static_dir / "fonts.css").read_text(encoding="utf-8")
        assert "ArchivoBlack-Regular.woff2" in fonts_css

    def test_neubrutalist_dark_has_no_duplicated_font_files(self):
        static_dir = theme_static_dir("neubrutalist-dark")
        assert (static_dir / "theme.css").is_file()
        assert not (static_dir / "fonts.css").exists()
        assert not (static_dir / "ArchivoBlack-Regular.woff2").exists()

    def test_neubrutalist_pair_inlines_include_css(self):
        styles = generate_theme_css({"light": "neubrutalist-light", "dark": "neubrutalist-dark"})
        assert len(styles.light_css_texts) == 1
        assert len(styles.dark_css_texts) == 1
        for css_text in (styles.light_css_texts[0], styles.dark_css_texts[0]):
            assert "body .card" in css_text
            assert "box-shadow: 4px 4px 0 var(--border);" in css_text
            assert "translate: 2px 2px;" in css_text

    def test_neubrutalist_css_beats_base_card_rule(self):
        for name in ("neubrutalist-light", "neubrutalist-dark"):
            css = (theme_static_dir(name) / "theme.css").read_text(encoding="utf-8")
            assert "body .card {" in css
            assert "text-shadow" in css
