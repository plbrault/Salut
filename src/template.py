import re


def resolve_config_vars(text, config, secrets=None):
    """Resolve ${...} template variables from config and secrets dicts."""
    def replace_var(match):
        var_path = match.group(1)
        if var_path.startswith("secrets."):
            secret_key = var_path[len("secrets."):]
            if secrets and isinstance(secrets, dict):
                value = _get_nested_value(secrets, secret_key)
                if value is not None:
                    return str(value)
            return ""
        value = _get_nested_value(config, var_path)
        if value is None:
            return match.group(0)
        return str(value)

    return re.sub(r'\$\{([^}]+)\}', replace_var, text)


def resolve_all_config_vars(config, secrets=None):
    """Recursively resolve ${...} in all string values of the config dict."""
    return _resolve_recursive(config, config, secrets)


def _resolve_recursive(obj, config, secrets=None):
    if isinstance(obj, str):
        return resolve_config_vars(obj, config, secrets)
    if isinstance(obj, dict):
        return {k: _resolve_recursive(v, config, secrets) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_recursive(item, config, secrets) for item in obj]
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
