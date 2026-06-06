from src.plugins.rss import RssPlugin
from src.database import Database


class TestRssDeduplication:
    def test_deduplicate_items_removes_duplicates(self):
        items = [
            {"link": "http://example.com/1", "title": "Article 1"},
            {"link": "http://example.com/2", "title": "Article 2"},
            {"link": "http://example.com/1", "title": "Article 1 Duplicate"},
        ]
        result = RssPlugin._deduplicate_items(items)  # pylint: disable=protected-access
        assert len(result) == 2
        assert result[0]["link"] == "http://example.com/1"
        assert result[1]["link"] == "http://example.com/2"

    def test_deduplicate_items_preserves_order(self):
        items = [
            {"link": "http://example.com/a", "title": "A"},
            {"link": "http://example.com/b", "title": "B"},
            {"link": "http://example.com/c", "title": "C"},
            {"link": "http://example.com/b", "title": "B Duplicate"},
        ]
        result = RssPlugin._deduplicate_items(items)  # pylint: disable=protected-access
        assert len(result) == 3
        assert [item["link"] for item in result] == [
            "http://example.com/a",
            "http://example.com/b",
            "http://example.com/c",
        ]

    def test_deduplicate_items_empty_list(self):
        result = RssPlugin._deduplicate_items([])  # pylint: disable=protected-access
        assert not result

    def test_deduplicate_items_no_duplicates(self):
        items = [
            {"link": "http://example.com/1"},
            {"link": "http://example.com/2"},
        ]
        result = RssPlugin._deduplicate_items(items)  # pylint: disable=protected-access
        assert len(result) == 2

    def test_deduplicate_items_all_same_link(self):
        items = [
            {"link": "http://example.com/same", "title": "Version 1"},
            {"link": "http://example.com/same", "title": "Version 2"},
            {"link": "http://example.com/same", "title": "Version 3"},
        ]
        result = RssPlugin._deduplicate_items(items)  # pylint: disable=protected-access
        assert len(result) == 1
        assert result[0]["title"] == "Version 1"


class TestRssUniqueConstraint:
    def test_unique_constraint_prevents_duplicate_inserts(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.init_schema(db)
        plugin = RssPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = "test_card"  # pylint: disable=protected-access

        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id="test_card",
            url="http://example.com/rss",
            title="Article 1",
            link="http://example.com/article1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/feed.xml",
            image_url="",
            feed_title="Test Feed",
        )

        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id="test_card",
            url="http://example.com/rss",
            title="Article 1 Updated",
            link="http://example.com/article1",
            published="2026-01-02T00:00:00",
            feed_url="http://example.com/feed.xml",
            image_url="",
            feed_title="Test Feed",
        )

        items = db.fetch_all(
            "SELECT * FROM feed_items WHERE card_id = ?",
            ("test_card",),
        )
        assert len(items) == 1
        assert items[0]["title"] == "Article 1 Updated"
        db.close()

    def test_unique_constraint_allows_different_links(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.init_schema(db)
        plugin = RssPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = "test_card"  # pylint: disable=protected-access

        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id="test_card",
            url="http://example.com/rss",
            title="Article 1",
            link="http://example.com/article1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/feed.xml",
            image_url="",
            feed_title="Test Feed",
        )

        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id="test_card",
            url="http://example.com/rss",
            title="Article 2",
            link="http://example.com/article2",
            published="2026-01-02T00:00:00",
            feed_url="http://example.com/feed.xml",
            image_url="",
            feed_title="Test Feed",
        )

        items = db.fetch_all(
            "SELECT * FROM feed_items WHERE card_id = ?",
            ("test_card",),
        )
        assert len(items) == 2
        db.close()


class TestRssTransactionWrapping:
    def test_transaction_commits_on_success(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.init_schema(db)
        plugin = RssPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = "test_card"  # pylint: disable=protected-access

        db.begin_transaction()
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id="test_card",
            url="http://example.com/rss",
            title="Article 1",
            link="http://example.com/article1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/feed.xml",
            image_url="",
            feed_title="Test Feed",
        )
        db.commit_transaction()

        items = db.fetch_all(
            "SELECT * FROM feed_items WHERE card_id = ?",
            ("test_card",),
        )
        assert len(items) == 1
        db.close()

    def test_transaction_rollback_on_error(self, tmp_path):
        db = Database(tmp_path / "test.db")
        RssPlugin.init_schema(db)
        plugin = RssPlugin()
        plugin._database = db  # pylint: disable=protected-access
        plugin._card_id = "test_card"  # pylint: disable=protected-access

        db.begin_transaction()
        plugin._insert_feed_item(  # pylint: disable=protected-access
            card_id="test_card",
            url="http://example.com/rss",
            title="Article 1",
            link="http://example.com/article1",
            published="2026-01-01T00:00:00",
            feed_url="http://example.com/feed.xml",
            image_url="",
            feed_title="Test Feed",
        )
        db.execute("ROLLBACK")

        items = db.fetch_all(
            "SELECT * FROM feed_items WHERE card_id = ?",
            ("test_card",),
        )
        assert len(items) == 0
        db.close()
