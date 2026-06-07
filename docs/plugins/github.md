# GitHub Plugin

Displays unread GitHub notifications in a card. Uses the GitHub Notifications API with a Personal Access Token.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `token` | string | yes | - | GitHub Personal Access Token (recommend `${secrets.github_token}`) |
| `schedule` | string | no | `*/5 * * * *` | Cron expression for refresh schedule |
| `max_items` | integer | no | `10` | Maximum number of notifications to display |

## Example

```yaml
cards:
  - title: GitHub Notifications
    plugin: github-notifications
    options:
      token: "${secrets.github_token}"
```

## Setup

1. Create a GitHub **classic** Personal Access Token at https://github.com/settings/tokens
2. Grant the `notifications` scope (read-only). Fine-grained tokens do not support this scope.
3. Store the token in `secrets.yml`:
   ```yaml
   github_token: your_token_here
   ```
4. Reference it in your card options as `${secrets.github_token}`

## Features

- Displays unread notifications grouped by thread
- Shows repo name, subject title, reason, and relative time
- Clicking a notification opens it in a new tab
- Configurable polling schedule (default: every 5 minutes)
- Configurable max items (default: 10)
- Graceful error message if token is not configured
