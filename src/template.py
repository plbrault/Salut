import re


def resolve_config_vars(text, config, secrets=None, i18n=None):
    """Resolve ${...} template variables from config, secrets, and i18n dicts."""
    def replace_var(match):
        var_path = match.group(1)
        if var_path.startswith("secrets."):
            secret_key = var_path[len("secrets."):]
            if secrets and isinstance(secrets, dict):
                value = _get_nested_value(secrets, secret_key)
                if value is not None:
                    return str(value)
            return ""
        if var_path.startswith("i18n."):
            i18n_key = var_path[len("i18n."):]
            if i18n and isinstance(i18n, dict):
                value = i18n.get(i18n_key)
                if value is not None:
                    return str(value)
            return i18n_key
        value = _get_nested_value(config, var_path)
        if value is None:
            return match.group(0)
        return str(value)

    return re.sub(r'\$\{([^}]+)\}', replace_var, text)


def resolve_all_config_vars(config, secrets=None, i18n=None):
    """Recursively resolve ${...} in all string values of the config dict."""
    return _resolve_recursive(config, config, secrets, i18n)


def _resolve_recursive(obj, config, secrets=None, i18n=None):
    if isinstance(obj, str):
        return resolve_config_vars(obj, config, secrets, i18n)
    if isinstance(obj, dict):
        return {k: _resolve_recursive(v, config, secrets, i18n) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_recursive(item, config, secrets, i18n) for item in obj]
    return obj


def _get_nested_value(data, path):
    """Get value from nested dict using dot notation (e.g., 'user_info.short_name')."""
    keys = path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current
