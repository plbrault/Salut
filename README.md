# Salut

`Salut` means `Hi` in French. It is a self-hosted starter page featuring customizable content cards.

## Prerequisites

- Python 3.14 (recommended to use [pyenv](https://github.com/pyenv/pyenv) to manage Python versions)
- [pipenv](https://pipenv.pypa.io/)
- [GitHub CLI](https://cli.github.com/) (`gh`) — required for the GitHub notifications card

## Installation

```bash
git clone <repo-url>
cd salut
pipenv install
```

If using pyenv, the `.python-version` file will automatically select Python 3.14 when you `cd` into the project directory.

## Configuration

Copy `starter.yml` to `config.yml` and edit it to customize your page:

```bash
cp starter.yml config.yml
```

`config.yml` is gitignored so your customizations stay local. If `config.yml` is absent, the server uses `starter.yml` as the default.

## Running

```bash
pipenv run app
```

The server starts at `http://localhost:8000`.

Use a custom port:

```bash
PORT=9001 pipenv run app
```

## Development

For development with hot-reloading templates and config:

```bash
pipenv run develop
```

This watches for changes to `.yml`/`.yaml` config files and `.html` templates, automatically refreshing the browser.

## Testing

```bash
pipenv run pytest
```

## Linting

```bash
pipenv run pylint
```

## License

Copyright © 2026 Pier-Luc Brault <pier-luc@brault.me>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
