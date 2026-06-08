## Purpose

Shared image caching helper for plugins that download and cache remote images.

## Requirements

### Requirement: ImageCache provides cache directory management
The system SHALL provide an `ImageCache` class that manages a cache directory at `cache/<namespace>/<card_id>/`. The class SHALL accept a namespace string, card ID string, and optional logger on construction.

#### Scenario: ImageCache resolves cache directory
- **WHEN** an `ImageCache` is created with namespace `"rss"` and card ID `"abc123"`
- **THEN** the `directory` property returns `Path("cache/rss/abc123/")`

#### Scenario: ImageCache creates directory on download
- **WHEN** `download` is called and the cache directory does not exist
- **THEN** the directory is created before writing the file

### Requirement: ImageCache computes stable card IDs
The system SHALL provide a static `compute_card_id` method that takes an options dict, serializes it to JSON with sorted keys, and returns the first 16 characters of the SHA-256 hex digest.

#### Scenario: Same options produce same card ID
- **WHEN** `compute_card_id` is called twice with the same options dict
- **THEN** the returned card ID is identical

#### Scenario: Different options produce different card IDs
- **WHEN** `compute_card_id` is called with two different options dicts
- **THEN** the returned card IDs are different

### Requirement: ImageCache derives file extensions
The system SHALL provide a static `get_extension` method that determines a file extension from a URL and content-type header. It SHALL check the content-type for known image MIME types first, then fall back to the URL path extension, then default to `.jpg`.

#### Scenario: Extension from content-type
- **WHEN** `get_extension` is called with content-type `"image/png"`
- **THEN** it returns `.png`

#### Scenario: Extension from URL when content-type is unknown
- **WHEN** `get_extension` is called with content-type `"application/octet-stream"` and URL ending in `.gif`
- **THEN** it returns `.gif`

#### Scenario: Default extension
- **WHEN** `get_extension` is called with unrecognized content-type and URL without an image extension
- **THEN** it returns `.jpg`

### Requirement: ImageCache generates hash-based filenames
The system SHALL provide a static `hash_filename` method that takes a remote image URL and optional content-type, computes the first 16 characters of the SHA-256 hex digest of the URL, and appends the derived file extension.

#### Scenario: Hash filename from image URL
- **WHEN** `hash_filename` is called with `"https://example.com/photo.jpg"` and content-type `"image/jpeg"`
- **THEN** the filename starts with 16 hex characters and ends with `.jpg`

#### Scenario: Same URL produces same filename
- **WHEN** `hash_filename` is called twice with the same image URL
- **THEN** the returned filename is identical

#### Scenario: Different URLs produce different filenames
- **WHEN** `hash_filename` is called with two different image URLs
- **THEN** the returned filenames are different

### Requirement: ImageCache downloads images safely
The system SHALL provide a `download` method that downloads an image from a URL and writes it to the cache directory. When called without an explicit filename, it SHALL derive the filename from `hash_filename(url, content_type)`. When called with an explicit filename, it SHALL use that name. It SHALL return the local URL path on success, or `None` on failure.

#### Scenario: Download with auto-derived filename
- **WHEN** `download` is called with a URL and no explicit filename
- **THEN** the file is saved with a hash-based filename and the local URL path is returned

#### Scenario: Download with explicit filename
- **WHEN** `download` is called with a URL and filename `"comic.jpg"`
- **THEN** the file is saved as `comic.jpg` and the local URL path is returned

#### Scenario: Download failure returns None
- **WHEN** the image download fails (network error, HTTP error, etc.)
- **THEN** `download` returns `None` and logs a warning

#### Scenario: Download failure does not write file
- **WHEN** the image download fails
- **THEN** no file is written to the cache directory

### Requirement: ImageCache cleans up orphaned files
The system SHALL provide a `cleanup_orphans` method that takes a set of referenced filenames and deletes any files in the cache directory that are not in that set. This is the only mechanism for deleting cache files.

#### Scenario: Orphaned files are deleted
- **WHEN** `cleanup_orphans` is called with `{"a1b2c3.jpg"}` and the cache directory contains `["a1b2c3.jpg", "old_file.jpg"]`
- **THEN** `old_file.jpg` is deleted and `a1b2c3.jpg` is preserved

#### Scenario: All files referenced — nothing deleted
- **WHEN** `cleanup_orphans` is called with `{"a1b2c3.jpg"}` and the cache directory contains `["a1b2c3.jpg"]`
- **THEN** no files are deleted

#### Scenario: Empty referenced set deletes all files
- **WHEN** `cleanup_orphans` is called with an empty set and the cache directory contains files
- **THEN** all files in the cache directory are deleted

#### Scenario: Nonexistent directory does not raise
- **WHEN** `cleanup_orphans` is called and the cache directory does not exist
- **THEN** no error is raised
