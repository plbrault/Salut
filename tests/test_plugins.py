from src.plugins import load_plugin, render_card
from src.plugins.html import render as html_render
from src.config import validate_config


class TestPluginLoading:
    def test_load_html_plugin(self):
        render = load_plugin("html")
        assert render is not None
        assert callable(render)

    def test_load_unknown_plugin(self):
        render = load_plugin("nonexistent")
        assert render is None


class TestHtmlPlugin:
    def test_renders_html(self):
        result = html_render({"html": "<p>Hello</p>"})
        assert result == "<p>Hello</p>"

    def test_renders_empty_when_no_html(self):
        result = html_render({})
        assert result == ""

    def test_renders_empty_when_empty_options(self):
        result = html_render({"html": ""})
        assert result == ""


class TestRenderCard:
    def test_render_html_card(self):
        card = {"plugin": "html", "options": {"html": "<p>Test</p>"}}
        result = render_card(card)
        assert result == "<p>Test</p>"

    def test_render_unknown_plugin(self):
        card = {"plugin": "unknown", "options": {}}
        result = render_card(card)
        assert "not found" in result

    def test_render_with_exception(self):
        card = {"plugin": "html", "options": {"html": "test"}}
        result = render_card(card)
        assert result == "test"


class TestColspan:
    def test_colspan_in_config(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Card",
                "plugin": "html",
                "options": {"html": "<p>Test</p>"},
                "colspan": 2,
            }]
        }
        validate_config(config)

    def test_colspan_default(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Card",
                "plugin": "html",
                "options": {"html": "<p>Test</p>"},
            }]
        }
        validate_config(config)
