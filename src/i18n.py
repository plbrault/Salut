import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_global_i18n(language):
    """Load global i18n translations with English fallback."""
    return _load_translations(BASE_DIR / "i18n", language)


def _load_translations(i18n_dir, language):
    """Load translations from a directory with English fallback."""
    en_file = i18n_dir / "en.json"
    translations = _load_json(en_file) if en_file.exists() else {}

    if language != "en":
        lang_file = i18n_dir / f"{language}.json"
        if lang_file.exists():
            lang_translations = _load_json(lang_file)
            translations.update(lang_translations)

    return translations


def _load_json(path):
    """Load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
