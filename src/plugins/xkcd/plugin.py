import hashlib
import json
import struct
from pathlib import Path

import requests

from src.config import ConfigError
from src.plugin import Plugin

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "cache" / "xkcd"


class XkcdPlugin(Plugin):
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
                f"{filename}: cards[{card_idx}].options is required for XKCD plugin."
            )

        schedule = options.get("schedule")
        if not schedule:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.schedule is required (cron expression)."
            )

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
            CREATE TABLE IF NOT EXISTS xkcd_comics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL DEFAULT '',
                comic_num INTEGER NOT NULL,
                title TEXT NOT NULL,
                img_url TEXT NOT NULL,
                alt_text TEXT NOT NULL,
                comic_url TEXT NOT NULL,
                explain_url TEXT NOT NULL,
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

        schedule = options.get("schedule", "0 9 * * *")

        self._fetch_comic()
        scheduler.add_job(
            self._fetch_comic,
            trigger=self.parse_schedule(schedule),
            id=f"xkcd_{self._card_id}",
            replace_existing=True,
        )

    def render(self, options):
        card_id = self._compute_card_id(options)
        row = self._database.fetch_one(
            "SELECT * FROM xkcd_comics WHERE card_id = ?",
            (card_id,),
        )

        if not row:
            return ""

        return self._template.render(
            comic_num=row["comic_num"],
            title=row["title"],
            image_url=row["img_url"],
            alt_text=row["alt_text"],
            comic_url=row["comic_url"],
            explain_url=row["explain_url"],
            img_width=row["img_width"],
            img_height=row["img_height"],
        )

    def _fetch_comic(self):
        try:
            self._logger.info("Fetching latest XKCD comic for card %s", self._card_id)
            response = requests.get(
                "https://xkcd.com/info.0.json", timeout=10
            )
            response.raise_for_status()
            data = response.json()

            comic_num = data["num"]
            title = data["title"]
            img_url = data["img"]
            alt_text = data["alt"]
            comic_url = f"https://xkcd.com/{comic_num}/"
            explain_url = f"https://www.explainxkcd.com/wiki/index.php/{comic_num}"

            self._delete_previous_comic()
            img_width, img_height = self._download_image(img_url)
            self._store_comic(
                card_id=self._card_id,
                comic_num=comic_num,
                title=title,
                img_url=img_url,
                alt_text=alt_text,
                comic_url=comic_url,
                explain_url=explain_url,
                img_width=img_width,
                img_height=img_height,
            )

            self._logger.info("XKCD comic #%d fetched for card %s", comic_num, self._card_id)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch XKCD comic: %s", e)

    def _delete_previous_comic(self):
        self._database.execute(
            "DELETE FROM xkcd_comics WHERE card_id = ?",
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

            self._logger.info("Downloading XKCD image: %s", img_url)
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()

            ext = self._get_extension(img_url, response.headers.get("content-type", ""))
            filepath = card_cache_dir / f"comic{ext}"
            filepath.write_bytes(response.content)
            self._logger.info("Saved XKCD image to %s", filepath)
            return self._get_image_dimensions(response.content)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to download XKCD image: %s — %s", img_url, e)
            return None, None

    def _store_comic(self, **kwargs):
        self._database.execute(
            """
            INSERT INTO xkcd_comics
            (card_id, comic_num, title, img_url, alt_text,
             comic_url, explain_url, img_width, img_height)
            VALUES (:card_id, :comic_num, :title, :img_url,
                    :alt_text, :comic_url, :explain_url,
                    :img_width, :img_height)
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
