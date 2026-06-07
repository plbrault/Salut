import json
import struct
import tempfile
from unittest.mock import Mock, MagicMock
from pathlib import Path

from src.plugins import load_plugin_class, render_card, setup_card
from src.plugin import Plugin
from src.plugins.html import HtmlPlugin
from src.plugins.rss import RssPlugin
from src.plugins.rss.plugin import RssPlugin as RssPluginDirect
from src.plugins.search import SearchPlugin
from src.plugins.weather import WeatherPlugin
from src.plugins.weather.plugin import WMO_ICONS
from src.plugins.calendar import CalendarPlugin
from src.plugins.xkcd import XkcdPlugin
from src.plugins.image import ImagePlugin
from src.database import Database
from src.config import validate_config, ConfigError
from src.i18n import _load_translations


class TestPluginLoading:
    def test_load_html_plugin(self):
        cls = load_plugin_class("html")
        assert cls is HtmlPlugin

    def test_load_rss_plugin(self):
        cls = load_plugin_class("rss")
        assert cls is RssPlugin

    def test_load_weather_plugin(self):
        cls = load_plugin_class("weather")
        assert cls is WeatherPlugin

    def test_load_unknown_plugin(self):
        cls = load_plugin_class("nonexistent")
        assert cls is None


class TestPluginCardStyleRules:
    def test_html_card_style_rules_returns_dict(self):
        assert isinstance(HtmlPlugin.card_style_rules(), dict)

    def test_rss_card_style_rules_returns_dict(self):
        assert isinstance(RssPlugin.card_style_rules(), dict)

    def test_search_card_style_rules_returns_dict(self):
        assert isinstance(SearchPlugin.card_style_rules(), dict)

    def test_weather_card_style_rules_returns_dict(self):
        assert isinstance(WeatherPlugin.card_style_rules(), dict)

    def test_all_plugins_have_card_style_rules(self):
        for plugin_cls in [HtmlPlugin, RssPlugin, SearchPlugin, WeatherPlugin]:
            assert hasattr(plugin_cls, "card_style_rules")
            assert callable(plugin_cls.card_style_rules)


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

    def test_init_schema_is_noop(self, tmp_path):
        HtmlPlugin.init_schema(Database(tmp_path / "test.db"))


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
        RssPlugin.init_schema(db)
        plugin = RssPlugin()
        plugin.setup({}, db, None, Mock())
        plugin._delete_feed_items(plugin._card_id)  # pylint: disable=protected-access
        result = plugin.render({})
        assert result == ""
        db.close()

    def test_rss_render_with_items(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.init_schema(db)
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
        RssPlugin.init_schema(db)
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
        RssPlugin.init_schema(db)
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
        RssPlugin.init_schema(db)
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


class TestSearchPlugin:
    def test_load_search_plugin(self):
        cls = load_plugin_class("search")
        assert cls is not None

    def test_search_is_subclass_of_plugin(self):
        assert issubclass(SearchPlugin, Plugin)

    def test_search_card_requires_options(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "options is required" in str(e)

    def test_search_card_requires_provider(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
                "options": {}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "provider" in str(e) or "options" in str(e)

    def test_search_card_invalid_provider(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
                "options": {"provider": "google"}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "duckduckgo" in str(e)

    def test_search_card_valid_config(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
                "options": {"provider": "duckduckgo"}
            }]
        }
        validate_config(config)

    def test_search_render_with_default_button_text(self):
        plugin = SearchPlugin()
        i18n_dir = Path(__file__).resolve().parent.parent / "src" / "plugins" / "search" / "i18n"
        plugin.set_translations(_load_translations(i18n_dir, "en"))
        result = plugin.render({"provider": "duckduckgo"})
        assert "Search" in result
        assert 'type="submit"' in result

    def test_search_form_submits_to_duckduckgo(self):
        plugin = SearchPlugin()
        result = plugin.render({"provider": "duckduckgo"})
        assert 'action="https://duckduckgo.com/"' in result

    def test_search_render_with_custom_button_text(self):
        plugin = SearchPlugin()
        result = plugin.render({"provider": "duckduckgo", "button_text": "Go"})
        assert "Go" in result
        assert 'type="submit"' in result

    def test_search_results_in_new_tab(self):
        plugin = SearchPlugin()
        result = plugin.render({"provider": "duckduckgo", "results_in_new_tab": True})
        assert 'target="_blank"' in result

    def test_search_results_in_same_tab_by_default(self):
        plugin = SearchPlugin()
        result = plugin.render({"provider": "duckduckgo"})
        assert 'target="_blank"' not in result

    def test_search_button_text_must_be_string(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
                "options": {"provider": "duckduckgo", "button_text": 123}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "button_text" in str(e)

    def test_search_results_in_new_tab_must_be_boolean(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
                "options": {"provider": "duckduckgo", "results_in_new_tab": "yes"}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "results_in_new_tab" in str(e)

    def test_search_wikipedia_provider(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
                "options": {"provider": "wikipedia"}
            }]
        }
        validate_config(config)

    def test_search_wikipedia_with_custom_language(self):
        plugin = SearchPlugin()
        result = plugin.render({"provider": "wikipedia", "language": "fr"})
        assert 'action="https://fr.wikipedia.org/w/index.php"' in result

    def test_search_wikipedia_default_language(self):
        plugin = SearchPlugin()
        result = plugin.render({"provider": "wikipedia"})
        assert 'action="https://en.wikipedia.org/w/index.php"' in result

    def test_search_language_must_be_string(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
                "options": {"provider": "wikipedia", "language": 123}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "language" in str(e)


class TestSearchPluginPlaceholder:
    def test_search_render_with_custom_placeholder_text(self):
        plugin = SearchPlugin()
        result = plugin.render({"provider": "duckduckgo", "placeholder_text": "Search the web..."})
        assert 'placeholder="Search the web..."' in result

    def test_search_render_with_default_placeholder_text(self):
        plugin = SearchPlugin()
        i18n_dir = Path(__file__).resolve().parent.parent / "src" / "plugins" / "search" / "i18n"
        plugin.set_translations(_load_translations(i18n_dir, "en"))
        result = plugin.render({"provider": "duckduckgo"})
        assert 'placeholder="Search"' in result

    def test_search_independent_placeholder_and_button_text(self):
        plugin = SearchPlugin()
        result = plugin.render({"provider": "duckduckgo", "placeholder_text": "Type here...", "button_text": "Go"})
        assert 'placeholder="Type here..."' in result
        assert "Go" in result

    def test_search_placeholder_text_must_be_string(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Search",
                "plugin": "search",
                "options": {"provider": "duckduckgo", "placeholder_text": 123}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "placeholder_text" in str(e)


class TestWeatherPlugin:  # pylint: disable=too-many-public-methods
    def _valid_options(self, **overrides):
        opts = {
            "provider": "open-meteo",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "location_name": "Paris",
            "schedule": "0 */2 * * *",
        }
        opts.update(overrides)
        return opts

    def test_load_weather_plugin(self):
        cls = load_plugin_class("weather")
        assert cls is WeatherPlugin

    def test_weather_is_subclass_of_plugin(self):
        assert issubclass(WeatherPlugin, Plugin)

    def test_weather_card_style_rules_returns_dict(self):
        assert isinstance(WeatherPlugin.card_style_rules(), dict)

    def test_weather_requires_options(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "options is required" in str(e)

    def test_weather_requires_provider(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": {"latitude": 48.8566, "longitude": 2.3522, "location_name": "Paris"}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "provider" in str(e)

    def test_weather_requires_open_meteo_provider(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": {
                    "provider": "weather-com",
                    "latitude": 48.8566,
                    "longitude": 2.3522,
                    "location_name": "Paris"
                }
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "open-meteo" in str(e)

    def test_weather_requires_latitude(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": {"provider": "open-meteo", "longitude": 2.3522, "location_name": "Paris"}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "latitude" in str(e)

    def test_weather_requires_longitude(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": {"provider": "open-meteo", "latitude": 48.8566, "location_name": "Paris"}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "longitude" in str(e)

    def test_weather_requires_location_name(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": {"provider": "open-meteo", "latitude": 48.8566, "longitude": 2.3522}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "location_name" in str(e)

    def test_weather_requires_schedule(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": self._valid_options(schedule=None)
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "schedule" in str(e)

    def test_weather_invalid_schedule_format(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": self._valid_options(schedule="invalid")
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "cron" in str(e)

    def test_weather_invalid_units(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": self._valid_options(units="kelvin")
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "units" in str(e)

    def test_weather_invalid_link_url_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": self._valid_options(link_url=123)
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "link_url" in str(e)

    def test_weather_valid_config(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": self._valid_options()
            }]
        }
        validate_config(config)

    def test_weather_valid_config_with_optional_fields(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": self._valid_options(
                    latitude=45.50884,
                    longitude=-73.58781,
                    location_name="Montréal (Québec)",
                    units="fahrenheit",
                    language="fr",
                    link_url="https://example.com"
                )
            }]
        }
        validate_config(config)

    def test_wmo_code_mapping(self):
        assert WMO_ICONS[0] == ("☀️", "Clear sky")
        assert WMO_ICONS[3] == ("☁️", "Overcast")
        assert WMO_ICONS[61] == ("🌧️", "Slight rain")
        assert WMO_ICONS[71] == ("❄️", "Slight snow")
        assert WMO_ICONS[95] == ("⛈️", "Thunderstorm")

    def test_wmo_unknown_code_returns_default(self):
        icon, desc = WMO_ICONS.get(999, ("🌡️", "Unknown"))
        assert icon == "🌡️"
        assert desc == "Unknown"

    def test_compute_card_id(self):
        options = self._valid_options()
        card_id = WeatherPlugin._compute_card_id(options)  # pylint: disable=protected-access
        assert isinstance(card_id, str)
        assert len(card_id) == 16

    def test_compute_card_id_same_options_same_id(self):
        opts1 = self._valid_options()
        opts2 = self._valid_options()
        assert WeatherPlugin._compute_card_id(opts1) == WeatherPlugin._compute_card_id(opts2)  # pylint: disable=protected-access

    def test_compute_card_id_different_options_different_id(self):
        opts1 = self._valid_options(location_name="Paris")
        opts2 = self._valid_options(location_name="London")
        assert WeatherPlugin._compute_card_id(opts1) != WeatherPlugin._compute_card_id(opts2)  # pylint: disable=protected-access

    def test_render_empty_when_no_data(self, tmp_path):
        db = Database(tmp_path / "test.db")
        WeatherPlugin.init_schema(db)
        plugin = WeatherPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = "test"  # pylint: disable=protected-access
        result = plugin.render(self._valid_options())
        assert "unavailable" in result
        db.close()

    def test_render_with_cached_data(self, tmp_path):
        db = Database(tmp_path / "test.db")
        WeatherPlugin.init_schema(db)
        options = self._valid_options()
        plugin = WeatherPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = plugin._compute_card_id(options)  # pylint: disable=protected-access
        weather_data = {
            "current": {
                "temperature_2m": 20,
                "apparent_temperature": 18,
                "relative_humidity_2m": 65,
                "weather_code": 0,
                "wind_speed_10m": 10,
                "is_day": 1,
            }
        }
        db.execute(
            "INSERT INTO weather_data (card_id, data) VALUES (?, ?)",
            (plugin._card_id, json.dumps(weather_data)),  # pylint: disable=protected-access
        )
        result = plugin.render(options)
        assert "20" in result
        assert "☀️" in result
        assert "Clear sky" in result
        assert "Paris" in result
        db.close()

    def test_render_night_icon(self, tmp_path):
        db = Database(tmp_path / "test.db")
        WeatherPlugin.init_schema(db)
        options = self._valid_options()
        plugin = WeatherPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = plugin._compute_card_id(options)  # pylint: disable=protected-access
        weather_data = {
            "current": {
                "temperature_2m": 15,
                "apparent_temperature": 13,
                "relative_humidity_2m": 70,
                "weather_code": 0,
                "wind_speed_10m": 5,
                "is_day": 0,
            }
        }
        db.execute(
            "INSERT INTO weather_data (card_id, data) VALUES (?, ?)",
            (plugin._card_id, json.dumps(weather_data)),  # pylint: disable=protected-access
        )
        result = plugin.render(options)
        assert "🌙" in result
        db.close()

    def test_render_with_link_url(self, tmp_path):
        db = Database(tmp_path / "test.db")
        WeatherPlugin.init_schema(db)
        options = self._valid_options(link_url="https://example.com/weather")
        plugin = WeatherPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = plugin._compute_card_id(options)  # pylint: disable=protected-access
        weather_data = {
            "current": {
                "temperature_2m": 20,
                "apparent_temperature": 18,
                "relative_humidity_2m": 65,
                "weather_code": 0,
                "wind_speed_10m": 10,
                "is_day": 1,
            }
        }
        db.execute(
            "INSERT INTO weather_data (card_id, data) VALUES (?, ?)",
            (plugin._card_id, json.dumps(weather_data)),  # pylint: disable=protected-access
        )
        result = plugin.render(options)
        assert '<a href="https://example.com/weather"' in result
        assert 'target="_blank"' in result
        db.close()

    def test_render_without_link_url(self, tmp_path):
        db = Database(tmp_path / "test.db")
        WeatherPlugin.init_schema(db)
        options = self._valid_options()
        plugin = WeatherPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = plugin._compute_card_id(options)  # pylint: disable=protected-access
        weather_data = {
            "current": {
                "temperature_2m": 20,
                "apparent_temperature": 18,
                "relative_humidity_2m": 65,
                "weather_code": 0,
                "wind_speed_10m": 10,
                "is_day": 1,
            }
        }
        db.execute(
            "INSERT INTO weather_data (card_id, data) VALUES (?, ?)",
            (plugin._card_id, json.dumps(weather_data)),  # pylint: disable=protected-access
        )
        result = plugin.render(options)
        assert 'class="block text-inherit no-underline"' not in result
        assert "open-meteo.com" in result
        db.close()

    def test_weather_card_css_class(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Weather",
                "plugin": "weather",
                "options": self._valid_options()
            }]
        }
        validate_config(config)

    def test_init_schema_creates_table(self, tmp_path):
        db = Database(tmp_path / "test.db")
        WeatherPlugin.init_schema(db)
        result = db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='weather_data'"
        )
        assert result is not None
        db.close()

    def test_each_weather_card_gets_its_own_id(self):
        db = Mock()
        sched = Mock()
        card1 = {"plugin": "weather", "options": self._valid_options(location_name="Paris")}
        card2 = {"plugin": "weather", "options": self._valid_options(location_name="London")}
        inst1 = setup_card(card1, db, sched)
        inst2 = setup_card(card2, db, sched)
        assert inst1 is not None
        assert inst2 is not None
        assert inst1._card_id != inst2._card_id  # pylint: disable=protected-access


class TestPluginDarkMode:
    def test_rss_template_no_hardcoded_colors(self):
        template_path = Path(__file__).resolve().parent.parent / "src" / "plugins" / "rss" / "template.html"
        content = template_path.read_text()
        assert "text-gray-" not in content
        assert "border-gray-" not in content
        assert "bg-gray-" not in content

    def test_weather_template_no_hardcoded_colors(self):
        template_path = Path(__file__).resolve().parent.parent / "src" / "plugins" / "weather" / "template.html"
        content = template_path.read_text()
        assert "text-gray-" not in content

    def test_weather_style_rules_use_css_variables(self):
        rules = WeatherPlugin.card_style_rules()
        assert "var(--text-muted)" in rules[".weather-detail"]
        assert "var(--text-faint)" in rules[".weather-provider"]
        assert "var(--text-faint)" in rules[".weather-provider a"]

    def test_html_style_rules_use_css_variables(self):
        rules = HtmlPlugin.card_style_rules()
        assert "var(--link)" in rules["a"]
        assert "var(--link-hover)" in rules["a:hover"]
        assert "var(--code-bg)" in rules["code"]
        assert "var(--code-bg)" in rules["pre"]

    def test_search_template_no_hardcoded_border(self):
        template_path = Path(__file__).resolve().parent.parent / "src" / "plugins" / "search" / "template.html"
        content = template_path.read_text()
        assert "#d1d5db" not in content
        assert "var(--border)" in content

    def test_calendar_template_no_hardcoded_colors(self):
        template_path = Path(__file__).resolve().parent.parent / "src" / "plugins" / "calendar" / "template.html"
        content = template_path.read_text()
        assert "text-gray-" not in content


class TestCalendarPlugin:  # pylint: disable=protected-access
    def _valid_options(self, **overrides):
        opts = {
            "calendars": [
                {"url": "https://caldav.example.com/cal1", "name": "Test Cal"}
            ],
            "schedule": "*/30 * * * *",
        }
        opts.update(overrides)
        return opts

    def test_load_calendar_plugin(self):
        cls = load_plugin_class("calendar")
        assert cls is CalendarPlugin

    def test_calendar_is_subclass_of_plugin(self):
        assert issubclass(CalendarPlugin, Plugin)

    def test_calendar_card_style_rules_returns_dict(self):
        assert isinstance(CalendarPlugin.card_style_rules(), dict)

    def test_calendar_requires_options(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "options is required" in str(e)

    def test_calendar_requires_calendars(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": {"schedule": "*/30 * * * *"}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "calendars" in str(e)

    def test_calendar_requires_non_empty_calendars(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": {"calendars": []}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "calendars" in str(e)

    def test_calendar_requires_url_in_entry(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": {"calendars": [{}], "schedule": "*/30 * * * *"}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "url" in str(e)

    def test_calendar_requires_schedule(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": {"calendars": [{"url": "https://caldav.example.com/cal1", "name": "Cal"}]}
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "schedule" in str(e)

    def test_calendar_invalid_schedule_format(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(schedule="invalid")
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "cron" in str(e)

    def test_calendar_invalid_auth_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{"url": "https://caldav.example.com/cal1", "name": "Cal", "auth_type": "oauth"}]
                )
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "auth_type" in str(e)

    def test_calendar_bearer_requires_token(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{"url": "https://caldav.example.com/cal1", "name": "Cal", "auth_type": "bearer"}]
                )
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "bearer_token" in str(e)

    def test_calendar_requires_name(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{"url": "https://caldav.example.com/cal1"}]
                )
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "name" in str(e)

    def test_calendar_valid_config_with_color(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{"url": "https://caldav.example.com/cal1", "name": "Work", "color": "#3b82f6"}]
                )
            }]
        }
        validate_config(config)

    def test_calendar_invalid_color_format(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{"url": "https://caldav.example.com/cal1", "name": "Work", "color": "blue"}]
                )
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "color" in str(e)

    def test_calendar_invalid_time_window_days(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(time_window_days=0)
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "time_window_days" in str(e)

    def test_calendar_invalid_max_events(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(max_events=-1)
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "max_events" in str(e)

    def test_calendar_valid_config(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options()
            }]
        }
        validate_config(config)

    def test_calendar_valid_config_with_ics_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{"url": "https://example.com/cal.ics", "type": "ics", "name": "ICS Cal"}]
                )
            }]
        }
        validate_config(config)

    def test_calendar_invalid_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{"url": "https://example.com/cal", "type": "webcal", "name": "Cal"}]
                )
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "type" in str(e)

    def test_calendar_auth_type_none_is_valid(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{"url": "https://example.com/cal", "auth_type": "none", "name": "Cal"}]
                )
            }]
        }
        validate_config(config)

    def test_calendar_valid_config_with_multiple_calendars(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[
                        {"url": "https://caldav.example.com/cal1", "name": "Cal1"},
                        {"url": "https://caldav.example.com/cal2",
                         "name": "Cal2", "auth_type": "bearer",
                         "bearer_token": "xxx"},
                    ]
                )
            }]
        }
        validate_config(config)

    def test_calendar_valid_config_with_optional_fields(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    time_window_days=14,
                    max_events=5,
                    calendars=[{
                        "url": "https://caldav.example.com/cal1",
                        "name": "Test Cal",
                        "link_url": "https://example.com/cal"
                    }]
                )
            }]
        }
        validate_config(config)

    def test_compute_card_id(self):
        options = self._valid_options()
        card_id = CalendarPlugin._compute_card_id(options)
        assert isinstance(card_id, str)
        assert len(card_id) == 16

    def test_compute_card_id_same_options_same_id(self):
        opts1 = self._valid_options()
        opts2 = self._valid_options()
        assert CalendarPlugin._compute_card_id(opts1) == CalendarPlugin._compute_card_id(opts2)

    def test_compute_card_id_different_options_different_id(self):
        opts1 = self._valid_options(calendars=[{"url": "https://a.example.com/cal"}])
        opts2 = self._valid_options(calendars=[{"url": "https://b.example.com/cal"}])
        assert CalendarPlugin._compute_card_id(opts1) != CalendarPlugin._compute_card_id(opts2)

    def test_init_schema_creates_table(self, tmp_path):
        db = Database(tmp_path / "test.db")
        CalendarPlugin.init_schema(db)
        result = db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_events'"
        )
        assert result is not None
        db.close()

    def test_render_empty_when_no_data(self, tmp_path):
        db = Database(tmp_path / "test.db")
        CalendarPlugin.init_schema(db)
        plugin = CalendarPlugin()
        i18n_dir = Path(__file__).resolve().parent.parent / "src" / "plugins" / "calendar" / "i18n"
        plugin.set_translations(_load_translations(i18n_dir, "en"))
        plugin._database = db
        plugin._card_id = "test"
        result = plugin.render(self._valid_options())
        assert "No upcoming events" in result
        db.close()

    def test_render_with_cached_events(self, tmp_path):
        db = Database(tmp_path / "test.db")
        CalendarPlugin.init_schema(db)
        options = self._valid_options()
        plugin = CalendarPlugin()
        plugin._database = db
        plugin._card_id = plugin._compute_card_id(options)
        events = [
            {"summary": "Team Meeting", "start": "2026-06-10T14:00:00", "is_allday": False},
            {"summary": "Project Deadline", "start": "2026-06-12", "is_allday": True},
        ]
        db.execute(
            "INSERT INTO calendar_events (card_id, events) VALUES (?, ?)",
            (plugin._card_id, json.dumps(events)),
        )
        result = plugin.render(options)
        assert "Team Meeting" in result
        assert "Project Deadline" in result
        assert "2026-06-10" in result
        assert "14:00" in result
        db.close()

    def test_render_empty_events_shows_message(self, tmp_path):
        db = Database(tmp_path / "test.db")
        CalendarPlugin.init_schema(db)
        options = self._valid_options()
        plugin = CalendarPlugin()
        i18n_dir = Path(__file__).resolve().parent.parent / "src" / "plugins" / "calendar" / "i18n"
        plugin.set_translations(_load_translations(i18n_dir, "en"))
        plugin._database = db
        plugin._card_id = plugin._compute_card_id(options)
        db.execute(
            "INSERT INTO calendar_events (card_id, events) VALUES (?, ?)",
            (plugin._card_id, json.dumps([])),
        )
        result = plugin.render(options)
        assert "No upcoming events" in result
        db.close()

    def test_each_calendar_card_gets_its_own_id(self):
        db = Mock()
        sched = Mock()
        card1 = {"plugin": "calendar", "options": self._valid_options(
            calendars=[{"url": "https://cal1.example.com", "name": "Cal1"}]
        )}
        card2 = {"plugin": "calendar", "options": self._valid_options(
            calendars=[{"url": "https://cal2.example.com", "name": "Cal2"}]
        )}
        inst1 = setup_card(card1, db, sched)
        inst2 = setup_card(card2, db, sched)
        assert inst1 is not None
        assert inst2 is not None
        assert inst1._card_id != inst2._card_id  # pylint: disable=protected-access

    def test_calendar_valid_config_with_link_url(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{
                        "url": "https://caldav.example.com/cal1",
                        "name": "Cal",
                        "link_url": "https://example.com/cal"
                    }]
                )
            }]
        }
        validate_config(config)

    def test_calendar_invalid_link_url_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Test",
            "language": "en",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": 3,
            "cards": [{
                "title": "Calendar",
                "plugin": "calendar",
                "options": self._valid_options(
                    calendars=[{
                        "url": "https://caldav.example.com/cal1",
                        "name": "Cal",
                        "link_url": 123
                    }]
                )
            }]
        }
        try:
            validate_config(config)
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "link_url" in str(e)

    def test_render_event_with_calendar_link_url(self, tmp_path):
        db = Database(tmp_path / "test.db")
        CalendarPlugin.init_schema(db)
        options = self._valid_options()
        plugin = CalendarPlugin()
        plugin._database = db
        plugin._card_id = plugin._compute_card_id(options)
        events = [{
            "summary": "Event",
            "start": "2026-06-10T14:00:00",
            "is_allday": False,
            "calendar_link_url": "https://example.com/cal"
        }]
        db.execute(
            "INSERT INTO calendar_events (card_id, events) VALUES (?, ?)",
            (plugin._card_id, json.dumps(events)),
        )
        result = plugin.render(options)
        assert '<a href="https://example.com/cal"' in result
        assert 'target="_blank"' in result
        assert "Event" in result
        db.close()

    def test_render_event_without_calendar_link_url(self, tmp_path):
        db = Database(tmp_path / "test.db")
        CalendarPlugin.init_schema(db)
        options = self._valid_options()
        plugin = CalendarPlugin()
        plugin._database = db
        plugin._card_id = plugin._compute_card_id(options)
        events = [{
            "summary": "Event",
            "start": "2026-06-10T14:00:00",
            "is_allday": False
        }]
        db.execute(
            "INSERT INTO calendar_events (card_id, events) VALUES (?, ?)",
            (plugin._card_id, json.dumps(events)),
        )
        result = plugin.render(options)
        assert "<a " not in result
        assert "Event" in result
        db.close()


