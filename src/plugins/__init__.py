import importlib


def load_plugin(name):
    try:
        module = importlib.import_module(f"src.plugins.{name}")
        return module.render
    except (ImportError, AttributeError):
        return None


def render_card(card):
    plugin_name = card.get("plugin")
    options = card.get("options", {})
    render = load_plugin(plugin_name)
    if render is None:
        return f'<p class="text-red-500">Plugin "{plugin_name}" not found</p>'
    try:
        return render(options)
    except Exception as e:  # pylint: disable=broad-except
        return f'<p class="text-red-500">Plugin error: {e}</p>'
