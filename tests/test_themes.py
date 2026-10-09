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
    resolve_theme,
    theme_chain,
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
    },
    "fonts": {"family": "Arial, sans-serif"},
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
        assert data["fonts"]["family"] == "'Inter', sans-serif"
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
        assert resolved["fonts"]["family"] == "Arial, sans-serif"
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
        _write_theme(tmp_path, "empty-font", {**FULL_THEME, "fonts": {"family": ""}})
        with pytest.raises(ThemeError, match="fonts.family"):
            load_resolved_theme("empty-font", tmp_path)

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
            "--font-family:", "--card-radius:",
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
