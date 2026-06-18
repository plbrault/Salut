from unittest.mock import Mock, MagicMock

import pytest

from src.plugins.rss import RssPlugin
from src.database import Database
from src.config import validate_config, ConfigError


class TestIncludeFieldsValidation:
    def _make_config(self, include_fields):
        return {
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
                    "schedule": "0 */6 * * *",
                    "include_fields": include_fields,
                }
            }]
        }

    def test_valid_include_fields(self):
        validate_config(self._make_config(["title", "description", "author"]))

    def test_include_fields_must_be_list(self):
        with pytest.raises(ConfigError, match="include_fields must be a list"):
            validate_config(self._make_config("title"))

    def test_include_fields_invalid_value(self):
        with pytest.raises(ConfigError, match="invalid value"):
            validate_config(self._make_config(["title", "invalid"]))

    def test_include_fields_empty_list(self):
        validate_config(self._make_config([]))


class TestTruncateFieldsValidation:
    def _make_config(self, truncate_fields):
        return {
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
                    "schedule": "0 */6 * * *",
                    "truncate_fields": truncate_fields,
                }
            }]
        }

    def test_valid_truncate_fields_integer(self):
        validate_config(self._make_config({"title": 100}))

    def test_valid_truncate_fields_dict(self):
        validate_config(self._make_config({
            "description": {"max_length": 200, "suffix": "..."}
        }))

    def test_valid_truncate_fields_dict_no_suffix(self):
        validate_config(self._make_config({
            "title": {"max_length": 100}
        }))

    def test_truncate_fields_must_be_dict(self):
        with pytest.raises(ConfigError, match="truncate_fields must be a dict"):
            validate_config(self._make_config("title"))

    def test_truncate_fields_invalid_key(self):
        with pytest.raises(ConfigError, match="invalid key"):
            validate_config(self._make_config({"invalid": 100}))

    def test_truncate_fields_non_positive_integer(self):
        with pytest.raises(ConfigError, match="must be a positive integer"):
            validate_config(self._make_config({"title": 0}))

    def test_truncate_fields_negative_integer(self):
        with pytest.raises(ConfigError, match="must be a positive integer"):
            validate_config(self._make_config({"title": -1}))

    def test_truncate_fields_dict_missing_max_length(self):
        with pytest.raises(ConfigError, match="max_length must be a positive integer"):
            validate_config(self._make_config({"title": {"suffix": "..."}}))

    def test_truncate_fields_dict_non_string_suffix(self):
        with pytest.raises(ConfigError, match="suffix must be a string"):
            validate_config(self._make_config({"title": {"max_length": 100, "suffix": 123}}))

    def test_truncate_fields_dict_invalid_value_type(self):
        with pytest.raises(ConfigError, match="must be an integer or a dict"):
            validate_config(self._make_config({"title": "invalid"}))


class TestTruncation:
    def test_no_truncation_when_under_limit(self):
        result = RssPlugin._truncate_text("Short text", 100)  # pylint: disable=protected-access
        assert result == "Short text"

    def test_truncation_at_word_boundary(self):
        text = "This is a long text that should be truncated at a word boundary"
        result = RssPlugin._truncate_text(text, 30)  # pylint: disable=protected-access
        assert result == "This is a long text that..."

    def test_truncation_with_custom_suffix(self):
        text = "This is a long text that should be truncated"
        result = RssPlugin._truncate_text(text, 30, suffix="…")  # pylint: disable=protected-access
        assert result == "This is a long text that…"

    def test_truncation_with_empty_suffix(self):
        text = "This is a long text that should be truncated"
        result = RssPlugin._truncate_text(text, 30, suffix="")  # pylint: disable=protected-access
        assert result == "This is a long text that"

    def test_truncation_no_word_boundary(self):
        text = "Supercalifragilisticexpialidocious"
        result = RssPlugin._truncate_text(text, 10)  # pylint: disable=protected-access
        assert result == "Supercalif..."

    def test_truncation_exact_length(self):
        text = "12345"
        result = RssPlugin._truncate_text(text, 5)  # pylint: disable=protected-access
        assert result == "12345"

    def test_truncation_one_over_limit(self):
        text = "123456"
        result = RssPlugin._truncate_text(text, 5)  # pylint: disable=protected-access
        assert result == "12345..."

    def test_feed_title_truncation(self):
        result = RssPlugin._truncate_text("A Very Long Feed Name That Goes On", 20)  # pylint: disable=protected-access
        assert result == "A Very Long Feed..."


class TestStripHtml:  # pylint: disable=too-few-public-methods
    def test_strip_basic_html(self):
        result = RssPlugin._strip_html("<p>Hello <b>world</b></p>")  # pylint: disable=protected-access
        assert result == "Hello world"

    def test_strip_html_entities(self):
        result = RssPlugin._strip_html("Hello &amp; world")  # pylint: disable=protected-access
        assert result == "Hello & world"

    def test_strip_nested_html(self):
        result = RssPlugin._strip_html("<div><span>Test</span></div>")  # pylint: disable=protected-access
        assert result == "Test"

    def test_strip_no_html(self):
        result = RssPlugin._strip_html("Plain text")  # pylint: disable=protected-access
        assert result == "Plain text"

    def test_strip_empty_string(self):
        result = RssPlugin._strip_html("")  # pylint: disable=protected-access
        assert result == ""


