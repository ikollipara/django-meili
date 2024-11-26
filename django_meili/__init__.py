"""Custom Django integration for MeiliSearch."""

__version__ = "0.0.8"

# Optional Support for DJP, a Django Plugin System
# https://djp.readthedocs.io/en/latest/index.html
try:
    import djp

    @djp.hookimpl
    def installed_apps():
        return ["django_meili"]

    @djp.hookimpl
    def settings(current_settings):
        current_settings["MEILISEARCH"] = current_settings.get("MEILISEARCH", {})

except (ImportError, ModuleNotFoundError):
    pass
