"""
clearindex.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the ClearIndexCommand class for the Django MeiliSearch app.
"""

from django.apps import apps
from django.core.management.base import BaseCommand

from django_meili._client import client as _client
from django_meili.models import IndexMixin


class Command(BaseCommand):
    help = "Clears the MeiliSearch index for the given model."

    def add_arguments(self, parser):
        parser.add_argument("model", type=str, help="The model to clear the index for.")

    def handle(self, *args, **options):
        model = self._resolve_model(options["model"])
        index = _client.get_index(model._meilisearch["index_name"])
        index.delete_all_documents()
        self.stdout.write(self.style.SUCCESS(f"Cleared index for {model}"))

    def _resolve_model(self, model: str) -> type[IndexMixin]:
        """
        Resolve the model from the given string.
        """
        try:
            Model = apps.get_model(model)
            if IndexMixin not in Model.__mro__:
                raise ValueError("Model does not inherit from IndexMixin")
        except LookupError as e:
            self.stdout.write(self.style.ERROR(f"Model not found: {model}"))
            exit(1)
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Invalid model: {model}"))
            exit(1)
        return Model
