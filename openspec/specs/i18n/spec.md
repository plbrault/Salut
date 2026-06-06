## Purpose

Internationalization (i18n) support for config-level text and plugin UI strings.

## Requirements

### Requirement: Global i18n translation files
The system SHALL provide translation files at `i18n/{language}.json` for config-level text. Each file SHALL be a flat JSON object mapping keys to translated strings.

#### Scenario: English translations exist
- **WHEN** the system loads global translations for `language: "en"`
- **THEN** it reads `i18n/en.json` and makes keys available via `${i18n.key}` syntax

#### Scenario: French translations exist
- **WHEN** the system loads global translations for `language: "fr"`
- **THEN** it reads `i18n/fr.json` and makes keys available via `${i18n.key}` syntax

#### Scenario: Missing language file falls back to English
- **WHEN** the system loads global translations for a language without a corresponding file
- **THEN** it falls back to `i18n/en.json`

### Requirement: Global i18n config variable resolution
The system SHALL resolve `${i18n.key}` variables in config values using the loaded global translations.

#### Scenario: i18n variable resolved
- **WHEN** a config value contains `${i18n.hi}` and `language: "fr"` with `i18n/fr.json` containing `"hi": "Salut"`
- **THEN** the variable is resolved to `"Salut"`

#### Scenario: i18n variable missing key falls back to key name
- **WHEN** a config value contains `${i18n.unknown_key}` and no translation exists for that key
- **THEN** the variable is resolved to the key name `"unknown_key"`

### Requirement: Per-plugin i18n translation files
Each plugin SHALL provide translation files at `src/plugins/{name}/i18n/{language}.json` for UI strings displayed by that plugin.

#### Scenario: Plugin loads translations for configured language
- **WHEN** a plugin is set up with `language: "fr"` and `src/plugins/{name}/i18n/fr.json` exists
- **THEN** the plugin loads French translations

#### Scenario: Plugin falls back to English for missing language
- **WHEN** a plugin is set up with `language: "de"` and `src/plugins/{name}/i18n/de.json` does not exist
- **THEN** the plugin loads `src/plugins/{name}/i18n/en.json`

#### Scenario: Plugin falls back to English for missing keys
- **WHEN** a plugin has French translations loaded but a key is missing from `fr.json`
- **THEN** `t(key)` returns the English translation from `en.json`

### Requirement: Plugin translation helper method
The base `Plugin` class SHALL provide a `t(key)` method that returns the translated string for the given key from the plugin's loaded translations.

#### Scenario: Key exists in current language
- **WHEN** `t("feels_like")` is called and French translations are loaded with `"feels_like": "Ressenti"`
- **THEN** the method returns `"Ressenti"`

#### Scenario: Key missing returns key name
- **WHEN** `t("nonexistent")` is called and no translation exists for that key
- **THEN** the method returns `"nonexistent"`

### Requirement: Weather plugin i18n
The weather plugin SHALL use i18n for all user-facing UI strings: "Feels like", "% humidity", "km/h wind", "Provided by", "Weather data unavailable.", "Unknown".

#### Scenario: Weather template uses translated labels
- **WHEN** the weather card is rendered with `language: "fr"`
- **THEN** the template displays "Ressenti" instead of "Feels like", "% humidité" instead of "% humidity", etc.

#### Scenario: Weather API uses configured language
- **WHEN** the weather plugin fetches data with `language: "fr"`
- **THEN** it passes `&language=fr` to the Open-Meteo API and receives French weather descriptions

### Requirement: Search plugin i18n
The search plugin SHALL use i18n for the default button text and placeholder text ("Search").

#### Scenario: Search button uses translated text
- **WHEN** the search card is rendered with `language: "fr"` and no custom `button_text`
- **THEN** the button displays "Rechercher" instead of "Search"

#### Scenario: Search placeholder uses translated text
- **WHEN** the search card is rendered with `language: "fr"` and no custom `placeholder_text`
- **THEN** the placeholder displays "Rechercher" instead of "Search"

### Requirement: Calendar plugin i18n
The calendar plugin SHALL use i18n for the empty state message ("No upcoming events.").

#### Scenario: Empty state uses translated text
- **WHEN** the calendar card has no events and `language: "fr"`
- **THEN** the card displays "Aucun événement à venir." instead of "No upcoming events."