class TestCalendarPluginDarkMode:  # pylint: disable=too-few-public-methods
    def test_calendar_style_rules_use_css_variables(self):
        rules = CalendarPlugin.card_style_rules()
        assert "var(--text-muted)" in rules[".calendar-date"]
        assert "var(--text)" in rules[".calendar-date-day"]
        assert "var(--text-muted)" in rules[".calendar-empty"]


class TestXkcdPlugin:  # pylint: disable=protected-access
    def test_load_xkcd_plugin(self):
        cls = load_plugin_class("xkcd")
        assert cls is XkcdPlugin

    def test_xkcd_is_subclass_of_plugin(self):
        assert issubclass(XkcdPlugin, Plugin)

    def test_validate_options_requires_schedule(self):
        try:
            XkcdPlugin.validate_options({"other": "value"}, 0, "test.yml")
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "schedule" in str(e)

    def test_validate_options_requires_valid_cron(self):
        try:
            XkcdPlugin.validate_options({"schedule": "not-a-cron"}, 0, "test.yml")
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "cron" in str(e)

    def test_validate_options_accepts_valid_cron(self):
        XkcdPlugin.validate_options({"schedule": "0 9 * * *"}, 0, "test.yml")

    def test_init_schema_creates_table(self, tmp_path):
        db = Database(tmp_path / "test.db")
        XkcdPlugin.init_schema(db)
        tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t["name"] for t in tables]
        assert "xkcd_comics" in table_names
        db.close()

    def test_render_returns_empty_when_no_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = Database(Path(tmp_dir) / "test.db")
            XkcdPlugin.init_schema(db)
            plugin = XkcdPlugin()
            plugin._database = db
            plugin._card_id = "test_card"
            result = plugin.render({})
            assert result == ""
            db.close()

    def test_render_returns_html_when_data_exists(self, tmp_path):
        db = Database(tmp_path / "test.db")
        XkcdPlugin.init_schema(db)
        plugin = XkcdPlugin()
        plugin._database = db
        options = {"schedule": "0 9 * * *"}
        card_id = plugin._compute_card_id(options)
        plugin._card_id = card_id
        db.execute(
            "INSERT INTO xkcd_comics"
            " (card_id, comic_num, title, img_url, alt_text,"
            " comic_url, explain_url, img_width, img_height)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                card_id, 3255, "Planetary Science",
                "https://imgs.xkcd.com/comics/planetary_science.png",
                "The research was overseen by...",
                "https://xkcd.com/3255/",
                "https://www.explainxkcd.com/wiki/index.php/3255",
                800, 600,
            ),
        )
        result = plugin.render(options)
        assert "Planetary Science" in result
        assert "https://xkcd.com/3255/" in result
        assert "Explain XKCD" in result
        assert 'width="800"' in result
        assert 'height="600"' in result
        db.close()

    def test_get_image_dimensions_returns_none_for_invalid(self):
        assert XkcdPlugin._get_image_dimensions(b"not an image") == (None, None)

    def test_get_image_dimensions_parses_png(self):
        width, height = 320, 240
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr_chunk = b'IHDR' + ihdr_data
        png_header = b'\x89PNG\r\n\x1a\n' + struct.pack('>I', len(ihdr_data)) + ihdr_chunk
        w, h = XkcdPlugin._get_image_dimensions(png_header)
        assert w == width
        assert h == height

    def test_get_image_dimensions_parses_jpeg(self):
        width, height = 640, 480
        sof_header = b'\xff\xd8\xff\xe0' + b'\x00\x10' + b'\x00' * 14
        sof_data = b'\xff\xc0\x00\x11\x08' + struct.pack('>HH', height, width) + b'\x00' * 6
        jpeg_data = sof_header + sof_data
        w, h = XkcdPlugin._get_image_dimensions(jpeg_data)
        assert w == width
        assert h == height

    def test_xkcd_card_style_rules_returns_dict(self):
        assert isinstance(XkcdPlugin.card_style_rules(), dict)


