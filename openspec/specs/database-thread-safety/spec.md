## Purpose

Thread-safe database access layer for Salut, supporting concurrent access from APScheduler threads.

## Requirements

### Requirement: Database provides per-thread connections
The `Database` class SHALL use `threading.local()` to maintain a separate `sqlite3.Connection` per thread. Each thread that accesses the database SHALL get its own connection, lazily created on first access in that thread.

#### Scenario: Main thread uses a dedicated connection
- **WHEN** `Database()` is instantiated on the main thread
- **THEN** the main thread's connection is created and stored in thread-local storage

#### Scenario: Background thread gets its own connection
- **WHEN** a scheduler thread calls `db.execute()` or any other `Database` method
- **THEN** a new `sqlite3.Connection` is created for that thread (if not already existing) and reused for subsequent calls on the same thread

#### Scenario: Concurrent threads do not interfere with each other's transactions
- **WHEN** thread A calls `begin_transaction()` and thread B also calls `begin_transaction()`
- **THEN** both transactions proceed without error, each on its own connection

### Requirement: Database maintains per-thread transaction state
The `Database` class SHALL track `_in_transaction` per thread alongside each thread's connection. This ensures that one thread's transaction state does not affect another thread's auto-commit behavior.

#### Scenario: Auto-commit respects per-thread transaction state
- **WHEN** thread A is in a transaction (called `begin_transaction()`) and thread B calls `db.execute()` on its own thread
- **THEN** thread B's `execute()` auto-commits, while thread A's `execute()` does not auto-commit

### Requirement: Database supports explicit rollback
The `Database` class SHALL provide a `rollback_transaction()` method that issues `ROLLBACK` and resets the per-thread transaction flag.

#### Scenario: Rollback resets transaction state
- **WHEN** `rollback_transaction()` is called within a transaction
- **THEN** the transaction is rolled back and the per-thread `_in_transaction` flag is set to `False`

#### Scenario: Rollback after a failed commit
- **WHEN** an exception occurs during a transactional write
- **THEN** calling `rollback_transaction()` restores the database to its pre-transaction state

### Requirement: All database connections use WAL mode
Each new `sqlite3.Connection` created for a thread SHALL have `PRAGMA journal_mode=WAL` executed on it.

#### Scenario: Background thread connection uses WAL mode
- **WHEN** a new connection is created for a background thread
- **THEN** WAL mode is set via `PRAGMA journal_mode=WAL`

### Requirement: Database row_factory is set per connection
Each new `sqlite3.Connection` SHALL have `row_factory = sqlite3.Row` set, ensuring `fetch_one` and `fetch_all` return dict-like results.

#### Scenario: Background thread connection has correct row_factory
- **WHEN** `fetch_one()` or `fetch_all()` is called from a background thread
- **THEN** results are returned as dictionaries, same as from the main thread