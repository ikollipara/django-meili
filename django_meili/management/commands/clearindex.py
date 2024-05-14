"""
clearindex.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the ClearIndexCommand class for the Django MeiliSearch app.
"""

from django.core.management.base import BaseCommand
from django_meili._client import client as _client


class Command(BaseCommand):
    help = "Clears the MeiliSearch index for the given model."

    def add_arguments(self, parser):
        parser.add_argument("model", type=str, help="The model to clear the index for.")

    def handle(self, *args, **options):
        model = options["model"]
        index = _client.get_index(model)
        index.delete_all_documents()
        self.stdout.write(self.style.SUCCESS(f"Cleared index for {model}"))
