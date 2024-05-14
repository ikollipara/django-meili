from typing import Iterable, Literal, Optional, TypedDict
from django.db import models
from meilisearch.models.task import Task
from meilisearch.client import TaskInfo
from ._client import client as _client
from .querysets import IndexQuerySet

# Create your models here.


_current_indices = [i.uid for i in _client.get_indexes()]

class MeiliGeo(TypedDict):
    lat: float | str
    lng: float | str

class _Meili(TypedDict):
    primary_key: str
    index_name: str
    displayed_fields: Iterable[str] | None
    searchable_fields: Iterable[str] | None
    filterable_fields: Iterable[str] | None
    sortable_fields: Iterable[str] | None
    supports_geo: bool

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

    meilisearch: IndexQuerySet
    _meilisearch: _Meili

    class MeiliMeta:
        displayed_fields: Iterable[str] = None
        searchable_fields: Iterable[str] = None
        filterable_fields: Iterable[str] = None
        sortable_fields: Iterable[str] = None
        supports_geo: bool = False
        index_name: str = None
        primary_key: str = "pk"

    def __init_subclass__(cls) -> None:
        index_name = getattr(cls.MeiliMeta, "index_name", cls.__name__)
        primary_key = getattr(cls.MeiliMeta, "primary_key", "pk")
        displayed_fields = getattr(cls.MeiliMeta, "displayed_fields", None)
        searchable_fields = getattr(cls.MeiliMeta, "searchable_fields", None)
        filterable_fields = getattr(cls.MeiliMeta, "filterable_fields", None)
        sortable_fields = getattr(cls.MeiliMeta, "sortable_fields", None)
        supports_geo = getattr(cls.MeiliMeta, "supports_geo", False)

        if supports_geo:
            filterable_fields = ("_geo",) + (filterable_fields or ())
            sortable_fields = ("_geo",) + (sortable_fields or ())

        (_client
         .create_index(index_name, primary_key)
         .update_display(index_name, displayed_fields)
         .update_searchable(index_name, searchable_fields)
         .update_filterable(index_name, filterable_fields)
         .update_sortable(index_name, sortable_fields))

        cls.meilisearch = IndexQuerySet(cls)
        cls._meilisearch = _Meili(
            primary_key=primary_key,
            displayed_fields=displayed_fields,
            searchable_fields=searchable_fields,
            filterable_fields=filterable_fields,
            sortable_fields=sortable_fields,
            supports_geo=supports_geo,
            index_name=index_name,
        )

        super().__init_subclass__()

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

        serialized_model = loads(
            serialize(
                "json",
                [self],
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
            )
        )[0]

        return serialized_model["fields"]

    def meili_geo(self) -> MeiliGeo:
        """ Return the geo-location for the model.

        If the model does not support geolocation, raise a ValueError.
        """

        raise ValueError("Model does not support geolocation")

    class Meta:
        abstract = True
