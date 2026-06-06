# Theme Toggle

## Purpose

Light/dark theme system with browser preference detection, local storage persistence, and a user-facing toggle button.

## Requirements

### Requirement: Theme system with light and dark modes
The system SHALL provide light and dark color schemes using CSS custom properties. Colors SHALL be defined as variables on `:root` for light mode and `[data-theme="dark"]` for dark mode.

#### Scenario: Light mode by default
- **WHEN** a user visits the page with no stored preference and browser prefers light mode
- **THEN** the page renders with light theme colors

#### Scenario: Dark mode by default
- **WHEN** a user visits the page with no stored preference and browser prefers dark mode
- **THEN** the page renders with dark theme colors

### Requirement: Browser preference detection
The system SHALL detect the browser's `prefers-color-scheme` media feature on initial load when no local storage override exists.

#### Scenario: Browser prefers dark
- **WHEN** the browser's `prefers-color-scheme` is `dark` and no `theme` key exists in local storage
- **THEN** the page applies dark mode

#### Scenario: Browser prefers light
- **WHEN** the browser's `prefers-color-scheme` is `light` and no `theme` key exists in local storage
- **THEN** the page applies light mode

### Requirement: Local storage persistence
The system SHALL persist the user's theme choice in local storage under the key `theme`. The stored value SHALL override the browser preference on subsequent visits.

#### Scenario: Theme stored on toggle
- **WHEN** the user clicks the theme toggle
- **THEN** the selected theme is saved to local storage as `theme`

#### Scenario: Theme restored on load
- **WHEN** the page loads and local storage contains `theme: "dark"`
- **THEN** the page applies dark mode regardless of browser preference

### Requirement: Theme toggle template variable
The system SHALL provide a `{{theme_toggle}}` client-side template variable that renders a theme toggle button. Users SHALL be able to place `{{theme_toggle}}` in the `page_header` config field or in an HTML card's content.

#### Scenario: Toggle in page header
- **WHEN** the `page_header` config contains `{{theme_toggle}}`
- **THEN** a theme toggle button is rendered in the header

#### Scenario: Toggle in HTML card
- **WHEN** an HTML card's `html` option contains `{{theme_toggle}}`
- **THEN** a theme toggle button is rendered inside that card

#### Scenario: Toggle appearance
- **WHEN** the theme toggle button is rendered
- **THEN** it displays a sun icon (☀️) in light mode and a moon icon (🌙) in dark mode

#### Scenario: Toggle switches theme
- **WHEN** the user clicks the theme toggle button
- **THEN** the theme switches from light to dark or dark to light

### Requirement: Theme toggle button styling
The theme toggle button SHALL have a standard appearance: a minimal circular button with an icon, hover effect, and no visible border.

#### Scenario: Toggle button has hover effect
- **WHEN** the user hovers over the theme toggle button
- **THEN** the button shows a subtle background change

### Requirement: Card dark mode support
Cards SHALL adapt their background, border, and text colors when dark mode is active. All child elements within cards SHALL also adapt — including text, links, borders, code blocks, and form elements — by using CSS custom properties instead of hardcoded colors.

#### Scenario: Dark mode card appearance
- **WHEN** dark mode is active
- **THEN** cards use a dark background, lighter border, and light text colors

#### Scenario: Light mode card appearance
- **WHEN** light mode is active
- **THEN** cards use a white background, gray border, and dark text colors

#### Scenario: Dark mode card child elements
- **WHEN** dark mode is active and a card contains text, links, code blocks, or form inputs
- **THEN** all child elements use CSS custom properties and maintain readable contrast against the dark card background
