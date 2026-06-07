import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import feedparser
import requests

from src.config import ConfigError
from src.plugin import Plugin

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "cache" / "image"
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

    def setup(self, options, database, scheduler, logger):
        self._database = database
        self._logger = logger
        self._card_id = self._compute_card_id(options)

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

    def render(self, options):
        card_id = self._compute_card_id(options)

        if not options.get("schedule"):
            self._fetch_image(options)
            row = self._database.fetch_one(
                "SELECT * FROM image_items WHERE card_id = ?",
                (card_id,),
            )
        else:
            row = self._database.fetch_one(
                "SELECT * FROM image_items WHERE card_id = ?",
                (card_id,),
            )

        if not row:
            return ""

        return self._template.render(
            image_url=row["img_url"],
            source_url=row["source_url"],
            img_width=row["img_width"],
            img_height=row["img_height"],
            footer_html=options.get("footer_html", ""),
        )

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
                return

            if not img_url:
                self._logger.warning("No image found for card %s", self._card_id)
                return

            self._delete_previous_image()
            img_width, img_height, ext = self._download_image(img_url)
            local_url = f"/cache/image/{self._card_id}/comic{ext}"
            self._store_image(
                card_id=self._card_id,
                source_url=source_link,
                img_url=local_url,
                img_width=img_width,
                img_height=img_height,
            )
            self._logger.info("Image fetched for card %s", self._card_id)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch image: %s", e)

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
        except (json.JSONDecodeError, RecursionError):
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
        card_cache_dir = CACHE_DIR / self._card_id
        if card_cache_dir.exists():
            for f in card_cache_dir.iterdir():
                f.unlink()

    def _download_image(self, img_url):
        try:
            card_cache_dir = CACHE_DIR / self._card_id
            card_cache_dir.mkdir(parents=True, exist_ok=True)

            if img_url.startswith("/") or img_url.startswith("file://"):
                path = img_url.replace("file://", "")
                data = Path(path).read_bytes()
                ext = Path(path).suffix or ".jpg"
            else:
                self._logger.info("Downloading image: %s", img_url)
                response = requests.get(img_url, timeout=10)
                response.raise_for_status()
                data = response.content
                ext = self._get_extension(img_url, response.headers.get("content-type", ""))

            filepath = card_cache_dir / f"comic{ext}"
            filepath.write_bytes(data)
            self._logger.info("Saved image to %s", filepath)
            width, height = self._get_image_dimensions(data)
            return width, height, ext
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to download image: %s — %s", img_url, e)
            return None, None, ".jpg"

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
    def _compute_card_id(options):
        raw = json.dumps(options, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

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
