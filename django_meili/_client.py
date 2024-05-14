"""
_client.py
Ian Kollipara <ian.kollipara@gmail.com>

This module contains the MeiliSearch client for the Django MeiliSearch app.
"""

from typing import Self
from meilisearch.client import Client as _Client
from meilisearch.task import TaskInfo
from meilisearch.models.task import Task
from ._settings import _DjangoMeiliSettings

MEILISEARCH_SETTINGS = _DjangoMeiliSettings.from_settings()

_client = _Client(
    f"http{'s' if MEILISEARCH_SETTINGS.https else ''}://{MEILISEARCH_SETTINGS.host}:{MEILISEARCH_SETTINGS.port}",
    MEILISEARCH_SETTINGS.master_key,
    timeout=MEILISEARCH_SETTINGS.timeout,
    client_agents=MEILISEARCH_SETTINGS.client_agents,
)

class Client:
    """ MeiliSearch client for Django MeiliSearch.

    This class is a wrapper around the MeiliSearch client that provides
    a more Django-like interface for interacting with the MeiliSearch
    server.
    """

    def __init__(self, client: _Client):
        self.client = client
        self.is_sync = MEILISEARCH_SETTINGS.sync

    def create_index(self, index_name: str, primary_key: str) -> Self:
        """ Create a new index with the given name and primary key.

        Args:
            index_name (str): The name of the index to create.
            primary_key (str): The primary key for the index.

        Returns:
            dict: The response from the MeiliSearch server.
        """
        if index_name not in self.get_indexes():
            self._handle_sync(self.client.create_index(index_name, {"primaryKey": primary_key}))
        return self

    def get_index(self, index_name: str):
        """ Get an index by name.

        Args:
            index_name (str): The name of the index to get.

        Returns:
            Index: The index with the given name.
        """

        return self.client.index(index_name)

    def wait_for_task(self, task_uid: str) -> Task | TaskInfo:
        """ Wait for a task to finish.

        Args:
            task_uid (str): The UID of the task to wait for.

        Returns:
            Task | TaskInfo: The task object.
        """

        task = self.client.wait_for_task(task_uid)
        return self._handle_sync(task)

    def get_indexes(self):
        """ Get all indexes.

        Returns:
            list[Index]: A list of all indexes.
        """

        return self.client.get_indexes()["results"]

    def update_display(self, index_name: str, attributes: dict | None) -> Self:
        if attributes is None:
            return self
        self._handle_sync(self.client.index(index_name).update_displayed_attributes(attributes))
        return self

    def update_searchable(self, index_name: str, attributes: dict | None) -> Self:
        if attributes is None:
            return self
        self._handle_sync(self.client.index(index_name).update_searchable_attributes(attributes))
        return self

    def update_filterable(self, index_name: str, attributes: dict | None) -> Self:
        if attributes is None:
            return self
        self._handle_sync(self.client.index(index_name).update_filterable_attributes(attributes))
        return self

    def update_sortable(self, index_name: str, attributes: dict | None) -> Self:
        if attributes is None:
            return self
        self._handle_sync(self.client.index(index_name).update_sortable_attributes(attributes))
        return self

    def _handle_sync(self, task: TaskInfo) -> Task | TaskInfo:
        """ Handle the sync task. """

        if self.is_sync:
            task = self.client.wait_for_task(task.task_uid)
            if task.status == "failed":
                raise Exception(task.error)
        return task

client = Client(_client)
