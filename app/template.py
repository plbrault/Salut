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
