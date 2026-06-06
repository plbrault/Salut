# Masonry Layout

## Purpose

This capability handles the masonry-style column layout for the starter page. Cards are arranged using a greedy column packing algorithm that minimizes the maximum column height, with support for colspan and responsive breakpoints.

## Requirements

### Requirement: Greedy column packing
The system SHALL place each card in the column span where the maximum current height is minimized, processing cards in config order.

#### Scenario: Short card fills gap next to tall card
- **WHEN** a short card follows a tall card in config
- **THEN** the short card is placed in the column with the most available space

#### Scenario: Colspan card placement
- **WHEN** a card has colspan > 1
- **THEN** the system finds the column span where the maximum height across all occupied columns is minimized

#### Scenario: Config order preserved
- **WHEN** card B comes after card A in config
- **THEN** card B is placed after card A in the packing algorithm (never before)

### Requirement: Responsive columns
The system SHALL adapt the number of columns based on viewport width.

#### Scenario: Desktop layout
- **WHEN** viewport width is >= 1024px
- **THEN** the grid uses the `columns` value from config

#### Scenario: Tablet layout
- **WHEN** viewport width is between 640px and 1023px
- **THEN** the grid uses min(2, columns) columns

#### Scenario: Mobile layout
- **WHEN** viewport width is < 640px
- **THEN** the grid uses 1 column

### Requirement: No flash of wrong layout
The system SHALL not show cards in incorrect positions before layout completes.

#### Scenario: Cards hidden during layout
- **WHEN** the page loads
- **THEN** cards are invisible until JavaScript completes the layout calculation

#### Scenario: Cards visible after layout
- **WHEN** layout calculation completes
- **THEN** all cards become visible in their final positions

### Requirement: Resize handling
The system SHALL recalculate layout on window resize.

#### Scenario: Debounced resize
- **WHEN** the window is resized
- **THEN** layout recalculates after a 100ms debounce period

#### Scenario: Column count updates on resize
- **WHEN** viewport crosses a breakpoint (640px or 1024px)
- **THEN** the column count updates and cards repack
