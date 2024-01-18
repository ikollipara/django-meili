from typing import Iterable, Literal, Optional
from django.db import models
from meilisearch import Client
from meilisearch.models.task import Task
from meilisearch.client import TaskInfo
from ._settings import _DjangoMeiliSettings

# Create your models here.

MEILISEARCH_SETTINGS = _DjangoMeiliSettings.from_settings()

_client = Client(
    f"http{'s' if MEILISEARCH_SETTINGS.https else ''}://{MEILISEARCH_SETTINGS.host}:{MEILISEARCH_SETTINGS.port}",
    MEILISEARCH_SETTINGS.master_key,
    timeout=MEILISEARCH_SETTINGS.timeout,
    client_agents=MEILISEARCH_SETTINGS.client_agents,
)

_current_indices = [i.uid for i in _client.get_indexes()["results"]]


def _await_for_task(task: TaskInfo) -> Task:
    task = _client.wait_for_task(task.task_uid)
    if task.status == "failed":
        raise Exception(task.error)
    return task


class IndexQuerySet:
    """
    IndexQuerySet is a wrapper around the MeiliSearch index
    to allow for easy searching and filtering. It mimics
    the QuerySet API, although it is not a subclass.
    """

    def __init__(self, model: type["IndexMixin"]):
        self.model = model
        self.index = _client.get_index(model.__name__)
        self.__offset = 0
        self.__limit = 20
        self.__filters: list[str] = []
        self.__sort: list[str] = []
        self.__matching_strategy: Literal["last", "all"] = "last"
        self.__attributes_to_search_on: list[str] = ["*"]

    def __repr__(self):
        return f"<IndexQuerySet for {self.model.__name__}>"

    def __str__(self):
        return f"IndexQuerySet for {self.model.__name__}"

    def __getitem__(self, index):
        if isinstance(index, slice):
            self.__offset = index.start
            self.__limit = index.stop
            return self
        else:
            raise TypeError("IndexQuerySet indices must be slices")

    def count(self):
        return self.index.get_stats().number_of_documents

    def order_by(self, *fields):
        for field in fields:
            if field.startswith("-"):
                self.__sort.append(f"{field[1:]}:desc")
            else:
                self.__sort.append(f"{field}:asc")
        return self

    def filter(self, **filters):
        for filter, value in filters.items():
            if "__" not in filter or "__exact" in filter:
                if (
                    value == ""
                    or (isinstance(value, list) and len(value) == 0)
                    or value == {}
                ):
                    self.__filters.append(f"{filter.split('_')[0]} IS EMPTY")
                elif value is None:
                    self.__filters.append(f"{filter.split('_')[0]} IS NULL")
                else:
                    self.__filters.append(
                        f"{filter.split('_')[0]} = '{value}'"
                        if isinstance(value, str)
                        else f"{filter.split('_')[0]} = {value}"
                    )
            elif "__gte" in filter:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"Cannot compare {type(value)} with int or float")
                self.__filters.append(f"{filter.split('_')[0]} >= {value}")
            elif "__gt" in filter:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"Cannot compare {type(value)} with int or float")
                self.__filters.append(f"{filter.split('_')[0]} > {value}")
            elif "__lte" in filter:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"Cannot compare {type(value)} with int or float")
                self.__filters.append(f"{filter.split('_')[0]} <= {value}")
            elif "__lt" in filter:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"Cannot compare {type(value)} with int or float")
                self.__filters.append(f"{filter.split('_')[0]} < {value}")
            elif "__in" in filter:
                if not isinstance(value, list):
                    raise TypeError(f"Cannot compare {type(value)} with list")
                self.__filters.append(f"{filter.split('_')[0]} IN {value}")
            elif "__range" in filter:
                if not isinstance(value, (range, list, tuple)):
                    raise TypeError(
                        f"Cannot compare {type(value)} with range, list or tuple"
                    )
                self.__filters.append(
                    f"{filter.split('_')[0]} {value[0]} TO {value[1]}"
                    if not isinstance(value, range)
                    else f"{filter.split('_')[0]} {value.start} TO {value.stop}"
                )
            elif "__exists" in filter:
                if not isinstance(value, bool):
                    raise TypeError(f"Cannot compare {type(value)} with bool")
                self.__filters.append(
                    f"{filter.split('_')[0]} {'NOT ' if not value else ''}EXISTS"
                )
            elif "__isnull" in filter:
                if not isinstance(value, bool):
                    raise TypeError(f"Cannot compare {type(value)} with bool")
                self.__filters.append(
                    f"{filter.split('_')[0]} {'NOT ' if not value else ''}IS NULL"
                )

        return self

    def matching_strategy(self, strategy: Literal["last", "all"]):
        self.__matching_strategy = strategy
        return self

    def attributes_to_search_on(self, *attributes):
        self.__attributes_to_search_on.append(*attributes)
        return self

    def search(self, q: str = ""):
        results = self.index.search(
            q,
            {
                "offset": self.__offset,
                "limit": self.__limit,
                "filter": self.__filters,
                "sort": self.__sort,
                "matchingStrategy": self.__matching_strategy,
                "attributesToSearchOn": self.__attributes_to_search_on,
            },
        )
        hits = results["hits"]
        return self.model.objects.filter(pk__in=[hit["id"] for hit in hits])


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

    displayed_fields: Iterable[str] = None
    searchable_fields: Iterable[str] = None
    filterable_fields: Iterable[str] = None

    def __init_subclass__(
        cls, *, index_name: Optional[str] = None, primary_key="pk"
    ) -> None:
        if index_name not in _current_indices:
            create_index_task = _client.create_index(
                cls.__name__ if not index_name else index_name,
                {"primaryKey": primary_key},
            )
            if MEILISEARCH_SETTINGS.sync:
                _await_for_task(create_index_task)

        if cls.displayed_fields:
            update = _client.index(cls.__name__).update_displayed_attributes(
                cls.displayed_fields
            )
            if MEILISEARCH_SETTINGS.sync:
                _await_for_task(update)

        if cls.searchable_fields:
            update = _client.index(cls.__name__).update_searchable_attributes(
                cls.searchable_fields
            )
            if MEILISEARCH_SETTINGS.sync:
                _await_for_task(update)
        if cls.filterable_fields:
            update = _client.index(cls.__name__).update_filterable_attributes(
                cls.filterable_fields
            )
            if MEILISEARCH_SETTINGS.sync:
                _await_for_task(update)

        cls.meilisearch = IndexQuerySet(cls)

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

    class Meta:
        abstract = True
