from django.apps import AppConfig


class DjangoMeiliConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_meili"

    def ready(self):
        """
        Register all IndexMixin subclasses with two signal methods,
        which will sync with meilisearch.
        """

        from django.db.models.signals import post_save, post_delete
        from django.conf import settings
        from .models import IndexMixin, _client

        def add_model(**kwargs):
            model: IndexMixin = kwargs["instance"]
            if model.meili_filter():
                serialized = model.meili_serialize()
                pk = model.pk if model._meilisearch['primary_key'] == 'pk' else model._meta.get_field(model._meilisearch['primary_key']).value_from_object(model)
                geo = model.meili_geo() if model._meilisearch['supports_geo'] else None
                task = _client.get_index(model._meilisearch['index_name']).add_documents(
                    [serialized | {"id": pk, "pk": model.pk} | ({"_geo": geo} if geo else {})]
                )
                if settings.DEBUG:
                    finished = _client.wait_for_task(task.task_uid)
                    if finished.status == "failed":
                        raise Exception(finished)

        def delete_model(**kwargs):
            model: IndexMixin = kwargs["instance"]
            if model.meili_filter():
                task = _client.get_index(model._meilisearch['index_name']).delete_document(
                    model._meta.get_field(model._meilisearch['primary_key']).value_from_object(model)
                )
                if settings.DEBUG:
                    finished = _client.wait_for_task(task.task_uid)
                    if finished.status == "failed":
                        raise Exception(finished)

        for model in IndexMixin.__subclasses__():
            post_save.connect(add_model, sender=model)
            post_delete.connect(delete_model, sender=model)
