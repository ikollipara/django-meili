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

        def add_model(model):
            """
            A closure to create the model based on save.
            Is specified to the model.
            """

            def inner(**kwargs):
                if kwargs["instance"].meili_filter():
                    serialized = kwargs["instance"].meili_serialize()
                    pk = kwargs["instance"].pk
                    task = _client.get_index(model.__name__).add_documents(
                        [serialized | {"id": pk, "pk": pk}]
                    )

                    if settings.DEBUG:
                        finished = _client.wait_for_task(task.task_uid)
                        if finished.status == "failed":
                            raise Exception(finished)

            return inner

        def delete_model(model):
            """
            A closure to remove the model based on delete.
            Is specified to the model.
            """

            def inner(**kwargs):
                if kwargs["instance"].meili_filter():
                    task = _client.get_index(model.__name__).delete_document(
                        kwargs["instance"].pk
                    )
                    if settings.DEBUG:
                        finished = _client.wait_for_task(task.task_uid)
                        if finished.status == "failed":
                            raise Exception(finished)

            return inner

        for model in IndexMixin.__subclasses__():
            post_save.connect(add_model(model), model)
            post_delete.connect(delete_model(model), model)
