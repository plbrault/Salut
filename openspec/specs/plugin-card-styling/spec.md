## Purpose

Plugin-defined card CSS classes and style rules. Each plugin's cards receive a CSS class derived from the plugin name, and plugins can define styling via a structured dict.

## Requirements

### Requirement: Cards receive a plugin-specific CSS class
The system SHALL assign each card a CSS class in the format `<plugin-name>-card` based on the card's `plugin` config value.

#### Scenario: Card data includes CSS class
- **WHEN** a card is rendered for a plugin
- **THEN** the card data contains a `css_class` field value like `"html-card"`

#### Scenario: Template applies plugin CSS class
- **WHEN** the template renders a card
- **THEN** the card's `<div>` element has both the `card` class and the plugin-specific CSS class

### Requirement: Plugins define card style rules
The `Plugin` base class SHALL expose a static method `card_style_rules` returning a `dict[str, str]` mapping sub-selectors to CSS declarations. Keys are relative to the card's CSS class (e.g. `"img"` becomes `.html-card img`). The base implementation returns an empty dict.

#### Scenario: Plugin provides CSS rules
- **WHEN** a plugin implements `card_style_rules`
- **THEN** the return value is a dict mapping sub-selectors to CSS declaration strings

#### Scenario: Plugin with no custom styling returns empty dict
- **WHEN** a plugin has no custom card styles
- **THEN** `card_style_rules` returns an empty dict `{}`

### Requirement: Card style rules are rendered in the page
The system SHALL collect all non-empty `card_style_rules` from plugin instances and render them in a `<style>` element in the HTML page, with each rule scoped to the plugin's card class.

#### Scenario: Style rules appear in page
- **WHEN** one or more plugins define non-empty `card_style_rules`
- **THEN** a `<style>` block containing CSS rules scoped to each plugin's card class is present in the rendered HTML

#### Scenario: No styles when all rules are empty
- **WHEN** all plugins return empty dicts from `card_style_rules`
- **THEN** no `<style>` block is rendered for plugin card styles
