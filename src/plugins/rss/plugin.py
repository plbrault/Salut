from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html import unescape
from pathlib import Path
from re import sub
from urllib.parse import urlparse

import feedparser
import requests

from src.config import ConfigError
from src.image_cache import ImageCache
from src.plugin import Plugin

VALID_INCLUDE_FIELDS = {"title", "description", "author"}
VALID_TRUNCATE_KEYS = {"title", "description", "author", "feed_title"}


class RssPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self._database = None
        self._logger = None
        self._card_id = None
        self._card_ids = {}
        self._template = self.load_template(Path(__file__).resolve().parent, "template.html")

    @staticmethod
    def _validate_truncate_value(key, value, filename, card_idx):
        prefix = f"{filename}: cards[{card_idx}].options.truncate_fields.{key}"
        if isinstance(value, int):
            if value <= 0:
                raise ConfigError(
                    f"{prefix} must be a positive integer."
                )
            return
        if isinstance(value, dict):
            max_length = value.get("max_length")
            if not isinstance(max_length, int) or max_length <= 0:
                raise ConfigError(
                    f"{prefix}.max_length must be a positive integer."
                )
            suffix = value.get("suffix", "...")
            if not isinstance(suffix, str):
                raise ConfigError(
                    f"{prefix}.suffix must be a string."
                )
            return
        raise ConfigError(
            f"{prefix} must be an integer or a dict with "
            "max_length and suffix."
        )

    @staticmethod
    def _validate_schedule(schedule, filename, card_idx):
        prefix = f"{filename}: cards[{card_idx}].options.schedule"
        if not schedule:
            raise ConfigError(f"{prefix} is required (cron expression).")
        if not isinstance(schedule, str):
            raise ConfigError(f"{prefix} must be a string.")
        parts = schedule.strip().split()
        if len(parts) not in (5, 6):
            raise ConfigError(
                f"{prefix} must be a valid cron expression (5 or 6 fields)."
            )

    @staticmethod
    def _validate_include_fields(include_fields, filename, card_idx):
        prefix = f"{filename}: cards[{card_idx}].options.include_fields"
        if not isinstance(include_fields, list):
            raise ConfigError(f"{prefix} must be a list.")
        for field in include_fields:
            if field not in VALID_INCLUDE_FIELDS:
                raise ConfigError(
                    f"{prefix} contains invalid value '{field}'. "
                    f"Valid values: {', '.join(sorted(VALID_INCLUDE_FIELDS))}."
                )

    @staticmethod
    def _validate_truncate_fields(truncate_fields, filename, card_idx):
        prefix = f"{filename}: cards[{card_idx}].options.truncate_fields"
        if not isinstance(truncate_fields, dict):
            raise ConfigError(f"{prefix} must be a dict.")
        for key, value in truncate_fields.items():
            if key not in VALID_TRUNCATE_KEYS:
                raise ConfigError(
                    f"{prefix} contains invalid key '{key}'. "
                    f"Valid keys: {', '.join(sorted(VALID_TRUNCATE_KEYS))}."
                )
            RssPlugin._validate_truncate_value(
                key, value, filename, card_idx
            )

    @staticmethod
    def validate_options(options, card_idx, filename):
        if not options:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options is required for RSS plugin."
            )

        feeds = options.get("feeds")
        if not feeds or not isinstance(feeds, list) or len(feeds) == 0:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.feeds "
                "must be a non-empty list."
            )

        RssPlugin._validate_schedule(
            options.get("schedule"), filename, card_idx
        )

        include_fields = options.get("include_fields")
        if include_fields is not None:
            RssPlugin._validate_include_fields(
                include_fields, filename, card_idx
            )

        truncate_fields = options.get("truncate_fields")
        if truncate_fields is not None:
            RssPlugin._validate_truncate_fields(
                truncate_fields, filename, card_idx
            )

        distinct_from = options.get("distinct_from")
        if distinct_from is not None:
            prefix = f"{filename}: cards[{card_idx}].options.distinct_from"
            if not isinstance(distinct_from, list):
                raise ConfigError(f"{prefix} must be a list.")
            for item in distinct_from:
                if not isinstance(item, str):
                    raise ConfigError(
                        f"{prefix} contains non-string value. "
                        "All items must be strings."
                    )

    @staticmethod
    def init_schema(database):
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS feed_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                published TEXT,
                feed_url TEXT NOT NULL,
                image_url TEXT,
                feed_title TEXT,
                description TEXT,
                author TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(card_id, link)
            )
            """
        )

    def setup(self, card_id, options, database, scheduler, logger):
        self._database = database
        self._logger = logger
        self._card_id = card_id

        feeds = options.get("feeds", [])
        max_items = options.get("max_items", 10)
        fetch_images = options.get("images", False)
        schedule = options.get("schedule", "0 */6 * * *")
        include_fields = options.get("include_fields", ["title"])
        distinct_from = options.get("distinct_from", [])

        if feeds:
            self._fetch_feeds(
                feeds, max_items, fetch_images, include_fields,
                distinct_from=distinct_from
            )
            scheduler.add_job(
                self._fetch_feeds,
                trigger=self.parse_schedule(schedule),
                args=[feeds, max_items, fetch_images, include_fields],
                kwargs={"distinct_from": distinct_from},
                id=f"rss_{self._card_id}",
                replace_existing=True,
            )

    def _apply_truncation(self, value, config):
        if isinstance(config, int):
            return self._truncate_text(value, config)
        if isinstance(config, dict):
            return self._truncate_text(
                value,
                config["max_length"],
                config.get("suffix", "...")
            )
        return value

    def _render_feed_item(self, item, truncate_fields):
        source = item.get("feed_title") or (
            urlparse(item["feed_url"]).hostname or ""
        ).replace("www.", "")

        title = item["title"]
        description = item.get("description", "")
        author = item.get("author", "")

        display_title = title if title else description
        display_title_key = "title" if title else "description"

        if display_title_key in truncate_fields:
            display_title = self._apply_truncation(
                display_title, truncate_fields[display_title_key]
            )

        if "description" in truncate_fields and title and description:
            description = self._apply_truncation(
                description, truncate_fields["description"]
            )

        if "author" in truncate_fields and author:
            author = self._apply_truncation(
                author, truncate_fields["author"]
            )

        if "feed_title" in truncate_fields:
            source = self._apply_truncation(
                source, truncate_fields["feed_title"]
            )

        return {
            "title": display_title,
            "description": description if title else "",
            "author": author,
            "link": item["link"],
            "image_url": item.get("image_url", ""),
            "source": source,
        }

    def render(self, cards):
        results = []
        for card in cards:
            options = card["options"]
            card_id = card["card_id"]
            items = self._get_feed_items(card_id)
            truncate_fields = options.get("truncate_fields", {})

            if not items:
                results.append("")
                continue

            feed_items = [
                self._render_feed_item(item, truncate_fields)
                for item in items
            ]

            results.append(self._template.render(items=feed_items))
        return results

    def _fetch_feeds(  # pylint: disable=too-many-locals
        self, feeds, max_items=10, fetch_images=False,
        include_fields=None, *, distinct_from=None
    ):
        if include_fields is None:
            include_fields = ["title"]
        if distinct_from is None:
            distinct_from = []
        self._logger.info("Fetching RSS feeds for card %s (%d feeds)", self._card_id, len(feeds))

        excluded = None
        if distinct_from:
            for ref_card_id in distinct_from:
                self._ensure_dependency_fetched(ref_card_id)
            excluded = self._build_exclusion_set(distinct_from)

        all_items = self._fetch_all_feeds(feeds, fetch_images, include_fields)

        precedence = {url: idx for idx, url in enumerate(feeds)}
        all_items.sort(key=lambda x: (x["published"] != "", x["published"]), reverse=True)
        all_items = self._deduplicate_items(all_items, precedence)

        if excluded is not None:
            filtered = [
                item for item in all_items
                if not self._is_excluded(item, excluded)
            ]
            self._logger.info(
                "Items after distinct_from filter: %d", len(filtered)
            )
            all_items = filtered

        all_items = all_items[:max_items]
        self._logger.info("Total items after sort/dedup/truncate: %d", len(all_items))

        if fetch_images:
            self._logger.info("Downloading images...")
            self._download_images(all_items)

        self._database.begin_transaction()
        try:
            self._delete_feed_items(self._card_id)

            for item in all_items:
                self._insert_feed_item(
                    card_id=self._card_id,
                    url=item["url"],
                    title=item["title"],
                    link=item["link"],
                    published=item["published"],
                    feed_url=item["feed_url"],
                    image_url=item["image_url"],
                    feed_title=item["feed_title"],
                    description=item.get("description", ""),
                    author=item.get("author", ""),
                )

            self._database.commit_transaction()
            self._logger.info("Finished fetching RSS feeds for card %s", self._card_id)
        except Exception:
            self._database.rollback_transaction()
            raise

        if fetch_images:
            referenced = set()
            rows = self._get_feed_items(self._card_id)
            for row in rows:
                img = row.get("image_url", "")
                if img:
                    referenced.add(Path(img).name)
            ImageCache("rss", self._card_id, self._logger).cleanup_orphans(referenced)

    @staticmethod
    def _get_published_date(entry):
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6]).isoformat()
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6]).isoformat()
        return ""

    def _get_description(self, entry, effective_fields):
        if "description" not in effective_fields:
            return ""
        description = entry.get("description", "")
        if not description:
            description = entry.get("summary", "")
        if description:
            description = self._strip_html(description)
        return description

    def _fetch_single_feed(self, feed_url, fetch_images, include_fields=None):
        if include_fields is None:
            include_fields = ["title"]
        try:
            self._logger.info("Fetching feed: %s", feed_url)
            response = requests.get(
                feed_url, timeout=10, headers={"User-Agent": "Salut/1.0"}
            )
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            feed_title = parsed.feed.get("title", "")
            self._logger.info(
                "Got %d entries from %s", len(parsed.entries), feed_url
            )
            has_titles = any(
                entry.get("title", "") for entry in parsed.entries
            )

            effective_fields = set(include_fields)
            if not has_titles:
                effective_fields.add("description")

            items = []
            for entry in parsed.entries:
                image_url = ""
                if fetch_images:
                    image_url = self._extract_image(entry)

                title = (
                    entry.get("title", "")
                    if "title" in effective_fields
                    else ""
                )
                author = (
                    entry.get("author", "")
                    if "author" in effective_fields
                    else ""
                )

                items.append({
                    "url": feed_url,
                    "title": title,
                    "link": entry.get("link", ""),
                    "published": self._get_published_date(entry),
                    "feed_url": feed_url,
                    "image_url": image_url,
                    "feed_title": feed_title,
                    "description": self._get_description(
                        entry, effective_fields
                    ),
                    "author": author,
                })
            return items
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning(
                "Failed to fetch feed: %s — %s", feed_url, e
            )
            return []

    @staticmethod
    def _extract_image(entry):
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url", "")
        if hasattr(entry, "media_content") and entry.media_content:
            for media in entry.media_content:
                if media.get("medium") == "image":
                    return media.get("url", "")
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image/"):
                    return enc.get("href", "")
        return ""

    @staticmethod
    def _strip_html(text):
        return unescape(sub(r"<[^>]+>", "", text))

    @staticmethod
    def _truncate_text(text, max_length, suffix="..."):
        if len(text) <= max_length:
            return text
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + suffix

    def _download_images(self, items):
        cache = ImageCache("rss", self._card_id, self._logger)
        for idx, item in enumerate(items):
            if not item["image_url"]:
                continue
            self._logger.info(
                "Downloading image %d/%d: %s", idx + 1, len(items), item["image_url"]
            )
            local_url = cache.download(item["image_url"])
            if local_url:
                item["image_url"] = local_url

    def _delete_feed_items(self, card_id):
        self._database.execute("DELETE FROM feed_items WHERE card_id = ?", (card_id,))

    def _insert_feed_item(self, **kwargs):
        kwargs.setdefault("description", "")
        kwargs.setdefault("author", "")
        self._database.execute(
            """
            INSERT OR REPLACE INTO feed_items
            (card_id, url, title, link, published, feed_url,
             image_url, feed_title, description, author)
            VALUES
            (:card_id, :url, :title, :link, :published, :feed_url,
             :image_url, :feed_title, :description, :author)
            """,
            kwargs,
        )

    def _get_feed_items(self, card_id):
        return self._database.fetch_all(
            "SELECT * FROM feed_items WHERE card_id = ? ORDER BY published DESC",
            (card_id,),
        )

    def _build_exclusion_set(self, distinct_from):
        excluded_links = set()
        excluded_titles = set()
        for ref_card_id in distinct_from:
            items = self._get_feed_items(ref_card_id)
            for item in items:
                link = item.get("link", "")
                if link:
                    excluded_links.add(link)
                title = item.get("title", "").strip()
                if title:
                    excluded_titles.add(title)
        return {"links": excluded_links, "titles": excluded_titles}

    def _ensure_dependency_fetched(self, ref_card_id):
        if self._get_feed_items(ref_card_id):
            return

        card = self._card_ids.get(ref_card_id)
        if card and card.get("plugin") == "rss":
            ref_options = card.get("options", {})
            ref_distinct = ref_options.get("distinct_from", [])
            for dep_id in ref_distinct:
                self._ensure_dependency_fetched(dep_id)
            self._fetch_dependency_card(ref_card_id, ref_options)

    def _fetch_dependency_card(self, ref_card_id, ref_options):
        ref_feeds = ref_options.get("feeds", [])
        if not ref_feeds:
            return
        ref_include = ref_options.get("include_fields", ["title"])
        ref_images = ref_options.get("images", False)
        self._logger.info(
            "Fetching dependency card %s before %s",
            ref_card_id, self._card_id
        )
        all_items = self._fetch_all_feeds(
            ref_feeds, ref_images, ref_include
        )
        self._database.begin_transaction()
        try:
            self._delete_feed_items(ref_card_id)
            for item in all_items:
                self._insert_feed_item(
                    card_id=ref_card_id,
                    url=item["url"],
                    title=item["title"],
                    link=item["link"],
                    published=item["published"],
                    feed_url=item["feed_url"],
                    image_url=item["image_url"],
                    feed_title=item["feed_title"],
                    description=item.get("description", ""),
                    author=item.get("author", ""),
                )
            self._database.commit_transaction()
        except Exception:
            self._database.rollback_transaction()
            raise

    @staticmethod
    def _is_excluded(item, excluded):
        link = item.get("link", "")
        if link in excluded["links"]:
            return True
        title = item.get("title", "").strip()
        if title and title in excluded["titles"]:
            return True
        return False

    def _fetch_all_feeds(self, feeds, fetch_images, include_fields):
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(
                lambda url: self._fetch_single_feed(url, fetch_images, include_fields), feeds
            ))
        return [item for items in results for item in items]

    def _filter_distinct(self, items, distinct_from):
        excluded = self._build_exclusion_set(distinct_from)
        filtered = [
            item for item in items
            if not self._is_excluded(item, excluded)
        ]
        self._logger.info(
            "Items after distinct_from filter: %d", len(filtered)
        )
        return filtered

    @staticmethod
    def _deduplicate_items(items, precedence=None):
        seen_links = set()
        link_deduped = []
        for item in items:
            link = item.get("link", "")
            if link not in seen_links:
                seen_links.add(link)
                link_deduped.append(item)

        if precedence is None:
            return link_deduped

        seen_titles = {}
        title_deduped = []
        for item in link_deduped:
            title = item.get("title", "").strip()
            description = item.get("description", "").strip()
            feed_url = item.get("feed_url", "")

            dedup_key = title if title else description

            if not dedup_key:
                title_deduped.append(item)
                continue

            if dedup_key in seen_titles:
                prev_item = seen_titles[dedup_key]
                prev_idx = precedence.get(prev_item.get("feed_url", ""), float("inf"))
                curr_idx = precedence.get(feed_url, float("inf"))
                if curr_idx < prev_idx:
                    title_deduped.remove(prev_item)
                    title_deduped.append(item)
                    seen_titles[dedup_key] = item
            else:
                seen_titles[dedup_key] = item
                title_deduped.append(item)

        return title_deduped
