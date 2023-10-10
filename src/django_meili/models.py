from typing import Optional
from django.db import models
from meilisearch import Client
from django.conf import settings

# Create your models here.

client = Client(
    f"http{'s' if settings.MEILISEARCH_HTTPS else ''}://{settings.MEILISEARCH_HOST}:{settings.MEILISEARCH_PORT}",
    settings.MEILISEARCH_MASTER_KEY,
)

_current_indices = [i.uid for i in client.get_indexes()["results"]]


class IndexMixin(models.Model):
    """
    Mixin to provide Meilisearch Index for the given model.

    ```python
    class Post(IndexMixin, models.Model):
        id = models.UUIDField()
        title = models.CharField(max_length=255)
        body = models.TextField()

        # Attributes to handle in Meilisearch
        displayed_fields = ("title", "body")
        searchable_fields = ("title", "body")
    ```

    ## Methods
    - meili_filter(self) -> bool
    - meili_serialize(self) -> dict[[str, Any]]
    """

    displayed_fields = None
    searchable_fields = None
    filterable_fields = None

    def __init_subclass__(
        cls, *, index_name: Optional[str] = None, primary_key="pk"
    ) -> None:
        if index_name not in _current_indices:
            client.create_index(
                cls.__name__ if not index_name else index_name,
                {"primaryKey": primary_key},
            )
        if cls.displayed_fields:
            client.index(cls.__name__).update_displayed_attributes(cls.displayed_fields)
        if cls.searchable_fields:
            client.index(cls.__name__).update_searchable_attributes(
                cls.searchable_fields
            )
        if cls.filterable_fields:
            client.index(cls.__name__).update_filterable_attributes(
                cls.filterable_fields
            )

    def meili_filter(self) -> bool:
        """
        A function to decide if the model should be added to meilisearch.

        For example, if a post model could be a draft and that draft shouldn't
        be in the search database, then this filter can make sure its not added.

        By default it just returns True.
        """

        return True

    def meili_serialize(self):
        """
        How to serialize the model to a dictionary to be used by meilisearch.

        By default uses django.core.serializers.serialize and json.loads
        """

        from django.core.serializers import serialize
        from json import loads

        return loads(
            serialize(
                "json",
                [self],
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
            )
        )[0]

    class Meta:
        abstract = True
