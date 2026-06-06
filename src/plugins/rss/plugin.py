import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

from src.plugin import Plugin

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "cache" / "rss"


class RssPlugin(Plugin):
    def __init__(self):
        self._database = None
        self._logger = None
        self._card_id = None
        self._template = self.load_template(Path(__file__).resolve().parent, "template.html")

    def setup(self, options, database, scheduler, logger):
        self._database = database
        self._logger = logger
        self._card_id = self._compute_card_id(options)

        feeds = options.get("feeds", [])
        max_items = options.get("max_items", 10)
        fetch_images = options.get("images", False)
        schedule = options.get("schedule", "0 */6 * * *")

        if feeds:
            self._fetch_feeds(feeds, max_items, fetch_images)
            scheduler.add_job(
                self._fetch_feeds,
                trigger=self.parse_schedule(schedule),
                args=[feeds, max_items, fetch_images],
                id=f"rss_{self._card_id}",
                replace_existing=True,
            )

    def render(self, options):
        card_id = self._compute_card_id(options)
        items = self._database.get_feed_items(card_id)

        if not items:
            return ""

        feed_items = []
        for item in items:
            source = item.get("feed_title") or urlparse(item["feed_url"]).hostname.replace("www.", "")
            feed_items.append({
                "title": item["title"],
                "link": item["link"],
                "image_url": item.get("image_url", ""),
                "source": source,
            })

        return self._template.render(items=feed_items)

    def _fetch_feeds(self, feeds, max_items=10, fetch_images=False):
        self._logger.info("Fetching RSS feeds for card %s (%d feeds)", self._card_id, len(feeds))
        self._database.delete_feed_items(self._card_id)

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(
                lambda url: self._fetch_single_feed(url, fetch_images), feeds
            ))

        all_items = [item for items in results for item in items]

        all_items.sort(key=lambda x: x["published"], reverse=True)
        all_items = all_items[:max_items]
        self._logger.info("Total items after sort/truncate: %d", len(all_items))

        if fetch_images:
            self._logger.info("Downloading images...")
            self._download_images(all_items)

        for item in all_items:
            self._database.insert_feed_item(
                card_id=self._card_id,
                url=item["url"],
                title=item["title"],
                link=item["link"],
                published=item["published"],
                feed_url=item["feed_url"],
                image_url=item["image_url"],
                feed_title=item["feed_title"],
            )

        self._logger.info("Finished fetching RSS feeds for card %s", self._card_id)

    def _fetch_single_feed(self, feed_url, fetch_images):
        try:
            self._logger.info("Fetching feed: %s", feed_url)
            response = requests.get(feed_url, timeout=10, headers={"User-Agent": "Salut/1.0"})
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            feed_title = parsed.feed.get("title", "")
            self._logger.info("Got %d entries from %s", len(parsed.entries), feed_url)
            items = []
            for entry in parsed.entries:
                published = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6]).isoformat()
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6]).isoformat()

                image_url = ""
                if fetch_images:
                    image_url = self._extract_image(entry)

                items.append({
                    "url": feed_url,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": published,
                    "feed_url": feed_url,
                    "image_url": image_url,
                    "feed_title": feed_title,
                })
            return items
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch feed: %s — %s", feed_url, e)
            return []

    @staticmethod
    def _compute_card_id(options):
        raw = json.dumps(options, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

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

    def _download_images(self, items):
        card_cache_dir = CACHE_DIR / self._card_id
        if card_cache_dir.exists():
            for f in card_cache_dir.iterdir():
                f.unlink()
        card_cache_dir.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor() as executor:
            list(executor.map(
                lambda args: self._download_single_image(card_cache_dir, len(items), *args),
                enumerate(items),
            ))

    def _download_single_image(self, card_cache_dir, total, idx, item):
        if not item["image_url"]:
            return
        try:
            self._logger.info(
                "Downloading image %d/%d: %s", idx + 1, total, item["image_url"]
            )
            response = requests.get(item["image_url"], timeout=10)
            response.raise_for_status()
            ext = self._get_extension(
                item["image_url"], response.headers.get("content-type", "")
            )
            filename = f"{idx}{ext}"
            filepath = card_cache_dir / filename
            filepath.write_bytes(response.content)
            item["image_url"] = f"/cache/rss/{self._card_id}/{filename}"
            self._logger.info("Saved image to %s", filepath)
        except Exception:  # pylint: disable=broad-except
            self._logger.warning("Failed to download image: %s", item["image_url"])

    @staticmethod
    def _get_extension(url, content_type):
        content_type_map = {
            "jpeg": ".jpg",
            "jpg": ".jpg",
            "png": ".png",
            "gif": ".gif",
            "webp": ".webp",
        }
        for key, ext in content_type_map.items():
            if key in content_type:
                return ext
        if url.endswith(".gif"):
            return ".gif"
        if url.endswith(".png"):
            return ".png"
        return ".jpg"
