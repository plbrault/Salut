import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import feedparser
import requests

from src.config import ConfigError
from src.image_cache import ImageCache
from src.plugin import Plugin

STATIC_CUSTOM_DIR = Path(__file__).resolve().parent.parent.parent.parent / "static" / "custom"

IMAGE_URL_RE = re.compile(
    r'https?://[^\s"\'<>]+\.(?:png|jpe?g|gif|webp|svg|bmp)',
    re.IGNORECASE,
)


class ImagePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self._database = None
        self._logger = None
        self._card_id = None
        self._template = self.load_template(
            Path(__file__).resolve().parent, "template.html"
        )

    @staticmethod
    def validate_options(options, card_idx, filename):
        if not options:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options is required for Image plugin."
            )

        provider_type = options.get("provider_type")
        if not provider_type:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.provider_type is required."
            )
        if provider_type not in ("rss", "rest", "file"):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.provider_type must be 'rss', 'rest', or 'file'."
            )

        url = options.get("url")
        if not url:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.url is required."
            )

        schedule = options.get("schedule")
        if schedule is not None:
            if not isinstance(schedule, str):
                raise ConfigError(
                    f"{filename}: cards[{card_idx}].options.schedule must be a string."
                )
            parts = schedule.strip().split()
            if len(parts) not in (5, 6):
                raise ConfigError(
                    f"{filename}: cards[{card_idx}].options.schedule must be a valid cron expression (5 or 6 fields)."
                )

    @staticmethod
    def init_schema(database):
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS image_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL,
                img_url TEXT NOT NULL,
                img_width INTEGER,
                img_height INTEGER,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def setup(self, options, database, scheduler, logger, *, card_id=None):
        self._database = database
        self._logger = logger
        self._card_id = card_id if card_id else self.compute_card_id(options)

        schedule = options.get("schedule")

        self._fetch_image(options)
        if schedule:
            scheduler.add_job(
                self._fetch_image,
                trigger=self.parse_schedule(schedule),
                args=[options],
                id=f"image_{self._card_id}",
                replace_existing=True,
            )

    def render(self, cards):
        results = []
        for card in cards:
            options = card["options"]
            card_id = card["card_id"]

            if not options.get("schedule"):
                row = self._fetch_image(options)
                if not row:
                    results.append("")
                    continue
                results.append(self._template.render(
                    image_url=row["img_url"],
                    source_url=row["source_url"],
                    img_width=row.get("img_width"),
                    img_height=row.get("img_height"),
                    footer_html=options.get("footer_html", ""),
                    dynamic=True,
                ))
                continue

            row = self._database.fetch_one(
                "SELECT * FROM image_items WHERE card_id = ?",
                (card_id,),
            )

            if not row:
                results.append("")
                continue

            results.append(self._template.render(
                image_url=row["img_url"],
                source_url=row["source_url"],
                img_width=row["img_width"],
                img_height=row["img_height"],
                footer_html=options.get("footer_html", ""),
                dynamic=False,
            ))
        return results

    def _fetch_image(self, options):
        try:
            provider_type = options.get("provider_type")
            self._logger.info("Fetching image for card %s (provider: %s)", self._card_id, provider_type)

            if provider_type == "rss":
                img_url, source_link = self._fetch_from_rss(options)
            elif provider_type == "rest":
                img_url, source_link = self._fetch_from_rest(options)
            elif provider_type == "file":
                img_url, source_link = self._fetch_from_file(options)
            else:
                return None

            if not img_url:
                self._logger.warning("No image found for card %s", self._card_id)
                return None

            schedule = options.get("schedule")
            if schedule:
                cache = ImageCache("image", self._card_id, self._logger)
                local_url = cache.download(img_url, filename="comic.jpg")
                if not local_url:
                    self._logger.warning("Failed to download image for card %s, keeping previous", self._card_id)
                    return None

                data = (cache.directory / "comic.jpg").read_bytes()
                img_width, img_height = self._get_image_dimensions(data)

                self._delete_previous_image()
                self._store_image(
                    card_id=self._card_id,
                    source_url=source_link,
                    img_url=local_url,
                    img_width=img_width,
                    img_height=img_height,
                )
                self._logger.info("Image fetched for card %s", self._card_id)
                return None

            return {
                "img_url": img_url,
                "source_url": source_link,
                "img_width": None,
                "img_height": None,
            }
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch image: %s", e)
            return None

    def _fetch_from_rss(self, options):
        url = options["url"]
        response = requests.get(url, timeout=10, headers={"User-Agent": "Salut/1.0"})
        response.raise_for_status()
        parsed = feedparser.parse(response.content)

        if not parsed.entries:
            return "", ""

        entry = parsed.entries[0]
        img_url = self._extract_rss_image(entry)
        source_link = entry.get("link", url)
        return img_url, source_link

    @staticmethod
    def _extract_rss_image(entry):
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

        return ImagePlugin._extract_img_from_content(entry)

    @staticmethod
    def _extract_img_from_content(entry):
        for field in ("content", "summary"):
            content = getattr(entry, field, None)
            if not content:
                continue
            if isinstance(content, list):
                for item in content:
                    html = item.get("value", "") if isinstance(item, dict) else str(item)
                    img_url = ImagePlugin._extract_img_tag(html)
                    if img_url:
                        return img_url
            else:
                img_url = ImagePlugin._extract_img_tag(str(content))
                if img_url:
                    return img_url
        return ""

    @staticmethod
    def _extract_img_tag(html):
        try:
            root = ET.fromstring(html)
            for elem in root.iter("img"):
                src = elem.get("src", "")
                if src:
                    return src
        except ET.ParseError:
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""

    def _fetch_from_rest(self, options):
        url = options["url"]
        method = options.get("request_method", "GET").upper()

        if method == "POST":
            response = requests.post(url, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")

        if content_type.startswith("image/"):
            return url, url

        return self._extract_from_response(response.text, content_type, url)

    def _extract_from_response(self, text, content_type, request_url):
        if "json" in content_type:
            return self._extract_from_json(text, request_url)
        return self._extract_from_xml(text, request_url)

    def _extract_from_json(self, text, request_url):
        try:
            data = json.loads(text)
            img_url = self._find_image_in_value(data)
            if img_url:
                return img_url, request_url
        except Exception:  # pylint: disable=broad-except
            pass
        return "", ""

    @staticmethod
    def _find_image_in_value(value, depth=0):
        if depth > 10:
            return ""
        if isinstance(value, str):
            if IMAGE_URL_RE.search(value):
                return value
        elif isinstance(value, dict):
            for val in value.values():
                result = ImagePlugin._find_image_in_value(val, depth + 1)
                if result:
                    return result
        elif isinstance(value, list):
            for item in value:
                result = ImagePlugin._find_image_in_value(item, depth + 1)
                if result:
                    return result
        return ""

    def _extract_from_xml(self, text, request_url):
        try:
            root = ET.fromstring(text)
            for elem in root.iter("img"):
                src = elem.get("src", "")
                if src:
                    return src, request_url
        except ET.ParseError:
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE)
            if match:
                return match.group(1), request_url
        return "", ""

    def _fetch_from_file(self, options):
        url = options["url"]
        source_path = STATIC_CUSTOM_DIR / url
        if not source_path.exists():
            self._logger.warning("File not found: %s", source_path)
            return "", ""
        return str(source_path), "#"

    def _delete_previous_image(self):
        self._database.execute(
            "DELETE FROM image_items WHERE card_id = ?",
            (self._card_id,),
        )

    def _store_image(self, **kwargs):
        self._database.execute(
            """
            INSERT INTO image_items
            (card_id, source_url, img_url, img_width, img_height)
            VALUES (:card_id, :source_url, :img_url, :img_width, :img_height)
            """,
            kwargs,
        )

    @staticmethod
    def _get_image_dimensions(data):
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            width, height = struct.unpack('>II', data[16:24])
            return width, height
        if data[:2] == b'\xff\xd8':
            offset = 2
            while offset < len(data) - 1:
                if data[offset] != 0xFF:
                    break
                marker = data[offset + 1]
                if marker in (0xC0, 0xC2):
                    height, width = struct.unpack('>HH', data[offset + 5:offset + 9])
                    return width, height
                offset += 2 + struct.unpack('>H', data[offset + 2:offset + 4])[0]
        return None, None
