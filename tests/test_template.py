from app.template import resolve_config_vars


class TestResolveConfigVars:
    def test_resolves_simple_var(self):
        config = {"name": "World"}
        result = resolve_config_vars("Hi ${name}", config)
        assert result == "Hi World"

    def test_resolves_nested_var(self):
        config = {"user_info": {"short_name": "Chris"}}
        result = resolve_config_vars("Hi ${user_info.short_name}", config)
        assert result == "Hi Chris"

    def test_resolves_multiple_vars(self):
        config = {"greeting": "Hi", "name": "Chris"}
        result = resolve_config_vars("${greeting} ${name}", config)
        assert result == "Hi Chris"

    def test_preserves_unknown_var(self):
        config = {"name": "Chris"}
        result = resolve_config_vars("Hi ${unknown}", config)
        assert result == "Hi ${unknown}"

    def test_preserves_non_var_syntax(self):
        config = {"name": "Chris"}
        result = resolve_config_vars("Hi {name}", config)
        assert result == "Hi {name}"

    def test_preserves_time_emoji_syntax(self):
        config = {"name": "Chris"}
        result = resolve_config_vars("Hi ${name} {{time_emoji}}", config)
        assert result == "Hi Chris {{time_emoji}}"

    def test_empty_string(self):
        config = {"name": "Chris"}
        result = resolve_config_vars("", config)
        assert result == ""

    def test_no_vars(self):
        config = {"name": "Chris"}
        result = resolve_config_vars("Hi World", config)
        assert result == "Hi World"

    def test_deeply_nested_path(self):
        config = {"a": {"b": {"c": "value"}}}
        result = resolve_config_vars("${a.b.c}", config)
        assert result == "value"

    def test_empty_config(self):
        result = resolve_config_vars("${name}", {})
        assert result == "${name}"

    def test_none_value(self):
        config = {"name": None}
        result = resolve_config_vars("${name}", config)
        assert result == "${name}"
