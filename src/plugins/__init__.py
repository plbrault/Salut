import importlib
import logging

from src.plugin import Plugin


def load_plugin_class(name):
    try:
        module = importlib.import_module(f"src.plugins.{name}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
                return obj
    except (ImportError, AttributeError):
        return None
    return None


def init_plugins_schemas(database):
    plugin_names = ["html", "rss", "weather", "calendar", "xkcd"]
    for name in plugin_names:
        plugin_class = load_plugin_class(name)
        if plugin_class is not None:
            plugin_class.init_schema(database)


def setup_card(card, database, scheduler, language="en"):
    plugin_name = card.get("plugin")
    options = card.get("options", {})
    plugin_class = load_plugin_class(plugin_name)
    if plugin_class is None:
        return None
    logger = logging.getLogger(f"src.plugins.{plugin_name}")
    logger.setLevel(logging.INFO)
    instance = plugin_class()
    instance.load_i18n(language)
    instance.setup(options, database, scheduler, logger)
    return instance


def render_card(card, instances):
    plugin_name = card.get("plugin")
    options = card.get("options", {})
    instance = instances.get(plugin_name)
    if instance is None:
        return f'<p class="text-red-500">Plugin "{plugin_name}" not found</p>'
    try:
        return instance.render(options)
    except Exception as e:  # pylint: disable=broad-except
        return f'<p class="text-red-500">Plugin error: {e}</p>'
