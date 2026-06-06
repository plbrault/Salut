import re


def resolve_config_vars(text, config):
    """Resolve ${...} template variables from config dict."""
    def replace_var(match):
        var_path = match.group(1)
        value = _get_nested_value(config, var_path)
        if value is None:
            return match.group(0)
        return str(value)

    return re.sub(r'\$\{([^}]+)\}', replace_var, text)


def resolve_all_config_vars(config):
    """Recursively resolve ${...} in all string values of the config dict."""
    return _resolve_recursive(config, config)


def _resolve_recursive(obj, config):
    if isinstance(obj, str):
        return resolve_config_vars(obj, config)
    if isinstance(obj, dict):
        return {k: _resolve_recursive(v, config) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_recursive(item, config) for item in obj]
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
