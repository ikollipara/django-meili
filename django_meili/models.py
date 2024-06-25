"""
models.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the models for the Django MeiliSearch app.
"""

from typing import Iterable, TypedDict

from django.conf import settings
from django.db import models
from meilisearch.models.task import TaskInfo

from ._client import client as _client
from .querysets import IndexQuerySet

# Create your models here.


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
    tasks: list[TaskInfo]


class IndexMixin(models.Model):
    """
    Mixin to provide Meilisearch Index for the given model.

    This mixin will create a Meilisearch index for the model and provide a
    queryset to interact with that index.

    To use this mixin, create a model that inherits from it and set the
    MeiliMeta class with the following attributes:
    - displayed_fields: The fields to display in search results.
    - searchable_fields: The fields to search on.
    - filterable_fields: The fields to filter on.
    - sortable_fields: The fields to sort on.
    - supports_geo: Whether the model supports geolocation.
    - index_name: The name of the index in Meilisearch.
    - primary_key: The primary key for the model.

    This mixin also defines a few methods that can be overridden:
    - meili_filter: A function to decide if the model should be added to meilisearch.
    - meili_serialize: How to serialize the model to a dictionary to be used by meilisearch.
    - meili_geo: Return the geo-location for the model. (If the model supports geolocation, else raise a ValueError.)

    Example:
    ```python
    from django.db import models
    from django_meili.models import IndexMixin

    class Post(IndexMixin, models.Model):
        title = models.CharField(max_length=255)
        body = models.TextField()

        class MeiliMeta:
            filterable_fields = ("title",)
            searchable_fields = ("id", "title", "body")
            displayed_fields = ("id", "title", "body")

        def __str__(self):
            return self.title
    ```
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

        if settings.MEILISEARCH.get("OFFLINE", False):
            cls._meilisearch = _Meili(
                primary_key=primary_key,
                index_name=index_name,
                displayed_fields=displayed_fields,
                searchable_fields=searchable_fields,
                filterable_fields=filterable_fields,
                sortable_fields=sortable_fields,
                supports_geo=supports_geo,
                tasks=[],
            )
        else:
            _client.create_index(index_name, primary_key).with_settings(
                index_name,
                displayed_fields,
                searchable_fields,
                filterable_fields,
                sortable_fields,
            )

        cls._meilisearch = _Meili(
            primary_key=primary_key,
            index_name=index_name,
            displayed_fields=displayed_fields,
            searchable_fields=searchable_fields,
            filterable_fields=filterable_fields,
            sortable_fields=sortable_fields,
            supports_geo=supports_geo,
            tasks=[task for task in _client.tasks],
        )
        _client.flush_tasks()

        cls.meilisearch = IndexQuerySet(cls)

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

        from json import loads

        from django.core.serializers import serialize

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
        """Return the geo-location for the model.

        If the model does not support geolocation, raise a ValueError.
        """

        raise ValueError("Model does not support geolocation")

    class Meta:
        abstract = True
