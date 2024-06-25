"""
_client.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the MeiliSearch client for the Django MeiliSearch app.
"""

from typing import Self

from meilisearch.client import Client as _Client
from meilisearch.models.task import Task
from meilisearch.task import TaskInfo

from ._settings import _DjangoMeiliSettings


class Client:
    """MeiliSearch client for Django MeiliSearch.

    This class is a wrapper around the MeiliSearch client that provides
    a more Django-like interface for interacting with the MeiliSearch
    server.
    """

    def __init__(self, settings: _DjangoMeiliSettings):
        self.client = _Client(
            f"http{'s' if settings.https else ''}://{settings.host}:{settings.port}",
            settings.master_key,
            timeout=settings.timeout,
            client_agents=settings.client_agents,
        )
        self.is_sync = settings.sync
        self.tasks = []

    def flush_tasks(self):
        """Flush all currently stored tasks."""

        self.tasks = []

    def with_settings(
        self,
        index_name: str,
        displayed_fields: list[str] | None = None,
        searchable_fields: list[str] | None = None,
        filterable_fields: list[str] | None = None,
        sortable_fields: list[str] | None = None,
    ):
        """Create a new index with the given settings.

        This method creates an index all at once with the desired settings.

        Args:
            index_name (str): The name of the index to create.
            primary_key (str): The primary key for the index.
            displayed_fields (list[str] | None): The fields to display in search results.
            searchable_fields (list[str] | None): The fields to search on.
            filterable_fields (list[str] | None): The fields to filter on.
            sortable_fields (list[str] | None): The fields to sort on.

        Returns:
            Self: The client object.
        """

        self.tasks.append(
            self._handle_sync(
                self.client.index(index_name).update_settings(
                    {
                        "displayedAttributes": displayed_fields or ["*"],
                        "searchableAttributes": searchable_fields or ["*"],
                        "filterableAttributes": filterable_fields or [],
                        "sortableAttributes": sortable_fields or [],
                    }
                )
            )
        )
        return self

    def create_index(self, index_name: str, primary_key: str):
        """Create a new index with the given name and primary key.

        Args:
            index_name (str): The name of the index to create.
            primary_key (str): The primary key for the index.

        Returns:
            dict: The response from the MeiliSearch server.
        """
        if index_name not in [i.uid for i in self.get_indexes()]:
            self.tasks.append(
                self._handle_sync(
                    self.client.create_index(index_name, {"primaryKey": primary_key})
                )
            )
        return self

    def get_index(self, index_name: str):
        """Get an index by name.

        Args:
            index_name (str): The name of the index to get.

        Returns:
            Index: The index with the given name.
        """

        return self.client.index(index_name)

    def wait_for_task(self, task_uid: str) -> Task | TaskInfo:
        """Wait for a task to finish.

        Args:
            task_uid (str): The UID of the task to wait for.

        Returns:
            Task | TaskInfo: The task object.
        """

        task = self.client.wait_for_task(task_uid)
        return self._handle_sync(task)

    def get_indexes(self):
        """Get all indexes.

        Returns:
            list[Index]: A list of all indexes.
        """

        return self.client.get_indexes()["results"]

    def update_display(self, index_name: str, attributes: dict | None) -> Self:
        if attributes is None:
            return self
        self._handle_sync(
            self.client.index(index_name).update_displayed_attributes(attributes)
        )
        return self

    def update_searchable(self, index_name: str, attributes: dict | None) -> Self:
        if attributes is None:
            return self
        self._handle_sync(
            self.client.index(index_name).update_searchable_attributes(attributes)
        )
        return self

    def update_filterable(self, index_name: str, attributes: dict | None) -> Self:
        if attributes is None:
            return self
        self._handle_sync(
            self.client.index(index_name).update_filterable_attributes(attributes)
        )
        return self

    def update_sortable(self, index_name: str, attributes: dict | None) -> Self:
        if attributes is None:
            return self
        self._handle_sync(
            self.client.index(index_name).update_sortable_attributes(attributes)
        )
        return self

    def _handle_sync(self, task: TaskInfo) -> Task | TaskInfo:
        """Handle the sync task."""

        if self.is_sync:
            task = self.client.wait_for_task(task.task_uid)
            if task.status == "failed":
                raise Exception(task.error)
        return task


client = Client(_DjangoMeiliSettings.from_settings())
