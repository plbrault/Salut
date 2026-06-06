from unittest.mock import Mock, MagicMock
from pathlib import Path

from src.plugins import load_plugin_class, render_card, setup_card
from src.plugin import Plugin
from src.plugins.html import HtmlPlugin
from src.plugins.rss import RssPlugin
from src.plugins.rss.plugin import RssPlugin as RssPluginDirect
from src.database import Database
from src.config import validate_config, ConfigError


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

    def test_setup_database_is_noop(self, tmp_path):
        HtmlPlugin.setup_database(Database(tmp_path / "test.db"))


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

    def test_rss_card_requires_schedule(self):
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
            assert "schedule" in str(e)

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
                    "schedule": "0 */6 * * *"
                }
            }]
        }
        validate_config(config)

    def test_rss_render_empty_when_no_items(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.setup_database(db)
        plugin = RssPlugin()
        plugin.setup({}, db, None, Mock())
        plugin._delete_feed_items(plugin._card_id)  # pylint: disable=protected-access
        result = plugin.render({})
        assert result == ""
        db.close()

    def test_rss_render_with_items(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.setup_database(db)
        options = {"feeds": ["http://example.com/rss"]}
        plugin = RssPlugin()
        plugin.setup(options, db, MagicMock(), Mock())
        plugin._delete_feed_items(plugin._card_id)  # pylint: disable=protected-access
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="http://example.com/rss",
            title="Test Article",
            link="http://example.com/article",
            published="2026-01-01T00:00:00",
            feed_url="http://feeds.example.com/rss",
            image_url="",
            feed_title="Example Feed",
        )
        result = plugin.render(options)
        assert "Test Article" in result
        assert "Example Feed" in result
        assert 'href="http://example.com/article"' in result
        db.close()

    def test_rss_render_strips_www_from_source(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.setup_database(db)
        options = {"feeds": ["https://www.example.com/rss"]}
        plugin = RssPlugin()
        plugin.setup(options, db, MagicMock(), Mock())
        plugin._delete_feed_items(plugin._card_id)  # pylint: disable=protected-access
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="https://www.example.com/rss",
            title="Test",
            link="https://www.example.com/article",
            published="2026-01-01T00:00:00",
            feed_url="https://www.example.com/feed.xml",
            image_url="",
            feed_title="",
        )
        result = plugin.render(options)
        assert "example.com" in result
        assert ">example.com<" in result
        db.close()

    def test_rss_render_prefers_feed_title(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.setup_database(db)
        options = {"feeds": ["https://www.example.com/rss"]}
        plugin = RssPlugin()
        plugin.setup(options, db, MagicMock(), Mock())
        plugin._delete_feed_items(plugin._card_id)  # pylint: disable=protected-access
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="https://www.example.com/rss",
            title="Test",
            link="https://www.example.com/article",
            published="2026-01-01T00:00:00",
            feed_url="https://www.example.com/feed.xml",
            image_url="",
            feed_title="My Cool Blog",
        )
        result = plugin.render(options)
        assert "My Cool Blog" in result
        assert ">My Cool Blog<" in result
        db.close()

    def test_rss_render_with_image(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.setup_database(db)
        options = {"feeds": ["http://example.com/rss"]}
        plugin = RssPlugin()
        plugin.setup(options, db, MagicMock(), Mock())
        plugin._delete_feed_items(plugin._card_id)  # pylint: disable=protected-access
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="http://example.com/rss",
            title="Test",
            link="http://example.com/article",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/feed.xml",
            image_url="/cache/rss/abc123/0.jpg",
            feed_title="Example",
        )
        result = plugin.render(options)
        assert "/cache/rss/abc123/0.jpg" in result
        db.close()


class TestLoadTemplate:  # pylint: disable=too-few-public-methods
    def test_load_template_returns_template(self):
        template_dir = Path(__file__).resolve().parent.parent / "src" / "plugins" / "rss"
        template = Plugin.load_template(template_dir, "template.html")
        result = template.render(items=[])
        assert result.strip() != ""


class TestMultipleRssCards:  # pylint: disable=too-few-public-methods
    def test_each_card_gets_its_own_setup(self):
        db = Mock()
        sched = Mock()
        card1 = {"plugin": "rss", "options": {
            "feeds": ["http://a.com/rss"],
            "schedule": "0 */6 * * *",
        }}
        card2 = {"plugin": "rss", "options": {
            "feeds": ["http://b.com/rss"],
            "schedule": "0 */6 * * *",
        }}
        inst1 = setup_card(card1, db, sched)
        inst2 = setup_card(card2, db, sched)
        assert inst1 is not None
        assert inst2 is not None
        assert inst1._card_id != inst2._card_id  # pylint: disable=protected-access
