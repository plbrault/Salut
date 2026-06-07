# Masonry Layout

## Purpose

This capability handles the masonry-style column layout for the starter page. Cards are arranged using a greedy column packing algorithm that minimizes the maximum column height, with support for colspan and responsive breakpoints.

## Requirements

### Requirement: Greedy column packing
The system SHALL process cards in config order. For each card, if it has no `column` attribute, the system SHALL place it in the column span where the maximum current height is minimized. If a card has a `column` attribute, the system SHALL place it after all preceding cards have been positioned, then place it at the bottom of the specified column.

#### Scenario: Short card fills gap next to tall card
- **WHEN** a short card follows a tall card in config
- **THEN** the short card is placed in the column with the most available space

#### Scenario: Colspan card placement
- **WHEN** a card has colspan > 1
- **THEN** the system finds the column span where the maximum height across all occupied columns is minimized

#### Scenario: Config order preserved
- **WHEN** card B comes after card A in config
- **THEN** card B is placed after card A in the packing algorithm (never before)

#### Scenario: Card with forced column
- **WHEN** a card has `column: 2`
- **THEN** the card is placed after all cards that precede it in config order have been placed, then positioned at the bottom of column 2

#### Scenario: Forced column does not create priority
- **WHEN** card B has `column: 1` and card A precedes card B in config but is not yet placed
- **THEN** card A is placed first (respecting config order), then card B is placed in column 1 after card A

#### Scenario: Card with forced column and colspan
- **WHEN** a card has `column: 1` and `colspan: 2`
- **THEN** the card starts at column 1 and spans columns 1-2, placed after existing cards in those columns

#### Scenario: Forced column ignores greedy algorithm
- **WHEN** a card has `column: 3` but columns 1 and 2 are shorter than column 3, and all preceding cards have been placed
- **THEN** the card is placed in column 3 (not the shorter columns)

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
