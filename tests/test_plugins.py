from unittest.mock import Mock

from src.plugins import load_plugin_class, render_card
from src.plugin import Plugin
from src.plugins.html import HtmlPlugin
from src.plugins.rss import RssPlugin
from src.plugins.rss.plugin import RssPlugin as RssPluginDirect
from src import database
from src.config import validate_config, ConfigError
from src.database import init_database


class TestPluginLoading:
    def test_load_html_plugin(self):
        cls = load_plugin_class("html")
        assert cls is HtmlPlugin

    def test_load_rss_plugin(self):
        cls = load_plugin_class("rss")
        assert cls is RssPlugin

    def test_load_unknown_plugin(self):
        cls = load_plugin_class("nonexistent")
        assert cls is None


class TestHtmlPlugin:
    def test_renders_html(self):
        plugin = HtmlPlugin()
        result = plugin.render({"html": "<p>Hello</p>"})
        assert result == "<p>Hello</p>"

    def test_renders_empty_when_no_html(self):
        plugin = HtmlPlugin()
        result = plugin.render({})
        assert result == ""

    def test_renders_empty_when_empty_options(self):
        plugin = HtmlPlugin()
        result = plugin.render({"html": ""})
        assert result == ""

    def test_setup_is_noop(self):
        plugin = HtmlPlugin()
        plugin.setup({}, None, None, None)


class TestRenderCard:
    def test_render_html_card(self):
        instances = {"html": HtmlPlugin()}
        card = {"plugin": "html", "options": {"html": "<p>Test</p>"}}
        result = render_card(card, instances)
        assert result == "<p>Test</p>"

    def test_render_unknown_plugin(self):
        card = {"plugin": "unknown", "options": {}}
        result = render_card(card, {})
        assert "not found" in result


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


class TestRssPlugin:
    def test_rss_is_subclass_of_plugin(self):
        assert issubclass(RssPlugin, Plugin)

    def test_html_is_subclass_of_plugin(self):
        assert issubclass(HtmlPlugin, Plugin)

    def test_rss_init_same_from_both_imports(self):
        assert RssPlugin is RssPluginDirect

    def test_rss_card_requires_options(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "RSS",
                "plugin": "rss",
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "options is required" in str(e)

    def test_rss_card_requires_feeds(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "RSS",
                "plugin": "rss",
                "options": {}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "options" in str(e)

    def test_rss_card_requires_refresh(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "RSS",
                "plugin": "rss",
                "options": {"feeds": ["http://example.com/rss"]}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "refresh" in str(e)

    def test_rss_card_valid_config(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "RSS",
                "plugin": "rss",
                "options": {
                    "feeds": ["http://example.com/rss"],
                    "refresh": "0 */6 * * *"
                }
            }]
        }
        validate_config(config)

    def test_rss_render_empty_when_no_items(self):
        init_database()
        plugin = RssPlugin()
        plugin.setup({}, database, None, Mock())
        result = plugin.render({"feeds": ["http://example.com/rss"]})
        assert result == ""
