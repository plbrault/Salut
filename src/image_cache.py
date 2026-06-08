import hashlib
import json
import logging
from pathlib import Path

import requests


CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


class ImageCache:
    def __init__(self, namespace, card_id, logger=None):
        self._namespace = namespace
        self._card_id = card_id
        self._logger = logger or logging.getLogger(__name__)

    @property
    def directory(self):
        return CACHE_DIR / self._namespace / self._card_id

    @staticmethod
    def compute_card_id(options):
        raw = json.dumps(options, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def get_extension(url, content_type):
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
    def hash_filename(image_url, content_type=""):
        name = hashlib.sha256(image_url.encode()).hexdigest()[:16]
        ext = ImageCache.get_extension(image_url, content_type)
        return f"{name}{ext}"

    def download(self, url, filename=None):
        try:
            self.directory.mkdir(parents=True, exist_ok=True)

            if url.startswith("/") or url.startswith("file://"):
                path = url.replace("file://", "")
                data = Path(path).read_bytes()
                if not filename:
                    filename = self.hash_filename(url)
            else:
                self._logger.info("Downloading image: %s", url)
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.content
                if not filename:
                    filename = self.hash_filename(url, response.headers.get("content-type", ""))

            filepath = self.directory / filename
            filepath.write_bytes(data)
            self._logger.info("Saved image to %s", filepath)
            return f"/cache/{self._namespace}/{self._card_id}/{filename}"
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to download image: %s — %s", url, e)
            return None

    def cleanup_orphans(self, referenced_filenames):
        if not self.directory.exists():
            return
        for f in self.directory.iterdir():
            if f.name not in referenced_filenames:
                f.unlink()
