"""
syncindex.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the SyncIndexCommand class for the Django MeiliSearch app.
"""

from typing import Type
from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from django_meili._client import client as _client
from django_meili.models import IndexMixin

DEFAULT_BATCH_SIZE = settings.MEILISEARCH.get("DEFAULT_BATCH_SIZE", 1000)


def batch_qs(qs, batch_size=DEFAULT_BATCH_SIZE):
    """
    Returns a (start, end, total, queryset) tuple for each batch in the given
    queryset.

    Usage:
        # Make sure to order your querset
        article_qs = Article.objects.order_by('id')
        for start, end, total, qs in batch_qs(article_qs):
            print "Now processing %s - %s of %s" % (start + 1, end, total)
            for article in qs:
                print article.body
    """
    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield qs[start:end]


class Command(BaseCommand):
    help = "Syncs the MeiliSearch index for the given model."

    def add_arguments(self, parser):
        parser.add_argument(
            "model",
            type=str,
            help="The model to sync the index for. This should be in the format <app_name>.<model_name>",
        )
        parser.add_argument(
            "--batch_size",
            action="store_true",
            default=DEFAULT_BATCH_SIZE,
            help="The batch size you want to import in (default: 1000)",
        )

    def handle(self, *args, **options):
        Model = self._resolve_model(options["model"])

        for qs in batch_qs(Model.objects.all(), options["batch_size"]):
            task = _client.get_index(Model.__name__).add_documents(
                [self._serialize(m) for m in qs if m.meili_filter()]
            )
        finished = _client.wait_for_task(task.task_uid)
        if finished.status == "failed":
            self.stderr.write(self.style.ERROR(finished.error))
            exit(1)
        self.stdout.write(self.style.SUCCESS(f"Synced index for {options['model']}"))

    def _serialize(self, model) -> dict:
        """
        Serialize the model instance into a dictionary.
        """

        serialized = model.meili_serialize()
        pk = model.pk
        return serialized | {"id": pk, "pk": pk}

    def _resolve_model(self, model: str):
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
