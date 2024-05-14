"""
syncindex.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the SyncIndexCommand class for the Django MeiliSearch app.
"""

from typing import Type
from django.core.management.base import BaseCommand
from django.apps import apps
from django_meili._client import client as _client
from django_meili.models import IndexMixin

class Command(BaseCommand):
    help = "Syncs the MeiliSearch index for the given model."

    def add_arguments(self, parser):
        parser.add_argument("model", type=str, help="The model to sync the index for. This should be in the format <app_name>.<model_name>")

    def handle(self, *args, **options):
        Model = self._resolve_model(options["model"])
        models = [self._serialize(m) for m in Model.objects.all() if m.meili_filter()]
        if len(models) == 0:
            self.stdout.write(self.style.WARNING(f"No documents to sync for {options['model']}"))
            return
        task = _client.get_index(Model.__name__).add_documents(models)
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
