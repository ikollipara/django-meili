"""
apps.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the Django app configuration for the Django MeiliSearch app.
"""

from typing import TYPE_CHECKING, Iterable, TypedDict

from django.apps import AppConfig
from meilisearch.models.task import TaskInfo

if TYPE_CHECKING:
    from django_meili.models import IndexMixin


class DjangoMeiliConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_meili"

    def ready(self):
        """
        Register all IndexMixin subclasses with two signal methods,
        which will sync with meilisearch.
        """

        from django.conf import settings
        from django.db.models.signals import post_delete, post_save

        from ._client import client as _client
        from .models import IndexMixin

        def add_model(**kwargs):
            """Add a model to the MeiliSearch index.

            This function is called when a model is saved and adds the model to the MeiliSearch index.
            """

            model: IndexMixin = kwargs["instance"]
            if model.meili_filter():
                serialized = model.meili_serialize()

                # Since the primary key can be any field, we need to check if it is 'pk' or another field.
                # If its 'pk', we can just use the model.pk, otherwise we need to get the value from the field.
                pk = (
                    model.pk
                    if model._meilisearch["primary_key"] == "pk"
                    else model._meta.get_field(
                        model._meilisearch["primary_key"]
                    ).value_from_object(model)
                )

                # This bit makes sure that geo is only added if the model supports it.
                geo = model.meili_geo() if model._meilisearch["supports_geo"] else None
                if settings.MEILISEARCH.get("OFFLINE", False):
                    return
                task = _client.get_index(
                    model._meilisearch["index_name"]
                ).add_documents(
                    [
                        serialized
                        | {"id": pk, "pk": model.pk}
                        | ({"_geo": geo} if geo else {})
                    ]
                )
                if settings.DEBUG:
                    finished = _client.wait_for_task(task.task_uid)
                    if finished.status == "failed":
                        raise Exception(finished)

        def delete_model(**kwargs):
            """Delete a model from the MeiliSearch index.

            This function is called when a model is deleted and removes the model from the MeiliSearch index.
            """

            model: IndexMixin = kwargs["instance"]
            if model.meili_filter():

                # Since the primary key can be any field, we need to check if it is 'pk' or another field.
                # If its 'pk', we can just use the model.pk, otherwise we need to get the value from the field.
                pk = (
                    model._meta.get_field(
                        model._meilisearch["primary_key"]
                    ).value_from_object(model)
                    if model._meilisearch["primary_key"] != "pk"
                    else model.pk
                )

                if settings.MEILISEARCH.get("OFFLINE", False):
                    return
                task = _client.get_index(
                    model._meilisearch["index_name"]
                ).delete_document(pk)
                if settings.DEBUG:
                    finished = _client.wait_for_task(task.task_uid)
                    if finished.status == "failed":
                        raise Exception(finished)

        # This loop connects the add_model and delete_model functions to the post_save and post_delete signals of all
        # Its also why the `django_meili` app needs to be loaded before all the user apps in the `INSTALLED_APPS` list.
        for model in IndexMixin.__subclasses__():
            post_save.connect(add_model, sender=model)
            post_delete.connect(delete_model, sender=model)
