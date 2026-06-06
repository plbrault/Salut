# Dark Mode

## Purpose

Ensures all plugin-rendered content uses theme-aware CSS custom properties for proper contrast in both light and dark modes.

## Requirements

### Requirement: Plugin templates use theme-aware colors
All plugin templates SHALL use CSS custom properties (`var(--text)`, `var(--text-muted)`, `var(--text-faint)`, `var(--border)`) for text, borders, and backgrounds instead of hardcoded color values. No Tailwind color utility classes (e.g., `text-gray-*`, `border-gray-*`, `bg-gray-*`) or inline hex color values SHALL be used in plugin templates.

#### Scenario: RSS plugin dark mode
- **WHEN** dark mode is active and the RSS plugin renders items
- **THEN** item titles, sources, borders, and hover states use CSS custom properties and remain readable

#### Scenario: Weather plugin dark mode
- **WHEN** dark mode is active and the weather plugin renders
- **THEN** the weather description, detail text, and provider link use CSS custom properties and remain readable

#### Scenario: Search plugin dark mode
- **WHEN** dark mode is active and the search plugin renders
- **THEN** the input border and button colors remain visible and properly contrasted

### Requirement: Plugin style rules use theme-aware colors
Plugin `card_style_rules()` methods SHALL return CSS declarations that reference CSS custom properties instead of hardcoded hex color values for backgrounds, text colors, and link colors.

#### Scenario: HTML plugin code blocks in dark mode
- **WHEN** dark mode is active and an HTML card contains `<code>` or `<pre>` elements
- **THEN** the code block background adapts to the dark theme using `var(--code-bg)`

#### Scenario: HTML plugin links in dark mode
- **WHEN** dark mode is active and an HTML card contains links
- **THEN** link text uses `var(--link)` and hover uses `var(--link-hover)` for proper contrast

#### Scenario: Weather plugin style rules in dark mode
- **WHEN** dark mode is active and weather plugin style rules are applied
- **THEN** `.weather-detail` and `.weather-provider` text colors use CSS custom properties

### Requirement: Card titles inherit theme text color
Card titles (`<h3>`) SHALL inherit or explicitly use the theme's text color variable so they are readable in both light and dark modes.

#### Scenario: Card title in dark mode
- **WHEN** dark mode is active
- **THEN** card titles render with light text on dark background
