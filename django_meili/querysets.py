"""
querysets.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the QuerySet classes for the Django MeiliSearch app.
"""

# Imports
from typing import NamedTuple, Literal, Self, TYPE_CHECKING
from ._client import _client

if TYPE_CHECKING:
    from .models import IndexMixin

class Radius(NamedTuple):
    """ A radius for a geosearch query. """
    lat: float | str
    lng: float | str
    radius: int

class BoundingBox(NamedTuple):
    """ A bounding box for a geosearch query. """
    top_right: tuple[float | str, float | str]
    bottom_left: tuple[float | str, float | str]

class Point(NamedTuple):
    """ A point for a geosearch query. """
    lat: float | str
    lng: float | str

class IndexQuerySet:
    """
    IndexQuerySet is a wrapper around the MeiliSearch index
    to allow for easy searching and filtering. It mimics
    the QuerySet API, although it is not a subclass.
    """

    def __init__(self, model: "IndexMixin"):
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

    def count(self) -> int:
        return self.index.get_stats().number_of_documents

    def order_by(self, *fields: str):
        for field in fields:
            geopoint = "_" if "geoPoint" in field else ""
            if field.startswith("-"):
                self.__sort.append(f"{geopoint}{field[1:]}:desc")
            else:
                self.__sort.append(f"{geopoint}{field}:asc")
        return self

    def filter(self, *geo_filters, **filters) -> Self:
        for geo_filter in geo_filters:
            if not self.model._meilisearch['supports_geo']:
                raise TypeError(
                    f"Model {self.model.__name__} does not support geo filters"
                )
            if not isinstance(geo_filter, (Radius, BoundingBox)):
                raise TypeError(
                    f"Unnamed Argument must be of type Radius or BoundingBox, not {type(geo_filter)}"
                )
            if isinstance(geo_filter, Radius):
                self.__filters.append(
                    f"_geoRadius({geo_filter.lat}, {geo_filter.lng}, {geo_filter.radius})"
                )
            elif isinstance(geo_filter, BoundingBox):
                self.__filters.append(
                    f"_geoBoundingBox([{geo_filter.top_right[0]}, {geo_filter.top_right[1]}], [{geo_filter.bottom_left[0]}, {geo_filter.bottom_left[1]}])"
                )
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
