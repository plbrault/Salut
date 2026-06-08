import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.image_cache import ImageCache


class TestComputeCardId:
    def test_same_options_same_id(self):
        opts = {"feeds": ["http://a.com"], "schedule": "0 */6 * * *"}
        assert ImageCache.compute_card_id(opts) == ImageCache.compute_card_id(opts)

    def test_different_options_different_id(self):
        opts1 = {"feeds": ["http://a.com"]}
        opts2 = {"feeds": ["http://b.com"]}
        assert ImageCache.compute_card_id(opts1) != ImageCache.compute_card_id(opts2)

    def test_returns_16_char_hex_string(self):
        opts = {"key": "value"}
        result = ImageCache.compute_card_id(opts)
        assert len(result) == 16
        int(result, 16)


class TestGetExtension:
    def test_from_content_type_jpeg(self):
        assert ImageCache.get_extension("http://example.com/img", "image/jpeg") == ".jpg"

    def test_from_content_type_png(self):
        assert ImageCache.get_extension("http://example.com/img", "image/png") == ".png"

    def test_from_content_type_gif(self):
        assert ImageCache.get_extension("http://example.com/img", "image/gif") == ".gif"

    def test_from_content_type_webp(self):
        assert ImageCache.get_extension("http://example.com/img", "image/webp") == ".webp"

    def test_from_url_fallback_gif(self):
        assert ImageCache.get_extension("http://example.com/photo.gif", "") == ".gif"

    def test_from_url_fallback_png(self):
        assert ImageCache.get_extension("http://example.com/photo.png", "") == ".png"

    def test_default_to_jpg(self):
        assert ImageCache.get_extension("http://example.com/img", "application/octet-stream") == ".jpg"


class TestHashFilename:
    def test_same_url_same_filename(self):
        url = "https://example.com/photo.jpg"
        assert ImageCache.hash_filename(url) == ImageCache.hash_filename(url)

    def test_different_url_different_filename(self):
        assert ImageCache.hash_filename("https://a.com/1.jpg") != ImageCache.hash_filename("https://b.com/2.jpg")

    def test_includes_extension(self):
        filename = ImageCache.hash_filename("https://example.com/photo.png", "image/png")
        assert filename.endswith(".png")

    def test_format(self):
        filename = ImageCache.hash_filename("https://example.com/photo.jpg")
        name, ext = filename.rsplit(".", 1)
        assert len(name) == 16
        int(name, 16)
        assert ext == "jpg"


class TestDownload:
    def test_auto_derived_filename(self, tmp_path):
        cache = ImageCache("rss", "testcard", logging.getLogger("test"))
        mock_response = MagicMock()
        mock_response.content = b"fake image data"
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.raise_for_status = MagicMock()

        with patch("src.image_cache.requests.get", return_value=mock_response):
            with patch("src.image_cache.CACHE_DIR", tmp_path):
                result = cache.download("https://example.com/photo.jpg")

        assert result is not None
        assert result.startswith("/cache/rss/testcard/")
        cache_dir = tmp_path / "rss" / "testcard"
        assert len(list(cache_dir.iterdir())) == 1
        saved_file = list(cache_dir.iterdir())[0]
        assert saved_file.read_bytes() == b"fake image data"

    def test_explicit_filename(self, tmp_path):
        cache = ImageCache("image", "testcard", logging.getLogger("test"))
        mock_response = MagicMock()
        mock_response.content = b"fake image data"
        mock_response.headers = {"content-type": "image/png"}
        mock_response.raise_for_status = MagicMock()

        with patch("src.image_cache.requests.get", return_value=mock_response):
            with patch("src.image_cache.CACHE_DIR", tmp_path):
                result = cache.download("https://example.com/photo.png", filename="comic.png")

        assert result == "/cache/image/testcard/comic.png"
        assert (tmp_path / "image" / "testcard" / "comic.png").read_bytes() == b"fake image data"

    def test_returns_none_on_failure(self, tmp_path):
        cache = ImageCache("rss", "testcard", logging.getLogger("test"))

        with patch("src.image_cache.requests.get", side_effect=Exception("network error")):
            with patch("src.image_cache.CACHE_DIR", tmp_path):
                result = cache.download("https://example.com/photo.jpg")

        assert result is None
        assert len(list((tmp_path / "rss" / "testcard").iterdir())) == 0

    def test_local_file(self, tmp_path):
        cache = ImageCache("rss", "testcard", logging.getLogger("test"))
        source = tmp_path / "source.jpg"
        source.write_bytes(b"local image data")

        with patch("src.image_cache.CACHE_DIR", tmp_path):
            result = cache.download(str(source))

        assert result is not None
        cache_dir = tmp_path / "rss" / "testcard"
        assert (cache_dir / Path(result).name).read_bytes() == b"local image data"


class TestCleanupOrphans:
    def test_deletes_orphaned_files(self, tmp_path):
        cache = ImageCache("rss", "testcard", logging.getLogger("test"))
        cache_dir = tmp_path / "rss" / "testcard"
        cache_dir.mkdir(parents=True)
        (cache_dir / "keep.jpg").write_bytes(b"keep")
        (cache_dir / "orphan.jpg").write_bytes(b"orphan")
        with patch("src.image_cache.CACHE_DIR", tmp_path):
            cache.cleanup_orphans({"keep.jpg"})
        assert not (cache_dir / "orphan.jpg").exists()
        assert (cache_dir / "keep.jpg").exists()

    def test_empty_set_deletes_all(self, tmp_path):
        cache = ImageCache("rss", "testcard", logging.getLogger("test"))
        cache_dir = tmp_path / "rss" / "testcard"
        cache_dir.mkdir(parents=True)
        (cache_dir / "a.jpg").write_bytes(b"a")
        (cache_dir / "b.jpg").write_bytes(b"b")
        with patch("src.image_cache.CACHE_DIR", tmp_path):
            cache.cleanup_orphans(set())
        assert len(list(cache_dir.iterdir())) == 0

    def test_nonexistent_directory_no_error(self):
        cache = ImageCache("rss", "nonexistent", logging.getLogger("test"))
        cache.cleanup_orphans({"a.jpg"})

    def test_no_files_nothing_happens(self, tmp_path):
        cache = ImageCache("rss", "testcard", logging.getLogger("test"))
        cache_dir = tmp_path / "rss" / "testcard"
        cache_dir.mkdir(parents=True)
        with patch("src.image_cache.CACHE_DIR", tmp_path):
            cache.cleanup_orphans({"keep.jpg"})
        assert len(list(cache_dir.iterdir())) == 0