class TestAutoFallback:  # pylint: disable=too-few-public-methods
    def test_feed_without_titles_extracts_description(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.init_schema(db)
        options = {"feeds": ["http://example.com/rss"]}
        plugin = RssPlugin()
        plugin.setup(options, db, MagicMock(), Mock())
        plugin._delete_feed_items(plugin._card_id)  # pylint: disable=protected-access

        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="http://example.com/rss",
            title="",
            link="http://example.com/1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/rss",
            image_url="",
            feed_title="Test Feed",
            description="Post content here",
            author="",
        )

        result = plugin.render([{"options": options, "card_id": plugin._card_id}])
        assert "Post content here" in result[0]
        db.close()


class TestDescriptionDedup:
    def test_dedup_by_description_when_titles_empty(self):
        items = [
            {
                "link": "http://feed-a.com/1",
                "title": "",
                "description": "Same content",
                "feed_url": "http://feed-a.com/rss",
            },
            {
                "link": "http://feed-b.com/1",
                "title": "",
                "description": "Same content",
                "feed_url": "http://feed-b.com/rss",
            },
        ]
        precedence = {
            "http://feed-a.com/rss": 0,
            "http://feed-b.com/rss": 1,
        }
        result = RssPlugin._deduplicate_items(items, precedence)  # pylint: disable=protected-access
        assert len(result) == 1
        assert result[0]["feed_url"] == "http://feed-a.com/rss"

    def test_no_dedup_when_titles_present(self):
        items = [
            {
                "link": "http://feed-a.com/1",
                "title": "Title A",
                "description": "Same content",
                "feed_url": "http://feed-a.com/rss",
            },
            {
                "link": "http://feed-b.com/1",
                "title": "Title B",
                "description": "Same content",
                "feed_url": "http://feed-b.com/rss",
            },
        ]
        precedence = {
            "http://feed-a.com/rss": 0,
            "http://feed-b.com/rss": 1,
        }
        result = RssPlugin._deduplicate_items(items, precedence)  # pylint: disable=protected-access
        assert len(result) == 2

    def test_no_dedup_when_both_empty(self):
        items = [
            {
                "link": "http://feed-a.com/1",
                "title": "",
                "description": "",
                "feed_url": "http://feed-a.com/rss",
            },
            {
                "link": "http://feed-b.com/1",
                "title": "",
                "description": "",
                "feed_url": "http://feed-b.com/rss",
            },
        ]
        precedence = {
            "http://feed-a.com/rss": 0,
            "http://feed-b.com/rss": 1,
        }
        result = RssPlugin._deduplicate_items(items, precedence)  # pylint: disable=protected-access
        assert len(result) == 2


class TestTemplateRendering:
    def _make_plugin(self, tmp_path, options=None):
        db = Database(tmp_path / "test.db")
        RssPlugin.init_schema(db)
        if options is None:
            options = {"feeds": ["http://example.com/rss"]}
        plugin = RssPlugin()
        plugin.setup(options, db, MagicMock(), Mock())
        return plugin, db, options

    def test_render_with_description_when_title_empty(self, tmp_path):
        plugin, db, options = self._make_plugin(tmp_path)
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="http://example.com/rss",
            title="",
            link="http://example.com/1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/rss",
            image_url="",
            feed_title="Test Feed",
            description="This is the post content",
            author="",
        )
        result = plugin.render([{"options": options, "card_id": plugin._card_id}])
        assert "This is the post content" in result[0]
        assert "Test Feed" in result[0]
        db.close()

    def test_render_with_author(self, tmp_path):
        plugin, db, options = self._make_plugin(tmp_path)
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="http://example.com/rss",
            title="Test Title",
            link="http://example.com/1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/rss",
            image_url="",
            feed_title="Test Feed",
            description="",
            author="John Doe",
        )
        result = plugin.render([{"options": options, "card_id": plugin._card_id}])
        assert "John Doe" in result[0]
        db.close()

    def test_render_truncates_description(self, tmp_path):
        options = {
            "feeds": ["http://example.com/rss"],
            "truncate_fields": {"description": 30}
        }
        plugin, db, _ = self._make_plugin(tmp_path, options)
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="http://example.com/rss",
            title="",
            link="http://example.com/1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/rss",
            image_url="",
            feed_title="Test Feed",
            description="This is a very long description that should be truncated at some point",
            author="",
        )
        result = plugin.render([{"options": options, "card_id": plugin._card_id}])
        assert "This is a very long..." in result[0]
        assert "that should be truncated" not in result[0]
        db.close()

    def test_render_truncates_feed_title(self, tmp_path):
        options = {
            "feeds": ["http://example.com/rss"],
            "truncate_fields": {"feed_title": 20}
        }
        plugin, db, _ = self._make_plugin(tmp_path, options)
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="http://example.com/rss",
            title="Test Title",
            link="http://example.com/1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/rss",
            image_url="",
            feed_title="A Very Long Feed Name That Goes On And On",
            description="",
            author="",
        )
        result = plugin.render([{"options": options, "card_id": plugin._card_id}])
        assert "A Very Long Feed..." in result[0]
        db.close()

    def test_render_with_description_and_title(self, tmp_path):
        options = {
            "feeds": ["http://example.com/rss"],
            "truncate_fields": {"description": 200}
        }
        plugin, db, _ = self._make_plugin(tmp_path, options)
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id=plugin._card_id,  # pylint: disable=protected-access
            url="http://example.com/rss",
            title="Test Title",
            link="http://example.com/1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/rss",
            image_url="",
            feed_title="Test Feed",
            description="This is the description",
            author="",
        )
        result = plugin.render([{"options": options, "card_id": plugin._card_id}])
        assert "Test Title" in result[0]
        assert "This is the description" in result[0]
        db.close()