class TestImagePlugin:  # pylint: disable=protected-access
    def test_load_image_plugin(self):
        cls = load_plugin_class("image")
        assert cls is ImagePlugin

    def test_image_is_subclass_of_plugin(self):
        assert issubclass(ImagePlugin, Plugin)

    def test_validate_options_requires_options(self):
        try:
            ImagePlugin.validate_options(None, 0, "test.yml")
            assert False, "Should have raised ConfigError"
        except ConfigError:
            pass

    def test_validate_options_requires_provider_type(self):
        try:
            ImagePlugin.validate_options({"url": "http://example.com"}, 0, "test.yml")
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "provider_type" in str(e)

    def test_validate_options_rejects_invalid_provider_type(self):
        try:
            ImagePlugin.validate_options(
                {"provider_type": "invalid", "url": "http://example.com"}, 0, "test.yml"
            )
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "provider_type" in str(e)

    def test_validate_options_requires_url(self):
        try:
            ImagePlugin.validate_options({"provider_type": "rss"}, 0, "test.yml")
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "url" in str(e)

    def test_validate_options_accepts_valid_rss(self):
        ImagePlugin.validate_options(
            {"provider_type": "rss", "url": "http://example.com/feed"}, 0, "test.yml"
        )

    def test_validate_options_accepts_valid_rest(self):
        ImagePlugin.validate_options(
            {"provider_type": "rest", "url": "http://example.com/api"}, 0, "test.yml"
        )

    def test_validate_options_accepts_valid_file(self):
        ImagePlugin.validate_options(
            {"provider_type": "file", "url": "image.png"}, 0, "test.yml"
        )

    def test_validate_options_accepts_optional_schedule(self):
        ImagePlugin.validate_options(
            {"provider_type": "rss", "url": "http://example.com/feed", "schedule": "0 9 * * *"},
            0, "test.yml",
        )

    def test_validate_options_rejects_invalid_schedule(self):
        try:
            ImagePlugin.validate_options(
                {"provider_type": "rss", "url": "http://example.com/feed", "schedule": "invalid"},
                0, "test.yml",
            )
            assert False, "Should have raised ConfigError"
        except ConfigError as e:
            assert "cron" in str(e)

    def test_init_schema_creates_table(self, tmp_path):
        db = Database(tmp_path / "test.db")
        ImagePlugin.init_schema(db)
        tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t["name"] for t in tables]
        assert "image_items" in table_names
        db.close()

    def test_get_image_dimensions_returns_none_for_invalid(self):
        assert ImagePlugin._get_image_dimensions(b"not an image") == (None, None)

    def test_get_image_dimensions_parses_png(self):
        width, height = 320, 240
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr_chunk = b'IHDR' + ihdr_data
        png_header = b'\x89PNG\r\n\x1a\n' + struct.pack('>I', len(ihdr_data)) + ihdr_chunk
        w, h = ImagePlugin._get_image_dimensions(png_header)
        assert w == width
        assert h == height

    def test_get_image_dimensions_parses_jpeg(self):
        width, height = 640, 480
        sof_header = b'\xff\xd8\xff\xe0' + b'\x00\x10' + b'\x00' * 14
        sof_data = b'\xff\xc0\x00\x11\x08' + struct.pack('>HH', height, width) + b'\x00' * 6
        jpeg_data = sof_header + sof_data
        w, h = ImagePlugin._get_image_dimensions(jpeg_data)
        assert w == width
        assert h == height

    def test_extract_rss_image_from_media_thumbnail(self):
        entry = Mock()
        entry.media_thumbnail = [{"url": "http://example.com/thumb.jpg"}]
        entry.media_content = None
        entry.enclosures = None
        del entry.content
        del entry.summary
        assert ImagePlugin._extract_rss_image(entry) == "http://example.com/thumb.jpg"

    def test_extract_rss_image_from_media_content(self):
        entry = Mock()
        entry.media_thumbnail = None
        entry.media_content = [{"medium": "image", "url": "http://example.com/media.png"}]
        entry.enclosures = None
        del entry.content
        del entry.summary
        assert ImagePlugin._extract_rss_image(entry) == "http://example.com/media.png"

    def test_extract_rss_image_from_enclosure(self):
        entry = Mock()
        entry.media_thumbnail = None
        entry.media_content = None
        entry.enclosures = [{"type": "image/jpeg", "href": "http://example.com/enc.jpg"}]
        del entry.content
        del entry.summary
        assert ImagePlugin._extract_rss_image(entry) == "http://example.com/enc.jpg"

    def test_extract_rss_image_from_img_tag(self):
        entry = Mock()
        entry.media_thumbnail = None
        entry.media_content = None
        entry.enclosures = None
        entry.content = [{"value": '<p>Text</p><img src="http://example.com/content.png"></p>'}]
        entry.summary = None
        assert ImagePlugin._extract_rss_image(entry) == "http://example.com/content.png"

    def test_extract_img_tag_from_xml(self):
        html = '<div><img src="http://example.com/test.jpg"></div>'
        assert ImagePlugin._extract_img_tag(html) == "http://example.com/test.jpg"

    def test_extract_img_tag_from_malformed_html(self):
        html = '<img src="http://example.com/test.jpg">'
        assert ImagePlugin._extract_img_tag(html) == "http://example.com/test.jpg"

    def test_find_image_in_value_string(self):
        assert ImagePlugin._find_image_in_value("http://example.com/photo.png") == "http://example.com/photo.png"

    def test_find_image_in_value_dict(self):
        data = {"image": "http://example.com/photo.jpg"}
        assert ImagePlugin._find_image_in_value(data) == "http://example.com/photo.jpg"

    def test_find_image_in_value_nested(self):
        data = {"data": {"items": [{"url": "http://example.com/pic.png"}]}}
        assert ImagePlugin._find_image_in_value(data) == "http://example.com/pic.png"

    def test_find_image_in_value_no_match(self):
        assert ImagePlugin._find_image_in_value("no image here") == ""

    def test_image_card_style_rules_returns_dict(self):
        assert isinstance(ImagePlugin.card_style_rules(), dict)
